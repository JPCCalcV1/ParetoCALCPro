""" START OF FILE: app.py - KAPITEL 1 """

import os
from datetime import datetime, timedelta
from flask import Flask, session, request, jsonify, render_template
try:
    from flask_migrate import Migrate
except ImportError:
    pass

# Modelle & Extensions
from models.user import db, User
from core.extensions import csrf, limiter

# Blueprints
from routes.routes_auth import auth_bp
from routes.routes_payment import payment_bp
from routes.routes_admin import admin_bp
from routes.mycalc_routes import mycalc_bp
from routes.routes_calc_param import param_calc_bp
from routes.routes_calc_takt import takt_calc_bp
from routes.routes_landing import landing_bp

def create_app():
    app = Flask(__name__)

    # Basis-Konfiguration
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "supersecret")
    db_url = os.getenv("DATABASE_URL", "sqlite:///test.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    print("DEBUG DB-URL =", app.config["SQLALCHEMY_DATABASE_URI"])
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    Migrate(app, db)  # Falls du migrations nutzt

    # CSRF & Rate-Limiter
    csrf.init_app(app)
    limiter.init_app(app)

    # Blueprint-Registrierung
    app.register_blueprint(landing_bp)        # kein prefix => "/"
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(payment_bp, url_prefix="/pay")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(mycalc_bp, url_prefix="/mycalc")
    app.register_blueprint(param_calc_bp, url_prefix="/calc/param")
    app.register_blueprint(takt_calc_bp, url_prefix="/calc/takt")

    @app.route("/")
    def landing_page():
        return render_template("landing_page.html")

    @app.route("/upgrade", methods=["GET"])
    def show_upgrade():
        return render_template("upgrade_page.html")

    @app.before_request
    def require_login():
        """
        Verhindert 307/401 bei /pay/webhook,
        da Stripe dort ohne Session-Zugriff POSTet.
        """
        public_routes = [
            "/",
            "/auth/login",
            "/auth/register",
            "/auth/whoami",
            "/favicon.ico",
            "/robots.txt",
            "/pay/webhook"  # Wichtig!
        ]
        if not any(request.path.startswith(r) for r in public_routes):
            if not session.get("user_id"):
                return jsonify({"error": "Not logged in"}), 401

    @app.before_request
    def check_license():
        # erst checken, ob route public ist oder ob user eingeloggt ist
        public_routes = [...]
        if request.path.startswith("/mycalc"):
            user_id = session.get("user_id")
            if not user_id:
                return redirect("/auth/login")
            user = User.query.get(user_id)
            if user.license_tier == "test":
                return redirect("/upgrade")
        # oder „license_level == no_access“ -> redirect("/upgrade")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)

""" END OF FILE: app.py - KAPITEL 1 """