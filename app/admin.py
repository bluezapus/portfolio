"""
Admin dashboard blueprint. All routes are protected by Flask-Login.
Provides CRUD for projects, write-ups, skills, experience, certifications,
social links, profile, appearance, settings, and contact messages.
Admin auth = session-based; every form carries CSRF protection.
"""
from flask import (
    Blueprint, render_template, request, redirect, url_for, flash, abort,
)
from flask_login import login_required, current_user
from werkzeug.datastructures import FileStorage
from .models import (
    db, Profile, Skill, Project, Writeup, Experience, Certification,
    SocialLink, SiteSettings, ContactMessage, AdminUser, Book,
)
from .forms import (
    ProfileForm, SkillForm, ProjectForm, WriteupForm, ExperienceForm,
    CertificationForm, SocialLinkForm, AppearanceForm, SiteSettingsForm, BookForm,
)
from . import utils

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.before_request
def _require_login():
    # Protect every admin route except the login route (handled in auth bp,
    # but guard here too for safety).
    if request.endpoint == "auth.login":
        return
    if not current_user.is_authenticated:
        return redirect(url_for("auth.login", next=request.full_path))


# --------------------------------------------------------------------------
# Dashboard
# --------------------------------------------------------------------------
@bp.route("/")
@login_required
def dashboard():
    counts = dict(
        projects=Project.query.count(),
        published_projects=Project.query.filter_by(published=True).count(),
        writeups=Writeup.query.count(),
        skills=Skill.query.filter_by(enabled=True).count(),
        experience=Experience.query.count(),
        certs=Certification.query.count(),
        unread=ContactMessage.query.filter_by(read=False).count(),
    )
    recent_messages = ContactMessage.query.order_by(
        ContactMessage.created_at.desc()).limit(5).all()
    return render_template("admin/dashboard.html", counts=counts,
                           recent_messages=recent_messages)


# --------------------------------------------------------------------------
# Profile
# --------------------------------------------------------------------------
@bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    profile = Profile.get_solo()
    form = ProfileForm(obj=profile)
    if form.validate_on_submit():
        old_image = profile.profile_image
        form.populate_obj(profile)
        if form.profile_image.data and isinstance(form.profile_image.data, FileStorage):
            try:
                path = utils.secure_upload(form.profile_image.data, "profile")
                profile.profile_image = path
            except ValueError as e:
                profile.profile_image = old_image
                flash(str(e), "danger")
                return render_template("admin/profile.html", form=form)
        db.session.commit()
        flash("Profile updated.", "success")
        return redirect(url_for("admin.profile"))
    return render_template("admin/profile.html", form=form)


# --------------------------------------------------------------------------
# Skills
# --------------------------------------------------------------------------
@bp.route("/skills")
@login_required
def skills():
    rows = Skill.query.order_by(Skill.category, Skill.display_order).all()
    return render_template("admin/skills.html", skills=rows)


@bp.route("/skills/new", methods=["GET", "POST"])
@login_required
def skill_new():
    form = SkillForm()
    if form.validate_on_submit():
        s = Skill(category=form.category.data, name=form.name.data,
                  enabled=form.enabled.data,
                  display_order=form.display_order.data or 0)
        db.session.add(s)
        db.session.commit()
        flash("Skill added.", "success")
        return redirect(url_for("admin.skills"))
    return render_template("admin/skill_form.html", form=form, title="Add Skill")


@bp.route("/skills/<int:id>/edit", methods=["GET", "POST"])
@login_required
def skill_edit(id):
    s = Skill.query.get_or_404(id)
    form = SkillForm(obj=s)
    if form.validate_on_submit():
        form.populate_obj(s)
        db.session.commit()
        flash("Skill updated.", "success")
        return redirect(url_for("admin.skills"))
    return render_template("admin/skill_form.html", form=form, title="Edit Skill")


@bp.route("/skills/<int:id>/delete", methods=["POST"])
@login_required
def skill_delete(id):
    s = Skill.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    flash("Skill deleted.", "info")
    return redirect(url_for("admin.skills"))


@bp.route("/skills/<int:id>/toggle", methods=["POST"])
@login_required
def skill_toggle(id):
    s = Skill.query.get_or_404(id)
    s.enabled = not s.enabled
    db.session.commit()
    flash("Skill visibility updated.", "info")
    return redirect(url_for("admin.skills"))


