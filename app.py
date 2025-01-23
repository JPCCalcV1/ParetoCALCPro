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
    app.config["SESSION_COOKIE_SAMESITE"] = "None"

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
    # --- Blueprints ---
    app.register_blueprint(landing_bp)  # => "/"
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(payment_bp, url_prefix="/pay")
    app.register_blueprint(admin_bp, url_prefix="/admin")
    app.register_blueprint(mycalc_bp, url_prefix="/mycalc")
    app.register_blueprint(param_calc_bp, url_prefix="/calc/param")
    app.register_blueprint(takt_calc_bp, url_prefix="/calc/takt")
    app.register_blueprint(account_bp, url_prefix="/account")
    app.register_blueprint(legal_bp, url_prefix="")

    # OPTIONAL: Falls du die alte /upgrade-Seite gar nicht mehr willst,
    # kannst du sie einfach weglassen oder eine "Redirect-Route" bauen:
    @app.route("/upgrade")
    def upgrade_redirect():
        # Sende User zur Landing-Page, Absprung #pricing
        return redirect("/#pricing")

    # Oder entferne "/upgrade" einfach komplett, wenn gar nicht mehr benötigt

    @app.route("/")
    def landing_page():
        return render_template("landing_page.html")

    # ---------------------------
    # 1) BEFORE_REQUEST: require_login
    # ---------------------------
    @app.before_request
    def require_login():
        # Public routes - alles, was ohne Login erreichbar sein soll:
        public_routes = [
            "/auth/login",
            "/auth/register",
            "/auth/whoami",
            "/favicon.ico",
            "/robots.txt",
            "/pay/webhook",
            "/pay/success",
            "/pay/cancel",
            "/",  # Landing
            "/static/",  # statische Assets
        ]
        # => alle Pfade, die mit obigen Strings beginnen, sind öffentlich

        path = request.path

        # 1) Check, ob path PUBLIC ist => return (kein Zwangslogin)
        #    => Sonderfall: if path.startswith("/static/") => return
        if path == "/" or path.startswith("/static/"):
            return
        if any(path.startswith(r) for r in public_routes):
            return

        # 2) Sonst => user_id + sso_token checken
        user_id = session.get("user_id")
        sso_token = session.get("sso_token")
        if not user_id or not sso_token:
            # Hier KEIN 401 => Lieber redirect zur Landing
            return redirect("/?msg=not-logged-in")

        user = User.query.get(user_id)
        if not user or user.current_session_token != sso_token:
            # Jemand hat sich mit dem gleichen Account in einem anderen Browser eingeloggt
            session.clear()
            return redirect("/?msg=session-invalid")

    # ---------------------------
    # 2) BEFORE_REQUEST: check_license
    # ---------------------------
    @app.before_request
    def check_license():
        """
        Gilt NUR für /mycalc-Routen -> Nur wenn Abo != 'test' und != 'no_access'
        """
        path = request.path
        if path.startswith("/mycalc"):
            user_id = session.get("user_id")
            if not user_id:
                return redirect("/auth/login?msg=need-login")
            user = User.query.get(user_id)
            if not user:
                return redirect("/auth/login?msg=user-missing")

            # "test" => ab zum Landing + #pricing
            # "no_access" => ab zum Landing + #pricing
            # license_level() gibt "no_access" zurück, wenn abgelaufen
            if user.license_tier == "test" or user.license_level() == "no_access":
                return redirect("/#pricing?msg=abo-required")

    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=False)

""" END OF FILE: app.py - KAPITEL 1 """