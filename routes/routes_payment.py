""" START OF FILE: routes_payment.py (Best-of) """

import os
import stripe
from flask import Blueprint, request, jsonify, session, current_app, render_template
from datetime import datetime, timedelta

# Models
from models.user import db, User
from models.payment_log import PaymentLog

# Falls du global CSRF verwendest:
from core.extensions import csrf

# Falls du Mails verschicken willst:
# from helpers.sendgrid_helper import send_email

payment_bp = Blueprint("payment_bp", __name__)

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
stripe.api_key = STRIPE_SECRET_KEY

# Price-Map: Hier trägst du deine Stripe-Preis-IDs ein (OneOff vs. Abo).
price_map = {
    "plus":     os.getenv("STRIPE_PRICE_PLUS", "price_plusXYZ"),
    "premium":  os.getenv("STRIPE_PRICE_PREMIUM", "price_premXYZ"),
    "extended": os.getenv("STRIPE_PRICE_EXTENDED", "price_extXYZ"),
}

# ------------------------------------
#   Einmalzahlung => /checkout-oneoff
# ------------------------------------
@payment_bp.route("/checkout-oneoff", methods=["POST"])
@csrf.exempt
def create_checkout_session_oneoff():
    """
    Beispiel: User zahlt EINMALIG => 365 Tage
    JSON-Eingabe: {"which_tier":"extended"}
    Achtung: Du brauchst in Stripe einen "one_time"-Preis
    für 'extended', wenn du das hier nutzt.
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error":"Not logged in"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error":"User not found"}), 404

    data_in = request.get_json() or {}
    which_tier = data_in.get("which_tier","extended")
    price_id = price_map.get(which_tier)
    if not price_id:
        return jsonify({"error":f"No price for {which_tier}"}), 400

    try:
        # mode="payment" => Einmalzahlung
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity":1}],
            mode="payment",
            success_url="https://www.jpccalc.de/pay/success",
            cancel_url="https://www.jpccalc.de/pay/cancel",
            metadata={
                "user_id": str(user.id),
                "which_tier": which_tier,
                "mode_used": "oneoff"  # optionales Debug-Feld
            }
        )
        return jsonify({"checkout_url": checkout_session.url}), 200
    except stripe.error.StripeError as se:
        current_app.logger.error("StripeError in checkout-oneoff: %s", str(se))
        return jsonify({"error": str(se)}), 500
    except Exception as ex:
        current_app.logger.error("Exception in checkout-oneoff: %s", str(ex))
        return jsonify({"error": str(ex)}), 500


# ------------------------------------
#   Abo => /checkout-sub (Subscription)
# ------------------------------------
@payment_bp.route("/checkout-sub", methods=["POST"])
@csrf.exempt
def create_checkout_session_subscription():
    """
    User bucht ein ABO => z. B. +30 Tage Verlängerung bei invoice.paid
    JSON-Eingabe: {"which_tier":"plus" | "premium" | "extended"}
    => subscription_data => metadata => user_id
    => trial_period_days => 7
    Achtung: Du brauchst einen "recurring"-Preis bei Stripe,
    wenn du "mode='subscription'" nutzt!
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error":"Not logged in"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error":"User not found"}), 404

    data_in = request.get_json() or {}
    which_tier = data_in.get("which_tier","plus")
    price_id = price_map.get(which_tier)
    if not price_id:
        return jsonify({"error":f"No price for {which_tier}"}), 400

    try:
        # mode="subscription"
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity":1}],
            mode="subscription",
            subscription_data={
                "trial_period_days": 7,  # Testphase, optional
                "metadata": {
                    "user_id": str(user.id),
                    "which_tier": which_tier,
                    "mode_used": "subscription"
                }
            },
            success_url="https://www.jpccalc.de/pay/success",
            cancel_url="https://www.jpccalc.de/pay/cancel"
        )
        return jsonify({"checkout_url": checkout_session.url}), 200
    except stripe.error.StripeError as se:
        current_app.logger.error("StripeError in checkout-sub: %s", str(se))
        return jsonify({"error": str(se)}), 500
    except Exception as ex:
        current_app.logger.error("Exception in checkout-sub: %s", str(ex))
        return jsonify({"error": str(ex)}), 500


