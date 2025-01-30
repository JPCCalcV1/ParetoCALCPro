""" START OF FILE: routes_auth.py (erweiterte Fassung) """

import os, uuid, io
from datetime import datetime, timedelta
import pyotp, qrcode

from flask import (
    Blueprint, request, jsonify, session,
    render_template, redirect, url_for, flash
)
from models.user import db, User
from core.extensions import csrf, limiter
from werkzeug.security import generate_password_hash, check_password_hash
from helpers.sendgrid_helper import send_email

auth_bp = Blueprint("auth_bp", __name__)

@auth_bp.route("/register", methods=["POST"])
@limiter.limit("150 per 15 minutes")
def register():
    """
    Registriert einen neuen User.
    - Setzt license_tier="test" + 7 Tage
    - Meldet den User sofort an, so dass er "session['user_id']" hat.
    - Leitet anschließend weiter zum /upgrade
    """
    data = request.get_json() or {}
    email = data.get("email","").strip().lower()
    password = data.get("password","")

    if not email or not password:
        return jsonify({"error":"Email/Pass fehlt"}), 400

    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error":"User existiert bereits"}), 400

    new_user = User(email, password)  # << nur Klartext übergeben
    new_user.license_tier = "test"
    new_user.license_expiry = datetime.now() + timedelta(days=7)

    db.session.add(new_user)
    db.session.commit()

    # Sende Willkommensmail
    subject = "Willkommen bei ParetoCalc!"
    text = f"Hallo {email},\n\nWillkommen bei ParetoCalc!\nViel Spaß beim Testen..."
    send_email(email, subject, text)

    # AUTO-LOGIN
    session["user_id"] = new_user.id
    new_token = str(uuid.uuid4())
    new_user.current_session_token = new_token
    db.session.commit()
    session["sso_token"] = new_token

    # Weiterleitung => /upgrade => der User kann direkt Checkout starten
    return jsonify({"message":"Registrierung ok", "next":"/upgrade"})


@auth_bp.route("/login", methods=["GET", "POST"])
@limiter.limit("150 per 15 minutes")  # Rate-Limit: max. 5 Logins in 15 Min
def login():
    if request.method == "GET":
        # Gib einfach das Login-Template zurück (HTML-Form)
        return render_template("login_form.html")

    # POST => JSON oder form
    if request.form and "email" in request.form:
        email = request.form["email"].strip().lower()
        password = request.form["password"]
        # Falls du z. B. in deinem login_form.html ein <input name="next" /> nutzt:
        next_param = request.form.get("next", "")
    else:
        data = request.get_json() or {}
        email = data.get("email", "").strip().lower()
        password = data.get("password", "")
        next_param = data.get("next", "")

    if not email or not password:
        return jsonify({"error": "Email/Pass fehlt"}), 400

    user = User.query.filter_by(email=email).first()
    if not user or not check_password_hash(user.password_hash, password):
        return jsonify({"error": "Wrong user/pass"}), 401

    # Session: Anti-Session-Fixation + Neuer Token
    session.clear()  # Wichtig: Session leeren, damit kein alter Cookie übernommen wird

    new_token = str(uuid.uuid4())
    user.current_session_token = new_token
    db.session.commit()

    session["user_id"] = user.id
    session["sso_token"] = new_token

    # Zusätzlich "next_param" im JSON zurückgeben, falls vorhanden
    return jsonify({
        "message": "Login ok",
        "license": user.license_level(),
        "next": next_param  # <-- Falls dein Frontend auf "next" reagiert
    })


@auth_bp.route("/logout", methods=["POST"])
def logout():
    if "user_id" in session:
        uid = session["user_id"]
        user = User.query.get(uid)
        if user:
            user.current_session_token = None
            db.session.commit()
    session.clear()
    return jsonify({"message": "Logout ok"}), 200


@auth_bp.route("/whoami", methods=["GET"])
def whoami():
    uid = session.get("user_id")
    if not uid:
        return jsonify({"logged_in": False}), 200
    user = User.query.get(uid)
    if not user:
        return jsonify({"logged_in": False}), 200
    return jsonify({
        "logged_in": True,
        "email": user.email,
        "license": user.license_level()
    }), 200

""" END OF FILE: routes_auth.py """


# Minimal 2FA
#@auth_bp.route("/2fa_setup", methods=["GET", "POST"])
#def twofa_setup():
    # Nur, wenn ein User eingeloggt ist
    #if "user_id" not in session:
    #    return "Not logged in", 403
    #user = User.query.get(session["user_id"])
    #if not user:
    #    return "User not found", 404

    # Erzeuge TOTP-Secret, falls nicht vorhanden
    #if not user.totp_secret:
    #    user.totp_secret = pyotp.random_base32()
    #    db.session.commit()

    #totp = pyotp.TOTP(user.totp_secret)
    #otp_uri = totp.provisioning_uri(name=user.email, issuer_name="ParetoCalc V2")

    # QR-Code generieren
    #qr_img = qrcode.make(otp_uri)
    #buf = io.BytesIO()
    #qr_img.save(buf, format="PNG")
    #qr_code_data = buf.getvalue()

    #if request.method == "POST":
        # Code prüfen
    #    code = request.form.get("code", "")
    #    if totp.verify(code):
    #        user.twofa_enabled = True  # NEU: 2FA aktivieren
    #        db.session.commit()
    #        return "2FA success"
    #    else:
    #        return "Falscher Code"

    # GET => Template + embedded QR
    #import base64
    #b64_qr = base64.b64encode(qr_code_data).decode()
    #return render_template("2fa_setup.html", b64_qr=b64_qr)