import os
import stripe
from flask import Blueprint, request, jsonify, session, current_app, render_template
from datetime import datetime, timedelta

from models.user import db, User
from models.payment_log import PaymentLog
from core.extensions import csrf
from helpers.sendgrid_helper import send_email  # falls du E-Mail nutzt

payment_bp = Blueprint("payment_bp", __name__)

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
stripe.api_key = STRIPE_SECRET_KEY

# Price-Map: "plus", "premium", "extended" (du hast V1 "test" entfernt)
price_map = {
    "plus":     os.getenv("STRIPE_PRICE_PLUS", "price_plusXYZ"),
    "premium":  os.getenv("STRIPE_PRICE_PREMIUM", "price_premXYZ"),
    "extended": os.getenv("STRIPE_PRICE_EXTENDED", "price_extXYZ"),
}


# ---------------------------------------------------------
#   CREATE-CHECKOUT-SESSION (V1)
# ---------------------------------------------------------

@payment_bp.route("/create-checkout-session", methods=["POST"])
@csrf.exempt
def create_checkout_session():
    """
    V1: Falls du nur EINE Art Payment hast (OneOff).
    Bleibt kompatibel, falls dein Frontend schon /create-checkout-session aufruft.
    """
    # current_app.logger.debug("==> V1 create_checkout_session (OneOff) CALLED")

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data_in = request.get_json() or {}
    which_tier = data_in.get("which_tier", "extended")  # default extended
    # current_app.logger.debug(f"[V1 create_session] which_tier={which_tier}")

    price_id = price_map.get(which_tier)
    # current_app.logger.debug(f"[V1 create_session] price_id={price_id}")

    if not price_id:
        return jsonify({"error": f"No price for {which_tier}"}), 400

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="payment",
            success_url="https://www.jpccalc.de/stripe/success",
            cancel_url="https://www.jpccalc.de/stripe/cancel",
            metadata={
                "user_id": user.id,
                "which_tier": which_tier
            }
        )
        # current_app.logger.debug(f"[V1 create_session] Stripe session url: {checkout_session.url}")
        return jsonify({"checkout_url": checkout_session.url}), 200

    except Exception as e:
        current_app.logger.error(f"[V1 create_session] Stripe Exception: {str(e)}")
        return jsonify({"error": str(e)}), 500


# ---------------------------------------------------------
#   CREATE-CHECKOUT-SESSION-SUBSCRIPTION (V2 ABO)
# ---------------------------------------------------------
@payment_bp.route("/checkout-sub", methods=["POST"])
@csrf.exempt
def create_checkout_session_subscription():
    """
    V2: Subscription => 7 Tage Trial, invoice.paid => +30 Tage
    """
    # print("[create_checkout_session_subscription] Route was called.")
    # current_app.logger.debug("==> create_checkout_session_subscription CALLED")

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data_in = request.get_json() or {}
    # Im Frontend: buyPlus() => { which_tier:"plus" }
    # buyPremium() => { which_tier:"premium" }
    which_tier = data_in.get("which_tier", "plus")
    # current_app.logger.debug(f"[SUBSCRIPTION] which_tier={which_tier}")

    price_id = price_map.get(which_tier)
    # current_app.logger.debug(f"[SUBSCRIPTION] price_id={price_id}")

    if not price_id:
        return jsonify({"error": f"No Price-ID for {which_tier}"}), 400

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="subscription",
            subscription_data={
                "trial_period_days": 7
            },
            success_url="https://www.jpccalc.de/stripe/success",
            cancel_url="https://www.jpccalc.de/stripe/cancel",
            metadata={
                "user_id": user.id,
                "which_tier": which_tier
            }
        )
        # current_app.logger.debug(f"[SUBSCRIPTION] Created session => {checkout_session.url}")
        return jsonify({"checkout_url": checkout_session.url}), 200

    except stripe.error.StripeError as e:
        current_app.logger.error(f"[SUBSCRIPTION] StripeError: {str(e)}")
        return jsonify({"error": str(e)}), 500

    except Exception as ex:
        current_app.logger.error(f"[SUBSCRIPTION] Other Exception: {str(ex)}")
        return jsonify({"error": str(ex)}), 500


# ---------------------------------------------------------
#   CREATE-CHECKOUT-SESSION-ONEOFF (V2 ABO-Einmal)
# ---------------------------------------------------------

