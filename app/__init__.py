from __future__ import annotations

from flask import Flask
from typing import Any

from .extensions import db
from .routes import main_bp
from .services import DB_PATH, init_database


def create_app(config_overrides: dict[str, Any] | None = None) -> Flask:
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH.as_posix()}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)
    app.register_blueprint(main_bp)

    with app.app_context():
        init_database(app.config["SQLALCHEMY_DATABASE_URI"])

    return app
