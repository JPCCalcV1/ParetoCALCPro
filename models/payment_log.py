""" START OF FILE: models/payment_log.py (Best-of Version) """

from datetime import datetime
# Wichtig: NICHT noch einmal db = SQLAlchemy() aufrufen!
# Stattdessen importieren wir db von deinem user-Modul.
from models.user import db

class PaymentLog(db.Model):
    __tablename__ = "payment_log"
    id = db.Column(db.Integer, primary_key=True)

    # Relationship zu user
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=True)

    # Stripe-spezifische Felder
    event_id = db.Column(db.String(64), nullable=True)  # z.B. evt_1N...
    event_type = db.Column(db.String(50), nullable=True)
    raw_data = db.Column(db.Text, nullable=True)

    # Status: "pending", "completed", "paid", "failed", etc.
    status = db.Column(db.String(20), default="pending")

    # Zeitstempel
    created_at = db.Column(db.DateTime, default=datetime.now)

    # Relationship:
    # Falls du schon "payments" statt "payment_logs" verwendet hast,
    # kannst du "backref='payments'" beibehalten.
    user = db.relationship("User", backref="payment_logs")

    def __repr__(self):
        return f"<PaymentLog id={self.id} status={self.status} event_id={self.event_id}>"

""" END OF FILE: models/payment_log.py """