# routes/routes_payment.py
import os
import stripe
from flask import Blueprint, request, jsonify, session
from datetime import datetime, timedelta

from models.user import db, User
from models.payment_log import PaymentLog
from core.extensions import csrf

# Für Payment-Fail E-Mail (falls du SendGrid o.Ä. nutzt)
# => Stelle sicher, dass du in helpers/sendgrid_helper.py ein send_email(...) hast.
from helpers.sendgrid_helper import send_email

payment_bp = Blueprint("payment_bp", __name__)

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
stripe.api_key = STRIPE_SECRET_KEY

# Deine Price-Map – anpassen an deine Stripe-Preise
price_map = {
    "test":     os.getenv("STRIPE_PRICE_TEST", "price_testXYZ"),
    "plus":     os.getenv("STRIPE_PRICE_PLUS", "price_plusXYZ"),
    "premium":  os.getenv("STRIPE_PRICE_PREMIUM", "price_premXYZ"),
    "extended": os.getenv("STRIPE_PRICE_EXTENDED", "price_extXYZ"),
}

# ---------------------------------------------------------
# V1-ROUTE: Falls du EINE Payment-Route (OneOff) behalten willst
# ---------------------------------------------------------
@payment_bp.route("/create-checkout-session", methods=["POST"])
def create_checkout_session():
    """
    V1: Falls du nur EINE Art Payment hast (OneOff).
    Bleibt kompatibel, falls dein Frontend schon /create-checkout-session aufruft.
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data_in = request.get_json() or {}
    which_tier = data_in.get("which_tier", "extended")

    price_id = price_map.get(which_tier)
    if not price_id:
        return jsonify({"error": f"No price for {which_tier}"}), 400

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="payment",
            success_url="https://yourdomain.com/pay/success",
            cancel_url="https://yourdomain.com/pay/cancel",
            metadata={
                "user_id": user.id,
                "which_tier": which_tier
            }
        )
        return jsonify({"checkout_url": checkout_session.url}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------
# NEU (V2): Subscription – 7 Tage Trial, dann invoice.paid => +30 Tage
# ---------------------------------------------------------
@payment_bp.route("/create-checkout-session-subscription", methods=["POST"])
def create_checkout_session_subscription():
    """
    Subscription: 7 Tage Trial -> invoice.paid => +30 Tage je Abrechnungszyklus.
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data_in = request.get_json() or {}
    which_tier = data_in.get("which_tier", "plus")

    try:
        price_id = price_map.get(which_tier)
        if not price_id:
            return jsonify({"error": f"No Price-ID for {which_tier}"}), 400

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            subscription_data={
                "trial_period_days": 7
            },
            success_url="https://yourdomain.com/pay/success",
            cancel_url="https://yourdomain.com/pay/cancel",
            metadata={
                "user_id": user.id,
                "which_tier": which_tier
            }
        )
        return jsonify({"checkout_url": checkout_session.url}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------
# NEU (V2): OneOff – 365 Tage, separate Route
# ---------------------------------------------------------
@payment_bp.route("/create-checkout-session-oneoff", methods=["POST"])
def create_checkout_session_oneoff():
    """
    OneOff: 365 Tage.
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data_in = request.get_json() or {}
    which_tier = data_in.get("which_tier", "extended")

    try:
        price_id = price_map.get(which_tier)
        if not price_id:
            return jsonify({"error": f"No price for {which_tier}"}), 400

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="payment",
            success_url="https://yourdomain.com/pay/success",
            cancel_url="https://yourdomain.com/pay/cancel",
            metadata={
                "user_id": user.id,
                "which_tier": which_tier
            }
        )
        return jsonify({"checkout_url": checkout_session.url}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------
# WEBHOOK – Nur hier CSRF-Exempt
# ---------------------------------------------------------
@payment_bp.route("/webhook", methods=["POST"])
@csrf.exempt  # Nur hier exempt, da Stripe JSON sendet ohne CSRF
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature", "")
    if not STRIPE_WEBHOOK_SECRET:
        return jsonify({"error": "No webhook secret"}), 500

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError as e:
        print("Signature error:", e)
        return jsonify({"error": "Invalid signature"}), 400

    # PaymentLog anlegen
    new_log = PaymentLog(
        user_id=None,
        event_id=event["id"],
        event_type=event["type"],
        raw_data=str(event),
        status="pending"  # NEU: Startet mit "pending"
    )
    db.session.add(new_log)
    db.session.commit()

    etype = event["type"]
    data_obj = event["data"]["object"]

    # -----------------------------------------------------
    # checkout.session.completed =>
    # - Mode "subscription": 7 Tage
    # - Mode "payment": 365 Tage
    # -----------------------------------------------------
    if etype == "checkout.session.completed":
        user_id = data_obj.get("metadata", {}).get("user_id")
        which_tier = data_obj.get("metadata", {}).get("which_tier", "extended")
        mode = data_obj.get("mode")

        if user_id:
            u = User.query.get(user_id)
            if u:
                if mode == "subscription":
                    u.license_tier = which_tier
                    u.license_expiry = datetime.now() + timedelta(days=7)
                    db.session.commit()
                elif mode == "payment":
                    u.license_tier = which_tier
                    u.license_expiry = datetime.now() + timedelta(days=365)
                    db.session.commit()

        # Payment completed => PaymentLog status = "completed"
        new_log.status = "completed"
        db.session.commit()

    # -----------------------------------------------------
    # invoice.paid => z.B. Subscription Renewal => +30 Tage
    # -----------------------------------------------------
    elif etype == "invoice.paid":
        sub_id = data_obj.get("subscription")
        if sub_id:
            sub_obj = stripe.Subscription.retrieve(sub_id)
            user_id = sub_obj.get("metadata", {}).get("user_id")
            which_tier = sub_obj.get("metadata", {}).get("which_tier", "plus")

            if user_id:
                u = User.query.get(user_id)
                if u:
                    # Falls license_expiry abgelaufen -> setze ab heute +30
                    # sonst hänge 30 Tage dran
                    if not u.license_expiry or u.license_expiry < datetime.now():
                        u.license_expiry = datetime.now() + timedelta(days=30)
                    else:
                        u.license_expiry += timedelta(days=30)
                    u.license_tier = which_tier
                    db.session.commit()

        new_log.status = "paid"
        db.session.commit()

    # -----------------------------------------------------
    # invoice.payment_failed => Access entziehen + E-Mail
    # -----------------------------------------------------
    elif etype == "invoice.payment_failed":
        sub_id = data_obj.get("subscription")
        if sub_id:
            sub_obj = stripe.Subscription.retrieve(sub_id)
            user_id = sub_obj.get("metadata", {}).get("user_id")
            if user_id:
                u = User.query.get(user_id)
                if u:
                    # Lizenz wegnehmen
                    u.license_tier = "no_access"
                    u.license_expiry = None
                    db.session.commit()

                    # => Sende E-Mail (Try/Catch, damit es den Workflow nicht stoppt)
                    try:
                        send_email(
                            to=u.email,
                            subject="Payment failed",
                            plain_body="Deine Zahlung schlug fehl! Bitte Zahlungsmethode aktualisieren.",
                            html_body="<p>Zahlung fehlgeschlagen. Bitte updaten!</p>"
                        )
                    except Exception as mail_ex:
                        print("SendGrid error:", mail_ex)

        new_log.status = "failed"
        db.session.commit()

    return jsonify({"status": "ok"}), 200