from flask import Flask, abort, request
from werkzeug.datastructures import WWWAuthenticate

from coursework.db import get_db
from coursework.storage import UserStore


def require_basic_auth() -> None:
    auth = request.authorization
    users = UserStore(get_db())
    if auth is None or auth.type != "basic" or not users.verify(auth.username or "", auth.password or ""):
        abort(
            401,
            "Valid username and password are required",
            www_authenticate=WWWAuthenticate("basic", {"realm": "Coursework"}),
        )


def init_app(app: Flask) -> None:
    app.before_request(require_basic_auth)
