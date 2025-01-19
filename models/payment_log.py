""" START OF FILE: models/payment_log.py - KAPITEL 1 """

from datetime import datetime
from models.user import db

class PaymentLog(db.Model):
    __tablename__ = "payment_log"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)
    event_id = db.Column(db.String(64), nullable=True)
    event_type = db.Column(db.String(50), nullable=True)
    raw_data = db.Column(db.Text, nullable=True)
    status = db.Column(db.String(20), default="pending")
    created_at = db.Column(db.DateTime, default=datetime.now)

    user = db.relationship("User", backref="payment_logs")

""" END OF FILE: models/payment_log.py - KAPITEL 1 """