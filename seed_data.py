"""Creates the SQLite database and adds demo login accounts.

Run this once before starting the app for the first time (safe to re-run -
it won't duplicate existing accounts):
    python seed_data.py

The catalogue, balance, and orders all come live from the furniture shop API
(see shop_api.py) - this only sets up who can log into our app.
"""
from werkzeug.security import generate_password_hash

import db

# email, password
DEMO_USERS = [
    ("alice@example.com", "password123"),
    ("bob@example.com", "password123"),
]


def seed():
    db.init_schema()

    conn = db.get_db()
    for email, password in DEMO_USERS:
        conn.execute(
            "INSERT OR IGNORE INTO users (email, password_hash) VALUES (?, ?)",
            (email, generate_password_hash(password)),
        )
    conn.commit()
    conn.close()

    print(f"Seeded {db.DB_PATH} with {len(DEMO_USERS)} demo login accounts.")


if __name__ == "__main__":
    seed()
