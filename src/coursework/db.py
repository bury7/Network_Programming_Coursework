lazy import sqlite3

import click
from flask import Flask, current_app, g
from flask.cli import with_appcontext

from coursework.storage import UserStore, connect


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = connect(current_app.config["DATABASE"])
    return g.db


def close_db(_error: BaseException | None = None) -> None:
    db = g.pop("db", None)
    if db is not None:
        db.close()


@click.command("add-user")
@click.argument("username")
@click.password_option()
@with_appcontext
def add_user_command(username: str, password: str) -> None:
    """Create a user or change the password of an existing one."""
    UserStore(get_db()).save(username, password)
    click.echo(f"User {username} saved.")


def init_app(app: Flask) -> None:
    app.teardown_appcontext(close_db)
    app.cli.add_command(add_user_command)
    if app.config["ADMIN_USERNAME"] and app.config["ADMIN_PASSWORD"]:
        with app.app_context():
            UserStore(get_db()).save(app.config["ADMIN_USERNAME"], app.config["ADMIN_PASSWORD"])
