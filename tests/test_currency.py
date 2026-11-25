from datetime import date, datetime, timedelta
from http import HTTPStatus
from unittest.mock import Mock

import pytest
import requests
lazy from flask.testing import FlaskClient

from coursework import currency
from tests.conftest import ADMIN


@pytest.fixture
def requested_days(monkeypatch: pytest.MonkeyPatch) -> list[date]:
    days: list[date] = []

    def fake_fetch_rate(_currency: str, day: date) -> float:
        days.append(day)
        return 41.5

    monkeypatch.setattr(currency, "fetch_rate", fake_fetch_rate)
    return days


def test_fetch_rate_reads_rate_from_nbu(monkeypatch: pytest.MonkeyPatch) -> None:
    rate = 45.3541
    get = Mock(return_value=Mock(json=Mock(return_value=[{"cc": "USD", "rate": rate}])))
    monkeypatch.setattr(requests, "get", get)

    assert currency.fetch_rate("USD", date(2026, 11, 25)) == rate
    assert get.call_args.kwargs["params"] == {"valcode": "USD", "date": "20261125", "json": ""}


def test_fetch_rate_returns_none_without_data(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(requests, "get", Mock(return_value=Mock(json=Mock(return_value=[]))))
    assert currency.fetch_rate("USD", date(2026, 11, 25)) is None


@pytest.mark.parametrize(("param", "offset"), [("today", 0), ("yesterday", 1)])
def test_rate_for_requested_day(client: FlaskClient, requested_days: list[date], param: str, offset: int) -> None:
    response = client.get(f"/currency?{param}", auth=ADMIN)
    assert response.status_code == HTTPStatus.OK
    assert requested_days == [datetime.now(currency.KYIV_TZ).date() - timedelta(days=offset)]


@pytest.mark.usefixtures("requested_days")
@pytest.mark.parametrize(
    ("content_type", "mimetype", "body"),
    [
        (None, "text/plain", "USD - 41,5"),
        ("text/html", "text/plain", "USD - 41,5"),
        ("application/json", "application/json", '{"currency":"USD","rate":41.5}\n'),
        (
            "application/xml; charset=utf-8",
            "application/xml",
            (
                "<?xml version='1.0' encoding='utf-8'?>\n"
                "<exchange_rate><currency>USD</currency><rate>41.5</rate></exchange_rate>"
            ),
        ),
    ],
)
def test_response_format_follows_content_type(
    client: FlaskClient, content_type: str | None, mimetype: str, body: str
) -> None:
    headers = {"Content-Type": content_type} if content_type else {}
    response = client.get("/currency?today", auth=ADMIN, headers=headers)
    assert response.mimetype == mimetype
    assert response.text == body


@pytest.mark.usefixtures("requested_days")
@pytest.mark.parametrize("query", ["", "today&yesterday", "tomorrow"])
def test_exactly_one_day_parameter_is_required(client: FlaskClient, query: str) -> None:
    assert client.get(f"/currency?{query}", auth=ADMIN).status_code == HTTPStatus.BAD_REQUEST


def test_text_keeps_every_digit_of_the_rate(client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(currency, "fetch_rate", Mock(return_value=1234.5678))
    assert client.get("/currency?today", auth=ADMIN).text == "USD - 1234,5678"


@pytest.mark.parametrize(
    "get",
    [
        Mock(side_effect=requests.ConnectionError),
        Mock(return_value=Mock(json=Mock(return_value=[{"cc": "USD"}]))),
        Mock(return_value=Mock(json=Mock(return_value={"message": "unexpected"}))),
        Mock(return_value=Mock(json=Mock(return_value="unexpected"))),
    ],
)
def test_nbu_failure_returns_bad_gateway(client: FlaskClient, monkeypatch: pytest.MonkeyPatch, get: Mock) -> None:
    monkeypatch.setattr(requests, "get", get)
    response = client.get("/currency?today", auth=ADMIN)
    assert response.status_code == HTTPStatus.BAD_GATEWAY
    assert response.json == {"error": "NBU API is unavailable"}


def test_missing_rate_returns_not_found(client: FlaskClient, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(currency, "fetch_rate", Mock(return_value=None))
    assert client.get("/currency?today", auth=ADMIN).status_code == HTTPStatus.NOT_FOUND
