"""Client for the Day 1 furniture shop API (day1.training.cognitivo.com.au).

This is the real source of truth for the catalogue, balances, and orders -
nothing about products or orders is stored locally. See architecture.md for
how this fits into the rest of the app.
"""
import os

import requests

BASE_URL = "https://day1.training.cognitivo.com.au"
TIMEOUT_SECONDS = 10


class ShopApiError(Exception):
    """Raised for any problem talking to the shop API - network issues,
    unexpected responses, or business errors without a more specific type
    below. The message is written to be shown directly to the buyer."""


class ProductNotFoundError(ShopApiError):
    pass


class InsufficientBalanceError(ShopApiError):
    pass


def _headers():
    api_key = os.environ.get("API_KEY")
    if not api_key:
        raise ShopApiError(
            "API_KEY is not set. Copy .env.example to .env and fill it in."
        )
    return {"X-Api-Key": api_key}


def _get(path, params=None):
    try:
        response = requests.get(
            f"{BASE_URL}{path}", headers=_headers(), params=params, timeout=TIMEOUT_SECONDS
        )
    except requests.exceptions.RequestException as error:
        raise ShopApiError(f"Could not reach the furniture shop ({error}).") from error

    if not response.ok:
        raise ShopApiError(f"The furniture shop returned an error ({response.status_code}).")
    return response.json()


def get_catalogue(category=None):
    """Products for browsing: item_id, product_name, category, price, colours -
    this is the fast search-index endpoint, not the image-heavy /catalogue one
    (see the Day 1 Participant Guide). category must match an existing category
    name exactly - there's no fuzzy, price, or colour filtering on the server,
    so anything like "cheap" or a colour has to be judged over these results by
    whoever calls this (see agent.py)."""
    params = {"category": category} if category else None
    return _get("/catalogue/search-index", params=params)


def get_product(item_id):
    """One exact product by item_id, with full details. Not for searching -
    only for looking up an item you already have the ID for."""
    try:
        response = requests.get(
            f"{BASE_URL}/catalogue/{item_id}", headers=_headers(), timeout=TIMEOUT_SECONDS
        )
    except requests.exceptions.RequestException as error:
        raise ShopApiError(f"Could not reach the furniture shop ({error}).") from error

    if response.status_code == 404:
        raise ProductNotFoundError(f"No product with item_id '{item_id}'.")
    if not response.ok:
        raise ShopApiError(f"The furniture shop returned an error ({response.status_code}).")
    return response.json()


def get_balance(user_id):
    """Returns {"user_id", "name", "balance"} for this shop account."""
    return _get(f"/users/{user_id}")


def get_order_history(user_id):
    return _get(f"/orders/{user_id}")


def place_order(user_id, item_id, quantity, idempotency_key):
    """Places a real order (this debits the account's balance). Raises
    ProductNotFoundError / InsufficientBalanceError / ShopApiError instead of
    ever letting an HTTP error or network failure bubble up uncaught -
    callers should catch these and show a friendly message.
    """
    headers = _headers()
    headers["Content-Type"] = "application/json"
    headers["Idempotency-Key"] = idempotency_key

    try:
        response = requests.post(
            f"{BASE_URL}/orders",
            headers=headers,
            json={"user_id": user_id, "items": [{"item_id": item_id, "quantity": quantity}]},
            timeout=TIMEOUT_SECONDS,
        )
    except requests.exceptions.RequestException as error:
        raise ShopApiError(f"Could not reach the furniture shop ({error}).") from error

    if response.status_code == 200:
        return response.json()

    detail = response.json().get("detail", "") if response.content else ""

    if response.status_code == 404:
        raise ProductNotFoundError(detail or "This item is no longer available.")
    if response.status_code == 402:
        raise InsufficientBalanceError(detail or "Insufficient balance for this order.")
    raise ShopApiError(detail or f"The furniture shop couldn't process this order ({response.status_code}).")
