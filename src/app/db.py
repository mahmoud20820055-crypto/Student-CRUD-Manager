"""SQLite helpers: connection per request + schema bootstrap."""
import sqlite3

from flask import Flask, current_app, g

SCHEMA = """
CREATE TABLE IF NOT EXISTS students (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    student_code  TEXT    NOT NULL UNIQUE,
    first_name    TEXT    NOT NULL,
    last_name     TEXT    NOT NULL,
    email         TEXT    NOT NULL UNIQUE,
    major         TEXT    NOT NULL,
    gpa           REAL    NOT NULL CHECK (gpa >= 0 AND gpa <= 4),
    enrolled_year INTEGER NOT NULL,
    created_at    TEXT    NOT NULL DEFAULT (datetime('now')),
    updated_at    TEXT    NOT NULL DEFAULT (datetime('now'))
);
"""


def get_db() -> sqlite3.Connection:
    if "db" not in g:
        g.db = sqlite3.connect(current_app.config["DATABASE_PATH"])
        g.db.row_factory = sqlite3.Row
    return g.db


def close_db(_exc=None) -> None:
    conn = g.pop("db", None)
    if conn is not None:
        conn.close()


def init_app(app: Flask) -> None:
    with sqlite3.connect(app.config["DATABASE_PATH"]) as conn:
        conn.executescript(SCHEMA)
    app.teardown_appcontext(close_db)
