"""Student CRUD Manager - Flask application factory."""
import os

from flask import Flask

from . import db
from .routes import api_bp, web_bp


def create_app(config: dict | None = None) -> Flask:
    app = Flask(__name__)
    app.json.sort_keys = False
    app.config.update(
        DATABASE_PATH=os.environ.get("DATABASE_PATH", os.path.join(app.instance_path, "students.db")),
    )
    if config:
        app.config.update(config)

    db_dir = os.path.dirname(app.config["DATABASE_PATH"])
    if db_dir:
        os.makedirs(db_dir, exist_ok=True)

    db.init_app(app)
    app.register_blueprint(api_bp)
    app.register_blueprint(web_bp)
    return app
