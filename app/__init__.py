"""
Flask Portfolio — Application Factory
Lightweight cybersecurity portfolio. No heavy frontend, no build step.
Server-side rendered with Jinja2 + SQLite.
"""
import os
import secrets
from flask import Flask, g, request, session, render_template
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from datetime import datetime

# SQLAlchemy instance (initialized in create_app to keep factory pattern).
db = SQLAlchemy()
login_manager = LoginManager()
csrf = CSRFProtect()


def create_app(test_config=None):
    app = Flask(__name__, instance_relative_config=True)

    # --- Configuration ---------------------------------------------------
    app.config.from_mapping(
        SECRET_KEY=os.environ.get("SECRET_KEY", secrets.token_hex(32)),
        SQLALCHEMY_DATABASE_URI="sqlite:///" + os.path.join(
            app.instance_path,
            os.environ.get("DATABASE_PATH", "portfolio.db"),
        ),
        SQLALCHEMY_TRACK_MODIFICATIONS=False,
        # Disabling autoescape on some render is not needed; Jinja autoescapes.
        MAX_UPLOAD_MB=int(os.environ.get("MAX_UPLOAD_MB", "5")),
        # Hard ceiling on any request body. PDF uploads go up to 100 MB, so
        # give headroom. Flask returns 413 if exceeded (clean rejection).
        MAX_CONTENT_LENGTH=200 * 1024 * 1024,
        SITE_URL=os.environ.get("SITE_URL", "http://localhost:8000"),
        FLASK_DEBUG=(os.environ.get("FLASK_DEBUG", "false").lower() == "true"),
        # Cookie Secure is OFF by default so the site works over plain HTTP
        # (LAN testing, no TLS). In production behind Nginx+SSL set
        # BEHIND_PROXY=1 (or SESSION_COOKIE_SECURE=1) to enable Secure cookies.
        SESSION_COOKIE_SECURE=(os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        REMEMBER_COOKIE_SECURE=(os.environ.get("SESSION_COOKIE_SECURE", "0") == "1"),
        REMEMBER_COOKIE_HTTPONLY=True,
        REMEMBER_COOKIE_SAMESITE="Lax",
        PERMANENT_SESSION_LIFETIME=3600 * 8,  # 8h admin sessions
    )

    if test_config:
        app.config.update(test_config)

    # Trust X-Forwarded-* when running behind a reverse proxy (Nginx + SSL).
    if os.environ.get("BEHIND_PROXY") == "1":
        from werkzeug.middleware.proxy_fix import ProxyFix
        app.wsgi_app = ProxyFix(app.wsgi_app, x_for=1, x_proto=1, x_host=1)

    # Load .env values that may override (safe: .env is gitignored).
    if not test_config:
        # Pull a few env vars that should always win if present.
        for key in ("SECRET_KEY", "MAX_UPLOAD_MB", "SITE_URL", "FLASK_DEBUG",
                    "SESSION_COOKIE_SECURE", "BEHIND_PROXY"):
            env_val = os.environ.get(key)
            if env_val is not None:
                if key == "FLASK_DEBUG":
                    app.config["FLASK_DEBUG"] = env_val.lower() == "true"
                elif key == "SESSION_COOKIE_SECURE":
                    secure = env_val == "1"
                    app.config["SESSION_COOKIE_SECURE"] = secure
                    app.config["REMEMBER_COOKIE_SECURE"] = secure
                elif key in ("MAX_UPLOAD_MB",):
                    app.config[key] = int(env_val)
                else:
                    app.config[key] = env_val

    # Ensure instance and uploads dirs exist.
    os.makedirs(app.instance_path, exist_ok=True)
    os.makedirs(os.path.join(app.root_path, "..", "uploads"), exist_ok=True)

    # --- Database init ---------------------------------------------------
    db.init_app(app)
    login_manager.init_app(app)
    csrf.init_app(app)
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "warning"

    # Load the logged-in admin user from the session.
    from .models import AdminUser
    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(AdminUser, int(user_id))

    # SQLite performance & reliability tuning (small VPS friendly).
    @app.before_request
    def _sqlite_pragmas():
        if db.engine.url.drivername == "sqlite":
            conn = db.engine.raw_connection()
            try:
                cur = conn.cursor()
                # WAL = better concurrency + fewer write locks for a small site.
                cur.execute("PRAGMA journal_mode=WAL;")
                # Synchronous NORMAL is safe with WAL and much faster.
                cur.execute("PRAGMA synchronous=NORMAL;")
                # Reasonable cache for 1GB RAM box.
                cur.execute("PRAGMA cache_size=-8000;")  # ~8MB
                cur.execute("PRAGMA foreign_keys=ON;")
                cur.execute("PRAGMA busy_timeout=5000;")
                conn.commit()
            finally:
                conn.close()

    # --- Security headers -------------------------------------------------
    @app.after_request
    def _security_headers(resp):
        resp.headers["X-Content-Type-Options"] = "nosniff"
        # SAMEORIGIN (not DENY): the public PDF reader embeds same-origin
        # PDFs in an <iframe>; DENY would block that and show "refused to connect".
        resp.headers["X-Frame-Options"] = "SAMEORIGIN"
        resp.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        resp.headers["X-XSS-Protection"] = "1; mode=block"
        resp.headers["Content-Security-Policy"] = (
            "default-src 'self'; "
            "img-src 'self' data: https:; "
            "style-src 'self' 'unsafe-inline'; "
            "script-src 'self'; "
            "object-src 'self' blob:; "
            "frame-src 'self' blob:; "
            "base-uri 'self'; "
            # Allow same-origin framing so the in-page PDF reader works;
            # 'none' would break the modal. We still block cross-origin framing.
            "frame-ancestors 'self'; "
            "form-action 'self'"
        )
        resp.headers["Permissions-Policy"] = (
            "geolocation=(), microphone=(), camera=(), "
            "payment=(), usb=(), interest-cohort=()"
        )
        # Remove server fingerprinting where possible.
        resp.headers["Server"] = "portfolio"
        return resp

    # --- CSRF token global for templates ---------------------------------
    @app.context_processor
    def _inject_globals():
        from .models import SiteSettings, SocialLink, ContactMessage
        from flask_login import current_user
        settings = SiteSettings.get_solo()
        socials = SocialLink.query.order_by(SocialLink.display_order).all()
        year = datetime.utcnow().year
        counts_unread = 0
        try:
            if current_user.is_authenticated:
                counts_unread = ContactMessage.query.filter_by(read=False).count()
        except Exception:
            counts_unread = 0
        return dict(
            settings=settings,
            socials=socials,
            year=year,
            counts_unread=counts_unread,
            request_path=request.path,
        )

    # --- Blueprints -------------------------------------------------------
    from . import models  # noqa: F401  (register models with db metadata)
    from .models import SiteSettings, SocialLink
    from .auth import bp as auth_bp
    from .public import bp as public_bp
    from .admin import bp as admin_bp
    app.register_blueprint(auth_bp)
    app.register_blueprint(public_bp)
    app.register_blueprint(admin_bp)

    # --- Error handlers ---------------------------------------------------
    @app.errorhandler(404)
    def not_found(e):
        return render_template("errors/404.html"), 404

    @app.errorhandler(500)
    def server_error(e):
        # Never leak tracebacks in production.
        return render_template("errors/500.html"), 500

    @app.errorhandler(413)
    def request_too_large(e):
        return render_template("errors/413.html"), 413

    # --- CLI / init hook --------------------------------------------------
    with app.app_context():
        db.create_all()
        SiteSettings.ensure_defaults()
        SocialLink.ensure_defaults()

    return app
