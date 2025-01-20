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

# Preiskonfiguration
price_map = {
    "plus":     os.getenv("STRIPE_PRICE_PLUS", "price_plusXYZ"),
    "premium":  os.getenv("STRIPE_PRICE_PREMIUM", "price_premXYZ"),
    "extended": os.getenv("STRIPE_PRICE_EXTENDED", "price_extXYZ"),
}

###################################################################
## Routen: /checkout-sub => ABO (Trial), /checkout-oneoff => Einmal
###################################################################
@payment_bp.route("/checkout-sub", methods=["POST"])
@csrf.exempt
def create_checkout_session_subscription():
    """
    Erzeugt eine Subscription-Checkout-Session mit z.B. 7-Tage-Trial.
    => checkout.session.completed => license_tier = which_tier, expiry = +7
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error":"User not found"}), 404

    data_in = request.get_json() or {}
    which_tier = data_in.get("which_tier","plus")

    price_id = price_map.get(which_tier)
    if not price_id:
        return jsonify({"error": f"No price for tier={which_tier}"}), 400

    try:
        current_app.logger.info(f"[checkout-sub] user_id={user_id}, tier={which_tier}, price_id={price_id}")
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity":1}],
            mode="subscription",
            subscription_data={
                "trial_period_days": 7,
                "metadata": {
                    "user_id": str(user.id),
                    "which_tier": which_tier,
                    "mode_used": "subscription"
                }
            },
            success_url="https://jpccalc.de/pay/success",
            cancel_url="https://jpccalc.de/pay/cancel"
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


@payment_bp.route("/checkout-oneoff", methods=["POST"])
@csrf.exempt
def create_checkout_session_oneoff():
    """
    Einmalzahlung => user => +365 Tage "extended" / "premium"
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error":"Not logged in"}),401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error":"User not found"}),404

    data_in = request.get_json() or {}
    which_tier = data_in.get("which_tier","extended")

    price_id = price_map.get(which_tier)
    if not price_id:
        return jsonify({"error": f"No price for tier={which_tier}"}), 400

    try:
        current_app.logger.info(f"[checkout-oneoff] user_id={user_id}, tier={which_tier}, price_id={price_id}")
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity":1}],
            mode="payment",
            success_url="https://www.jpccalc.de/pay/success",
            cancel_url="https://www.jpccalc.de/pay/cancel",
            metadata={
                "user_id": str(user.id),
                "which_tier": which_tier,
                "mode_used": "payment"
            }
        )
        current_app.logger.info(f"[checkout-oneoff] Created session.id={checkout_session.id}, url={checkout_session.url}")
        return jsonify({"checkout_url": checkout_session.url}),200

    except stripe.error.StripeError as se:
        current_app.logger.exception(f"[checkout-oneoff] StripeError: {se}")
        return jsonify({"error": str(se)}),500
    except Exception as ex:
        current_app.logger.exception(f"[checkout-oneoff] Exception: {ex}")
        return jsonify({"error": str(ex)}),500


##############################################################
## WEBHOOK: Hier "checkout.session.completed" => +7 Tage Trial
##          invoice.paid => +30 Tage Verlängerung
##          invoice.payment_failed => "no_access"
##############################################################
from flask import Blueprint, request, jsonify, session, current_app, render_template
from datetime import datetime, timedelta
import stripe
import os

from models.user import db, User
from models.payment_log import PaymentLog
from core.extensions import csrf

payment_bp = Blueprint("payment_bp", __name__)

# ENV-Variablen / Konfiguration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
stripe.api_key = STRIPE_SECRET_KEY

@payment_bp.route("/webhook", methods=["POST"])
@csrf.exempt
def stripe_webhook():
    """
    Stripe-Webhook: verarbeitet Events wie
    - checkout.session.completed
    - invoice.paid
    - invoice.payment_failed
    etc.

    Erweiterung:
    - Speichert ggf. stripe_subscription_id im User, falls ABO
    - optional SendGrid-E-Mail bei PaymentFailed oder so
    """
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

    # Hilfsfunktion: user_id => DB
    def get_user_from_metadata(meta):
        uid_str = meta.get("user_id")
        if not uid_str:
            return None
        return User.query.get(int(uid_str))

    ########################################
    ## 1) checkout.session.completed
    ########################################
    if etype == "checkout.session.completed":
        meta = data_obj.get("metadata", {})
        which_tier = meta.get("which_tier", "plus")
        mode_used = meta.get("mode_used", "payment")  # "subscription" oder "payment"

        user = get_user_from_metadata(meta)
        if not user:
            current_app.logger.warning("[webhook:session.completed] No user => abort")
            return jsonify({"status":"ok"}), 200

        old_tier = user.license_tier

        # ABO => +7 Tage Trial
        if mode_used == "subscription":
            user.license_tier = which_tier
            user.license_expiry = datetime.now() + timedelta(days=7)
            # neu: subscription id (ggf. expand in Session.create)
            sub_id = data_obj.get("subscription")
            if sub_id:   # falls Stripe es hier liefert
                user.stripe_subscription_id = sub_id

        # OneOff => +365
        elif mode_used == "payment":
            user.license_tier = which_tier
            user.license_expiry = datetime.now() + timedelta(days=365)
            # OneOff => kein subscription_id
        else:
            current_app.logger.warning(
                f"[webhook:session.completed] unknown mode={mode_used}, ignoring"
            )

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
            # hole subscription-Objekt
            sub_obj = stripe.Subscription.retrieve(sub_id)
            meta = sub_obj.get("metadata", {})
            user = get_user_from_metadata(meta)
            which_tier = meta.get("which_tier", "plus")

            if user:
                old_tier = user.license_tier
                # ABO => +30 Tage
                if not user.license_expiry or user.license_expiry < datetime.now():
                    user.license_expiry = datetime.now() + timedelta(days=30)
                else:
                    user.license_expiry += timedelta(days=30)
                user.license_tier = which_tier

                # optional: ensure local user.stripe_subscription_id is stored
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
                # optional: user.stripe_subscription_id = None
                db.session.commit()

                new_log.user_id = user.id
                new_log.status = "failed"
                db.session.commit()

                current_app.logger.info(
                    f"[webhook:payment_failed] user={user.email}, {old_tier} => no_access"
                )

                # Optional: Send E-Mail via SendGrid:
                # from helpers.sendgrid_helper import send_email
                # send_email(
                #    user.email,
                #    subject="Zahlung fehlgeschlagen",
                #    text_content="Deine Abo-Zahlung schlug fehl. Wir haben deine Lizenz ausgesetzt...",
                #    html_content="<p>Deine Abo-Zahlung schlug fehl...</p>"
                # )
        else:
            current_app.logger.warning("[webhook:payment_failed] No sub_id => ignoring")

    else:
        current_app.logger.info(f"[webhook] Unhandled event type: {etype}")

    return jsonify({"status":"ok"}),200


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

""" END OF FILE: routes_payment.py - FINAL TRIAL LOGIC """