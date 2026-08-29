"""
Gunicorn configuration for the cybersecurity portfolio.
Tuned for a small VPS: 2 vCPU / 1 GB RAM. Keep memory low.

Memory budget on 1 GB RAM:
  - OS + Nginx + SSH + Python overhead: ~300-400 MB
  - Gunicorn master: ~30 MB (fixed)
  - Each sync worker (Flask + SQLAlchemy + Werkzeug): ~40-70 MB resident
  - With 2 workers + 2 threads => total app RAM ~150-200 MB

Recommended for 1 GB RAM:
  workers = 2
  threads = 2
  (keeps peak app memory well under 350 MB)

Formula (general): workers = (2 * CPU) + 1, but cap it on tiny RAM.
For 2 vCPU that would be 5 workers — too much for 1 GB, so we deliberately
use 2 workers + threads instead. If you have 2 GB RAM, raise to workers=3.

Only change these if you measured real RAM usage under load.
"""
import multiprocessing
import os

# Bound to localhost; Nginx proxies to it.
bind = "127.0.0.1:8000"

# Concurrency: threads let one worker serve multiple requests (I/O like DB).
workers = int(os.environ.get("GUNICORN_WORKERS", "2"))
threads = int(os.environ.get("GUNICORN_THREADS", "2"))

# Keep-alive to reduce reconnect overhead behind Nginx.
keepalive = 5

# Timeouts — generous for small VPS but protect against hangs.
timeout = 60
graceful_timeout = 30

# Single request per connection to free workers (Nginx handles keep-alive).
# (left default; harmless)

# Logging
accesslog = os.environ.get("GUNICORN_ACCESSLOG", "-")  # "-" = stderr
errorlog = os.environ.get("GUNICORN_ERRORLOG", "-")
loglevel = os.environ.get("GUNICORN_LOGLEVEL", "info")

# Security / hardening
# Do not leak the gunicorn version header.
gunicorn_logo = False

# Preload the app so the DB connection pool is shared and startup is faster.
preload_app = True

# Limit request size to match our upload cap (5 MB default) + overhead.
max_requests = 1000          # recycle workers to avoid memory creep
max_requests_jitter = 100
limit_request_line = 8192
limit_request_field_size = 8192

# Worker class: default sync is the lightest for this workload (no gevent/uvloop
# dependency, no async code needed). Do NOT switch to an async class unless you
# add background work — it would only increase RAM here.
worker_class = "sync"

# Disable the default behaviour of restarting on code change (production).
reload = False

# PID file for the systemd/supervisor integration.
pidfile = os.environ.get("GUNICORN_PIDFILE", "gunicorn.pid")

# User/group can be set by the systemd unit; left unset here.
