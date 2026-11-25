from datetime import date, datetime, timedelta
from xml.etree.ElementTree import Element, SubElement, tostring
from zoneinfo import ZoneInfo

import requests
from flask import Blueprint, Response, abort, jsonify, request
lazy from flask.typing import ResponseReturnValue

API_URL = "https://bank.gov.ua/NBUStatService/v1/statdirectory/exchange"
KYIV_TZ = ZoneInfo("Europe/Kyiv")
REQUEST_TIMEOUT = 10
DAY_OFFSETS = {"today": 0, "yesterday": 1}

bp = Blueprint("currency", __name__)


def fetch_rate(currency: str, day: date) -> float | None:
    params = {"valcode": currency, "date": f"{day:%Y%m%d}", "json": ""}
    response = requests.get(API_URL, params=params, timeout=REQUEST_TIMEOUT)
    response.raise_for_status()
    rates = response.json()
    return rates[0]["rate"] if rates else None


def to_xml(tag: str, data: dict[str, object]) -> str:
    root = Element(tag)
    for key, value in data.items():
        SubElement(root, key).text = str(value)
    return tostring(root, encoding="unicode", xml_declaration=True)


def render_rate(code: str, rate: float) -> ResponseReturnValue:
    content_type = request.headers.get("Content-Type", "").partition(";")[0].strip().lower()
    data = {"currency": code, "rate": rate}
    if content_type == "application/json":
        return jsonify(data)
    if content_type == "application/xml":
        return Response(to_xml("exchange_rate", data), mimetype="application/xml")
    return Response(f"{code} - {rate}".replace(".", ","), mimetype="text/plain")


@bp.get("/currency")
def currency() -> ResponseReturnValue:
    days = [day for day in DAY_OFFSETS if request.args.get(day) is not None]
    if len(days) != 1:
        abort(400, "Pass exactly one parameter: today or yesterday")

    day = datetime.now(KYIV_TZ).date() - timedelta(days=DAY_OFFSETS[days[0]])
    try:
        rate = fetch_rate("USD", day)
    except requests.RequestException, LookupError, TypeError:
        abort(502, "NBU API is unavailable")

    if rate is None:
        abort(404, f"No USD rate for {day:%d.%m.%Y}")
    return render_rate("USD", rate)
