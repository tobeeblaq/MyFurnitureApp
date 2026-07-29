"""Creates the SQLite database and fills it with demo users and placeholder
furniture products.

Run this once before starting the app for the first time (safe to re-run -
it won't duplicate existing users or products):
    python seed_data.py
"""
import sqlite3

from werkzeug.security import generate_password_hash

DB_PATH = "furniture.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    email TEXT UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    budget_total REAL NOT NULL,
    budget_spent REAL NOT NULL DEFAULT 0
);

CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT NOT NULL,
    price REAL NOT NULL,
    image_url TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS orders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    created_at TEXT NOT NULL,
    total_amount REAL NOT NULL,
    FOREIGN KEY (user_id) REFERENCES users (id)
);

CREATE TABLE IF NOT EXISTS order_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    order_id INTEGER NOT NULL,
    product_id INTEGER NOT NULL,
    quantity INTEGER NOT NULL,
    unit_price REAL NOT NULL,
    FOREIGN KEY (order_id) REFERENCES orders (id),
    FOREIGN KEY (product_id) REFERENCES products (id)
);
"""

# email, password, starting budget
DEMO_USERS = [
    ("alice@example.com", "password123", 1000.00),
    ("bob@example.com", "password123", 500.00),
]

# Placeholder catalogue - swap this for real products later (see requirements.md).
PLACEHOLDER_PRODUCTS = [
    ("Oak Desk", "A solid oak desk with plenty of legroom.", 249.99,
     "https://placehold.co/300x200?text=Oak+Desk"),
    ("Office Chair", "Ergonomic office chair with lumbar support.", 149.50,
     "https://placehold.co/300x200?text=Office+Chair"),
    ("Bookshelf", "Five-shelf bookcase, holds up to 150 books.", 89.00,
     "https://placehold.co/300x200?text=Bookshelf"),
    ("Sofa", "Three-seater fabric sofa in charcoal grey.", 599.00,
     "https://placehold.co/300x200?text=Sofa"),
    ("Coffee Table", "Round coffee table with a glass top.", 129.99,
     "https://placehold.co/300x200?text=Coffee+Table"),
    ("Bed Frame", "Queen-size bed frame, dark walnut finish.", 349.00,
     "https://placehold.co/300x200?text=Bed+Frame"),
]


def seed():
    conn = sqlite3.connect(DB_PATH)
    conn.executescript(SCHEMA)

    for email, password, budget in DEMO_USERS:
        conn.execute(
            "INSERT OR IGNORE INTO users (email, password_hash, budget_total, budget_spent) "
            "VALUES (?, ?, ?, 0)",
            (email, generate_password_hash(password), budget),
        )

    already_has_products = conn.execute("SELECT COUNT(*) FROM products").fetchone()[0]
    if already_has_products == 0:
        conn.executemany(
            "INSERT INTO products (name, description, price, image_url) VALUES (?, ?, ?, ?)",
            PLACEHOLDER_PRODUCTS,
        )

    conn.commit()
    conn.close()
    print(
        f"Seeded {DB_PATH} with {len(DEMO_USERS)} demo users and "
        f"{len(PLACEHOLDER_PRODUCTS)} placeholder products (skipped any that already existed)."
    )


if __name__ == "__main__":
    seed()
