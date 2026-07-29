"""Flask routes for MyFurnitureApp.

Pages: /login (log in), / (catalogue / home page + current order),
/orders (order history), plus form-handling routes for adding items to the
order and confirming it. See architecture.md for how these fit together.
"""
import base64

from flask import Flask, Response, abort, flash, redirect, render_template, request, session, url_for
from werkzeug.security import check_password_hash

import db

app = Flask(__name__)
# Signs the session cookie. Fine for a local demo; a real deployment would
# load this from an environment variable instead of hardcoding it.
app.secret_key = "dev-secret-key-change-this-for-real-use"


def current_user():
    user_id = session.get("user_id")
    if user_id is None:
        return None
    return db.get_user_by_id(user_id)


def cart_with_total():
    """The cart lives in the session as a list of {product_id, name, price,
    quantity} dicts, built up as the buyer clicks "Add to order"."""
    cart = session.get("cart", [])
    total = sum(item["price"] * item["quantity"] for item in cart)
    return cart, total


@app.route("/")
def home():
    user = current_user()
    if user is None:
        return redirect(url_for("login"))

    products = db.get_all_products()
    cart, cart_total = cart_with_total()
    remaining_budget = user["budget_total"] - user["budget_spent"]

    return render_template(
        "catalogue.html",
        user=user,
        products=products,
        cart=cart,
        cart_total=cart_total,
        remaining_budget=remaining_budget,
    )


@app.route("/product-image/<int:product_id>")
def product_image(product_id):
    """Serves a product's image as its own small response instead of inlining
    it into the catalogue page - the MongoDB catalogue stores images as
    base64 data, and 700+ of those inline on one page would be huge."""
    product = db.get_product_by_id(product_id)
    if product is None:
        abort(404)

    image_url = product["image_url"]
    if image_url.startswith("data:"):
        header, encoded = image_url.split(",", 1)
        mime_type = header.removeprefix("data:").split(";")[0]
        return Response(base64.b64decode(encoded), mimetype=mime_type)

    return redirect(image_url)


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
        session["cart"] = []
        return redirect(url_for("home"))

    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/add-to-cart", methods=["POST"])
def add_to_cart():
    if current_user() is None:
        return redirect(url_for("login"))

    product = db.get_product_by_id(int(request.form["product_id"]))
    quantity = int(request.form["quantity"])

    if product is not None and quantity > 0:
        cart = session.get("cart", [])
        cart.append({
            "product_id": product["id"],
            "name": product["name"],
            "price": product["price"],
            "quantity": quantity,
        })
        session["cart"] = cart

    return redirect(url_for("home"))


@app.route("/clear-cart", methods=["POST"])
def clear_cart():
    session["cart"] = []
    return redirect(url_for("home"))


@app.route("/confirm-order", methods=["POST"])
def confirm_order():
    user = current_user()
    if user is None:
        return redirect(url_for("login"))

    cart, cart_total = cart_with_total()
    remaining_budget = user["budget_total"] - user["budget_spent"]

    if not cart:
        flash("Your order is empty.")
        return redirect(url_for("home"))

    if cart_total > remaining_budget:
        over_by = cart_total - remaining_budget
        flash(f"This order would put you ${over_by:.2f} over budget. Remove something and try again.")
        return redirect(url_for("home"))

    db.create_order(user["id"], cart)
    session["cart"] = []
    flash("Order placed!")
    return redirect(url_for("orders"))


@app.route("/orders")
def orders():
    user = current_user()
    if user is None:
        return redirect(url_for("login"))

    orders_with_items = [
        {"order": order, "items": db.get_items_for_order(order["id"])}
        for order in db.get_orders_for_user(user["id"])
    ]
    remaining_budget = user["budget_total"] - user["budget_spent"]

    return render_template(
        "orders.html", user=user, orders=orders_with_items, remaining_budget=remaining_budget
    )


if __name__ == "__main__":
    app.run(debug=True)
