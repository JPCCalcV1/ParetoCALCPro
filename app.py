# app.py
import os
import logging
from flask import Flask
from config import DevConfig
from core.extensions import db, login_manager, csrf, limiter

# Blueprint-Imports
from routes.routes_auth import auth_bp
from routes.routes_admin import admin_bp
from routes.routes_calc import calc_bp
from routes.routes_gpt import gpt_bp
from routes.routes_payment import payment_bp
from routes.routes_calc_main import main_calc_bp
from routes.routes_calc_param import param_calc_bp
from routes.routes_calc_takt import takt_calc_bp
from routes.routes_landing import landing_bp

def create_app():
    app = Flask(__name__)
    app.config.from_object(DevConfig)

    # Optional: Basic Logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s'
    )

    # Init Extensions
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    limiter.init_app(app)

    # Blueprints
    app.register_blueprint(auth_bp,     url_prefix='/admin')
    app.register_blueprint(admin_bp,    url_prefix='/admin')
    app.register_blueprint(calc_bp,     url_prefix='/calc')
    app.register_blueprint(gpt_bp,      url_prefix='/gpt')
    app.register_blueprint(payment_bp,  url_prefix='/pay')
    app.register_blueprint(main_calc_bp,  url_prefix='/calc')
    app.register_blueprint(param_calc_bp, url_prefix='/calc/param')
    app.register_blueprint(takt_calc_bp,  url_prefix='/calc/takt')
    app.register_blueprint(landing_bp,  url_prefix='')

    return app

if __name__ == "__main__":
    flask_app = create_app()
    # Für Dev-Zwecke
    flask_app.run(host="0.0.0.0", port=5001, debug=True)