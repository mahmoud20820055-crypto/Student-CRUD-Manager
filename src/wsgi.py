"""WSGI entry point used by gunicorn (and `python src/wsgi.py` for local dev)."""
import os

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8000)), debug=True)
