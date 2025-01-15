# routes/routes_payment.py

import os
from datetime import datetime, timedelta
from flask import Blueprint, request, jsonify
from flask_login import current_user, login_required
from core.extensions import db, csrf
from models.payment import PaymentLog
from models.user import User
import stripe

stripe.api_key = os.environ.get('STRIPE_SECRET_KEY', 'sk_test_123')

payment_bp = Blueprint('payment_bp', __name__)

@payment_bp.route('/create-checkout-session', methods=['POST'])
@login_required
def create_checkout_session():
    """Erzeugt eine Stripe-Checkout-Session und legt einen PaymentLog an."""
    price_data = {
        'currency': 'eur',
        'unit_amount': 9999,
        'product_data': {
            'name': 'ParetoCalc Subscription'
        }
    }
    try:
        price = stripe.Price.create(**price_data)
        session = stripe.checkout.Session.create(
            payment_method_types=['card'],
            line_items=[{'price': price.id, 'quantity': 1}],
            mode='subscription',
            success_url='https://your-domain.com/success?session_id={CHECKOUT_SESSION_ID}',
            cancel_url='https://your-domain.com/cancel',
            metadata={
                'user_id': current_user.id
            }
        )

        payment_log = PaymentLog(
            user_id=current_user.id,
            status='pending'
        )
        db.session.add(payment_log)
        db.session.commit()

        return jsonify({
            'checkout_url': session.url,
            'session_id': session.id
        }), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@payment_bp.route('/webhook', methods=['POST'])
@csrf.exempt
def stripe_webhook():
    """Stripe-Webhooks verarbeiten (invoice.paid, invoice.payment_failed, etc.)."""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET', '')

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400

    event_type = event['type']
    if event_type == 'invoice.paid':
        handle_invoice_paid(event)
    elif event_type == 'invoice.payment_failed':
        handle_invoice_failed(event)
    # ggf. mehr events abfangen

    return jsonify({'status': 'success'}), 200

def handle_invoice_paid(event):
    """Setzt PaymentLog auf 'paid', entfernt GracePeriod."""
    invoice = event['data']['object']
    user_id = invoice['metadata'].get('user_id')
    if user_id:
        payment_log = PaymentLog.query.filter_by(
            user_id=user_id, status='pending'
        ).order_by(PaymentLog.created_at.desc()).first()
        if payment_log:
            payment_log.status = 'paid'
            payment_log.expiry_date = None
            payment_log.updated_at = datetime.utcnow()
            db.session.commit()

def handle_invoice_failed(event):
    """Setzt PaymentLog auf 'failed' + GracePeriod (z. B. 5 Tage)."""
    invoice = event['data']['object']
    user_id = invoice['metadata'].get('user_id')
    if user_id:
        payment_log = PaymentLog.query.filter_by(
            user_id=user_id, status='pending'
        ).order_by(PaymentLog.created_at.desc()).first()
        if payment_log:
            payment_log.status = 'failed'
            grace_days = determine_grace_period(user_id)
            payment_log.expiry_date = datetime.utcnow() + timedelta(days=grace_days)
            payment_log.updated_at = datetime.utcnow()
            db.session.commit()

def determine_grace_period(user_id):
    """Bestimmt dynamisch die GracePeriod in Tagen."""
    user = User.query.get(user_id)
    if user and user.is_admin:
        return 7  # z. B. Admin 7 Tage
    return 5  # Standard 5 Tage