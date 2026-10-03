import sqlite3
from pathlib import Path

from flask import current_app, g


def get_db():
    if "db" not in g:
        Path(current_app.instance_path).mkdir(parents=True, exist_ok=True)
        g.db = sqlite3.connect(current_app.config["DATABASE"])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(_error=None):
    db = g.pop("db", None)
    if db is not None:
        db.close()


def init_db():
    db = get_db()
    schema = Path(current_app.root_path, "schema.sql").read_text(encoding="utf-8")
    db.executescript(schema)
    db.commit()


def init_app(app):
    app.teardown_appcontext(close_db)
