"""JSON API for the Next.js frontend (see frontend/).

This sits next to the existing server-rendered pages in app.py - both share
the same Flask app, session/login logic, and business modules (db.py,
shop_api.py, agent.py). Nothing about the catalogue/balance/orders logic is
duplicated here; these routes just return JSON instead of rendering HTML.

register_api_routes() takes the already-built `app` and helpers as arguments
rather than importing them from app.py - app.py runs as "__main__" when
started directly, so an `import app` in here would re-execute app.py as a
second, separate module (and a second, unused Flask instance).
"""
import uuid

from flask import jsonify, request, session
from werkzeug.security import check_password_hash

import agent
import db
import shop_api


def register_api_routes(app, current_user, shop_user_id):
    def fetch_balance_silent():
        """Same idea as app.fetch_balance(), but doesn't flash() - the
        frontend shows its own error banners instead of Flask's flash
        messages."""
        try:
            return shop_api.get_balance(shop_user_id)["balance"]
        except shop_api.ShopApiError:
            return None

    @app.route("/api/me")
    def api_me():
        user = current_user()
        if user is None:
            return jsonify({"authenticated": False})

        return jsonify({
            "authenticated": True,
            "email": user["email"],
            "balance": fetch_balance_silent(),
        })

    @app.route("/api/login", methods=["POST"])
    def api_login():
        data = request.get_json(silent=True) or {}
        email = data.get("email", "")
        password = data.get("password", "")
        user = db.get_user_by_email(email)

        if user is None or not check_password_hash(user["password_hash"], password):
            return jsonify({"error": "Wrong email or password."}), 401

        session["user_id"] = user["id"]
        return jsonify({"email": user["email"], "balance": fetch_balance_silent()})

    @app.route("/api/logout", methods=["POST"])
    def api_logout():
        session.clear()
        return jsonify({})

    @app.route("/api/catalogue")
    def api_catalogue():
        if current_user() is None:
            return jsonify({"error": "Not logged in."}), 401

        try:
            products = shop_api.get_catalogue()
        except shop_api.ShopApiError as error:
            return jsonify({"error": f"Could not load the catalogue right now: {error}"}), 502

        return jsonify({"products": products})

    @app.route("/api/buy", methods=["POST"])
    def api_buy():
        if current_user() is None:
            return jsonify({"error": "Not logged in."}), 401

        data = request.get_json(silent=True) or {}
        item_id = data.get("item_id")
        quantity = int(data.get("quantity", 1))
        if not item_id:
            return jsonify({"error": "item_id is required."}), 400

        # A fresh key per request - if the click is somehow submitted twice,
        # the shop API will charge for it twice too. A retry of the *same*
        # attempt (e.g. the browser resending after a dropped connection)
        # would need to reuse a key, which isn't a case this simple form
        # triggers.
        idempotency_key = str(uuid.uuid4())

        try:
            result = shop_api.place_order(shop_user_id, item_id, quantity, idempotency_key)
            return jsonify({
                "message": f"Order placed! Total ${result['total_price']:.2f}.",
                "total_price": result["total_price"],
                "remaining_balance": result["remaining_balance"],
            })
        except shop_api.ProductNotFoundError:
            return jsonify({"error": "This item is no longer available."}), 404
        except shop_api.InsufficientBalanceError:
            return jsonify({"error": "Insufficient balance for this order."}), 402
        except shop_api.ShopApiError as error:
            return jsonify({"error": f"Could not place this order right now: {error}"}), 502

    @app.route("/api/assistant", methods=["POST"])
    def api_assistant():
        if current_user() is None:
            return jsonify({"error": "Not logged in."}), 401

        data = request.get_json(silent=True) or {}
        question = (data.get("message") or "").strip()
        if not question:
            return jsonify({"error": "Type a request first."}), 400

        try:
            reply, trace, pending = agent.ask(question, shop_user_id, session.get("pending_purchase"))
            session["pending_purchase"] = pending
        except agent.AgentError as error:
            return jsonify({"error": str(error)}), 503

        return jsonify({"reply": reply, "trace": trace, "pending_purchase": pending})

    @app.route("/api/orders")
    def api_orders():
        if current_user() is None:
            return jsonify({"error": "Not logged in."}), 401

        try:
            past_orders = shop_api.get_order_history(shop_user_id)
        except shop_api.ShopApiError as error:
            return jsonify({"error": f"Could not load order history right now: {error}"}), 502

        return jsonify({"orders": past_orders})
