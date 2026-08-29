"""
Public website blueprint: homepage, about, projects, write-ups, contact,
plus SEO endpoints (robots.txt, sitemap.xml). All content server-rendered
from the database. Output is autoescaped by Jinja2.
"""
import os
from flask import (
    Blueprint, render_template, request, redirect, url_for, abort, flash,
    send_from_directory, Response, current_app,
)
from flask_login import current_user
from .models import (
    db, Profile, Skill, Project, Writeup, Experience, Certification,
    SocialLink, SiteSettings, ContactMessage, Book,
)
from .forms import ContactForm
from . import utils

bp = Blueprint("public", __name__)


def _settings():
    return SiteSettings.get_solo()


def _seo_data():
    s = _settings()
    return {
        "seo_title": s.seo_title or s.site_name,
        "seo_description": s.seo_description or s.site_description,
        "canonical": request.url,
    }


@bp.route("/")
def home():
    profile = Profile.get_solo()
    settings = _settings()
    skills = Skill.grouped()
    featured = Project.query.filter_by(featured=True, published=True).order_by(
        Project.created_at.desc()).limit(3).all()
    latest_writeups = Writeup.query.filter_by(status="published").order_by(
        Writeup.published_date.desc()).limit(3).all()
    socials = SocialLink.query.filter_by(enabled=True).order_by(
        SocialLink.display_order).all()
    return render_template(
        "public/home.html",
        profile=profile, settings=settings, skills=skills,
        featured=featured, writeups=latest_writeups, socials=socials,
        **_seo_data(),
    )


@bp.route("/about")
def about():
    profile = Profile.get_solo()
    settings = _settings()
    skills = Skill.grouped()
    experience = Experience.query.order_by(Experience.display_order).all()
    certs = Certification.query.order_by(Certification.display_order).all()
    return render_template(
        "public/about.html", profile=profile, settings=settings,
        skills=skills, experience=experience, certs=certs, **_seo_data(),
    )


@bp.route("/projects")
def projects():
    page = request.args.get("page", 1, type=int)
    per_page = 9
    q = Project.query.filter_by(published=True)
    pagination = q.order_by(Project.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    return render_template(
        "public/projects.html", projects=pagination.items,
        pagination=pagination, settings=_settings(), **_seo_data(),
    )


@bp.route("/projects/<slug>")
def project_detail(slug):
    project = Project.query.filter_by(slug=slug, published=True).first_or_404()
    settings = _settings()
    return render_template(
        "public/project_detail.html", project=project, settings=settings,
        seo_title=project.title, seo_description=project.short_description,
        canonical=url_for("public.project_detail", slug=slug, _external=True),
    )


@bp.route("/writeups")
def writeups():
    page = request.args.get("page", 1, type=int)
    per_page = 6
    q = Writeup.query.filter_by(status="published")
    pagination = q.order_by(Writeup.published_date.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    return render_template(
        "public/writeups.html", writeups=pagination.items,
        pagination=pagination, settings=_settings(), **_seo_data(),
    )


@bp.route("/writeups/<slug>")
def writeup_detail(slug):
    w = Writeup.query.filter_by(slug=slug, status="published").first_or_404()
    html = utils.render_markdown(w.content)
    settings = _settings()
    return render_template(
        "public/writeup_detail.html", writeup=w, content_html=html,
        settings=settings, seo_title=w.title, seo_description=w.summary,
        canonical=url_for("public.writeup_detail", slug=slug, _external=True),
    )


@bp.route("/books")
def books():
    page = request.args.get("page", 1, type=int)
    per_page = 9
    q = Book.query.filter_by(published=True)
    pagination = q.order_by(Book.display_order, Book.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False)
    return render_template(
        "public/books.html", books=pagination.items,
        pagination=pagination, settings=_settings(), **_seo_data(),
    )


@bp.route("/books/<slug>")
def book_detail(slug):
    book = Book.query.filter_by(slug=slug, published=True).first_or_404()
    settings = _settings()
    return render_template(
        "public/book_detail.html", book=book, settings=settings,
        seo_title=book.title, seo_description=book.description,
        canonical=url_for("public.book_detail", slug=slug, _external=True),
    )


@bp.route("/contact", methods=["GET", "POST"])
def contact():
    form = ContactForm()
    if form.validate_on_submit():
        msg = ContactMessage(
            name=form.name.data, email=form.email.data,
            subject=form.subject.data or "(no subject)", message=form.message.data)
        db.session.add(msg)
        db.session.commit()
        flash("Message sent. Thank you!", "success")
        return redirect(url_for("public.contact"))
    return render_template(
        "public/contact.html", form=form, settings=_settings(), **_seo_data(),
    )


@bp.route("/uploads/<path:filename>")
def uploaded_file(filename):
    # Serve uploaded media from the uploads/ dir. CSP limits where it loads.
    upload_dir = current_app.config.get("UPLOAD_FOLDER", None)
    base = upload_dir or os.path.join(current_app.root_path, "..", "uploads")
    return send_from_directory(base, filename)


# --------------------------------------------------------------------------
# SEO
# --------------------------------------------------------------------------
@bp.route("/robots.txt")
def robots_txt():
    settings = _settings()
    allow = "Allow" if settings.robots_index else "Disallow"
    sitemap_url = (current_app.config.get("SITE_URL") or request.url_root).rstrip("/") + "/sitemap.xml"
    body = f"User-agent: *\n{allow}: /\nDisallow: /admin/\n\nSitemap: {sitemap_url}\n"
    return Response(body, mimetype="text/plain")


@bp.route("/sitemap.xml")
def sitemap_xml():
    settings = _settings()
    site_url = (current_app.config.get("SITE_URL") or request.url_root).rstrip("/")
    urls = [""]
    urls += ["/about", "/projects", "/writeups", "/contact", "/books"]
    for p in Project.query.filter_by(published=True).all():
        urls.append(f"/projects/{p.slug}")
    for w in Writeup.query.filter_by(status="published").all():
        urls.append(f"/writeups/{w.slug}")
    for b in Book.query.filter_by(published=True).all():
        urls.append(f"/books/{b.slug}")
    lines = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
    for u in urls:
        lines.append(f"  <url><loc>{site_url}{u}</loc></url>")
    lines.append("</urlset>")
    return Response("\n".join(lines), mimetype="application/xml")
