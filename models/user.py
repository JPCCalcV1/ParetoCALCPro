# models/user.py

from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()

class User(db.Model):
    __tablename__ = "user"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)

    # License-Felder
    license_tier = db.Column(db.String(20), default="test")  # e.g. "test","plus","premium","extended","no_access"
    license_expiry = db.Column(db.DateTime, default=None)

    # GPT-Felder
    gpt_used_count = db.Column(db.Integer, default=0)
    gpt_allowed_count = db.Column(db.Integer, default=10)

    # Addons (CSV) => z.B. "AI-Assistent,ExportXLS"
    addons = db.Column(db.String(200), default="")

    # 2FA-Secret (TOTP), optional
    totp_secret = db.Column(db.String(32), nullable=True)

    # Single Sign-On
    current_session_token = db.Column(db.String(64), nullable=True)

    # NEU: TOTP-Enable
    twofa_enabled = db.Column(db.Boolean, default=False)

    def __init__(self, email, raw_password):
        self.email = email
        self.set_password(raw_password)

    def set_password(self, raw_password):
        self.password_hash = generate_password_hash(raw_password)

    def check_password(self, raw_password):
        return check_password_hash(self.password_hash, raw_password)

    def has_valid_license(self):
        if not self.license_expiry:
            return False
        return datetime.now() < self.license_expiry

    def license_level(self):
        if not self.has_valid_license():
            return "no_access"
        return self.license_tier

    @property
    def is_admin(self):
        # Z.B. "admin@paretocalc.com" => Admin
        return self.email == "admin@paretocalc.com"