# --------------------------------------------------------------------------
# Projects
# --------------------------------------------------------------------------
@bp.route("/projects")
@login_required
def projects():
    rows = Project.query.order_by(Project.created_at.desc()).all()
    return render_template("admin/projects.html", projects=rows)


@bp.route("/projects/new", methods=["GET", "POST"])
@login_required
def project_new():
    form = ProjectForm()
    if form.validate_on_submit():
        slug = form.slug.data or utils.slugify(form.title.data)
        if Project.query.filter_by(slug=slug).first():
            flash("Slug already exists. Choose a unique one.", "danger")
            return render_template("admin/project_form.html", form=form, title="Add Project")
        p = Project(title=form.title.data, slug=slug,
                    short_description=form.short_description.data,
                    full_description=form.full_description.data,
                    category=form.category.data, technologies=form.technologies.data,
                    github_url=form.github_url.data or "", demo_url=form.demo_url.data or "",
                    featured=form.featured.data, published=form.published.data)
        if form.image.data:
            try:
                p.image = utils.secure_upload(form.image.data, "projects")
            except ValueError as e:
                flash(str(e), "danger")
                return render_template("admin/project_form.html", form=form, title="Add Project")
        db.session.add(p)
        db.session.commit()
        flash("Project added.", "success")
        return redirect(url_for("admin.projects"))
    return render_template("admin/project_form.html", form=form, title="Add Project")


@bp.route("/projects/<int:id>/edit", methods=["GET", "POST"])
@login_required
def project_edit(id):
    p = Project.query.get_or_404(id)
    form = ProjectForm(obj=p)
    if form.validate_on_submit():
        new_slug = form.slug.data or utils.slugify(form.title.data)
        existing = Project.query.filter_by(slug=new_slug).first()
        if existing and existing.id != p.id:
            flash("Slug already exists. Choose a unique one.", "danger")
            return render_template("admin/project_form.html", form=form, title="Edit Project")
        p.title = form.title.data
        p.slug = new_slug
        p.short_description = form.short_description.data
        p.full_description = form.full_description.data
        p.category = form.category.data
        p.technologies = form.technologies.data
        p.github_url = form.github_url.data or ""
        p.demo_url = form.demo_url.data or ""
        p.featured = form.featured.data
        p.published = form.published.data
        if form.image.data:
            try:
                p.image = utils.secure_upload(form.image.data, "projects")
            except ValueError as e:
                flash(str(e), "danger")
                return render_template("admin/project_form.html", form=form, title="Edit Project")
        db.session.commit()
        flash("Project updated.", "success")
        return redirect(url_for("admin.projects"))
    return render_template("admin/project_form.html", form=form, title="Edit Project")


@bp.route("/projects/<int:id>/delete", methods=["POST"])
@login_required
def project_delete(id):
    p = Project.query.get_or_404(id)
    db.session.delete(p)
    db.session.commit()
    flash("Project deleted.", "info")
    return redirect(url_for("admin.projects"))


# --------------------------------------------------------------------------
# Write-ups
# --------------------------------------------------------------------------
@bp.route("/writeups")
@login_required
def writeups():
    rows = Writeup.query.order_by(Writeup.published_date.desc()).all()
    return render_template("admin/writeups.html", writeups=rows)


@bp.route("/writeups/new", methods=["GET", "POST"])
@login_required
def writeup_new():
    form = WriteupForm()
    if form.validate_on_submit():
        slug = form.slug.data or utils.slugify(form.title.data)
        if Writeup.query.filter_by(slug=slug).first():
            flash("Slug already exists. Choose a unique one.", "danger")
            return render_template("admin/writeup_form.html", form=form, title="Add Write-up")
        w = Writeup(title=form.title.data, slug=slug, summary=form.summary.data,
                    content=form.content.data, category=form.category.data,
                    tags=form.tags.data, status=form.status.data)
        if form.cover_image.data:
            try:
                w.cover_image = utils.secure_upload(form.cover_image.data, "writeups")
            except ValueError as e:
                flash(str(e), "danger")
                return render_template("admin/writeup_form.html", form=form, title="Add Write-up")
        db.session.add(w)
        db.session.commit()
        flash("Write-up added.", "success")
        return redirect(url_for("admin.writeups"))
    return render_template("admin/writeup_form.html", form=form, title="Add Write-up")


