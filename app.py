""" START OF CODE: app.py (create_app) - With /pay/webhook as public route """

import os
from datetime import datetime, timedelta

from flask import Flask, session, request, jsonify, render_template
try:
    from flask_migrate import Migrate
except ImportError:
    pass

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

    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "supersecret")
    db_url = os.getenv("DATABASE_URL", "sqlite:///test.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)
    Migrate(app, db)

    # CSRF global
    csrf.init_app(app)
    # Rate-Limiter init
    limiter.init_app(app)

    # Blueprint-Registrierung
    app.register_blueprint(landing_bp)  # ohne url_prefix => "/"
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
        Ensure that routes not in the 'public_routes' require an active session.
        IMPORTANT: '/pay/webhook' is now in the public routes to avoid 307 or 401
        during Stripe Webhook calls.
        """
        public_routes = [
            "/",
            "/auth/login",
            "/auth/register",
            "/auth/whoami",
            "/stripe/webhook",
            "/pay/webhook",   # <-- ADDED TO ALLOW STRIPE WEBHOOK WITHOUT REDIRECT
            "/favicon.ico",
            "/robots.txt"
        ]

        # Wenn Route NICHT in den public_routes => check session
        if not any(request.path.startswith(r) for r in public_routes):
            if not session.get("user_id"):
                return jsonify({"error": "Not logged in"}), 401

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)
""" END OF CODE: app.py (create_app) - With /pay/webhook as public route """