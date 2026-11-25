from http import HTTPStatus

lazy from flask import Flask
lazy from flask.testing import FlaskClient

from tests.conftest import ADMIN


def test_request_without_credentials_is_rejected(client: FlaskClient) -> None:
    response = client.get("/")
    assert response.status_code == HTTPStatus.UNAUTHORIZED
    assert response.headers["WWW-Authenticate"] == "Basic realm=Coursework"
    assert response.json == {"error": "Valid username and password are required"}


def test_wrong_password_is_rejected(client: FlaskClient) -> None:
    assert client.get("/", auth=(ADMIN[0], "wrong")).status_code == HTTPStatus.UNAUTHORIZED


def test_unknown_user_is_rejected(client: FlaskClient) -> None:
    assert client.get("/", auth=("nobody", ADMIN[1])).status_code == HTTPStatus.UNAUTHORIZED


def test_valid_credentials_are_accepted(client: FlaskClient) -> None:
    response = client.get("/", auth=ADMIN)
    assert response.status_code == HTTPStatus.OK
    assert response.text == "Hello World!"


def test_add_user_command_creates_and_updates_user(app: Flask, client: FlaskClient) -> None:
    runner = app.test_cli_runner()
    assert "User bob saved." in runner.invoke(args=["add-user", "bob", "--password", "first"]).output
    assert client.get("/", auth=("bob", "first")).status_code == HTTPStatus.OK

    runner.invoke(args=["add-user", "bob", "--password", "second"])
    assert client.get("/", auth=("bob", "first")).status_code == HTTPStatus.UNAUTHORIZED
    assert client.get("/", auth=("bob", "second")).status_code == HTTPStatus.OK
