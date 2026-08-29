# ⬢ Cybersecurity Portfolio (Flask)

A lightweight, production-ready personal portfolio for cybersecurity
professionals. Built with **Flask + Jinja2 + SQLite**, server-side rendered,
no JavaScript build step, no Node, no Docker, no Redis, no Celery.

Designed to run comfortably on a **2 vCPU / 1 GB RAM** VPS behind **Nginx +
Gunicorn**.

---

## Features

- **Public site**: Home, About, Projects, Write-ups, Books, Contact — all
  rendered from the database.
- **Reading Room (Books)**: upload PDF e-books from the admin; visitors browse
  a book-style grid and read the PDF in a same-page modal reader (or open it in
  a new tab). PDFs are validated by extension + `%PDF` magic bytes, capped at
  **100 MB**.
- **Admin dashboard**: full CRUD for profile, skills, projects, write-ups,
  books, experience, certifications, social links, messages.
- **Appearance customization**: change colors, radius, logo, profile image live
  from the admin — no code edits (CSS variables).
- **Markdown-ish write-ups**: safe, dependency-free renderer (no external
  Markdown library). HTML is escaped first; only a whitelist of tags is
  produced, and links are scheme-checked.
- **Secure media upload**: extension + MIME (magic bytes) whitelist, size limit,
  random filenames, SVG sanitization.
- **Security**: password hashing (Werkzeug), CSRF (Flask-WTF),
  HttpOnly/SameSite session cookies, login rate limiting, security headers
  (CSP, X-Frame-Options, X-Content-Type-Options, Referrer-Policy), SQLite
  hardening (WAL).
- **SEO**: dynamic titles, meta/OG tags, `robots.txt`, `sitemap.xml`, editable
  from admin.
- **Accessibility**: semantic HTML, skip link, aria labels, keyboard
  navigation, readable contrast.

---

## Requirements

- Python **3.11+**
- A Linux server (Ubuntu/Debian 64-bit recommended)
- Nginx + Gunicorn for production
- ~1 GB RAM minimum

No other services (DB, cache, queue) are required. The database is a single
SQLite file.

---

## Quick Start (one command)

A helper script installs everything and creates the first admin account:

```bash
chmod +x deploy.sh
./deploy.sh
```

`deploy.sh` will:
1. Create/use a Python virtualenv in `./venv`
2. Install dependencies from `requirements.txt`
3. Create `.env` with a random `SECRET_KEY` (if missing)
4. Initialize the database (`init_db.py`) and seed example content
5. Create the **first admin user interactively** (username + password)
6. (Optional) start Gunicorn locally so you can preview at `http://localhost:8000`

> The admin account is **never created automatically with a default password**.
> You set it yourself when the script prompts you. See "Admin accounts" below.

---

## Manual Installation

```bash
# 1. Place the project (e.g. at /opt/portfolio)
sudo mkdir -p /opt/portfolio
sudo cp -r portfolio/* /opt/portfolio/

# 2. Create a virtualenv
cd /opt/portfolio
python3 -m venv venv
./venv/bin/pip install --upgrade pip
./venv/bin/pip install -r requirements.txt
```

## Configuration

Copy `.env.example` to `.env` and edit:

```bash
cp .env.example .env
nano .env
```

At minimum set a strong `SECRET_KEY`:

```bash
python3 -c "import secrets; print(secrets.token_hex(32))"
```

> The `.env` file is gitignored and must never be committed.

Key variables:

| Variable            | Default        | Meaning                                            |
|---------------------|----------------|----------------------------------------------------|
| `SECRET_KEY`        | *(required)*   | Flask session signing key (keep secret)            |
| `FLASK_DEBUG`       | `false`        | Dev only; never `true` in production               |
| `MAX_UPLOAD_MB`     | `5`            | Cap for image uploads (MB)                         |
| `SITE_URL`          | `http://localhost:8000` | Canonical URL for SEO/sitemap              |
| `SESSION_COOKIE_SECURE` | `0`        | Set `1` behind HTTPS (Nginx+SSL)                   |
| `BEHIND_PROXY`      | `0`            | Set `1` behind a reverse proxy                     |

