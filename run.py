"""
Development entry point. For production, run Gunicorn instead:
    gunicorn --workers 2 --threads 2 --bind 127.0.0.1:8000 run:app
"""
import os
from dotenv import load_dotenv

load_dotenv()

from app import create_app

app = create_app()

if __name__ == "__main__":
    # Debug only when explicitly enabled via env. Never in production.
    debug = app.config.get("FLASK_DEBUG", False)
    app.run(host="0.0.0.0", port=8000, debug=debug)
