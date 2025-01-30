# FILE: models/user.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    # Lizenz-Felder
    license_tier = db.Column(db.String(20), default="test")
    license_expiry = db.Column(db.DateTime, default=None)

    # GPT-Felder
    gpt_used_count = db.Column(db.Integer, default=0)
    gpt_allowed_count = db.Column(db.Integer, default=35)
    addons = db.Column(db.String(200), default="")

    # 2FA-Felder
    totp_secret = db.Column(db.String(32), nullable=True)
    twofa_enabled = db.Column(db.Boolean, default=False)

    # Session / SSO
    current_session_token = db.Column(db.String(64), nullable=True)

    # NEU: Stripe-Subscription
    # => Speichert z.B. "sub_1NHUW7C2pJSqIWqO..."
    stripe_subscription_id = db.Column(db.String(64), nullable=True)

    def __init__(self, email, raw_password):
        self.email = email
        self.set_password(raw_password)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def has_valid_license(self):
        """
        Prüft, ob license_expiry noch in der Zukunft liegt.
        """
        if not self.license_expiry:
            return False
        return datetime.now() < self.license_expiry

    def license_level(self):
        """
        Gibt den license_tier zurück, falls expiry nicht abgelaufen ist,
        sonst 'no_access'.
        """
        if not self.has_valid_license():
            return "no_access"
        return self.license_tier

    @property
    def is_admin(self):
        """
        Beispiel: E-Mail 'admin@paretocalc.com' => Admin-Check.
        """
        return self.email.lower() == "admin@paretocalc.com"