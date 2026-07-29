"""Database helpers for our own login system.

Everything about the catalogue, balance, and orders now comes live from the
furniture shop API (see shop_api.py) - the only thing left to store locally
is who's allowed to log into this app. One SQLite file (furniture.db),
created by seed_data.py.
"""
import sqlite3

DB_PATH = "furniture.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL
);
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # lets us access columns by name, e.g. row["email"]
    return conn


def init_schema():
    conn = get_db()
    conn.executescript(SCHEMA)
    conn.commit()
    conn.close()


def get_user_by_email(email):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE email = ?", (email,)).fetchone()
    conn.close()
    return user


def get_user_by_id(user_id):
    conn = get_db()
    user = conn.execute("SELECT * FROM users WHERE id = ?", (user_id,)).fetchone()
    conn.close()
    return user