@payment_bp.route("/create-checkout-session-oneoff", methods=["POST"])
@csrf.exempt
def create_checkout_session_oneoff():
    """
    OneOff: 365 Tage => Gleiche Logik wie V1, aber separat.
    """
    # current_app.logger.debug("==> create_checkout_session_oneoff CALLED")

    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data_in = request.get_json() or {}
    which_tier = data_in.get("which_tier", "extended")
    # current_app.logger.debug(f"[ONEOFF] which_tier={which_tier}")

    price_id = price_map.get(which_tier)
    # current_app.logger.debug(f"[ONEOFF] price_id={price_id}")

    if not price_id:
        return jsonify({"error": f"No price for {which_tier}"}), 400

    try:
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            mode="payment",
            success_url="https://www.jpccalc.de/stripe/success",
            cancel_url="https://www.jpccalc.de/stripe/cancel",
            metadata={
                "user_id": user.id,
                "which_tier": which_tier
            }
        )
        # current_app.logger.debug(f"[ONEOFF] Created session => {checkout_session.url}")
        return jsonify({"checkout_url": checkout_session.url}), 200

    except stripe.error.StripeError as e:
        current_app.logger.error(f"[ONEOFF] StripeError: {str(e)}")
        return jsonify({"error": str(e)}), 500

    except Exception as ex:
        current_app.logger.error(f"[ONEOFF] Other Exception: {str(ex)}")
        return jsonify({"error": str(ex)}), 500


# ---------------------------------------------------------
#   WEBHOOK
# ---------------------------------------------------------
@payment_bp.route("/webhook", methods=["POST"])
@csrf.exempt
def stripe_webhook():
    payload = request.data
    sig_header = request.headers.get("Stripe-Signature", "")
    # current_app.logger.debug("[WEBHOOK] Received payload size=%d" % len(payload))

    if not STRIPE_WEBHOOK_SECRET:
        current_app.logger.error("[WEBHOOK] No STRIPE_WEBHOOK_SECRET configured.")
        return jsonify({"error": "No webhook secret"}), 500

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except stripe.error.SignatureVerificationError as e:
        current_app.logger.error("[WEBHOOK] Signature error: %s", str(e))
        return jsonify({"error": "Invalid signature"}), 400

    etype = event["type"]
    data_obj = event["data"]["object"]
    # current_app.logger.debug(f"[WEBHOOK] Event type={etype}")

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
            # print("[Webhook] No user_id in metadata => ignoring.")
            return None
        user = User.query.get(uid)
        if not user:
            # print(f"[Webhook] User with id={uid} not found in DB.")
            return None
        return user

    # 4) Verzweige nach event type
    if etype == "checkout.session.completed":
        which_tier = data_obj.get("metadata", {}).get("which_tier", "extended")
        mode = data_obj.get("mode")
        user = get_user_from_metadata(data_obj.get("metadata", {}))

        if user:
            # print(f"[Webhook] checkout.session.completed for user={user.email}, tier={which_tier}, mode={mode}")
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
            # print("[Webhook] Warning: No valid user found for checkout.session.completed")
            pass

    elif etype == "invoice.paid":
        sub_id = data_obj.get("subscription")
        if sub_id:
            sub_obj = stripe.Subscription.retrieve(sub_id)
            meta = sub_obj.get("metadata", {})
            user = get_user_from_metadata(meta)
            which_tier = meta.get("which_tier", "plus")

            if user:
                # print(f"[Webhook] invoice.paid for user={user.email}, tier={which_tier}")
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
                # print("[Webhook] invoice.paid: No valid user found => ignoring.")
                pass
        else:
            # print("[Webhook] invoice.paid: No subscription ID => ignoring.")
            pass

    elif etype == "invoice.payment_failed":
        sub_id = data_obj.get("subscription")
        if sub_id:
            sub_obj = stripe.Subscription.retrieve(sub_id)
            meta = sub_obj.get("metadata", {})
            user = get_user_from_metadata(meta)

            if user:
                # print(f"[Webhook] invoice.payment_failed for user={user.email}")
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
                        # print("[Webhook] Payment failed, but no user/email => cannot send email.")
                        pass
                except Exception as mail_ex:
                    # print("[Webhook] SendGrid error:", mail_ex)
                    pass

                new_log.status = "failed"
                db.session.commit()
            else:
                # print("[Webhook] invoice.payment_failed: No valid user found => ignoring.")
                pass
        else:
            # print("[Webhook] invoice.payment_failed: No subscription ID => ignoring.")
            pass
    else:
        # print(f"[Webhook] Unhandled event type: {etype}")
        pass

    return jsonify({"status": "ok"}), 200

@payment_bp.route("/success", methods=["GET"])
def payment_success():
    return render_template("stripe/payment_success.html")

@payment_bp.route("/cancel", methods=["GET"])
def payment_cancel():
    return render_template("stripe/payment_cancel.html")
