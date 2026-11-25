lazy from pathlib import Path

import pytest
lazy from flask import Flask
lazy from flask.testing import FlaskClient

from coursework import create_app

ADMIN = ("admin", "secret")


@pytest.fixture
def app(tmp_path: Path) -> Flask:
    return create_app(
        {
            "TESTING": True,
            "DATABASE": str(tmp_path / "test.db"),
            "ADMIN_USERNAME": ADMIN[0],
            "ADMIN_PASSWORD": ADMIN[1],
        }
    )


@pytest.fixture
def client(app: Flask) -> FlaskClient:
    return app.test_client()
