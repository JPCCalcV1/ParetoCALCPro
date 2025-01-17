# routes/routes_admin.py

from flask import Blueprint, render_template, request, jsonify, session
from functools import wraps
from datetime import datetime, timedelta
from models.user import db, User
from models.payment_log import PaymentLog
from core.extensions import csrf

admin_bp = Blueprint("admin_bp", __name__)

@admin_bp.route("/create_admin_temp", methods=["POST"])
@csrf.exempt
def create_admin_temp():
    data = request.get_json() or {}
    email = data.get("email","").strip().lower()
    raw_pw = data.get("password","")
    if not email or not raw_pw:
        return jsonify({"error":"Email/Pass fehlt"}),400

    # Check, ob user existiert
    existing = User.query.filter_by(email=email).first()
    if existing:
        return jsonify({"error":"User existiert bereits"}),400

    new_user = User(email, raw_pw)
    # Admin = z.B. license_tier = "extended"
    new_user.license_tier = "extended"
    new_user.license_expiry = datetime.now() + timedelta(days=365)
    db.session.add(new_user)
    db.session.commit()

    return jsonify({"message":f"Admin {email} angelegt"}),200

def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        uid = session.get("user_id")
        if not uid:
            return jsonify({"error":"Not logged in"}),401
        user = User.query.get(uid)
        # Hier: check user.is_admin
        if not user or not user.is_admin:
            return jsonify({"error":"No admin rights"}),403
        return f(*args, **kwargs)
    return decorated

@admin_bp.route("/dashboard", methods=["GET"])
@admin_required
def admin_dashboard():
    return render_template("admin_dashboard.html")

@admin_bp.route("/users", methods=["GET"])
@admin_required
def list_users():
    users= User.query.all()
    out=[]
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
    data= request.get_json() or {}
    user_id= data.get("user_id")
    tier= data.get("license_tier","test")
    user= User.query.get(user_id)
    if not user:
        return jsonify({"error":"User not found"}),404

    user.license_tier= tier
    if tier=="test":
        user.gpt_allowed_count=10
    elif tier=="plus":
        user.gpt_allowed_count=25
    elif tier=="premium":
        user.gpt_allowed_count=50
    elif tier=="extended":
        user.gpt_allowed_count=200
    else:
        user.gpt_allowed_count=0

    user.gpt_used_count=0
    db.session.commit()
    return jsonify({"message":f"{user.email} => {tier}"}),200

@admin_bp.route("/addon/set", methods=["POST"])
@csrf.exempt
@admin_required
def set_addon():
    data= request.get_json() or {}
    user_id= data.get("user_id")
    addon= data.get("addon","").strip()

    user= User.query.get(user_id)
    if not user:
        return jsonify({"error":"User not found"}),404

    curr= user.addons.split(",") if user.addons else []
    if addon and addon not in curr:
        curr.append(addon)
    user.addons= ",".join([c for c in curr if c])
    db.session.commit()
    return jsonify({"message":f"Addon '{addon}' set for {user.email}"}),200

@admin_bp.route("/stripe_events", methods=["GET"])
@admin_required
def list_stripe_events():
    logs= PaymentLog.query.all()
    out=[]
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
    data= request.get_json() or {}
    user_id= data.get("user_id")
    allowed_count= data.get("allowed_count",50)
    user= User.query.get(user_id)
    if not user:
        return jsonify({"error":"User not found"}),404

    user.gpt_allowed_count= allowed_count
    db.session.commit()
    return jsonify({"message":f"{user.email} => GPT allowed {allowed_count}"}),200