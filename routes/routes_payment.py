""" START OF FILE: routes/payment.py (Stripe Webhook mit Extended Debugging) """

import os
import stripe
from flask import Blueprint, request, jsonify, session, current_app, render_template
from datetime import datetime, timedelta

from models.user import db, User
from models.payment_log import PaymentLog

# Falls du global CSRF verwendest
from core.extensions import csrf

# => E-Mail optional
# from helpers.sendgrid_helper import send_email

payment_bp = Blueprint("payment_bp", __name__)

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
stripe.api_key = STRIPE_SECRET_KEY

price_map = {
    "plus":     os.getenv("STRIPE_PRICE_PLUS", "price_plusXYZ"),
    "premium":  os.getenv("STRIPE_PRICE_PREMIUM", "price_premXYZ"),
    "extended": os.getenv("STRIPE_PRICE_EXTENDED", "price_extXYZ"),
}

@payment_bp.route("/checkout-sub", methods=["POST"])
@csrf.exempt
def create_checkout_session_subscription():
    """
    ABO => Der User kann +30 Tage oder +365 (extended) im invoice.paid erhalten.
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error": "User not found"}), 404

    data_in = request.get_json() or {}
    which_tier = data_in.get("which_tier", "plus")
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
            success_url="https://www.jpccalc.de/pay/success",
            cancel_url="https://www.jpccalc.de/pay/cancel"
        )
        current_app.logger.info(f"[checkout-sub] Created checkout_session id={checkout_session.id}, url={checkout_session.url}")
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
    EINMALZAHLUNG => user.license_expiry = now+365
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
        return jsonify({"error":f"No price for {which_tier}"}),400

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
                "mode_used": "oneoff"
            }
        )
        current_app.logger.info(f"[checkout-oneoff] Created checkout_session id={checkout_session.id}, url={checkout_session.url}")
        return jsonify({"checkout_url": checkout_session.url}),200

    except stripe.error.StripeError as se:
        current_app.logger.exception(f"[checkout-oneoff] StripeError: {se}")
        return jsonify({"error": str(se)}),500
    except Exception as ex:
        current_app.logger.exception(f"[checkout-oneoff] Exception: {ex}")
        return jsonify({"error": str(ex)}),500


@payment_bp.route("/webhook", methods=["POST"])
@csrf.exempt
def stripe_webhook():
    """
    EXTENDED DEBUGGING:
    Hier werden alle relevanten Stripe-Events verarbeitet.
    """
    current_app.logger.info("==> Entering stripe_webhook (extended debug)")

    payload = request.data
    sig_header = request.headers.get("Stripe-Signature","")
    current_app.logger.info(f"[webhook] Payload size={len(payload)}, sig_header={sig_header[:30]}...")

    if not STRIPE_WEBHOOK_SECRET:
        current_app.logger.error("[webhook] No STRIPE_WEBHOOK_SECRET set => abort")
        return jsonify({"error": "No webhook secret"}), 500

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
        current_app.logger.info(f"[webhook] Validated event id={event['id']}, type={event['type']}")
    except stripe.error.SignatureVerificationError as e:
        current_app.logger.exception(f"[webhook] Signature error: {e}")
        return jsonify({"error":"Invalid signature"}),400

    etype = event["type"]
    data_obj = event["data"]["object"]

    # PaymentLog anlegen
    new_log = PaymentLog(
        user_id=None,
        event_id=event["id"],
        event_type=etype,
        raw_data=str(event),
        status="pending"
    )
    db.session.add(new_log)
    db.session.commit()
    current_app.logger.info(f"[webhook] PaymentLog created => id={new_log.id}, event_type={etype}")

    def get_user_from_metadata(meta):
        current_app.logger.info(f"[webhook->get_user_from_metadata] meta={meta}")
        uid_str = meta.get("user_id")
        if not uid_str:
            current_app.logger.warning("[webhook->get_user_from_metadata] No user_id in meta")
            return None
        user_obj = User.query.get(int(uid_str))
        if user_obj:
            current_app.logger.info(f"[webhook->get_user_from_metadata] Found user => {user_obj.email}, id={user_obj.id}")
        else:
            current_app.logger.warning(f"[webhook->get_user_from_metadata] No user with id={uid_str} found in DB")
        return user_obj

    # ------------------------------------------------
    # A) checkout.session.completed => initial Payment
    # ------------------------------------------------
    if etype == "checkout.session.completed":
        meta = data_obj.get("metadata", {})
        current_app.logger.info(f"[webhook] checkout.session.completed => meta={meta}")

        user = get_user_from_metadata(meta)
        mode = data_obj.get("mode")  # "payment" or "subscription"
        which_tier = meta.get("which_tier","extended")

        current_app.logger.info(
            f"[webhook] session.completed: mode={mode}, tier={which_tier}, user_found={bool(user)}"
        )

        if user:
            if mode == "payment":
                # => OneOff => +365 Tage
                old_tier = user.license_tier
                user.license_tier = which_tier
                user.license_expiry = datetime.now() + timedelta(days=365)
                db.session.commit()

                current_app.logger.info(
                    f"[webhook] OneOff upgrade: {user.email}: {old_tier} => {which_tier}, expiry in 365 days"
                )

            elif mode == "subscription":
                # ABO => z. B. +7 Tage Trial
                old_tier = user.license_tier
                user.license_tier = which_tier
                user.license_expiry = datetime.now() + timedelta(days=7)
                db.session.commit()

                current_app.logger.info(
                    f"[webhook] Subscription start: {user.email}: {old_tier} => {which_tier}, expiry+7 days"
                )

            new_log.user_id = user.id
            new_log.status = "completed"
            db.session.commit()

        else:
            current_app.logger.warning("[webhook] session.completed but no valid user => no license update")

    # ------------------------------------------------
    # B) invoice.paid => Subscription Verlängerung
    # ------------------------------------------------
    elif etype == "invoice.paid":
        current_app.logger.info("[webhook] invoice.paid triggered")
        sub_id = data_obj.get("subscription")
        current_app.logger.info(f"[webhook] invoice.paid => sub_id={sub_id}")

        if sub_id:
            sub_obj = stripe.Subscription.retrieve(sub_id)
            meta = sub_obj.get("metadata", {})
            user = get_user_from_metadata(meta)
            which_tier = meta.get("which_tier","plus")

            current_app.logger.info(
                f"[webhook] invoice.paid => tier={which_tier}, user_found={bool(user)}"
            )

            if user:
                # z. B. +30 Tage ABO
                old_expiry = user.license_expiry
                old_tier = user.license_tier

                if not user.license_expiry or user.license_expiry < datetime.now():
                    user.license_expiry = datetime.now() + timedelta(days=30)
                else:
                    user.license_expiry += timedelta(days=30)
                user.license_tier = which_tier

                db.session.commit()
                new_log.user_id = user.id
                new_log.status = "paid"
                db.session.commit()

                current_app.logger.info(
                    f"[webhook] invoice.paid => {user.email}: from tier={old_tier}, old_expiry={old_expiry} => new tier={which_tier}, expiry={user.license_expiry}"
                )
            else:
                current_app.logger.warning(f"[webhook] invoice.paid => No user found => no update")
        else:
            current_app.logger.warning("[webhook] invoice.paid => No sub_id => ignoring")

    # ------------------------------------------------
    # C) invoice.payment_failed => ABO fehlgeschlagen
    # ------------------------------------------------
    elif etype == "invoice.payment_failed":
        current_app.logger.info("[webhook] invoice.payment_failed triggered")
        sub_id = data_obj.get("subscription")
        current_app.logger.info(f"[webhook] invoice.payment_failed => sub_id={sub_id}")

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
                    f"[webhook] invoice.payment_failed => user={user.email} from tier={old_tier} => no_access"
                )

                # E-Mail optional
                # try:
                #     send_email(
                #       to_email=user.email,
                #       subject="Abo fehlgeschlagen",
                #       body_text="Bitte Kreditkarte aktualisieren",
                #       body_html="<p>Deine Zahlung schlug fehl...</p>"
                #     )
                # except Exception as mail_ex:
                #     current_app.logger.exception(f"[webhook] SendGrid error: {mail_ex}")
            else:
                current_app.logger.warning("[webhook] invoice.payment_failed => No user => ignoring")
        else:
            current_app.logger.warning("[webhook] invoice.payment_failed => No sub_id => ignoring")

    else:
        current_app.logger.info(f"[webhook] Unhandled event type: {etype}")

    current_app.logger.info("[webhook] Done => returning 200")
    return jsonify({"status": "ok"}), 200

@payment_bp.route("/success", methods=["GET"])
def payment_success():
    return render_template("pay/payment_success.html")

@payment_bp.route("/cancel", methods=["GET"])
def payment_cancel():
    return render_template("pay/payment_cancel.html")

@payment_bp.route("/test", methods=["GET"])
def test_payment_route():
    return jsonify({"message":"Payment blueprint is running (debug)!"}),200

""" END OF FILE: routes/payment.py (Stripe Webhook mit Extended Debugging) """