@bp.route("/writeups/<int:id>/edit", methods=["GET", "POST"])
@login_required
def writeup_edit(id):
    w = Writeup.query.get_or_404(id)
    form = WriteupForm(obj=w)
    if form.validate_on_submit():
        new_slug = form.slug.data or utils.slugify(form.title.data)
        existing = Writeup.query.filter_by(slug=new_slug).first()
        if existing and existing.id != w.id:
            flash("Slug already exists. Choose a unique one.", "danger")
            return render_template("admin/writeup_form.html", form=form, title="Edit Write-up")
        w.title = form.title.data
        w.slug = new_slug
        w.summary = form.summary.data
        w.content = form.content.data
        w.category = form.category.data
        w.tags = form.tags.data
        w.status = form.status.data
        if form.cover_image.data:
            try:
                w.cover_image = utils.secure_upload(form.cover_image.data, "writeups")
            except ValueError as e:
                flash(str(e), "danger")
                return render_template("admin/writeup_form.html", form=form, title="Edit Write-up")
        db.session.commit()
        flash("Write-up updated.", "success")
        return redirect(url_for("admin.writeups"))
    return render_template("admin/writeup_form.html", form=form, title="Edit Write-up")


@bp.route("/writeups/<int:id>/delete", methods=["POST"])
@login_required
def writeup_delete(id):
    w = Writeup.query.get_or_404(id)
    db.session.delete(w)
    db.session.commit()
    flash("Write-up deleted.", "info")
    return redirect(url_for("admin.writeups"))


# --------------------------------------------------------------------------
# Experience
# --------------------------------------------------------------------------
@bp.route("/experience")
@login_required
def experience():
    rows = Experience.query.order_by(Experience.display_order).all()
    return render_template("admin/experience.html", items=rows)


@bp.route("/experience/new", methods=["GET", "POST"])
@login_required
def experience_new():
    form = ExperienceForm()
    if form.validate_on_submit():
        e = Experience(company=form.company.data, position=form.position.data,
                       start_date=form.start_date.data, end_date=form.end_date.data,
                       description=form.description.data, technologies=form.technologies.data,
                       display_order=form.display_order.data or 0)
        db.session.add(e)
        db.session.commit()
        flash("Experience added.", "success")
        return redirect(url_for("admin.experience"))
    return render_template("admin/experience_form.html", form=form, title="Add Experience")


@bp.route("/experience/<int:id>/edit", methods=["GET", "POST"])
@login_required
def experience_edit(id):
    e = Experience.query.get_or_404(id)
    form = ExperienceForm(obj=e)
    if form.validate_on_submit():
        form.populate_obj(e)
        db.session.commit()
        flash("Experience updated.", "success")
        return redirect(url_for("admin.experience"))
    return render_template("admin/experience_form.html", form=form, title="Edit Experience")


@bp.route("/experience/<int:id>/delete", methods=["POST"])
@login_required
def experience_delete(id):
    e = Experience.query.get_or_404(id)
    db.session.delete(e)
    db.session.commit()
    flash("Experience deleted.", "info")
    return redirect(url_for("admin.experience"))


# --------------------------------------------------------------------------
# Certifications
# --------------------------------------------------------------------------
@bp.route("/certifications")
@login_required
def certifications():
    rows = Certification.query.order_by(Certification.display_order).all()
    return render_template("admin/certifications.html", items=rows)


@bp.route("/certifications/new", methods=["GET", "POST"])
@login_required
def certification_new():
    form = CertificationForm()
    if form.validate_on_submit():
        c = Certification(name=form.name.data, organization=form.organization.data,
                          date=form.date.data, credential_url=form.credential_url.data or "",
                          description=form.description.data,
                          display_order=form.display_order.data or 0)
        db.session.add(c)
        db.session.commit()
        flash("Certification added.", "success")
        return redirect(url_for("admin.certifications"))
    return render_template("admin/certification_form.html", form=form, title="Add Certification")


@bp.route("/certifications/<int:id>/edit", methods=["GET", "POST"])
@login_required
def certification_edit(id):
    c = Certification.query.get_or_404(id)
    form = CertificationForm(obj=c)
    if form.validate_on_submit():
        form.populate_obj(c)
        db.session.commit()
        flash("Certification updated.", "success")
        return redirect(url_for("admin.certifications"))
    return render_template("admin/certification_form.html", form=form, title="Edit Certification")


