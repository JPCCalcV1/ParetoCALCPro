from flask import Blueprint, render_template, request, jsonify, session, current_app
from functools import wraps
from datetime import datetime, timedelta

# Achtung: importiere NICHT erneut "db = SQLAlchemy()",
# sondern nutze dein existing db-Objekt
from models.user import db, User
from models.payment_log import PaymentLog
from core.extensions import csrf

admin_bp = Blueprint("admin_bp", __name__)

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        uid = session.get("user_id")
        if not uid:
            return jsonify({"error": "Not logged in"}), 401
        user = User.query.get(uid)
        if not user or not user.is_admin:
            return jsonify({"error": "No admin rights"}), 403
        return f(*args, **kwargs)
    return decorated

@admin_bp.route("/create_admin_temp", methods=["POST"])
@csrf.exempt
def create_admin_temp():
    """
    Erstellt schnell einen Admin-User.
    JSON-Beispiel: { "email":"admin@paretocalc.com", "password":"abc123" }
    """
    data = request.get_json() or {}
    email = data.get("email","").strip().lower()
    raw_pw = data.get("password","")

    if not email or not raw_pw:
        return jsonify({"error":"Email/Pass fehlt"}), 400

    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error":"User existiert bereits"}), 400

    new_user = User(email, raw_pw)
    # Admin = license_tier = "extended", 1 Jahr
    new_user.license_tier = "extended"
    new_user.license_expiry = datetime.now() + timedelta(days=365)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message": f"Admin {email} angelegt"}), 200

@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def admin_dashboard():
    """
    Rendert das Admin-Dashboard Template (admin_dashboard.html).
    """
    return render_template("admin_dashboard.html")

@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    """
    Liefert JSON-Liste aller User (inkl. license, addons, GPT-Counts).
    """
    users = User.query.all()
    current_app.logger.info("[admin/users] Found %d users from DB %s", len(users),
                            current_app.config["SQLALCHEMY_DATABASE_URI"])
    out = []
    for u in users:
        out.append({
            "id": u.id,
            "email": u.email,
            "license": u.license_tier,
            "license_expiry": str(u.license_expiry) if u.license_expiry else None,
            "addons": u.addons,
            "gpt_used_count": u.gpt_used_count,
            "gpt_allowed_count": u.gpt_allowed_count
        })
    return jsonify(out)

@admin_bp.route("/set_license", methods=["POST"])
@csrf.exempt
@admin_required
def set_license():
    """
    Setzt license_tier eines Users manuell.
    JSON-Beispiel: { "user_id": 5, "license_tier": "premium" }
    """
    data = request.get_json() or {}
    user_id = data.get("user_id")
    tier = data.get("license_tier", "test")

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error":"User not found"}), 404

    user.license_tier = tier
    # GPT-Limits je nach Tier
    if tier == "test":
        user.gpt_allowed_count = 10
    elif tier == "plus":
        user.gpt_allowed_count = 25
    elif tier == "premium":
        user.gpt_allowed_count = 50
    elif tier == "extended":
        user.gpt_allowed_count = 200
    else:
        user.gpt_allowed_count = 0

    # Reset usage
    user.gpt_used_count = 0
    db.session.commit()
    return jsonify({"message": f"{user.email} => {tier}"}), 200

@admin_bp.route("/addon/set", methods=["POST"])
@csrf.exempt
@admin_required
def set_addon():
    """
    Fügt dem User ein Addon hinzu (z. B. 'GPT-Export').
    JSON: { "user_id": 5, "addon": "GPT-Export" }
    """
    data = request.get_json() or {}
    user_id = data.get("user_id")
    addon = data.get("addon","").strip()

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error":"User not found"}), 404

    curr = user.addons.split(",") if user.addons else []
    if addon and addon not in curr:
        curr.append(addon)
    user.addons = ",".join([c for c in curr if c])
    db.session.commit()
    return jsonify({"message": f"Addon '{addon}' set for {user.email}"}), 200

@admin_bp.route("/stripe_events", methods=["GET"])
@admin_required
def list_stripe_events():
    """
    Zeigt die PaymentLogs aus der DB an.
    """
    logs = PaymentLog.query.all()
    out = []
    for l in logs:
        out.append({
            "id": l.id,
            "event_id": l.event_id,
            "event_type": l.event_type,
            "raw_data": l.raw_data[:200],
            "created_at": str(l.created_at)
        })
    return jsonify(out)

@admin_bp.route("/set_gpt_count", methods=["POST"])
@csrf.exempt
@admin_required
def set_gpt_count():
    """
    Manuell GPT-Kontingent (allowed_count) verändern.
    JSON: { "user_id": 5, "allowed_count": 100 }
    """
    data = request.get_json() or {}
    user_id = data.get("user_id")
    allowed_count = data.get("allowed_count", 50)

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error":"User not found"}), 404

    user.gpt_allowed_count = allowed_count
    db.session.commit()
    return jsonify({"message": f"{user.email} => GPT allowed {allowed_count}"}), 200

# NEU: Delete user
@admin_bp.route("/delete_user", methods=["POST"])
@csrf.exempt
@admin_required
def delete_user():
    """
    Löscht einen User komplett aus der Datenbank.
    JSON-Beispiel: { "user_id": 5 }
    """
    data = request.get_json() or {}
    user_id = data.get("user_id")

    if not user_id:
        return jsonify({"error":"user_id fehlt"}), 400

    user = User.query.get(user_id)
    if not user:
        return jsonify({"error":"User not found"}), 404

    # Optional: Verhindern, dass man sich selbst löscht, oder den Admin user?
    # if user.email == "admin@paretocalc.com":
    #    return jsonify({"error":"Cannot delete main admin"}), 403

    db.session.delete(user)
    db.session.commit()
    return jsonify({"message": f"User {user.email} wurde gelöscht"}), 200

# FILE: routes/routes_admin.py (Erweiterung)
@admin_bp.route("/cron/trial_reminder", methods=["GET"])
def cron_trial_reminder():
    """
    Durchläuft alle user, die z.B. ABO + TRIAL in 2 Tagen enden -> Email
    """
    # 1) Hole ABO-User
    #    "trial_end" -> da du license_expiry in user hast
    #    ODER du guckst in user.stripe_subscription_id -> stripe data
    #    Wir machen hier mal nur user.license_expiry:
    from helpers.sendgrid_helper import send_email

    soon = datetime.now() + timedelta(days=2)

    # Bsp: wir wollen user, die license_tier in [plus, premium], license_expiry < soon, >= now
    # und stripe_subscription_id != None
    users = User.query.filter(
        User.stripe_subscription_id != None,
        User.license_tier.in_(["plus","premium","extended"]),
        User.license_expiry >= datetime.now(),
        User.license_expiry <= soon
    ).all()

    cnt = 0
    for u in users:
        subject = "Hinweis: Deine Testphase endet in Kürze"
        txt = f"""Hallo {u.email},
deine Testphase oder dein Trial endet bald (am {u.license_expiry}).
Falls du kündigen möchtest, besuche bitte dein Dashboard /account.
Ansonsten läuft dein ABO wie geplant weiter.
Grüße,
Dein ParetoCalc-Team
"""
        send_email(u.email, subject, txt)
        cnt += 1

    return jsonify({"message": f"Reminder sent to {cnt} user(s)."})