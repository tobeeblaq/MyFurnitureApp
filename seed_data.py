"""Creates the SQLite database, adds demo users, and loads the furniture
catalogue from the shared MongoDB training database.

Run this once before starting the app for the first time, and again any
time you want to re-sync the catalogue (safe to re-run - it won't duplicate
existing demo users):
    python seed_data.py

Needs a MONGODB_URI environment variable (see .env.example). If it isn't
set, or the connection fails, this falls back to a handful of placeholder
products instead of leaving the catalogue empty.
"""
import os

from dotenv import load_dotenv
from pymongo import MongoClient
from werkzeug.security import generate_password_hash

import db

# email, password, starting budget
DEMO_USERS = [
    ("alice@example.com", "password123", 1000.00),
    ("bob@example.com", "password123", 500.00),
]

# Used only if MongoDB isn't reachable - keeps the app usable offline.
PLACEHOLDER_PRODUCTS = [
    {"name": "Oak Desk", "description": "A solid oak desk with plenty of legroom.",
     "price": 249.99, "image_url": "https://placehold.co/300x200?text=Oak+Desk"},
    {"name": "Office Chair", "description": "Ergonomic office chair with lumbar support.",
     "price": 149.50, "image_url": "https://placehold.co/300x200?text=Office+Chair"},
    {"name": "Bookshelf", "description": "Five-shelf bookcase, holds up to 150 books.",
     "price": 89.00, "image_url": "https://placehold.co/300x200?text=Bookshelf"},
    {"name": "Sofa", "description": "Three-seater fabric sofa in charcoal grey.",
     "price": 599.00, "image_url": "https://placehold.co/300x200?text=Sofa"},
    {"name": "Coffee Table", "description": "Round coffee table with a glass top.",
     "price": 129.99, "image_url": "https://placehold.co/300x200?text=Coffee+Table"},
    {"name": "Bed Frame", "description": "Queen-size bed frame, dark walnut finish.",
     "price": 349.00, "image_url": "https://placehold.co/300x200?text=Bed+Frame"},
]


def seed_users():
    conn = db.get_db()
    for email, password, budget in DEMO_USERS:
        conn.execute(
            "INSERT OR IGNORE INTO users (email, password_hash, budget_total, budget_spent) "
            "VALUES (?, ?, ?, 0)",
            (email, generate_password_hash(password), budget),
        )
    conn.commit()
    conn.close()


def describe(doc):
    """Builds a human-readable description from a MongoDB catalog document -
    the source data has no description field, just category/colours/dimensions."""
    colours = doc.get("colours") or []
    colour_text = ", ".join(colours) if colours else "colour not specified"

    dims = []
    for label, key in (("wide", "width"), ("deep", "depth"), ("high", "height")):
        value = doc.get(key)
        if value:
            dims.append(f"{value:g}cm {label}")
    dims_text = ", ".join(dims) if dims else "dimensions not specified"

    category = doc.get("category", "Furniture")
    return f"{category}. Available in {colour_text}. {dims_text}."


def image_data_uri(doc):
    """The catalog's "image_url" field is actually a base64-encoded image,
    not a link - this turns it into a data: URI a browser <img> tag can show
    directly, so no separate image hosting is needed."""
    encoded = doc.get("image_url")
    if not encoded:
        return "https://placehold.co/300x200?text=No+Image"
    mime_type = doc.get("image_mime_type") or "image/jpeg"
    return f"data:{mime_type};base64,{encoded}"


def fetch_products_from_mongo():
    load_dotenv()
    uri = os.environ.get("MONGODB_URI")
    if not uri:
        raise RuntimeError(
            "MONGODB_URI is not set. Copy .env.example to .env and fill in "
            "the connection string."
        )

    client = MongoClient(uri, serverSelectionTimeoutMS=8000)
    try:
        catalog_collection = client.get_default_database()["catalog"]
        docs = list(catalog_collection.find())
    finally:
        client.close()

    return [
        {
            "name": doc.get("product_name", "Unnamed product"),
            "description": describe(doc),
            "price": doc.get("price") or 0.0,
            "image_url": image_data_uri(doc),
        }
        for doc in docs
    ]


def seed():
    db.init_schema()
    seed_users()

    try:
        products = fetch_products_from_mongo()
        db.replace_all_products(products)
        print(f"Loaded {len(products)} products from the MongoDB catalogue.")
    except Exception as error:
        print(f"Could not load products from MongoDB ({error}).")
        print("Falling back to placeholder products instead.")
        db.replace_all_products(PLACEHOLDER_PRODUCTS)

    print(f"Seeded {db.DB_PATH} with {len(DEMO_USERS)} demo users.")


if __name__ == "__main__":
    seed()
