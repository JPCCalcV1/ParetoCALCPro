# routes/routes_auth.py

import pyotp
import qrcode
import io
from flask import Blueprint, request, render_template, redirect, url_for, session, flash
from flask_login import login_user, current_user, logout_user, login_required
from core.extensions import db, limiter
from models.user import User

auth_bp = Blueprint('auth_bp', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
@limiter.limit("5/minute")
def admin_login():
    """Einfacher Admin-Login mit TOTP-Check (falls secret vorhanden)."""
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password) and user.is_admin:
            login_user(user)
            if user.totp_secret:
                return redirect(url_for('auth_bp.totp_verify'))
            else:
                return redirect(url_for('auth_bp.totp_setup'))
        else:
            flash("Ungültige Admin-Credentials", "danger")

    return render_template('admin/login.html')

@auth_bp.route('/logout')
@login_required
def admin_logout():
    logout_user()
    return redirect(url_for('auth_bp.admin_login'))

@auth_bp.route('/totp_setup', methods=['GET', 'POST'])
@login_required
def totp_setup():
    """Setzt TOTP-Secret und zeigt QR-Code an."""
    if not current_user.is_admin:
        return "Nur Admin erlaubt", 403

    if request.method == 'POST':
        code = request.form.get('code')
        totp = pyotp.TOTP(current_user.totp_secret)
        if totp.verify(code):
            flash("TOTP eingerichtet!", "success")
            return redirect(url_for('auth_bp.totp_verify'))
        else:
            flash("Falscher Code, versuche es erneut.", "danger")

    # Secret generieren, falls noch nicht vorhanden
    if not current_user.totp_secret:
        new_secret = pyotp.random_base32()
        current_user.totp_secret = new_secret
        db.session.commit()
    else:
        new_secret = current_user.totp_secret

    # QR-Code erzeugen
    otp_uri = pyotp.TOTP(new_secret).provisioning_uri(
        name=current_user.email,
        issuer_name="ParetoCalc V2"
    )
    qr_img = qrcode.make(otp_uri)
    buf = io.BytesIO()
    qr_img.save(buf, format='PNG')
    qr_code_data = buf.getvalue()

    return render_template('admin/totp_setup.html', qr_code_data=qr_code_data)

@auth_bp.route('/totp_verify', methods=['GET', 'POST'])
@login_required
def totp_verify():
    """Fragt den 6-stelligen TOTP-Code ab."""
    if not current_user.is_admin:
        return "Nur Admin erlaubt", 403

    if request.method == 'POST':
        code = request.form.get('code')
        totp = pyotp.TOTP(current_user.totp_secret)
        if totp.verify(code):
            session['2fa_verified'] = True
            flash("2FA erfolgreich!", "success")
            return redirect(url_for('auth_bp.admin_dashboard_placeholder'))
        else:
            flash("Falscher TOTP-Code, bitte erneut eingeben.", "danger")

    return render_template('admin/totp_verify.html')

@auth_bp.route('/dashboard')
@login_required
def admin_dashboard_placeholder():
    """Simple Placeholder, hier könnte man später auf /admin/dashboard verweisen."""
    if not current_user.is_admin:
        return "Nur Admin erlaubt", 403
    return render_template('admin/dashboard_placeholder.html')