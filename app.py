"""Flask routes for MyFurnitureApp.

Pages: /login (log in), / (catalogue + balance), /orders (order history),
plus /buy for placing a real order through the furniture shop API. See
architecture.md for how these fit together.
"""
import os
import uuid

from dotenv import load_dotenv
from flask import Flask, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

import agent
import db
import shop_api

load_dotenv()

# The shop API only knows about one real account for this whole training
# exercise - every demo login in our app (alice@, bob@) acts through it.
SHOP_USER_ID = os.environ.get("SHOP_USER_ID")

app = Flask(__name__)
# Signs the session cookie. Fine for a local demo; a real deployment would
# load this from an environment variable instead of hardcoding it.
app.secret_key = "dev-secret-key-change-this-for-real-use"


def current_user():
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return db.get_user_by_id(user_id)


def fetch_balance():
    """Returns the real balance from the shop API, or None (with a flashed
    message) if it couldn't be fetched - callers show "unavailable" instead
    of crashing the page."""
    try:
        return shop_api.get_balance(SHOP_USER_ID)["balance"]
    except shop_api.ShopApiError as error:
        flash(f"Could not load your balance right now: {error}")
        return None


@app.route("/")
def home():
    user = current_user()
    if user is None:
        return redirect(url_for("login"))

    try:
        products = shop_api.get_catalogue()
    except shop_api.ShopApiError as error:
        products = []
        flash(f"Could not load the catalogue right now: {error}")

    return render_template("catalogue.html", user=user, products=products, balance=fetch_balance())


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form["email"]
        password = request.form["password"]
        user = db.get_user_by_email(email)

        if user is None or not check_password_hash(user["password_hash"], password):
            flash("Wrong email or password.")
            return render_template("login.html")

        session["user_id"] = user["id"]
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/buy", methods=["POST"])
def buy():
    if current_user() is None:
        return redirect(url_for("login"))

    item_id = request.form["item_id"]
    quantity = int(request.form.get("quantity", 1))
    # A fresh key per click - if the click is somehow submitted twice, the
    # shop API will charge for it twice too. A retry of the *same* attempt
    # (e.g. the browser resending after a dropped connection) would need to
    # reuse a key, which isn't a case this simple form triggers.
    idempotency_key = str(uuid.uuid4())

    try:
        result = shop_api.place_order(SHOP_USER_ID, item_id, quantity, idempotency_key)
        flash(
            f"Order placed! Total ${result['total_price']:.2f}. "
            f"Remaining balance: ${result['remaining_balance']:.2f}."
        )
    except shop_api.ProductNotFoundError:
        flash("This item is no longer available.")
    except shop_api.InsufficientBalanceError:
        flash("Insufficient balance for this order.")
    except shop_api.ShopApiError as error:
        flash(f"Could not place this order right now: {error}")

    return redirect(url_for("home"))


@app.route("/assistant", methods=["GET", "POST"])
def assistant():
    user = current_user()
    if user is None:
        return redirect(url_for("login"))

    question = ""
    reply = None
    trace = []

    if request.method == "POST":
        question = request.form.get("message", "").strip()
        if not question:
            flash("Type a request first.")
        else:
            try:
                reply, trace, pending = agent.ask(
                    question, SHOP_USER_ID, session.get("pending_purchase")
                )
                session["pending_purchase"] = pending
            except agent.AgentError as error:
                flash(str(error))

    return render_template(
        "assistant.html",
        user=user,
        balance=fetch_balance(),
        question=question,
        reply=reply,
        trace=trace,
        pending_purchase=session.get("pending_purchase"),
    )


@app.route("/orders")
def orders():
    user = current_user()
    if user is None:
        return redirect(url_for("login"))

    try:
        past_orders = shop_api.get_order_history(SHOP_USER_ID)
    except shop_api.ShopApiError as error:
        past_orders = []
        flash(f"Could not load order history right now: {error}")

    return render_template("orders.html", user=user, orders=past_orders, balance=fetch_balance())


if __name__ == "__main__":
    app.run(debug=True)
