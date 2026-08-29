"""
SQLAlchemy ORM models for the portfolio.
All timestamps are stored as UTC. No raw SQL used.
"""
from datetime import datetime, timezone
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


def _utcnow():
    return datetime.now(timezone.utc)


class AdminUser(UserMixin, db.Model):
    __tablename__ = "admin_user"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), unique=True, nullable=False, index=True)
    email = db.Column(db.String(160), nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    def set_password(self, password):
        # Werkzeug pbkdf2:sha256 by default — no plaintext storage.
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


class Profile(db.Model):
    """Single-row table holding the owner's public profile."""
    __tablename__ = "profile"
    id = db.Column(db.Integer, primary_key=True)
    full_name = db.Column(db.String(120), default="Your Name")
    title = db.Column(db.String(120), default="Cybersecurity Professional")
    subtitle = db.Column(db.String(160), default="Linux & Network Specialist")
    description = db.Column(db.Text, default="")
    location = db.Column(db.String(120), default="")
    email = db.Column(db.String(160), default="")
    profile_image = db.Column(db.String(255), default="")
    cv_url = db.Column(db.String(255), default="")
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    @classmethod
    def get_solo(cls):
        row = cls.query.first()
        if row is None:
            row = cls()
            db.session.add(row)
            db.session.commit()
        return row


class Skill(db.Model):
    __tablename__ = "skill"
    id = db.Column(db.Integer, primary_key=True)
    category = db.Column(db.String(80), nullable=False, default="General")
    name = db.Column(db.String(120), nullable=False)
    enabled = db.Column(db.Boolean, default=True, nullable=False)
    display_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)

    @classmethod
    def grouped(cls):
        rows = cls.query.filter_by(enabled=True).order_by(
            cls.category, cls.display_order, cls.name
        ).all()
        groups = {}
        for r in rows:
            groups.setdefault(r.category, []).append(r)
        return groups


class Project(db.Model):
    __tablename__ = "project"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(160), nullable=False)
    slug = db.Column(db.String(200), unique=True, nullable=False, index=True)
    short_description = db.Column(db.String(300), default="")
    full_description = db.Column(db.Text, default="")
    category = db.Column(db.String(80), default="General")
    technologies = db.Column(db.Text, default="")  # comma-separated
    github_url = db.Column(db.String(255), default="")
    demo_url = db.Column(db.String(255), default="")
    image = db.Column(db.String(255), default="")
    featured = db.Column(db.Boolean, default=False, nullable=False)
    published = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)


class Writeup(db.Model):
    __tablename__ = "writeup"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    summary = db.Column(db.Text, default="")
    content = db.Column(db.Text, default="")  # markdown-ish / safe HTML
    category = db.Column(db.String(80), default="General")
    tags = db.Column(db.Text, default="")  # comma-separated
    cover_image = db.Column(db.String(255), default="")
    published_date = db.Column(db.DateTime, default=_utcnow)
    status = db.Column(db.String(20), default="published", nullable=False)  # draft|published
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)


class Experience(db.Model):
    __tablename__ = "experience"
    id = db.Column(db.Integer, primary_key=True)
    company = db.Column(db.String(160), nullable=False)
    position = db.Column(db.String(160), nullable=False)
    start_date = db.Column(db.String(40), default="")
    end_date = db.Column(db.String(40), default="")
    description = db.Column(db.Text, default="")
    technologies = db.Column(db.Text, default="")
    display_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)


class Certification(db.Model):
    __tablename__ = "certification"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    organization = db.Column(db.String(160), default="")
    date = db.Column(db.String(40), default="")
    credential_url = db.Column(db.String(255), default="")
    description = db.Column(db.Text, default="")
    display_order = db.Column(db.Integer, default=0, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)


class Book(db.Model):
    """E-book / PDF content shown in the public 'Books' reader."""
    __tablename__ = "book"
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    slug = db.Column(db.String(220), unique=True, nullable=False, index=True)
    author = db.Column(db.String(160), default="")
    description = db.Column(db.Text, default="")
    category = db.Column(db.String(80), default="General")
    cover_image = db.Column(db.String(255), default="")
    pdf_path = db.Column(db.String(255), default="")  # relative to uploads/
    display_order = db.Column(db.Integer, default=0, nullable=False)
    published = db.Column(db.Boolean, default=True, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)


class SocialLink(db.Model):
    __tablename__ = "social_link"
    id = db.Column(db.Integer, primary_key=True)
    label = db.Column(db.String(60), nullable=False)
    url = db.Column(db.String(255), default="")
    icon = db.Column(db.String(40), default="link")  # simple named icon
    display_order = db.Column(db.Integer, default=0, nullable=False)
    enabled = db.Column(db.Boolean, default=True, nullable=False)

    @classmethod
    def ensure_defaults(cls):
        if cls.query.count() == 0:
            defaults = [
                ("GitHub", "https://github.com/", "github", 1),
                ("LinkedIn", "https://linkedin.com/", "linkedin", 2),
                ("Hack The Box", "https://app.hackthebox.com/", "htb", 3),
            ]
            for label, url, icon, order in defaults:
                db.session.add(cls(label=label, url=url, icon=icon, display_order=order))
            db.session.commit()


class SiteSettings(db.Model):
    """
    Single-row table for site-wide + appearance settings.
    'solo' access pattern: always read the first (only) row.
    """
    __tablename__ = "site_settings"
    id = db.Column(db.Integer, primary_key=True)

    # Site
    site_name = db.Column(db.String(120), default="Portfolio")
    site_description = db.Column(db.Text, default="Cybersecurity portfolio.")
    email = db.Column(db.String(160), default="")
    location = db.Column(db.String(120), default="")
    cv_url = db.Column(db.String(255), default="")
    github_url = db.Column(db.String(255), default="")
    linkedin_url = db.Column(db.String(255), default="")
    htb_url = db.Column(db.String(255), default="")
    favicon = db.Column(db.String(255), default="")

    # SEO
    seo_title = db.Column(db.String(160), default="Portfolio")
    seo_description = db.Column(db.Text, default="")
    robots_index = db.Column(db.Boolean, default=True, nullable=False)

    # Appearance (CSS variables)
    primary_color = db.Column(db.String(16), default="#00ff9c")
    accent_color = db.Column(db.String(16), default="#00d4ff")
    background_color = db.Column(db.String(16), default="#0a0e14")
    card_color = db.Column(db.String(16), default="#131a24")
    text_color = db.Column(db.String(16), default="#e6edf3")
    muted_color = db.Column(db.String(16), default="#8b98a5")
    border_radius = db.Column(db.Integer, default=8, nullable=False)

    logo = db.Column(db.String(255), default="")
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    @classmethod
    def get_solo(cls):
        row = cls.query.first()
        if row is None:
            row = cls()
            db.session.add(row)
            db.session.commit()
        return row

    @classmethod
    def ensure_defaults(cls):
        cls.get_solo()


class ContactMessage(db.Model):
    __tablename__ = "contact_message"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(120), nullable=False)
    email = db.Column(db.String(160), nullable=False)
    subject = db.Column(db.String(200), default="")
    message = db.Column(db.Text, nullable=False)
    read = db.Column(db.Boolean, default=False, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow, nullable=False)
