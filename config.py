# config.py
import os

class DevConfig:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'sqlite:///paretocalc_dev.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    WTF_CSRF_ENABLED = True
    WTF_CSRF_SECRET_KEY = os.environ.get('WTF_CSRF_SECRET_KEY', 'another-dev-secret')

    DEBUG = True

class ProdConfig(DevConfig):
    DEBUG = False
    # Z. B. echte PostgreSQL-URL auf Render:
    # SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://user:pass@host/dbname')
    # SECRET_KEY = os.environ['SECRET_KEY']
    # Weitere Prod-Settings ...