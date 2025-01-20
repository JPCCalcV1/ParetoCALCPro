# FILE: routes/routes_account.py

import os
import stripe
from flask import Blueprint, request, session, render_template, jsonify, redirect, url_for, flash
from datetime import datetime, timedelta
from models.user import db, User
from helpers.sendgrid_helper import send_email  # falls du sowas hast
from functools import wraps
from core.extensions import csrf  # <--- das fehlte!
account_bp = Blueprint("account_bp", __name__)

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
stripe.api_key = STRIPE_SECRET_KEY

def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if "user_id" not in session:
            # oder flash("Bitte zuerst einloggen.")
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
    user_id = session["user_id"]
    user = User.query.get(user_id)
    if not user:
        # Falls nicht vorhanden => Abbruch
        return redirect("/auth/logout")

    # Check ABO: subscription?
    sub_id = getattr(user, "stripe_subscription_id", None)

    # Minimale Info, um z. B. next_billing_date anzuzeigen:
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
    user_id = session["user_id"]
    user = User.query.get(user_id)
    if not user or not user.stripe_subscription_id:
        return jsonify({"error":"No subscription to cancel."}), 400

    try:
        stripe.Subscription.modify(
            user.stripe_subscription_id,
            cancel_at_period_end=True
        )
        user.license_tier = "test"
        user.license_expiry = datetime.now()  # etc...
        db.session.commit()

        # OPTIONAL: SendGrid-Mail
        from helpers.sendgrid_helper import send_email
        subject = "Abo-Kündigung bestätigt"
        txt = f"""Hallo {user.email},
dein Abo (Subscription ID: {user.stripe_subscription_id}) wurde gekündigt.
Du behältst den Zugang bis Periodenende. 
Grüße,
Dein ParetoCalc-Team
"""
        send_email(
            user.email,
            subject,
            txt,
            f"<p>{txt}</p>"
        )

        # User Experience
        return redirect(url_for("account_bp.my_account_home"))

    except Exception as e:
        return jsonify({"error": str(e)}), 500
@account_bp.route("/upgrade", methods=["POST"])
@csrf.exempt
@login_required
def upgrade_plan():
    """
    Falls der User z. B. von 'plus' auf 'premium' wechseln will,
    oder 'test' => 'plus' etc.
    => Erzeugt einen Stripe-Checkout => mode="subscription"
       aber subscription_data={metadata=...}
    => Dann leitet er um => /pay/success
    => Ähnlich wie in routes_payment 'checkout-sub'
    """
    user_id = session["user_id"]
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error":"User not found"}),404

    data_in = request.get_json() or {}
    which_tier = data_in.get("which_tier","premium")

    # Hole price_id => env.STRIPE_PRICE_...
    price_map = {
        "plus": os.getenv("STRIPE_PRICE_PLUS","price_xxx"),
        "premium": os.getenv("STRIPE_PRICE_PREMIUM","price_yyy"),
        "extended": os.getenv("STRIPE_PRICE_EXTENDED","price_zzz"),
    }
    price_id = price_map.get(which_tier)
    if not price_id:
        return jsonify({"error": f"No price for tier={which_tier}"}),400

    try:
        # Erzeuge Session
        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity":1}],
            mode="subscription",
            subscription_data={
                "trial_period_days": 0,  # oder 7 => je nach logic
                "metadata": {
                    "user_id": str(user.id),
                    "which_tier": which_tier
                }
            },
            success_url="https://jpccalc.de/pay/success",
            cancel_url="https://jpccalc.de/pay/cancel"
        )
        return jsonify({"checkout_url": checkout_session.url})
    except stripe.error.StripeError as se:
        return jsonify({"error": str(se)}),500
    except Exception as ex:
        return jsonify({"error": str(ex)}),500

@account_bp.route("/2fa/toggle", methods=["POST"])
@csrf.exempt
@login_required
def toggle_2fa():
    """
    Beispiel: User kann 2FA an-/abschalten.
    Du hast in user.twofa_enabled ein Boolean?
    """
    user_id = session["user_id"]
    user = User.query.get(user_id)
    if not user:
        return jsonify({"error":"User not found"}),404

    # toggle
    user.twofa_enabled = not user.twofa_enabled
    db.session.commit()

    # flash("2FA ist nun aktiviert" oder "...deaktiviert")
    return redirect(url_for("account_bp.my_account_home"))