@bp.route("/certifications/<int:id>/delete", methods=["POST"])
@login_required
def certification_delete(id):
    c = Certification.query.get_or_404(id)
    db.session.delete(c)
    db.session.commit()
    flash("Certification deleted.", "info")
    return redirect(url_for("admin.certifications"))


# --------------------------------------------------------------------------
# Social links
# --------------------------------------------------------------------------
@bp.route("/social-links")
@login_required
def social_links():
    rows = SocialLink.query.order_by(SocialLink.display_order).all()
    return render_template("admin/social_links.html", items=rows)


@bp.route("/social-links/new", methods=["GET", "POST"])
@login_required
def social_link_new():
    form = SocialLinkForm()
    if form.validate_on_submit():
        s = SocialLink(label=form.label.data, url=form.url.data or "",
                       icon=form.icon.data or "link", enabled=form.enabled.data,
                       display_order=form.display_order.data or 0)
        db.session.add(s)
        db.session.commit()
        flash("Link added.", "success")
        return redirect(url_for("admin.social_links"))
    return render_template("admin/social_link_form.html", form=form, title="Add Social Link")


@bp.route("/social-links/<int:id>/edit", methods=["GET", "POST"])
@login_required
def social_link_edit(id):
    s = SocialLink.query.get_or_404(id)
    form = SocialLinkForm(obj=s)
    if form.validate_on_submit():
        form.populate_obj(s)
        db.session.commit()
        flash("Link updated.", "success")
        return redirect(url_for("admin.social_links"))
    return render_template("admin/social_link_form.html", form=form, title="Edit Social Link")


@bp.route("/social-links/<int:id>/delete", methods=["POST"])
@login_required
def social_link_delete(id):
    s = SocialLink.query.get_or_404(id)
    db.session.delete(s)
    db.session.commit()
    flash("Link deleted.", "info")
    return redirect(url_for("admin.social_links"))


# --------------------------------------------------------------------------
# Appearance
# --------------------------------------------------------------------------
_DEFAULT_APPEARANCE = dict(
    primary_color="#00ff9c", accent_color="#00d4ff", background_color="#0a0e14",
    card_color="#131a24", text_color="#e6edf3", muted_color="#8b98a5",
    border_radius=8,
)


@bp.route("/appearance", methods=["GET", "POST"])
@login_required
def appearance():
    s = SiteSettings.get_solo()
    form = AppearanceForm(obj=s)
    if form.validate_on_submit():
        old_logo = s.logo
        s.primary_color = form.primary_color.data
        s.accent_color = form.accent_color.data
        s.background_color = form.background_color.data
        s.card_color = form.card_color.data
        s.text_color = form.text_color.data
        s.muted_color = form.muted_color.data
        s.border_radius = form.border_radius.data or 8
        if form.logo.data and isinstance(form.logo.data, FileStorage):
            try:
                s.logo = utils.secure_upload(form.logo.data, "brand")
            except ValueError as e:
                s.logo = old_logo
                flash(str(e), "danger")
                return render_template("admin/appearance.html", form=form, defaults=_DEFAULT_APPEARANCE)
        db.session.commit()
        flash("Appearance saved.", "success")
        return redirect(url_for("admin.appearance"))
    return render_template("admin/appearance.html", form=form, defaults=_DEFAULT_APPEARANCE)


@bp.route("/appearance/reset", methods=["POST"])
@login_required
def appearance_reset():
    s = SiteSettings.get_solo()
    for k, v in _DEFAULT_APPEARANCE.items():
        setattr(s, k, v)
    db.session.commit()
    flash("Appearance reset to defaults.", "info")
    return redirect(url_for("admin.appearance"))


# --------------------------------------------------------------------------
# Settings
# --------------------------------------------------------------------------
@bp.route("/settings", methods=["GET", "POST"])
@login_required
def settings():
    s = SiteSettings.get_solo()
    form = SiteSettingsForm(obj=s)
    if form.validate_on_submit():
        old_favicon = s.favicon
        form.populate_obj(s)
        if form.favicon.data and isinstance(form.favicon.data, FileStorage):
            try:
                s.favicon = utils.secure_upload(form.favicon.data, "brand")
            except ValueError as e:
                s.favicon = old_favicon
                flash(str(e), "danger")
                return render_template("admin/settings.html", form=form)
        db.session.commit()
        flash("Settings saved.", "success")
        return redirect(url_for("admin.settings"))
    return render_template("admin/settings.html", form=form)