# ------------------------------------
#    Webhook => /webhook
# ------------------------------------
@payment_bp.route("/webhook", methods=["POST"])
@csrf.exempt
def stripe_webhook():
    """
    Hier verarbeitet dein Server die Stripe-Ereignisse:
    checkout.session.completed, invoice.paid, invoice.payment_failed, etc.
    """
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature","")

    if not STRIPE_WEBHOOK_SECRET:
        current_app.logger.error("No STRIPE_WEBHOOK_SECRET set!")
        return jsonify({"error":"No webhook secret"}), 500

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError as e:
        current_app.logger.error("Signature error: %s", str(e))
        return jsonify({"error":"Invalid signature"}), 400

    etype = event["type"]
    data_obj = event["data"]["object"]

    # Log in PaymentLog
    new_log = PaymentLog(
        user_id=None,
        event_id=event["id"],
        event_type=etype,
        raw_data=str(event),
        status="pending"
    )
    db.session.add(new_log)
    db.session.commit()

    def get_user_from_metadata(meta):
        uid = meta.get("user_id")
        if not uid:
            return None
        return User.query.get(int(uid))

    # -----------------------------------
    # A) CHECKOUT.SESSION.COMPLETED => initialer Kauf
    # -----------------------------------
    if etype == "checkout.session.completed":
        meta = data_obj.get("metadata", {})
        user = get_user_from_metadata(meta)
        mode = data_obj.get("mode")  # "payment" (oneoff) or "subscription"
        which_tier = meta.get("which_tier", "extended")

        if user:
            if mode == "payment":
                # => Einmalzahlung => +365 Tage
                user.license_tier = which_tier
                user.license_expiry = datetime.now() + timedelta(days=365)
            elif mode == "subscription":
                # ABO => +7 Tage (Trial).
                # Verlängerung später via "invoice.paid"
                user.license_tier = which_tier
                user.license_expiry = datetime.now() + timedelta(days=7)
            db.session.commit()

            new_log.user_id = user.id
            new_log.status = "completed"
            db.session.commit()

    # -----------------------------------
    # B) INVOICE.PAID => Verlängerung ABO
    # -----------------------------------
    elif etype == "invoice.paid":
        sub_id = data_obj.get("subscription")
        if sub_id:
            sub_obj = stripe.Subscription.retrieve(sub_id)
            meta = sub_obj.get("metadata", {})
            user = get_user_from_metadata(meta)
            which_tier = meta.get("which_tier","plus")

            if user:
                # Standard ABO => +30 Tage
                # Du könntest bei extended += 365 Tage machen
                if not user.license_expiry or user.license_expiry < datetime.now():
                    user.license_expiry = datetime.now() + timedelta(days=30)
                else:
                    user.license_expiry += timedelta(days=30)
                user.license_tier = which_tier
                db.session.commit()

                new_log.user_id = user.id
                new_log.status = "paid"
                db.session.commit()

    # -----------------------------------
    # C) INVOICE.PAYMENT_FAILED => ABO-Fehlschlag
    # -----------------------------------
    elif etype == "invoice.payment_failed":
        sub_id = data_obj.get("subscription")
        if sub_id:
            sub_obj = stripe.Subscription.retrieve(sub_id)
            meta = sub_obj.get("metadata", {})
            user = get_user_from_metadata(meta)

            if user:
                user.license_tier = "no_access"
                user.license_expiry = None
                db.session.commit()

                # Falls du eine E-Mail schicken willst:
                # try:
                #     send_email(
                #         user.email,
                #         "Payment fehlgeschlagen",
                #         "Deine Abo-Zahlung schlug fehl.",
                #         "<p>Bitte Zahlungsmethode aktualisieren.</p>"
                #     )
                # except Exception as mail_ex:
                #     current_app.logger.exception(f"SendGrid error: {mail_ex}")

                new_log.user_id = user.id
                new_log.status = "failed"
                db.session.commit()

    else:
        # current_app.logger.info(f"Ignored event type: {etype}")
        pass

    return jsonify({"status": "ok"}), 200


@payment_bp.route("/success", methods=["GET"])
def payment_success():
    """
    Zeigt die 'Zahlung erfolgreich'-Seite (pay/payment_success.html).
    """
    return render_template("pay/payment_success.html")


@payment_bp.route("/cancel", methods=["GET"])
def payment_cancel():
    """
    Zeigt die 'Zahlung abgebrochen'-Seite (pay/payment_cancel.html).
    """
    return render_template("pay/payment_cancel.html")


# Debug: optional
@payment_bp.route("/test", methods=["GET"])
def test_payment_route():
    """
    Einfache Test-Route, um zu checken, ob payment_bp läuft.
    """
    return jsonify({"message":"Payment blueprint is running!"}),200

""" END OF FILE: routes_payment.py (Best-of) """
