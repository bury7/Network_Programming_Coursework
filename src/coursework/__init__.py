import json
import os
from pathlib import Path

from flask import Flask
from werkzeug.exceptions import HTTPException
lazy from flask.typing import ResponseReturnValue

from coursework import auth, currency, db, items

PROJECT_ROOT = Path(__file__).resolve().parents[2]


def handle_http_error(error: HTTPException) -> ResponseReturnValue:
    response = error.get_response()
    response.data = json.dumps({"error": error.description})
    response.content_type = "application/json"
    return response


def hello_world() -> str:
    return "Hello World!"


def create_app(config: dict[str, object] | None = None) -> Flask:
    app = Flask(__name__, instance_path=str(PROJECT_ROOT / "instance"))
    app.config.from_mapping(
        DATABASE=str(Path(app.instance_path) / "coursework.db"),
        ADMIN_USERNAME=os.getenv("ADMIN_USERNAME"),
        ADMIN_PASSWORD=os.getenv("ADMIN_PASSWORD"),
        MAX_CONTENT_LENGTH=1024 * 1024,
    )
    if config:
        app.config.update(config)
    Path(app.config["DATABASE"]).parent.mkdir(parents=True, exist_ok=True)

    db.init_app(app)
    auth.init_app(app)
    app.register_error_handler(HTTPException, handle_http_error)
    app.add_url_rule("/", view_func=hello_world)
    app.register_blueprint(currency.bp)
    app.register_blueprint(items.bp)
    return app
