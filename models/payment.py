# models/payment.py

from datetime import datetime
from core.extensions import db

class PaymentLog(db.Model):
    __tablename__ = 'payment_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    status = db.Column(db.String(50), default='pending')  # 'pending', 'paid', 'failed', ...
    expiry_date = db.Column(db.DateTime, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<PaymentLog id={self.id} user_id={self.user_id} status={self.status}>"