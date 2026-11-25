from http import HTTPStatus

import pytest
from werkzeug.exceptions import BadRequest
lazy from flask.testing import FlaskClient

from coursework.items import MAX_PRICE, parse_item
from tests.conftest import ADMIN

T_SHIRT = {"name": "T-shirt", "price": 499.99, "color": "black"}
CAP = {"name": "Cap", "price": 250.0, "color": "red"}


def test_parse_item_returns_clean_item() -> None:
    item = parse_item({"name": "  T-shirt ", "price": 500, "color": " black", "extra": "ignored"})
    assert item == {"name": "T-shirt", "price": 500.0, "color": "black"}
    assert isinstance(item["price"], float)


def test_parse_item_accepts_price_limits() -> None:
    assert parse_item({**CAP, "price": 0})["price"] == 0
    assert parse_item({**CAP, "price": MAX_PRICE})["price"] == MAX_PRICE


@pytest.mark.parametrize(
    "data",
    [
        None,
        ["T-shirt", 499.99, "black"],
        {"price": 499.99, "color": "black"},
        {**T_SHIRT, "name": "   "},
        {**T_SHIRT, "name": 42},
        {**T_SHIRT, "price": "499.99"},
        {**T_SHIRT, "price": True},
        {**T_SHIRT, "price": -0.01},
        {**T_SHIRT, "price": MAX_PRICE + 1},
        {**T_SHIRT, "price": 10**400},
        {**T_SHIRT, "price": float("nan")},
        {**T_SHIRT, "price": float("inf")},
        {**T_SHIRT, "color": ""},
        {**T_SHIRT, "color": None},
    ],
)
def test_parse_item_rejects_invalid_data(data: object) -> None:
    with pytest.raises(BadRequest):
        parse_item(data)


def test_items_require_auth(client: FlaskClient) -> None:
    assert client.get("/items").status_code == HTTPStatus.UNAUTHORIZED


def test_create_and_read_item(client: FlaskClient) -> None:
    created = client.post("/items", json=T_SHIRT, auth=ADMIN)
    assert created.status_code == HTTPStatus.CREATED
    assert created.json == {"id": 1, **T_SHIRT}
    assert created.headers["Location"] == "/items/1"

    assert client.get("/items/1", auth=ADMIN).json == {"id": 1, **T_SHIRT}
    assert client.get("/items", auth=ADMIN).json == [{"id": 1, **T_SHIRT}]


def test_create_invalid_item_returns_error(client: FlaskClient) -> None:
    response = client.post("/items", json={**T_SHIRT, "price": -1}, auth=ADMIN)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert response.json == {"error": f"price must be a number from 0 to {MAX_PRICE}"}
    assert client.get("/items", auth=ADMIN).json == []


def test_update_item(client: FlaskClient) -> None:
    client.post("/items", json=T_SHIRT, auth=ADMIN)
    response = client.put("/items/1", json=CAP, auth=ADMIN)
    assert response.status_code == HTTPStatus.OK
    assert response.json == {"id": 1, **CAP}


def test_delete_item(client: FlaskClient) -> None:
    client.post("/items", json=T_SHIRT, auth=ADMIN)
    assert client.delete("/items/1", auth=ADMIN).status_code == HTTPStatus.NO_CONTENT
    assert client.get("/items/1", auth=ADMIN).status_code == HTTPStatus.NOT_FOUND


@pytest.mark.parametrize("method", ["get", "put", "delete"])
def test_missing_item_returns_not_found(client: FlaskClient, method: str) -> None:
    response = getattr(client, method)("/items/99", json=CAP, auth=ADMIN)
    assert response.status_code == HTTPStatus.NOT_FOUND
    assert response.json == {"error": "Item 99 not found"}


def test_replace_and_clear_catalog(client: FlaskClient) -> None:
    client.post("/items", json=T_SHIRT, auth=ADMIN)

    replaced = client.put("/items", json=[CAP, T_SHIRT], auth=ADMIN)
    assert replaced.status_code == HTTPStatus.OK
    assert replaced.json == [{"id": 2, **CAP}, {"id": 3, **T_SHIRT}]

    assert client.delete("/items", auth=ADMIN).status_code == HTTPStatus.NO_CONTENT
    assert client.get("/items", auth=ADMIN).json == []


def test_invalid_replace_keeps_catalog(client: FlaskClient) -> None:
    client.post("/items", json=T_SHIRT, auth=ADMIN)
    response = client.put("/items", json=[CAP, {"name": "Broken"}], auth=ADMIN)
    assert response.status_code == HTTPStatus.BAD_REQUEST
    assert client.get("/items", auth=ADMIN).json == [{"id": 1, **T_SHIRT}]


def test_post_is_not_allowed_on_single_item(client: FlaskClient) -> None:
    assert client.post("/items/1", json=CAP, auth=ADMIN).status_code == HTTPStatus.METHOD_NOT_ALLOWED
