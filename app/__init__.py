from __future__ import annotations

import os
from dotenv import load_dotenv
from flask import Flask
from typing import Any

from .extensions import db
from .routes import main_bp
from .services import DB_PATH, init_database


def create_app(config_overrides: dict[str, Any] | None = None) -> Flask:
    load_dotenv()
    app = Flask(__name__, template_folder="templates", static_folder="static")
    app.config["SQLALCHEMY_DATABASE_URI"] = f"sqlite:///{DB_PATH.as_posix()}"
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
    hf_token = os.getenv("HF_API_TOKEN", "")
    app.config["HF_API_TOKEN"] = hf_token
    llm_enabled_env = os.getenv("LLM_ENABLED")
    if llm_enabled_env is None:
        app.config["LLM_ENABLED"] = bool(hf_token)
    else:
        app.config["LLM_ENABLED"] = llm_enabled_env.lower() == "true"
    app.config["HF_MODEL"] = os.getenv("HF_MODEL", "openai/gpt-oss-120b:fastest")
    app.config["HF_TIMEOUT"] = int(os.getenv("HF_TIMEOUT", "30"))
    if config_overrides:
        app.config.update(config_overrides)

    db.init_app(app)
    app.register_blueprint(main_bp)

    with app.app_context():
        init_database(app.config["SQLALCHEMY_DATABASE_URI"])

    return app
