"""
Initialize the SQLite database and seed default (placeholder) content so the
site looks complete immediately after install. Safe to run multiple times;
it only creates what is missing.
"""
import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app, db
from app.models import (
    SiteSettings, Profile, Skill, Experience, Certification,
    SocialLink, Project, Writeup, Book,
)


def seed_defaults():
    s = SiteSettings.get_solo()
    s.site_name = s.site_name or "Your Name"
    s.seo_title = s.seo_title or "Your Name — Cybersecurity Portfolio"
    s.site_description = s.site_description or (
        "Cybersecurity professional portfolio: Linux, networking, SOC and penetration testing.")
    s.seo_description = s.seo_description or s.site_description
    db.session.commit()

    profile = Profile.get_solo()
    profile.full_name = profile.full_name or "Your Name"
    profile.title = profile.title or "Cybersecurity Professional"
    profile.subtitle = profile.subtitle or "Linux & Network Specialist"
    profile.description = profile.description or (
        "IT professional focused on cybersecurity, Linux infrastructure, network "
        "operations, SOC analysis and penetration testing. Passionate about "
        "defensive security, threat hunting, and hardening systems.")
    db.session.commit()

    SocialLink.ensure_defaults()

    if Skill.query.count() == 0:
        defaults = [
            ("Networking", "TCP/IP"), ("Networking", "VLAN"), ("Networking", "DHCP"),
            ("Networking", "NAT"), ("Networking", "Routing"), ("Networking", "MikroTik"),
            ("Linux", "Ubuntu"), ("Linux", "Debian"), ("Linux", "SSH"),
            ("Linux", "systemd"), ("Linux", "UFW"), ("Linux", "iptables"),
            ("Cybersecurity", "SOC Analysis"), ("Cybersecurity", "Network Enumeration"),
            ("Cybersecurity", "Wireshark"), ("Cybersecurity", "Nmap"),
            ("Cybersecurity", "Incident Response"), ("Cybersecurity", "Threat Hunting"),
            ("Cybersecurity", "Penetration Testing"),
        ]
        for i, (cat, name) in enumerate(defaults):
            db.session.add(Skill(category=cat, name=name, enabled=True, display_order=i))
        db.session.commit()

    if Experience.query.count() == 0:
        db.session.add(Experience(
            company="Example Corp", position="Security Operations Analyst",
            start_date="2023", end_date="Present",
            description="Monitor and triage security events, perform threat hunting, "
                        "and support incident response on a 24/7 SOC.",
            technologies="Splunk, Wireshark, SentinelOne, Elastic", display_order=1))
        db.session.add(Experience(
            company="Linux Systems Ltd", position="Linux Systems Administrator",
            start_date="2021", end_date="2023",
            description="Managed Ubuntu/Debian servers, automated hardening with "
                        "Ansible, and maintained firewall policy with UFW/iptables.",
            technologies="Ubuntu, Debian, Ansible, UFW, iptables", display_order=2))
        db.session.commit()

    if Certification.query.count() == 0:
        db.session.add(Certification(
            name="Example Security+", organization="ExampleVendor", date="2024",
            credential_url="", description="Foundational security certification.",
            display_order=1))
        db.session.commit()

    if Book.query.count() == 0:
        db.session.add(Book(
            title="Sample Cybersecurity Handbook",
            slug="sample-cybersecurity-handbook",
            author="Portfolio Author",
            description="Replace this with your own PDF via the admin Books page.",
            category="General",
            pdf_path="books/sample.pdf",
            display_order=0, published=True))
        db.session.commit()

    print("Default content seeded.")


def main():
    app = create_app()
    with app.app_context():
        db.create_all()
        SiteSettings.ensure_defaults()
        seed_defaults()
    print("Database initialized at:", os.path.join(app.instance_path,
          os.environ.get("DATABASE_PATH", "portfolio.db")))


if __name__ == "__main__":
    main()