# -------------------------------------------------------------------------
# Books (e-book PDF reader)
# -------------------------------------------------------------------------
@bp.route("/books")
@login_required
def books():
    rows = Book.query.order_by(Book.display_order, Book.created_at.desc()).all()
    return render_template("admin/books.html", books=rows)


@bp.route("/books/new", methods=["GET", "POST"])
@login_required
def book_new():
    form = BookForm()
    if form.validate_on_submit():
        slug = form.slug.data or utils.slugify(form.title.data)
        if Book.query.filter_by(slug=slug).first():
            flash("Slug already exists. Choose a unique one.", "danger")
            return render_template("admin/book_form.html", form=form, title="Add Book")
        b = Book(title=form.title.data, slug=slug, author=form.author.data or "",
                 description=form.description.data, category=form.category.data or "General",
                 display_order=form.display_order.data or 0, published=form.published.data)
        db.session.add(b)
        db.session.flush()
        try:
            if form.cover_image.data and isinstance(form.cover_image.data, FileStorage):
                b.cover_image = utils.secure_upload(form.cover_image.data, "books")
            if form.pdf.data and isinstance(form.pdf.data, FileStorage):
                b.pdf_path = utils.secure_pdf_upload(form.pdf.data, "books")
        except ValueError as e:
            db.session.rollback()
            flash(str(e), "danger")
            return render_template("admin/book_form.html", form=form, title="Add Book")
        db.session.commit()
        flash("Book added.", "success")
        return redirect(url_for("admin.books"))
    return render_template("admin/book_form.html", form=form, title="Add Book")


@bp.route("/books/<int:id>/edit", methods=["GET", "POST"])
@login_required
def book_edit(id):
    b = Book.query.get_or_404(id)
    form = BookForm(obj=b)
    if form.validate_on_submit():
        new_slug = form.slug.data or utils.slugify(form.title.data)
        existing = Book.query.filter_by(slug=new_slug).first()
        if existing and existing.id != b.id:
            flash("Slug already exists. Choose a unique one.", "danger")
            return render_template("admin/book_form.html", form=form, title="Edit Book")
        b.title = form.title.data
        b.slug = new_slug
        b.author = form.author.data or ""
        b.description = form.description.data
        b.category = form.category.data or "General"
        b.display_order = form.display_order.data or 0
        b.published = form.published.data
        try:
            if form.cover_image.data and isinstance(form.cover_image.data, FileStorage):
                b.cover_image = utils.secure_upload(form.cover_image.data, "books")
            if form.pdf.data and isinstance(form.pdf.data, FileStorage):
                b.pdf_path = utils.secure_pdf_upload(form.pdf.data, "books")
        except ValueError as e:
            flash(str(e), "danger")
            return render_template("admin/book_form.html", form=form, title="Edit Book")
        db.session.commit()
        flash("Book updated.", "success")
        return redirect(url_for("admin.books"))
    return render_template("admin/book_form.html", form=form, title="Edit Book", book=b)


@bp.route("/books/<int:id>/delete", methods=["POST"])
@login_required
def book_delete(id):
    b = Book.query.get_or_404(id)
    db.session.delete(b)
    db.session.commit()
    flash("Book deleted.", "info")
    return redirect(url_for("admin.books"))


# -------------------------------------------------------------------------
# Messages
# -------------------------------------------------------------------------
@bp.route("/messages")
@login_required
def messages():
    page = request.args.get("page", 1, type=int)
    pagination = ContactMessage.query.order_by(
        ContactMessage.created_at.desc()).paginate(page=page, per_page=15, error_out=False)
    return render_template("admin/messages.html", messages=pagination.items,
                           pagination=pagination)


@bp.route("/messages/<int:id>")
@login_required
def message_detail(id):
    m = ContactMessage.query.get_or_404(id)
    if not m.read:
        m.read = True
        db.session.commit()
    return render_template("admin/message_detail.html", message=m)


@bp.route("/messages/<int:id>/toggle", methods=["POST"])
@login_required
def message_toggle(id):
    m = ContactMessage.query.get_or_404(id)
    m.read = not m.read
    db.session.commit()
    return redirect(url_for("admin.messages"))


@bp.route("/messages/<int:id>/delete", methods=["POST"])
@login_required
def message_delete(id):
    m = ContactMessage.query.get_or_404(id)
    db.session.delete(m)
    db.session.commit()
    flash("Message deleted.", "info")
    return redirect(url_for("admin.messages"))
