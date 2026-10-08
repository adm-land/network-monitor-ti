import os
from flask import Flask
from flask_login import LoginManager
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
from dotenv import load_dotenv
from werkzeug.middleware.proxy_fix import ProxyFix

load_dotenv()

db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()
login_manager.login_view = "main.login"
login_manager.login_message = "Inicia sesión para continuar."


def create_app(test_config=None):
    app = Flask(__name__)
    production = os.getenv("APP_ENV", "development").lower() == "production"

    app.config.update(
        SECRET_KEY=os.getenv("SECRET_KEY", "dev-key-change-me"),
        SQLALCHEMY_DATABASE_URI=os.getenv("DATABASE_URL", "sqlite:///network_monitor.db"),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        MONITOR_MODE=os.getenv("MONITOR_MODE", "live").lower(),
        MONITOR_TIMEOUT=float(os.getenv("MONITOR_TIMEOUT", "1.5")),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_SECURE=production,
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_SECURE=production,
    )
    if test_config:
        app.config.update(test_config)

    if production:
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)

    from .routes import bp
    app.register_blueprint(bp)

    with app.app_context():
        db.create_all()

    return app
