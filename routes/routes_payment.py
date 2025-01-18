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
        app.logger.debug(f"Price-ID für {which_tier}: {price_id}")  # Log hinzufügen
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
@csrf.exempt
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature", "")

    # 1) Check Webhook-Secret
    if not STRIPE_WEBHOOK_SECRET:
        print("[Webhook] Error: No STRIPE_WEBHOOK_SECRET configured.")
        return jsonify({"error": "No webhook secret"}), 500

    # 2) Signaturprüfung
    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError as e:
        print("[Webhook] Signature error:", e)
        return jsonify({"error": "Invalid signature"}), 400

    etype = event["type"]
    data_obj = event["data"]["object"]
    print(f"[Webhook] Received event type: {etype}")  # Debug-Log

    # 3) PaymentLog anlegen
    new_log = PaymentLog(
        user_id=None,
        event_id=event["id"],
        event_type=etype,
        raw_data=str(event),
        status="pending"
    )
    db.session.add(new_log)
    db.session.commit()

    # -- Hilfsfunktion: Safely get user-Objekt (abbrechen, wenn None)
    def get_user_from_metadata(meta_dict):
        """Liest 'user_id' aus metadaten und gibt User-Objekt zurück (oder None)."""
        uid = meta_dict.get("user_id")
        if not uid:
            print("[Webhook] No user_id in metadata => ignoring.")
            return None
        user = User.query.get(uid)
        if not user:
            print(f"[Webhook] User with id={uid} not found in DB.")
        return user

    # 4) Verzweige nach event type
    if etype == "checkout.session.completed":
        which_tier = data_obj.get("metadata", {}).get("which_tier", "extended")
        mode = data_obj.get("mode")
        user = get_user_from_metadata(data_obj.get("metadata", {}))

        if user:
            print(f"[Webhook] checkout.session.completed for user={user.email}, tier={which_tier}, mode={mode}")
            if mode == "subscription":
                user.license_tier = which_tier
                user.license_expiry = datetime.now() + timedelta(days=7)
            elif mode == "payment":
                user.license_tier = which_tier
                user.license_expiry = datetime.now() + timedelta(days=365)
            db.session.commit()
            new_log.status = "completed"
            db.session.commit()
        else:
            print("[Webhook] Warning: No valid user found for checkout.session.completed")

    elif etype == "invoice.paid":
        sub_id = data_obj.get("subscription")
        if sub_id:
            sub_obj = stripe.Subscription.retrieve(sub_id)
            meta = sub_obj.get("metadata", {})
            user = get_user_from_metadata(meta)
            which_tier = meta.get("which_tier", "plus")

            if user:
                print(f"[Webhook] invoice.paid for user={user.email}, tier={which_tier}")
                # Falls license_expiry abgelaufen -> setze ab heute +30
                # sonst hänge 30 Tage dran
                if not user.license_expiry or user.license_expiry < datetime.now():
                    user.license_expiry = datetime.now() + timedelta(days=30)
                else:
                    user.license_expiry += timedelta(days=30)
                user.license_tier = which_tier
                db.session.commit()
                new_log.status = "paid"
                db.session.commit()
            else:
                print("[Webhook] invoice.paid: No valid user found => ignoring.")
        else:
            print("[Webhook] invoice.paid: No subscription ID => ignoring.")

    elif etype == "invoice.payment_failed":
        sub_id = data_obj.get("subscription")
        if sub_id:
            sub_obj = stripe.Subscription.retrieve(sub_id)
            meta = sub_obj.get("metadata", {})
            user = get_user_from_metadata(meta)

            if user:
                print(f"[Webhook] invoice.payment_failed for user={user.email}")
                user.license_tier = "no_access"
                user.license_expiry = None
                db.session.commit()

                # => E-Mail
                try:
                    if user and user.email:
                        send_email(
                            user.email,
                            "Payment failed",
                            "Deine Zahlung schlug fehl! Bitte Zahlungsmethode aktualisieren.",
                            "<p>Zahlung fehlgeschlagen. Bitte updaten!</p>"
                        )
                    else:
                        print("[Webhook] Payment failed, but no user/email => cannot send email.")
                except Exception as mail_ex:
                    print("[Webhook] SendGrid error:", mail_ex)

                new_log.status = "failed"
                db.session.commit()
            else:
                print("[Webhook] invoice.payment_failed: No valid user found => ignoring.")
        else:
            print("[Webhook] invoice.payment_failed: No subscription ID => ignoring.")
    else:
        print(f"[Webhook] Unhandled event type: {etype}")

    return jsonify({"status": "ok"}), 200