---

## Database Initialization

```bash
./venv/bin/python init_db.py
```

This creates `instance/portfolio.db` and seeds placeholder content (example
skills, projects, and one sample book) so the site looks complete immediately.

> **Important**: `init_db.py` does **NOT** create any admin user.

## Admin accounts

There is **no default username/password baked into the code**. A fresh deploy
has zero admin users — login will fail until you create one.

Create the first admin (interactive, password is hashed, never plaintext):

```bash
./venv/bin/python create_admin.py
```

You will be prompted for username, email, and password. The password must be at
least 8 characters.

- On a brand-new server (cloned repo), run this once after `init_db.py`.
- If you copy the whole `instance/` folder (not a fresh clone), the existing
  admin account travels with the database file — but `.db` files are gitignored,
  so a normal `git clone` starts with no users.
- To add more admins later, run `create_admin.py` again (it asks before adding
  an extra user).

---

## Run Development Server

```bash
export FLASK_DEBUG=true   # local only
./venv/bin/python run.py
# → http://localhost:8000
```

> `FLASK_DEBUG` must be `false` (or unset) in production. Debug mode exposes
> stack traces and the Werkzeug console. It is disabled by default.

---

## Production Deployment

### 1. Gunicorn

The repo ships `gunicorn.conf.py` tuned for 1 GB RAM (2 workers + 2 threads).
From the project directory:

```bash
./venv/bin/gunicorn --config gunicorn.conf.py --chdir /opt/portfolio run:app
```

Or override via environment:

```bash
GUNICORN_WORKERS=2 GUNICORN_THREADS=2 ./venv/bin/gunicorn -c gunicorn.conf.py run:app
```

**Worker/thread recommendation (1 GB RAM):**

| RAM     | vCPU | workers | threads | est. app RAM |
|---------|------|---------|---------|--------------|
| 1 GB    | 2    | 2       | 2       | ~200 MB      |
| 2 GB    | 2    | 3       | 2       | ~300 MB      |
| 1 GB    | 1    | 1       | 2       | ~120 MB      |

Do **not** blindly use `2*CPU+1` workers — on 1 GB that overcommits RAM.
Measure real resident memory under load and adjust.

### 2. systemd service

```bash
sudo cp deploy/portfolio.service /etc/systemd/system/portfolio.service
sudo nano /etc/systemd/system/portfolio.service   # set your SECRET_KEY + domain
sudo systemctl daemon-reload
sudo systemctl enable --now portfolio
sudo systemctl status portfolio
```

The service runs Gunicorn bound to `127.0.0.1:8000` (Nginx sits in front).

### 3. Nginx

