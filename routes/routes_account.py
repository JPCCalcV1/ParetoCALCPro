""" START OF FILE: routes_account.py - FINAL with 'Kill-Old-Then-New' Upgrade """

import os
import stripe
from flask import Blueprint, request, session, render_template, jsonify, redirect, url_for, flash
from datetime import datetime, timedelta
from models.user import db, User
from helpers.sendgrid_helper import send_email  # falls du sowas hast
from functools import wraps
from core.extensions import csrf
from flask import current_app

account_bp = Blueprint("account_bp", __name__)

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
stripe.api_key = STRIPE_SECRET_KEY

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            # optional: flash("Bitte zuerst einloggen.")
            return redirect("/auth/login")
        return f(*args, **kwargs)
    return decorated

@account_bp.route("/", methods=["GET"])
@csrf.exempt
@login_required
def my_account_home():
    """
    Kunden-Dashboard, zeigt:
    - Aktuellen Plan (license_tier)
    - license_expiry
    - ABO-Infos (Subscription ID, next billing, cancel-Button)
    - 2FA-Status (falls du es hast)
    """
    user_id = session.get("user_id")
    user = User.query.get(user_id)
    if not user:
        # Falls nicht vorhanden => Abbruch => logout
        return redirect("/auth/logout")

    sub_id = user.stripe_subscription_id

    next_billing = None
    if sub_id:
        try:
            sub_obj = stripe.Subscription.retrieve(sub_id)
            next_billing_ts = sub_obj.get("current_period_end")  # Unix timestamp
            if next_billing_ts:
                next_billing = datetime.utcfromtimestamp(next_billing_ts)
        except:
            pass

    return render_template("account/dashboard.html",
        user=user,
        subscription_id=sub_id,
        next_billing_date=next_billing,
    )

@account_bp.route("/cancel", methods=["POST"])
@csrf.exempt
@login_required
def cancel_subscription():
    """
    Kündigt das aktuelle Abo => "cancel_at_period_end=True".
    => Lokal: license_tier="test", license_expiry=now() => entzieht sofort Zugriff
    => Du kannst das ändern, wenn du dem User die Restlaufzeit gewähren willst.
    """
    user_id = session.get("user_id")
    user = User.query.get(user_id)
    if not user or not user.stripe_subscription_id:
        return jsonify({"error": "No subscription to cancel."}), 400

    try:
        stripe.Subscription.modify(
            user.stripe_subscription_id,
            cancel_at_period_end=True
        )
        user.license_tier = "test"
        user.license_expiry = datetime.now()
        db.session.commit()

        # OPTIONAL: SendGrid-Mail
        subject = "Abo-Kündigung bestätigt"
        txt = f"""Hallo {user.email},
dein Abo (Subscription ID: {user.stripe_subscription_id}) wurde gekündigt.
Du behältst den Zugang bei Stripe noch bis Periodenende, 
aber wir haben dich local bereits auf 'test' gesetzt.
Grüße,
Dein ParetoCalc-Team
"""
        send_email(
            user.email,
            subject,
            txt,
            f"<p>{txt}</p>"
        )

        return redirect(url_for("account_bp.my_account_home"))
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@account_bp.route("/upgrade", methods=["POST"])
@csrf.exempt
@login_required
def upgrade_plan():
    """
    Erlaubt Up-/Downgrade des bestehenden ABO:
      - Killt altes A   bo (user.stripe_subscription_id), falls vorhanden
      - Erzeugt neues ABO => plus => 7 Tage trial, premium/extended => 0
      - Verhindert "No user => abort" im Webhook durch: metadata={'user_id':..., 'which_tier':...}
      - Minimal-lösung, KEIN Extra-Feld für Extended => user hat nur EIN ABO am Ende
    """
    user_id = session.get("user_id")
    if not user_id:
        return jsonify({"error": "Not logged in"}), 401

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error":"User not found"}),404

    data_in = request.get_json() or {}
    which_tier = data_in.get("which_tier","plus")  # 'plus', 'premium' oder 'extended'

    # Price-Map anpassen an deine ENV-Variablen (Beispiele):
    price_map = {
        "plus":     os.getenv("STRIPE_PRICE_PLUS","price_plusXYZ"),
        "premium":  os.getenv("STRIPE_PRICE_PREMIUM","price_premXYZ"),
        "extended": os.getenv("STRIPE_PRICE_EXTENDED","price_extXYZ"),
    }
    price_id = price_map.get(which_tier)
    if not price_id:
        return jsonify({"error": f"No price for tier='{which_tier}'"}), 400

    # Trial nur bei plus
    if which_tier == "plus":
        trial_days = 7
    else:
        trial_days = 0

    try:
        # 1) Altes ABO killen (falls user bereits stripe_subscription_id hat)
        if user.stripe_subscription_id:
            try:
                stripe.Subscription.delete(user.stripe_subscription_id)
                current_app.logger.info(f"[upgrade_plan] Killed old sub {user.stripe_subscription_id}")
            except stripe.error.StripeError as e:
                current_app.logger.warning(f"Could not delete old sub: {e}")

            user.stripe_subscription_id = None
            db.session.commit()

        # 2) subscription_data erstellen
        if trial_days > 0:
            # plus => 7 Tage => trial_period_days=7
            subscription_data = {
                "trial_period_days": trial_days,
                "metadata": {
                    "user_id": str(user.id),
                    "which_tier": which_tier
                }
            }
        else:
            # premium/extended => KEIN trial => trial_period_days weglassen
            subscription_data = {
                "metadata": {
                    "user_id": str(user.id),
                    "which_tier": which_tier
                }
            }

        # 3) Neue Subscription über Stripe-Checkout
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity":1}],
            mode="subscription",
            subscription_data=subscription_data,
            success_url="https://paretocalc.com/pay/success",
            cancel_url="https://paretocalc.com/pay/cancel"
        )

        current_app.logger.info(
            f"[upgrade_plan] user_id={user.id}, tier={which_tier}, created new sub => session {checkout_session.id}"
        )

        return jsonify({"checkout_url": checkout_session.url}), 200

    except stripe.error.StripeError as se:
        current_app.logger.exception(f"[upgrade_plan] StripeError: {se}")
        return jsonify({"error": str(se)}), 500
    except Exception as ex:
        current_app.logger.exception(f"[upgrade_plan] Exception: {ex}")
        return jsonify({"error": str(ex)}), 500
@account_bp.route("/2fa/toggle", methods=["POST"])
@csrf.exempt
@login_required
def toggle_2fa():
    """
    Beispiel: User kann 2FA an-/abschalten.
    Du hast in user.twofa_enabled ein Boolean?
    """
    user_id = session.get("user_id")
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error":"User not found"}),404

    # Toggle 2FA
    user.twofa_enabled = not user.twofa_enabled
    db.session.commit()
    return redirect(url_for("account_bp.my_account_home"))

""" END OF FILE: routes_account.py """