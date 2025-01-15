# models/gpt_session.py

from datetime import datetime
from core.extensions import db

class GPTSession(db.Model):
    __tablename__ = 'gpt_sessions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    allowed_count = db.Column(db.Integer, default=10)
    used_count = db.Column(db.Integer, default=0)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<GPTSession id={self.id} user_id={self.user_id} used={self.used_count}/{self.allowed_count}>"