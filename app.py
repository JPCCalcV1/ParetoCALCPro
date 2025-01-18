import os
from datetime import datetime, timedelta

from flask import Flask, session, request, jsonify, render_template
print(">>> Vor Import von flask_migrate <<<")
try:
    from flask_migrate import Migrate
    print(">>> Nach Import von flask_migrate <<<")
except ImportError as e:
    print(f"ImportError: {e}")

from models.user import db, User
from core.extensions import csrf, limiter

# Blueprints
from routes.routes_auth import auth_bp
from routes.routes_payment import payment_bp
from routes.routes_admin import admin_bp
from routes.mycalc_routes import mycalc_bp
from routes.routes_calc_param import param_calc_bp
from routes.routes_calc_takt import takt_calc_bp

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
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(payment_bp, url_prefix="/pay")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(mycalc_bp, url_prefix="/mycalc")
    app.register_blueprint(param_calc_bp, url_prefix="/calc/param")
    app.register_blueprint(takt_calc_bp, url_prefix="/calc/takt")


    # Optional: Public Landing
    @app.route("/")
    def landing_page():
        return render_template("landing_page.html")  # Deine Landing-Page o.Ä.

    # Beispiel: /upgrade => Template mit Payment-Buttons
    @app.route("/upgrade", methods=["GET"])
    def show_upgrade():
        return render_template("upgrade_page.html")

    # Vor jedem Request => check public vs. login
    @app.before_request
    def require_login():
        # Definiere public routes/prefixes
        public_routes = [
            "/",  # Landing
            "/auth/login",
            "/auth/register",
            "/auth/whoami",  # optional
            "/pay/webhook",
            "/favicon.ico",
            "/robots.txt"
        ]

        # Wenn Route NICHT in den public_routes beginnt => check session
        if not any(request.path.startswith(r) for r in public_routes):
            if not session.get("user_id"):
                return jsonify({"error": "Not logged in"}), 401

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True)


