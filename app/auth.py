"""
Authentication blueprint: admin login / logout.
Uses Flask-Login + Werkzeug hashing + CSRF + simple per-IP rate limiting.
"""
from flask import Blueprint, render_template, redirect, url_for, request, flash
from flask_login import login_user, logout_user, current_user
from .models import db, AdminUser
from .forms import LoginForm
from . import utils

bp = Blueprint("auth", __name__, url_prefix="/admin")


@bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("admin.dashboard"))

    form = LoginForm()
    # Rate limit key = IP (proxy-aware best-effort).
    client_ip = request.headers.get("X-Forwarded-For", request.remote_addr)
    client_ip = client_ip.split(",")[0].strip()

    if form.validate_on_submit():
        if not utils.login_allowed(client_ip):
            flash("Too many failed attempts. Please wait a minute.", "danger")
            return render_template("auth/login.html", form=form), 429

        user = AdminUser.query.filter_by(username=form.username.data).first()
        if user is None or not user.check_password(form.password.data):
            utils.register_failed_login(client_ip)
            flash("Invalid username or password.", "danger")
            return render_template("auth/login.html", form=form)

        utils.clear_login(client_ip)
        login_user(user, remember=form.remember.data)
        flash("Welcome back!", "success")
        next_page = request.args.get("next")
        if next_page and next_page.startswith("/"):
            return redirect(next_page)
        return redirect(url_for("admin.dashboard"))

    return render_template("auth/login.html", form=form)


@bp.route("/logout")
def logout():
    logout_user()
    flash("You have been signed out.", "info")
    return redirect(url_for("auth.login"))
