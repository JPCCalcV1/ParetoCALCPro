""" START OF FILE: app.py - KAPITEL 1 """

import os
from datetime import datetime, timedelta

# Wichtig: Hier importieren wir auch "redirect", damit NameError verschwindet
from flask import Flask, session, request, jsonify, render_template, redirect

try:
    from flask_migrate import Migrate
except ImportError:
    Migrate = None

# Modelle & Extensions
from models.user import db, User
from core.extensions import csrf, limiter
from flask_login import LoginManager  # <-- Neu hinzugefügt

# Blueprints
from routes.routes_auth import auth_bp
from routes.routes_payment import payment_bp
from routes.routes_admin import admin_bp
from routes.mycalc_routes import mycalc_bp
from routes.routes_calc_param import param_calc_bp
from routes.routes_calc_takt import takt_calc_bp
from routes.routes_landing import landing_bp
from routes.routes_account import account_bp
from routes.legal import legal_bp

def create_app():
    app = Flask(__name__)

    # Basis-Konfiguration
    app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "supersecret")
    db_url = os.getenv("DATABASE_URL", "sqlite:///test.db")
    app.config["SQLALCHEMY_DATABASE_URI"] = db_url
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    app.config["SESSION_COOKIE_SECURE"] = True
    app.config["SESSION_COOKIE_HTTPONLY"] = True
    app.config["SESSION_COOKIE_SAMESITE"] = "Strict"

    print("DEBUG DB-URL =", app.config["SQLALCHEMY_DATABASE_URI"])

    db.init_app(app)
    if Migrate:
        Migrate(app, db)  # Falls du migrations nutzt

    # CSRF & Rate-Limiter
    csrf.init_app(app)
    limiter.init_app(app)
    # 1) LoginManager anlegen
    login_manager = LoginManager()
    login_manager.init_app(app)  # <-- Das sagt Flask: wir nutzen Flask-Login

    @login_manager.user_loader
    def load_user(user_id):
        # Muss ein User-Objekt zurückgeben, wenn existiert, sonst None
        return User.query.get(int(user_id))
    # Blueprint-Registrierung
    # Achte darauf, dass *genau* dieses payment_bp kommt, in dem /checkout-sub definiert ist
    app.register_blueprint(landing_bp)                   # kein prefix => "/"
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(payment_bp, url_prefix="/pay")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(mycalc_bp, url_prefix="/mycalc")
    app.register_blueprint(param_calc_bp, url_prefix="/calc/param")
    app.register_blueprint(takt_calc_bp, url_prefix="/calc/takt")
    app.register_blueprint(account_bp, url_prefix="/account")
    app.register_blueprint(legal_bp, url_prefix="")

    @app.route("/")
    def landing_page():
        return render_template("landing_page.html")

    @app.route("/upgrade", methods=["GET"])
    def show_upgrade():
        """Zeigt deine Upgrade-Seite an.
        Hier klickt der User ggf. auf ein Subscription-Button,
        welcher ein POST /pay/checkout-sub auslöst."""
        return render_template("upgrade_page.html")

    ###################################################################
    ## BEFORE REQUEST 1: require_login
    ###################################################################
    @app.before_request
    def require_login():
        # Diese Routen dürfen auch ohne Login besucht werden
        public_routes = [
            "/", "/auth/login", "/auth/register", "/auth/whoami",
            "/favicon.ico", "/robots.txt", "/pay/webhook", "/upgrade"
        ]
        if not any(request.path.startswith(r) for r in public_routes):
            # Neu: Prüfung, ob user_id & Token in der Session vorhanden und gültig
            user_id = session.get("user_id")
            sso_token = session.get("sso_token")
            if not user_id or not sso_token:
                return jsonify({"error": "Not logged in"}), 401

            # Abgleich mit DB
            user = User.query.get(user_id)
            if not user or user.current_session_token != sso_token:
                session.clear()
                return redirect("/auth/login")

    ###################################################################
    ## BEFORE REQUEST 2: check_license
    ###################################################################
    @app.before_request
    def check_license():
        # Nur /mycalc braucht 'echtes' Abo => Abfangen
        if request.path.startswith("/mycalc"):
            user_id = session.get("user_id")
            if not user_id:
                # Wenn nicht eingeloggt => redirect => /auth/login
                return redirect("/auth/login")
            user = User.query.get(user_id)
            if not user:
                # Fallback
                return redirect("/auth/login")
            # Falls "test" => ab zum Upgrade
            if user.license_tier == "test":
                return redirect("/upgrade?msg=Bitte%20ein%20Abo%20abschliessen!")
            # Falls "no_access" => ab zum Upgrade
            if user.license_level() == "no_access":
                return redirect("/upgrade?msg=Zugang%20abgelaufen!")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=False)

""" END OF FILE: app.py - KAPITEL 1 """