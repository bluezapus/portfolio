"""
Create the first (or an additional) admin user.
Usage:
    python create_admin.py
You will be prompted interactively for username, email and password.
The password is hashed with Werkzeug (never stored in plaintext).
"""
import getpass
import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app, db
from app.models import AdminUser


def main():
    app = create_app()
    with app.app_context():
        existing = AdminUser.query.all()
        if existing:
            print(f"Note: {len(existing)} admin user(s) already exist.")
            add_more = input("Create an additional admin? [y/N]: ").strip().lower()
            if add_more != "y":
                print("Aborted.")
                return

        username = input("Username: ").strip()
        if not username or len(username) < 3:
            print("Username must be at least 3 characters.")
            return
        if AdminUser.query.filter_by(username=username).first():
            print("That username already exists.")
            return

        email = input("Email: ").strip()
        password = getpass.getpass("Password (min 8 chars): ")
        if len(password) < 8:
            print("Password must be at least 8 characters.")
            return
        confirm = getpass.getpass("Confirm password: ")
        if password != confirm:
            print("Passwords do not match.")
            return

        user = AdminUser(username=username, email=email)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()
        print(f"Admin user '{username}' created successfully.")


if __name__ == "__main__":
    main()