```bash
sudo cp deploy/nginx-portfolio.conf /etc/nginx/sites-available/portfolio
sudo ln -s /etc/nginx/sites-available/portfolio /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Edit the config to set your `server_name` (domain or IP).

### 4. SSL (Let's Encrypt)

```bash
sudo apt install -y certbot python3-certbot-nginx
sudo certbot --nginx -d yourdomain.com -d www.yourdomain.com
```

Certbot edits the Nginx config to add the 443 listener automatically. Renewals
are scheduled by the certbot package.

After enabling HTTPS, set `SESSION_COOKIE_SECURE=1` and `BEHIND_PROXY=1` in the
systemd unit (or `.env`) so Secure cookies work.

---

## Backup & Restore (SQLite)

SQLite is a single file — backups are simple file copies. **Stop the service
first** to get a consistent snapshot (or use `.backup` since WAL is enabled).

### Backup

```bash
sudo systemctl stop portfolio
cp /opt/portfolio/instance/portfolio.db /backup/portfolio-$(date +%F).db
# Copy uploads (PDFs, images) too:
rsync -a /opt/portfolio/uploads/ /backup/uploads-$(date +%F)/
sudo systemctl start portfolio
```

Automate with cron, e.g. nightly:

```cron
0 3 * * * systemctl stop portfolio && cp /opt/portfolio/instance/portfolio.db /backup/portfolio-$(date +\%F).db && systemctl start portfolio
```

### Restore

```bash
sudo systemctl stop portfolio
cp /backup/portfolio-2026-01-01.db /opt/portfolio/instance/portfolio.db
rsync -a /backup/uploads-2026-01-01/ /opt/portfolio/uploads/
sudo systemctl start portfolio
```

> Note: restoring the DB also restores the admin accounts stored in it.

---

## Security Notes

- **Secrets**: `SECRET_KEY` lives only in `.env` (gitignored) or the systemd
  unit. It is never hardcoded in source.
- **Sessions**: `HttpOnly`, `SameSite=Lax`, and `Secure` when behind HTTPS.
- **Uploads**: extension + MIME whitelist, random names, 5 MB cap for images /
  **100 MB for PDFs**, no executable types, SVG content sanitized.
- **CSRF**: every state-changing form is protected.
- **Login rate limit**: 5 attempts / 60s per IP.
- **Headers**: CSP (allows same-origin framing for the PDF reader),
  `X-Frame-Options: SAMEORIGIN`, `X-Content-Type-Options: nosniff`,
  Referrer-Policy, Permissions-Policy.
- **Errors**: debug off in production; 500 page never leaks tracebacks.
- **Admin routes**: all protected by Flask-Login; unauthenticated requests
  redirect to login.
- **No default admin**: every deployment starts with zero admin users; you
  create the first one via `create_admin.py` (or `deploy.sh`).

---

## Project Structure

```
portfolio/
├── app/
│   ├── __init__.py        # app factory, config, headers, pragmas
│   ├── models.py          # SQLAlchemy ORM models (incl. Book)
│   ├── auth.py            # login / logout (Flask-Login + rate limit)
│   ├── public.py          # public site + SEO routes (+ /books)
│   ├── admin.py           # admin dashboard (CRUD, incl. books)
│   ├── forms.py           # WTForms (CSRF)
│   ├── utils.py           # slugify, safe markdown, secure upload, limiter
│   ├── templates/         # base, public/, admin/, auth/, errors/
│   └── static/            # css/, js/, images/
├── instance/portfolio.db  # SQLite DB (gitignored)
├── uploads/               # uploaded media (gitignored, incl. books/)
├── create_admin.py        # create first admin
├── init_db.py             # init DB + seed defaults
├── run.py                 # dev/WSGI entry
├── requirements.txt
├── .env.example
├── .gitignore
├── gunicorn.conf.py
├── deploy.sh              # one-command install + admin creation
├── deploy/                # systemd + nginx configs
└── README.md
```


## Troubleshooting

`sudo nano /etc/nginx/sites-available/portfolio`

```
    # Uploaded media (admin-managed images + books).
    location /uploads/ {
        alias /var/www/portfolio/uploads/;
        expires 7d;
        add_header Cache-Control "public";
        access_log off;
        # Never execute anything from uploads; serve as static only.
        types { }
        default_type application/octet-stream;
    }

```
```
    # Uploaded media (admin-managed images + books).
    location /uploads/ {
        alias /var/www/portfolio/uploads/;
        expires 7d;
        add_header Cache-Control "public";
        access_log off;

        types {
            application/pdf                      pdf;
            image/png                            png;
            image/jpeg                           jpg jpeg;
            image/gif                            gif;
            image/webp                           webp;
            image/svg+xml                        svg;
        }
        default_type application/octet-stream;

        add_header X-Frame-Options "SAMEORIGIN" always;
        add_header Content-Security-Policy "frame-ancestors 'self'" always;
    }

```

---

## License

MIT — use it, adapt it, secure it.
