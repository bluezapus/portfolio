#!/usr/bin/env bash
#
# deploy.sh — one-command install for the Cybersecurity Portfolio Flask app.
#
# What it does:
#   1. Create/use a Python virtualenv (./venv)
#   2. Install dependencies from requirements.txt
#   3. Create .env with a random SECRET_KEY (if missing)
#   4. Initialize the database + seed example content (init_db.py)
#   5. Create the FIRST admin user
#        - interactively (default), or
#        - non-interactively if ADMIN_USER and ADMIN_PASS are exported
#   6. (optional) start Gunicorn for a local preview
#
# Usage:
#   ./deploy.sh                 # interactive admin creation
#   ADMIN_USER=admin ADMIN_PASS='S3cret!Pass' ./deploy.sh   # non-interactive
#   PREVIEW=1 ./deploy.sh       # also start Gunicorn after setup
#
# Safe to re-run: it will not overwrite an existing .env or re-create admins
# unless you explicitly add more via create_admin.py.

set -euo pipefail

cd "$(dirname "$0")"

PYTHON="${PYTHON:-python3}"

echo "==> Checking Python version..."
if ! command -v "$PYTHON" >/dev/null 2>&1; then
  echo "ERROR: $PYTHON not found. Install Python 3.11+ first." >&2
  exit 1
fi
PY_VER="$("$PYTHON" -c 'import sys; print("%d.%d" % sys.version_info[:2])')"
if [ "$(printf '%s\n' "3.11" "$PY_VER" | sort -V | head -n1)" != "3.11" ]; then
  echo "ERROR: Python 3.11+ required (found $PY_VER)." >&2
  exit 1
fi
echo "    Python $PY_VER OK"

echo "==> Setting up virtualenv..."
if [ ! -x venv/bin/python ]; then
  "$PYTHON" -m venv venv
fi
# shellcheck disable=SC1091
source venv/bin/activate

echo "==> Installing dependencies..."
pip install --quiet --upgrade pip
pip install --quiet -r requirements.txt
echo "    done"

echo "==> Preparing .env..."
if [ ! -f .env ]; then
  if [ -f .env.example ]; then
    cp .env.example .env
  else
    touch .env
  fi
  # Append a fresh random SECRET_KEY (idempotent: only if not already set)
  if ! grep -q '^SECRET_KEY=' .env; then
    SECRET="$(python -c 'import secrets; print(secrets.token_hex(32))')"
    printf 'SECRET_KEY=%s\n' "$SECRET" >> .env
    echo "    generated SECRET_KEY"
  fi
else
  echo "    .env already exists, leaving it untouched"
fi

echo "==> Initializing database + seeding content..."
python init_db.py

echo "==> Creating admin user..."
if [ -n "${ADMIN_USER:-}" ] && [ -n "${ADMIN_PASS:-}" ]; then
  echo "    non-interactive mode (ADMIN_USER/ADMIN_PASS provided)"
  python - <<PY
import os, sys
from app import create_app, db
from app.models import AdminUser
app = create_app()
with app.app_context():
    if AdminUser.query.filter_by(username=os.environ["ADMIN_USER"]).first():
        print("    admin '%s' already exists, skipping" % os.environ["ADMIN_USER"])
        sys.exit(0)
    if len(os.environ["ADMIN_PASS"]) < 8:
        print("ERROR: ADMIN_PASS must be at least 8 characters", file=sys.stderr)
        sys.exit(1)
    u = AdminUser(username=os.environ["ADMIN_USER"],
                  email=os.environ.get("ADMIN_EMAIL", "admin@example.com"))
    u.set_password(os.environ["ADMIN_PASS"])
    db.session.add(u)
    db.session.commit()
    print("    admin '%s' created" % os.environ["ADMIN_USER"])
PY
else
  echo "    launching interactive create_admin.py ..."
  python create_admin.py
fi

echo ""
echo "==> Setup complete."
echo "    Admin login:  /admin/login"
echo "    Public site:  /"
echo "    Books:        /books"
if [ "${PREVIEW:-0}" = "1" ]; then
  echo "==> Starting Gunicorn preview on 127.0.0.1:8000 ..."
  exec ./venv/bin/gunicorn --workers 2 --threads 2 --bind 127.0.0.1:8000 run:app
fi
echo "    For production: configure deploy/portfolio.service + deploy/nginx-portfolio.conf"
