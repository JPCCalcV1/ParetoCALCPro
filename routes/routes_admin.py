# routes/routes_admin.py

from flask import Blueprint, render_template
from flask_login import login_required, current_user
from core.extensions import limiter

admin_bp = Blueprint('admin_bp', __name__)

# Limitiere alle Routen in diesem Blueprint auf 5 requests pro Minute
@admin_bp.before_request
@limiter.limit("5/minute")
def admin_rate_limit():
    pass  # Leer, da wir nur das Limit setzen

@admin_bp.route('/dashboard')
@login_required
def dashboard():
    if not current_user.is_admin:
        return "Nur Admin erlaubt", 403
    return render_template('admin/dashboard.html')

@admin_bp.route('/users')
@login_required
def users_list():
    if not current_user.is_admin:
        return "Nur Admin erlaubt", 403

    # Dummy-Daten (später echte DB-Abfrage)
    all_users = [
        {"username": "alice",   "email": "alice@example.com",   "role": "admin"},
        {"username": "bob",     "email": "bob@example.com",     "role": "user"},
        {"username": "charlie", "email": "charlie@example.com", "role": "user"}
    ]

    return render_template('admin/users.html', all_users=all_users)