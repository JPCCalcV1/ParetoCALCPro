# models/payment_log.py

from datetime import datetime
from core.extensions import db

class PaymentLog(db.Model):
    __tablename__ = "payment_log"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    event_id = db.Column(db.String(100), nullable=True)
    event_type = db.Column(db.String(50), nullable=True)
    raw_data = db.Column(db.Text, nullable=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    # NEU: status-Feld
    status = db.Column(db.String(20), default="pending")

    # Relationship (falls du willst)
    user = db.relationship("User", backref="payments")

    def __repr__(self):
        return f"<PaymentLog id={self.id} status={self.status} event_id={self.event_id}>"