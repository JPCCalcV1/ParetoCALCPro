#################################################################################
# Routen_payment.py (absolut komplette Fassung, die du 1:1 reinkopieren kannst) #
#################################################################################
import os
import stripe
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify, session, current_app, render_template
from models.user import db, User
from models.payment_log import PaymentLog
from core.extensions import csrf

payment_bp = Blueprint("payment_bp", __name__)

# ENV-Variablen
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
stripe.api_key = STRIPE_SECRET_KEY

# Preiskonfiguration: 3 ABO-Preise
price_map = {
    "plus":     os.getenv("STRIPE_PRICE_PLUS", "price_plusXYZ"),     # monthly
    "premium":  os.getenv("STRIPE_PRICE_PREMIUM", "price_premXYZ"),  # monthly
    "extended": os.getenv("STRIPE_PRICE_EXTENDED", "price_extXYZ"),  # yearly
}

###################################################################
## Subscription-Checkout => /checkout-sub
##  => plus: 7 Tage Test
##  => premium: 0 Tage
##  => extended: 0 Tage (Jahresabo)
###################################################################
@payment_bp.route("/checkout-sub", methods=["POST"])
@csrf.exempt
def create_checkout_session_subscription():
    """
    Erzeugt ein Subscription-Checkout. Max. 1 ABO pro User:
      - Killt immer das alte Abo in user.stripe_subscription_id
      - if which_tier="plus" => 7 Tage Trial
      - if premium/extended => kein trial_period_days
    => Verhindert "minimum # of trial days=1" Stripe-Error
    => Extended enthält alle Premium-Features (Jahresabo).
    => Manuelle Teil-Refunds bei Upgrade via Stripe-Dashboard.
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data_in = request.get_json() or {}
    which_tier = data_in.get("which_tier", "plus")  # default plus

    price_id = price_map.get(which_tier)
    if not price_id:
        return jsonify({"error": f"No price for tier={which_tier}"}), 400

    # Trial nur bei plus
    if which_tier == "plus":
        trial_days = 7
    else:
        trial_days = 0

    try:
        current_app.logger.info(
            f"[checkout-sub] user_id={user_id}, tier={which_tier}, price_id={price_id}, trial={trial_days}"
        )

        # 1) Altes Abo killen, egal ob plus/premium/extended
        #    => So existiert nur 1 ABO pro User.
        if user.stripe_subscription_id:
            try:
                stripe.Subscription.delete(user.stripe_subscription_id)
                current_app.logger.info(
                    f"[checkout-sub] Killed old sub {user.stripe_subscription_id}"
                )
            except stripe.error.StripeError as e:
                current_app.logger.warning(f"Could not delete old sub: {e}")

            user.stripe_subscription_id = None
            db.session.commit()

        # 2) subscription_data
        if trial_days > 0:
            # plus => 7 Tage
            subscription_data = {
                "trial_period_days": trial_days,
                "metadata": {
                    "user_id": str(user.id),
                    "which_tier": which_tier,
                    "mode_used": "subscription"
                }
            }
        else:
            # premium/extended => 0 => wir lassen trial_period_days ganz weg
            subscription_data = {
                "metadata": {
                    "user_id": str(user.id),
                    "which_tier": which_tier,
                    "mode_used": "subscription"
                }
            }

        # 3) Neues ABO => checkout
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            subscription_data=subscription_data,
            success_url="https://paretocalc.com/pay/success",
            cancel_url="https://paretocalc.com/pay/cancel"
        )

        current_app.logger.info(
            f"[checkout-sub] Created session.id={checkout_session.id}, url={checkout_session.url}"
        )
        return jsonify({"checkout_url": checkout_session.url}), 200

    except stripe.error.StripeError as e:
        current_app.logger.exception(f"[checkout-sub] StripeError: {e}")
        return jsonify({"error": str(e)}), 500
    except Exception as ex:
        current_app.logger.exception(f"[checkout-sub] Exception: {ex}")
        return jsonify({"error": str(ex)}), 500

###################################################################
## checkout-oneoff => AUSKOMMENTIERT, wenn du Extended als ABO willst
###################################################################
# @payment_bp.route("/checkout-oneoff", methods=["POST"])
# @csrf.exempt
# def create_checkout_session_oneoff():
#     """
#     Nicht mehr gebraucht, wenn 'extended' ein Jahres-Abo ist.
#     Nur auskommentiert, falls du es später wieder reaktivieren willst.
#     """
#     return jsonify({"error":"Einmalzahlung nicht mehr angeboten"}), 400

