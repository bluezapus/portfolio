"""
WTForms definitions. All forms carry CSRF protection automatically
(Flask-WTF enables it globally). Server-side validation keeps the app safe
even if client-side validation is bypassed.
"""
from flask_wtf import FlaskForm
from wtforms import (
    StringField, PasswordField, BooleanField, TextAreaField,
    SelectField, SubmitField, IntegerField, URLField, FileField,
)
from wtforms.validators import (
    DataRequired, Email, Length, Optional, URL, Regexp,
)


class LoginForm(FlaskForm):
    username = StringField("Username", validators=[
        DataRequired(), Length(min=3, max=64)])
    password = PasswordField("Password", validators=[
        DataRequired(), Length(min=8, max=128)])
    remember = BooleanField("Remember me")
    submit = SubmitField("Sign in")


class ProfileForm(FlaskForm):
    full_name = StringField("Full Name", validators=[DataRequired(), Length(max=120)])
    title = StringField("Professional Title", validators=[DataRequired(), Length(max=120)])
    subtitle = StringField("Subtitle", validators=[Optional(), Length(max=160)])
    description = TextAreaField("Short Bio", validators=[Optional(), Length(max=2000)])
    location = StringField("Location", validators=[Optional(), Length(max=120)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=160)])
    cv_url = URLField("CV URL", validators=[Optional(), URL(), Length(max=255)])
    profile_image = FileField("Profile Image", validators=[Optional()])
    submit = SubmitField("Save Profile")


class SkillForm(FlaskForm):
    category = StringField("Category", validators=[DataRequired(), Length(max=80)])
    name = StringField("Skill Name", validators=[DataRequired(), Length(max=120)])
    enabled = BooleanField("Enabled")
    display_order = IntegerField("Display Order", validators=[Optional()], default=0)
    submit = SubmitField("Save Skill")


class ProjectForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=160)])
    slug = StringField("Slug", validators=[Optional(), Length(max=200),
                        Regexp(r"^[\w-]*$", message="Letters, numbers, - and _ only.")])
    short_description = StringField("Short Description", validators=[Optional(), Length(max=300)])
    full_description = TextAreaField("Full Description", validators=[Optional(), Length(max=8000)])
    category = StringField("Category", validators=[Optional(), Length(max=80)])
    technologies = StringField("Technologies (comma separated)",
                               validators=[Optional(), Length(max=500)])
    github_url = URLField("GitHub URL", validators=[Optional(), URL(), Length(max=255)])
    demo_url = URLField("Demo URL", validators=[Optional(), URL(), Length(max=255)])
    image = FileField("Project Image", validators=[Optional()])
    featured = BooleanField("Featured")
    published = BooleanField("Published")
    submit = SubmitField("Save Project")


class WriteupForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    slug = StringField("Slug", validators=[Optional(), Length(max=220),
                        Regexp(r"^[\w-]*$", message="Letters, numbers, - and _ only.")])
    summary = TextAreaField("Summary", validators=[Optional(), Length(max=1000)])
    content = TextAreaField("Content (Markdown supported)", validators=[Optional(), Length(max=20000)])
    category = StringField("Category", validators=[Optional(), Length(max=80)])
    tags = StringField("Tags (comma separated)", validators=[Optional(), Length(max=300)])
    cover_image = FileField("Cover Image", validators=[Optional()])
    status = SelectField("Status", choices=[("published", "Published"), ("draft", "Draft")])
    submit = SubmitField("Save Write-up")


class ExperienceForm(FlaskForm):
    company = StringField("Company", validators=[DataRequired(), Length(max=160)])
    position = StringField("Position", validators=[DataRequired(), Length(max=160)])
    start_date = StringField("Start Date", validators=[Optional(), Length(max=40)])
    end_date = StringField("End Date", validators=[Optional(), Length(max=40)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=2000)])
    technologies = StringField("Technologies", validators=[Optional(), Length(max=500)])
    display_order = IntegerField("Display Order", validators=[Optional()], default=0)
    submit = SubmitField("Save Experience")


class CertificationForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=200)])
    organization = StringField("Organization", validators=[Optional(), Length(max=160)])
    date = StringField("Date", validators=[Optional(), Length(max=40)])
    credential_url = URLField("Credential URL", validators=[Optional(), URL(), Length(max=255)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=1000)])
    display_order = IntegerField("Display Order", validators=[Optional()], default=0)
    submit = SubmitField("Save Certification")


class SocialLinkForm(FlaskForm):
    label = StringField("Label", validators=[DataRequired(), Length(max=60)])
    url = URLField("URL", validators=[Optional(), URL(), Length(max=255)])
    icon = StringField("Icon", validators=[Optional(), Length(max=40)])
    enabled = BooleanField("Enabled")
    display_order = IntegerField("Display Order", validators=[Optional()], default=0)
    submit = SubmitField("Save Link")


class BookForm(FlaskForm):
    title = StringField("Title", validators=[DataRequired(), Length(max=200)])
    slug = StringField("Slug", validators=[Optional(), Length(max=220),
                        Regexp(r"^[\w-]*$", message="Letters, numbers, - and _ only.")])
    author = StringField("Author", validators=[Optional(), Length(max=160)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=1000)])
    category = StringField("Category", validators=[Optional(), Length(max=80)])
    cover_image = FileField("Cover Image", validators=[Optional()])
    pdf = FileField("PDF File", validators=[Optional()])
    display_order = IntegerField("Display Order", validators=[Optional()], default=0)
    published = BooleanField("Published")
    submit = SubmitField("Save Book")


class AppearanceForm(FlaskForm):
    primary_color = StringField("Primary Color", validators=[DataRequired(), Length(max=16)])
    accent_color = StringField("Accent Color", validators=[DataRequired(), Length(max=16)])
    background_color = StringField("Background Color", validators=[DataRequired(), Length(max=16)])
    card_color = StringField("Card Color", validators=[DataRequired(), Length(max=16)])
    text_color = StringField("Text Color", validators=[DataRequired(), Length(max=16)])
    muted_color = StringField("Muted Text Color", validators=[DataRequired(), Length(max=16)])
    border_radius = IntegerField("Border Radius (px)", validators=[DataRequired()], default=8)
    logo = FileField("Logo", validators=[Optional()])
    submit = SubmitField("Save Appearance")


class SiteSettingsForm(FlaskForm):
    site_name = StringField("Site Name", validators=[DataRequired(), Length(max=120)])
    site_description = TextAreaField("Site Description", validators=[Optional(), Length(max=1000)])
    email = StringField("Email", validators=[Optional(), Email(), Length(max=160)])
    location = StringField("Location", validators=[Optional(), Length(max=120)])
    cv_url = URLField("CV URL", validators=[Optional(), URL(), Length(max=255)])
    github_url = URLField("GitHub URL", validators=[Optional(), URL(), Length(max=255)])
    linkedin_url = URLField("LinkedIn URL", validators=[Optional(), URL(), Length(max=255)])
    htb_url = URLField("Hack The Box URL", validators=[Optional(), URL(), Length(max=255)])
    favicon = FileField("Favicon", validators=[Optional()])
    seo_title = StringField("SEO Title", validators=[Optional(), Length(max=160)])
    seo_description = TextAreaField("SEO Description", validators=[Optional(), Length(max=1000)])
    robots_index = BooleanField("Allow search engines to index")
    submit = SubmitField("Save Settings")


class ContactForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(min=2, max=120)])
    email = StringField("Email", validators=[DataRequired(), Email(), Length(max=160)])
    subject = StringField("Subject", validators=[Optional(), Length(max=200)])
    message = TextAreaField("Message", validators=[DataRequired(), Length(min=5, max=5000)])
    submit = SubmitField("Send Message")
