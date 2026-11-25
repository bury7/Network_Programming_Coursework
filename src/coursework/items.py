from flask import Blueprint, abort, jsonify, request, url_for
lazy from flask.typing import ResponseReturnValue

from coursework.db import get_db
from coursework.storage import Catalog, NewItem

MAX_PRICE = 1_000_000_000

bp = Blueprint("items", __name__)


def parse_item(data: object) -> NewItem:
    if not isinstance(data, dict):
        abort(400, "Expected a JSON object with name, price and color")
    name, price, color = data.get("name"), data.get("price"), data.get("color")
    if not isinstance(name, str) or not name.strip():
        abort(400, "name must be a non-empty string")
    if isinstance(price, bool) or not isinstance(price, int | float) or not 0 <= price <= MAX_PRICE:
        abort(400, f"price must be a number from 0 to {MAX_PRICE}")
    if not isinstance(color, str) or not color.strip():
        abort(400, "color must be a non-empty string")
    return {"name": name.strip(), "price": float(price), "color": color.strip()}


@bp.get("/items")
def list_items() -> ResponseReturnValue:
    return jsonify(Catalog(get_db()).list_items())


@bp.post("/items")
def create_item() -> ResponseReturnValue:
    item = Catalog(get_db()).add_item(parse_item(request.get_json(silent=True)))
    return jsonify(item), 201, {"Location": url_for("items.get_item", item_id=item["id"])}


@bp.put("/items")
def replace_items() -> ResponseReturnValue:
    data = request.get_json(silent=True)
    if not isinstance(data, list):
        abort(400, "Expected a JSON array of items")
    return jsonify(Catalog(get_db()).replace_items([parse_item(entry) for entry in data]))


@bp.delete("/items")
def delete_items() -> ResponseReturnValue:
    Catalog(get_db()).clear()
    return "", 204


@bp.get("/items/<int:item_id>")
def get_item(item_id: int) -> ResponseReturnValue:
    item = Catalog(get_db()).get_item(item_id)
    if item is None:
        abort(404, f"Item {item_id} not found")
    return jsonify(item)


@bp.put("/items/<int:item_id>")
def update_item(item_id: int) -> ResponseReturnValue:
    item = Catalog(get_db()).update_item(item_id, parse_item(request.get_json(silent=True)))
    if item is None:
        abort(404, f"Item {item_id} not found")
    return jsonify(item)


@bp.delete("/items/<int:item_id>")
def delete_item(item_id: int) -> ResponseReturnValue:
    if not Catalog(get_db()).delete_item(item_id):
        abort(404, f"Item {item_id} not found")
    return "", 204