###################################################################
## WEBHOOK:
## => checkout.session.completed => Tier setzen
## => invoice.paid => ABO-Verlängerung
## => invoice.payment_failed => "no_access"
###################################################################
@payment_bp.route("/webhook", methods=["POST"])
@csrf.exempt
def stripe_webhook():
    current_app.logger.info("[webhook] => Payment/Webhook invoked")

    payload = request.data
    sig_header = request.headers.get("Stripe-Signature","")
    if not STRIPE_WEBHOOK_SECRET:
        current_app.logger.error("[webhook] No STRIPE_WEBHOOK_SECRET set!")
        return jsonify({"error":"No webhook secret"}),500

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        current_app.logger.info(f"[webhook] Received event={event['type']}, id={event['id']}")
    except stripe.error.SignatureVerificationError as e:
        current_app.logger.warning(f"[webhook] Invalid signature: {e}")
        return jsonify({"error":"Invalid signature"}),400

    etype = event["type"]
    data_obj = event["data"]["object"]

    # PaymentLog => DB
    new_log = PaymentLog(
        event_id=event["id"],
        event_type=etype,
        raw_data=str(event),
        status="pending"
    )
    db.session.add(new_log)
    db.session.commit()

    def get_user_from_metadata(meta):
        uid_str = meta.get("user_id")
        if not uid_str:
            return None
        return User.query.get(int(uid_str))

    ########################################
    ## 1) checkout.session.completed
    ########################################
    if etype == "checkout.session.completed":
        sub_id = data_obj.get("subscription")  # z. B. "sub_ABC123"
        if not sub_id:
            current_app.logger.warning("[webhook:session.completed] No subscription => abort")
            return jsonify({"status": "ok"}), 200

        # Subscription-Objekt abrufen, dort stehen i. d. R. die metadata
        sub_obj = stripe.Subscription.retrieve(sub_id)
        meta = sub_obj.get("metadata", {})
        which_tier = meta.get("which_tier", "plus")
        mode_used = meta.get("mode_used", "subscription")

        # user abfragen
        user = get_user_from_metadata(meta)
        if not user:
            current_app.logger.warning("[webhook:session.completed] No user => abort")
            return jsonify({"status": "ok"}), 200

        old_tier = user.license_tier

        if mode_used == "subscription":
            user.license_tier = which_tier
            user.stripe_subscription_id = sub_id
        elif mode_used == "payment":
            user.license_tier = which_tier
            user.license_expiry = datetime.now() + timedelta(days=365)
        else:
            current_app.logger.warning(f"[webhook:session.completed] unknown mode={mode_used}, ignoring")

        db.session.commit()
        new_log.user_id = user.id
        new_log.status = "completed"
        db.session.commit()

        current_app.logger.info(
            f"[webhook:session.completed] user={user.email}, old_tier={old_tier} => {which_tier}, "
            f"expiry={user.license_expiry}"
        )

    ########################################
    ## 2) invoice.paid => ABO-Verlängerung
    ########################################
    elif etype == "invoice.paid":
        sub_id = data_obj.get("subscription")
        if sub_id:
            sub_obj = stripe.Subscription.retrieve(sub_id)
            meta = sub_obj.get("metadata", {})
            user = get_user_from_metadata(meta)
            which_tier = meta.get("which_tier", "plus")

            if user:
                old_tier = user.license_tier

                # ABO => +30 Tage für plus/premium, +365 für extended
                if which_tier in ["plus","premium"]:
                    extend_days = 30
                elif which_tier == "extended":
                    extend_days = 365
                else:
                    extend_days = 30  # fallback

                # Verlängern
                if not user.license_expiry or user.license_expiry < datetime.now():
                    user.license_expiry = datetime.now() + timedelta(days=extend_days)
                else:
                    user.license_expiry += timedelta(days=extend_days)

                user.license_tier = which_tier
                if not user.stripe_subscription_id:
                    user.stripe_subscription_id = sub_id

                db.session.commit()
                new_log.user_id = user.id
                new_log.status = "paid"
                db.session.commit()

                current_app.logger.info(
                    f"[webhook:invoice.paid] user={user.email}, {old_tier} => {which_tier}, "
                    f"expiry={user.license_expiry}"
                )
        else:
            current_app.logger.warning("[webhook:invoice.paid] No subscription => ignoring")

    ########################################
    ## 3) invoice.payment_failed => ABO-Fehlschlag
    ########################################
    elif etype == "invoice.payment_failed":
        sub_id = data_obj.get("subscription")
        if sub_id:
            sub_obj = stripe.Subscription.retrieve(sub_id)
            meta = sub_obj.get("metadata", {})
            user = get_user_from_metadata(meta)

            if user:
                old_tier = user.license_tier
                user.license_tier = "no_access"
                user.license_expiry = None
                db.session.commit()

                new_log.user_id = user.id
                new_log.status = "failed"
                db.session.commit()

                current_app.logger.info(
                    f"[webhook:payment_failed] user={user.email}, {old_tier} => no_access"
                )

    else:
        current_app.logger.info(f"[webhook] Unhandled event type: {etype}")

    return jsonify({"status":"ok"}), 200


###################################################################
## success/cancel => einfache Templates
###################################################################
@payment_bp.route("/success", methods=["GET"])
def payment_success():
    return render_template("pay/payment_success.html")

@payment_bp.route("/cancel", methods=["GET"])
def payment_cancel():
    return render_template("pay/payment_cancel.html")

@payment_bp.route("/test", methods=["GET"])
def test_payment_route():
    return jsonify({"message":"Payment blueprint with TRIAL logic ready"}),200

""" END OF FILE: routes_payment.py """