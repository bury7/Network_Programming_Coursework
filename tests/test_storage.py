import sqlite3
from contextlib import closing
lazy from collections.abc import Generator
lazy from pathlib import Path

import pytest

from coursework.storage import Catalog, NewItem, UserStore, connect

T_SHIRT: NewItem = {"name": "T-shirt", "price": 499.99, "color": "black"}
CAP: NewItem = {"name": "Cap", "price": 250.0, "color": "red"}


@pytest.fixture
def connection(tmp_path: Path) -> Generator[sqlite3.Connection]:
    with closing(connect(tmp_path / "test.db")) as connection:
        yield connection


def test_ids_are_not_reused_after_clear(connection: sqlite3.Connection) -> None:
    catalog = Catalog(connection)
    catalog.add_item(T_SHIRT)
    catalog.clear()
    assert catalog.add_item(CAP) == {"id": 2, **CAP}


def test_replace_items_rolls_back_on_error(connection: sqlite3.Connection) -> None:
    catalog = Catalog(connection)
    catalog.add_item(T_SHIRT)
    broken: NewItem = {"name": None, "price": 1.0, "color": "x"}  # ty: ignore[invalid-argument-type]
    with pytest.raises(sqlite3.IntegrityError):
        catalog.replace_items([CAP, broken])
    assert catalog.list_items() == [{"id": 1, **T_SHIRT}]


def test_user_store_saves_and_updates_password(connection: sqlite3.Connection) -> None:
    users = UserStore(connection)
    users.save("alice", "first")
    users.save("alice", "second")
    assert users.verify("alice", "second")
    assert not users.verify("alice", "first")
    assert not users.verify("bob", "second")
