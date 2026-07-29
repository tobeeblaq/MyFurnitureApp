"""Database helpers: one small function per query the app needs.

Everything lives in a single SQLite file (furniture.db), created by
seed_data.py. No ORM - just plain SQL, since the schema is small and this
needs to stay easy to follow.
"""
import sqlite3

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


def get_all_products():
    conn = get_db()
    products = conn.execute("SELECT * FROM products ORDER BY name").fetchall()
    conn.close()
    return products


def get_product_by_id(product_id):
    conn = get_db()
    product = conn.execute("SELECT * FROM products WHERE id = ?", (product_id,)).fetchone()
    conn.close()
    return product


def replace_all_products(products):
    """Wipes the catalogue and inserts this list instead.

    products is a list of dicts with name, description, price, image_url.
    Used to load the shared MongoDB catalogue in place of the placeholder
    products - see seed_data.py.
    """
    conn = get_db()
    conn.execute("DELETE FROM products")
    conn.executemany(
        "INSERT INTO products (name, description, price, image_url) "
        "VALUES (:name, :description, :price, :image_url)",
        products,
    )
    conn.commit()
    conn.close()


def create_order(user_id, cart_items):
    """Saves an order and its line items, and increases the user's budget_spent.

    cart_items is a list of dicts: {"product_id", "name", "price", "quantity"}.
    unit_price is copied from the item's current price, so the order keeps
    showing what was actually paid even if a product's price changes later.
    Returns the order total.
    """
    total = sum(item["price"] * item["quantity"] for item in cart_items)

    conn = get_db()
    cur = conn.execute(
        "INSERT INTO orders (user_id, created_at, total_amount) VALUES (?, datetime('now'), ?)",
        (user_id, total),
    )
    order_id = cur.lastrowid

    for item in cart_items:
        conn.execute(
            "INSERT INTO order_items (order_id, product_id, quantity, unit_price) "
            "VALUES (?, ?, ?, ?)",
            (order_id, item["product_id"], item["quantity"], item["price"]),
        )

    conn.execute(
        "UPDATE users SET budget_spent = budget_spent + ? WHERE id = ?",
        (total, user_id),
    )
    conn.commit()
    conn.close()
    return total


def get_orders_for_user(user_id):
    conn = get_db()
    orders = conn.execute(
        "SELECT * FROM orders WHERE user_id = ? ORDER BY created_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return orders


def get_items_for_order(order_id):
    conn = get_db()
    items = conn.execute(
        "SELECT order_items.*, products.name AS product_name "
        "FROM order_items JOIN products ON order_items.product_id = products.id "
        "WHERE order_id = ?",
        (order_id,),
    ).fetchall()
    conn.close()
    return items
