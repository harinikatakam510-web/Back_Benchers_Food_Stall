from flask import Flask, render_template, request, jsonify, Response, redirect
from datetime import datetime, timedelta, timezone
from functools import wraps
import hmac
import json
import os
import sqlite3
import sys
import time
import uuid
import razorpay
from dotenv import load_dotenv

# Load settings from a local .env file
# (on Render, the dashboard Environment Variables are used instead).
load_dotenv()

# The emoji in the print() logs crash on consoles that aren't UTF-8
# (common on Windows), which would break the payment endpoints.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

IST = timezone(timedelta(hours=5, minutes=30))


# ============================================================
# RAZORPAY CONFIGURATION
# ============================================================

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")

razorpay_client = None

if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:
    razorpay_client = razorpay.Client(
        auth=(RAZORPAY_KEY_ID, RAZORPAY_KEY_SECRET)
    )


# ============================================================
# ADMIN LOGIN
#
# Set ADMIN_USERNAME and ADMIN_PASSWORD in .env / Render.
# If ADMIN_PASSWORD is not set, the admin pages stay locked.
# ============================================================

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")


def admin_required(view):

    @wraps(view)
    def wrapper(*args, **kwargs):

        if not ADMIN_PASSWORD:
            return Response(
                "Admin is locked. Set ADMIN_PASSWORD in the environment variables.",
                503
            )

        auth = request.authorization

        if (
            not auth
            or not hmac.compare_digest(auth.username or "", ADMIN_USERNAME)
            or not hmac.compare_digest(auth.password or "", ADMIN_PASSWORD)
        ):
            return Response(
                "Login required.",
                401,
                {"WWW-Authenticate": 'Basic realm="Back Benchers Admin"'}
            )

        return view(*args, **kwargs)

    return wrapper


# ============================================================
# MENU PRICES (in ₹)
#
# ⭐ This is the ONLY place prices live.
#    The menu page, the cart and the payment all use these.
#
# Each product maps (option, size) -> price.
# To add a product, add it here AND add its card in menu.html
# (with data-product="<exact same name>").
# ============================================================

MENU = {

    "Chips Mix Loaded": {
        ("Veg Loaded", "Mini"): 49,
        ("Veg Loaded", "Large"): 69,
        ("Non Veg Loaded", "Mini"): 59,
        ("Non Veg Loaded", "Large"): 79,
    },

    "Masaka Bun": {
        ("Masaka Bun", ""): 49,
        ("Chocolate Masaka Bun", ""): 49,
        ("Mixed Flavour Bun", ""): 69,
    },

    "Veg Loaded French Fries": {
        ("", "Mini"): 59,
        ("", "Large"): 89,
    },

    "Non Veg Loaded French Fries": {
        ("", "Mini"): 69,
        ("", "Large"): 99,
    },

    "Golisoda": {
        ("Blueberry", ""): 30,
        ("Lemon", ""): 30,
        ("Orange", ""): 30,
        ("Mango", ""): 30,
    },

    "Back Benchers Burger": {
        ("Veg Burger", "Mini"): 49,
        ("Veg Burger", "Large"): 69,
        ("Non Veg Burger", "Mini"): 59,
        ("Non Veg Burger", "Large"): 89,
    },

    "Bangalore Special Sweet": {("", ""): 49},
    "Black Forest": {("", ""): 89},
    "Kaju Chicken Fry": {("", ""): 99},
    "Chocolate Cake": {("", ""): 89},
    "Soft Drink": {("", ""): 15},
    "Samosa": {("", ""): 15},

    # COMBOS (names match data-product in menu.html)

    "Drink + Samosa Combo": {("", ""): 25},
    "Cake + Samosa + Soft Drink Combo": {("", ""): 149},
    "Kaju Chicken Fry + Drink + Chaco Chaco Combo": {("", ""): 179},

}

MAX_QUANTITY_PER_ITEM = 20


@app.context_processor
def menu_prices_for_templates():
    """
    Makes prices available in every template:

      {{ price("Black Forest") }}           -> 89
      {{ menu_prices | tojson }}            -> used by script.js
    """

    def price(name, option="", size=""):
        return MENU[name][(option, size)]

    menu_prices = {
        name: {f"{option}|{size}": amount for (option, size), amount in choices.items()}
        for name, choices in MENU.items()
    }

    return {
        "price": price,
        "menu_prices": menu_prices,
        "max_quantity": MAX_QUANTITY_PER_ITEM,
    }


def price_cart(cart_items):
    """
    Rebuild the cart using MENU prices.

    Returns (items, total_paise) or raises ValueError
    with a message for the customer.
    """

    if not isinstance(cart_items, list) or not cart_items:
        raise ValueError("Cart is empty.")

    items = []
    total_paise = 0

    for cart_item in cart_items:

        if not isinstance(cart_item, dict):
            raise ValueError("Invalid cart item.")

        name = str(cart_item.get("name") or "").strip()
        option = str(cart_item.get("option") or "").strip()
        size = str(cart_item.get("size") or "").strip()

        price = MENU.get(name, {}).get((option, size))

        if price is None:
            raise ValueError(
                f"'{name}' is not available. "
                "Please remove it from your cart and add it again from the menu."
            )

        try:
            quantity = int(cart_item.get("quantity", 1))
        except (TypeError, ValueError):
            raise ValueError("Invalid quantity.")

        if quantity < 1 or quantity > MAX_QUANTITY_PER_ITEM:
            raise ValueError(
                f"Quantity for '{name}' must be between 1 and {MAX_QUANTITY_PER_ITEM}."
            )

        items.append({
            "name": name,
            "option": option,
            "size": size,
            "price": price,
            "quantity": quantity,
        })

        total_paise += price * quantity * 100

    return items, total_paise


# ============================================================
# DATABASE
#
# Local:  SQLite file (database.db)
# Online: set DATABASE_URL to a Postgres database.
#
# Render's free plan wipes local files on every restart and
# deploy, so online you MUST use DATABASE_URL or orders are lost.
# ============================================================

DATABASE_URL = os.getenv("DATABASE_URL")
SQLITE_PATH = os.path.join(BASE_DIR, "database.db")


def run_query(sql, params=(), fetch=None):
    """
    Run one SQL statement. Write SQL with ? placeholders.

    fetch = None  -> returns number of affected rows
    fetch = "one" -> returns one row as dict (or None)
    fetch = "all" -> returns list of dicts
    """

    if DATABASE_URL:

        import psycopg
        from psycopg.rows import dict_row

        with psycopg.connect(DATABASE_URL, row_factory=dict_row) as conn:
            cur = conn.execute(sql.replace("?", "%s"), params)

            if fetch == "one":
                return cur.fetchone()

            if fetch == "all":
                return cur.fetchall()

            return cur.rowcount

    conn = sqlite3.connect(SQLITE_PATH)
    conn.row_factory = sqlite3.Row

    try:
        with conn:
            cur = conn.execute(sql, params)

            if fetch == "one":
                row = cur.fetchone()
                return dict(row) if row else None

            if fetch == "all":
                return [dict(row) for row in cur.fetchall()]

            return cur.rowcount

    finally:
        conn.close()


def init_db():

    run_query("""
        CREATE TABLE IF NOT EXISTS orders (
            razorpay_order_id   TEXT PRIMARY KEY,
            order_id            TEXT UNIQUE NOT NULL,
            customer_name       TEXT NOT NULL,
            phone               TEXT NOT NULL,
            table_name          TEXT NOT NULL,
            items               TEXT NOT NULL,
            total_paise         INTEGER NOT NULL,
            payment_status      TEXT NOT NULL,
            status              TEXT NOT NULL,
            razorpay_payment_id TEXT UNIQUE,
            created_at          TEXT NOT NULL
        )
    """)

    # Small key/value store shared by every copy of the site
    # (used for the automatic switch to the new website).

    run_query("""
        CREATE TABLE IF NOT EXISTS app_state (
            key   TEXT PRIMARY KEY,
            value TEXT NOT NULL
        )
    """)


def get_state(key):
    row = run_query("SELECT value FROM app_state WHERE key = ?", (key,), fetch="one")
    return row["value"] if row else None


def set_state(key, value):
    run_query(
        """
        INSERT INTO app_state (key, value) VALUES (?, ?)
        ON CONFLICT (key) DO UPDATE SET value = excluded.value
        """,
        (key, value)
    )


def order_to_json(row):
    """Convert a DB row into the shape the templates expect."""

    created = datetime.fromisoformat(row["created_at"])

    return {
        "orderId": row["order_id"],
        "customerName": row["customer_name"],
        "phone": row["phone"],
        "table": row["table_name"],
        "items": json.loads(row["items"]),
        "total": row["total_paise"] / 100,
        "createdAt": created.strftime("%d-%m-%Y %I:%M %p"),
        "payment": "Razorpay",
        "paymentStatus": row["payment_status"],
        "transactionId": row["razorpay_payment_id"],
        "status": row["status"],
    }


def mark_order_paid(razorpay_order_id, razorpay_payment_id):
    """
    Mark a saved order as Paid. Used by /place-order and the webhook.

    Returns (row, error_message).
    Safe to call twice for the same payment.
    """

    # "AND payment_status = 'Pending'" makes sure an order
    # can only be confirmed once.

    updated = run_query(
        """
        UPDATE orders
        SET payment_status = 'Paid',
            status = 'Confirmed',
            razorpay_payment_id = ?
        WHERE razorpay_order_id = ?
          AND payment_status = 'Pending'
        """,
        (razorpay_payment_id, razorpay_order_id)
    )

    row = run_query(
        "SELECT * FROM orders WHERE razorpay_order_id = ?",
        (razorpay_order_id,),
        fetch="one"
    )

    if row is None:
        return None, "Order not found."

    # Already confirmed with this same payment
    # (browser + webhook both arrived) -> still OK.

    if not updated and row["razorpay_payment_id"] != razorpay_payment_id:
        return None, "This order has already been paid."

    if updated:

        order = order_to_json(row)

        print()
        print("==============================================")
        print("🔔 NEW PAID ORDER")
        print("==============================================")
        print("Order ID:", order["orderId"])
        print("Customer:", order["customerName"])
        print("Phone:", order["phone"])
        print("Payment ID:", razorpay_payment_id)
        print("Amount: ₹", order["total"])
        print("----------------------------------------------")
        print("Items:")

        for item in order["items"]:
            print(" -", item["name"], "| Qty:", item["quantity"], "| ₹", item["price"])

        print("==============================================")
        print()

    return row, None


init_db()


# ============================================================
# PAGES
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


@app.route("/menu")
def menu():
    return render_template("menu.html")


@app.route("/cart")
def cart():
    return render_template("cart.html")


@app.route("/checkout")
def checkout():
    return render_template("checkout.html")


@app.route("/success")
def success():
    return render_template("success.html")


# ============================================================
# CREATE RAZORPAY ORDER
#
# 1. Checks customer details
# 2. Prices the cart using MENU (ignores browser prices)
# 3. Creates the Razorpay order
# 4. Saves the order as "Pending" in the database
# ============================================================

@app.route("/create-order", methods=["POST"])
@app.route("/api/create-order", methods=["POST"])
def create_order():

    try:

        if razorpay_client is None:

            print("❌ Razorpay environment variables missing.")

            return jsonify({
                "success": False,
                "message": (
                    "Razorpay is not configured. "
                    "Please add RAZORPAY_KEY_ID and "
                    "RAZORPAY_KEY_SECRET in Render Environment Variables."
                )
            }), 500

        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "success": False,
                "message": "No payment data received."
            }), 400

        # ----------------------------------------------------
        # CUSTOMER DETAILS
        # ----------------------------------------------------

        customer_name = str(data.get("customerName", "")).strip()[:100]
        phone = str(data.get("phone", "")).strip()
        table = str(data.get("table") or "Pre-Booking").strip()[:50]

        if not customer_name:
            return jsonify({
                "success": False,
                "message": "Please enter your name."
            }), 400

        if not phone.isdigit() or len(phone) != 10:
            return jsonify({
                "success": False,
                "message": "Enter a valid 10-digit mobile number."
            }), 400

        # ----------------------------------------------------
        # PRICE THE CART ON THE SERVER
        # ----------------------------------------------------

        try:
            items, amount_in_paise = price_cart(data.get("items"))
        except ValueError as e:
            return jsonify({
                "success": False,
                "message": str(e)
            }), 400

        # ----------------------------------------------------
        # CREATE RAZORPAY ORDER
        # ----------------------------------------------------

        order_id = "BB" + uuid.uuid4().hex[:8].upper()

        razorpay_order = razorpay_client.order.create({
            "amount": amount_in_paise,
            "currency": "INR",
            "receipt": order_id,
            "notes": {
                "stall": "Back Benchers Food Stall",
                "orderId": order_id,
                # Which copy of the website took this order
                # (used by the automatic switch to the new website).
                "site": request.host
            }
        })

        # ----------------------------------------------------
        # SAVE AS PENDING
        # ----------------------------------------------------

        run_query(
            """
            INSERT INTO orders (
                razorpay_order_id, order_id, customer_name, phone,
                table_name, items, total_paise, payment_status,
                status, created_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, 'Pending', 'Awaiting Payment', ?)
            """,
            (
                razorpay_order["id"],
                order_id,
                customer_name,
                phone,
                table,
                json.dumps(items),
                amount_in_paise,
                datetime.now(IST).isoformat(),
            )
        )

        print()
        print("==============================================")
        print("💳 RAZORPAY ORDER CREATED")
        print("==============================================")
        print("Order ID:", order_id)
        print("Razorpay Order ID:", razorpay_order["id"])
        print("Amount: ₹", amount_in_paise / 100)
        print("==============================================")
        print()

        return jsonify({
            "success": True,
            "message": "Razorpay order created successfully.",
            "key": RAZORPAY_KEY_ID,
            "orderId": razorpay_order["id"],
            "amount": amount_in_paise,
            "total": amount_in_paise / 100,
            "currency": "INR",
            "receipt": order_id
        }), 200

    except Exception as e:

        print()
        print("==============================================")
        print("❌ RAZORPAY CREATE ORDER ERROR")
        print("==============================================")
        print(type(e).__name__)
        print(str(e))
        print("==============================================")
        print()

        # Always return JSON so the frontend doesn't show
        # "Unexpected token '<'".

        return jsonify({
            "success": False,
            "message": "Unable to create Razorpay order."
        }), 500


# ============================================================
# PLACE ORDER
#
# Called AFTER successful Razorpay payment.
# Verifies the signature and marks the saved order as Paid.
# Items and total come from the database, not the browser.
# ============================================================

@app.route("/place-order", methods=["POST"])
def place_order():

    try:

        if razorpay_client is None:
            return jsonify({
                "success": False,
                "message": "Razorpay is not configured."
            }), 500

        data = request.get_json(silent=True)

        if not data:
            return jsonify({
                "success": False,
                "message": "No order data received."
            }), 400

        razorpay_payment_id = str(data.get("razorpay_payment_id", "")).strip()
        razorpay_order_id = str(data.get("razorpay_order_id", "")).strip()
        razorpay_signature = str(data.get("razorpay_signature", "")).strip()

        if not razorpay_payment_id or not razorpay_order_id or not razorpay_signature:
            return jsonify({
                "success": False,
                "message": "Payment details are missing."
            }), 400

        # ----------------------------------------------------
        # VERIFY SIGNATURE
        # ----------------------------------------------------

        try:

            razorpay_client.utility.verify_payment_signature({
                "razorpay_order_id": razorpay_order_id,
                "razorpay_payment_id": razorpay_payment_id,
                "razorpay_signature": razorpay_signature
            })

        except razorpay.errors.SignatureVerificationError:

            print()
            print("❌ SIGNATURE VERIFICATION FAILED")
            print("Payment ID:", razorpay_payment_id)
            print("Order ID:", razorpay_order_id)
            print()

            return jsonify({
                "success": False,
                "message": "Payment verification failed."
            }), 400

        # ----------------------------------------------------
        # MAKE SURE THE MONEY IS CAPTURED
        #
        # If "auto capture" is off in the Razorpay account,
        # payments stay "authorized" and are refunded to the
        # customer after a few days. Capture them here.
        # ----------------------------------------------------

        payment = razorpay_client.payment.fetch(razorpay_payment_id)

        if payment.get("order_id") != razorpay_order_id:
            return jsonify({
                "success": False,
                "message": "Payment does not belong to this order."
            }), 400

        if payment.get("status") == "authorized":
            payment = razorpay_client.payment.capture(
                razorpay_payment_id,
                payment["amount"],
                {"currency": payment.get("currency", "INR")}
            )

        if payment.get("status") != "captured":
            return jsonify({
                "success": False,
                "message": "Payment is not complete yet. Please contact the stall."
            }), 400

        # ----------------------------------------------------
        # MARK AS PAID
        # ----------------------------------------------------

        row, error = mark_order_paid(razorpay_order_id, razorpay_payment_id)

        if error:
            return jsonify({
                "success": False,
                "message": error
            }), 400

        order = order_to_json(row)

        return jsonify({
            "success": True,
            "message": "Payment successful. Order confirmed.",
            "orderId": order["orderId"],
            "paymentStatus": "Paid",
            "status": order["status"],
            "order": order
        }), 200

    except Exception as e:

        print()
        print("==============================================")
        print("❌ PLACE ORDER ERROR")
        print("==============================================")
        print(type(e).__name__)
        print(str(e))
        print("==============================================")
        print()

        return jsonify({
            "success": False,
            "message": "Something went wrong while placing the order."
        }), 500


# ============================================================
# RAZORPAY WEBHOOK
#
# Razorpay calls this directly when an order is paid.
# It confirms the order even if the customer closed the
# browser before /place-order ran.
#
# Setup: Razorpay Dashboard -> Webhooks -> Add New Webhook
#   URL:    https://<your-site>/razorpay-webhook
#   Secret: same value as RAZORPAY_WEBHOOK_SECRET
#   Events: order.paid
# ============================================================

RAZORPAY_WEBHOOK_SECRET = os.getenv("RAZORPAY_WEBHOOK_SECRET")


@app.route("/razorpay-webhook", methods=["POST"])
def razorpay_webhook():

    if razorpay_client is None or not RAZORPAY_WEBHOOK_SECRET:
        return jsonify({
            "success": False,
            "message": "Webhook is not configured."
        }), 503

    body = request.get_data(as_text=True)
    signature = request.headers.get("X-Razorpay-Signature", "")

    try:
        razorpay_client.utility.verify_webhook_signature(
            body,
            signature,
            RAZORPAY_WEBHOOK_SECRET
        )
    except razorpay.errors.SignatureVerificationError:
        print("❌ WEBHOOK SIGNATURE FAILED")
        return jsonify({"success": False}), 400

    event = json.loads(body)

    # A blocked payment can mean Razorpay has moved approval
    # to the new website — see AUTOMATIC SWITCH below.

    if event.get("event") == "payment.failed":
        payment = event.get("payload", {}).get("payment", {}).get("entity", {})
        record_if_website_blocked(payment)
        return jsonify({"success": True})

    # Other events are acknowledged but ignored.

    if event.get("event") != "order.paid":
        return jsonify({"success": True})

    payload = event.get("payload", {})
    razorpay_order_id = payload.get("order", {}).get("entity", {}).get("id")
    razorpay_payment_id = payload.get("payment", {}).get("entity", {}).get("id")

    if not razorpay_order_id or not razorpay_payment_id:
        return jsonify({"success": False}), 400

    row, error = mark_order_paid(razorpay_order_id, razorpay_payment_id)

    if error:
        print("⚠️ Webhook:", error, razorpay_order_id)

    # Always 200 for valid webhooks so Razorpay doesn't keep retrying.

    return jsonify({"success": True})


# ============================================================
# AUTOMATIC SWITCH TO THE NEW WEBSITE
#
# Razorpay only accepts payments from approved websites.
# While a new website is "under review", the old one keeps
# working. When Razorpay approves the new one, payments on
# the old one start failing with "website mismatch".
#
# On the OLD site, set:
#   SWITCH_TO_URL = https://<new-site>.onrender.com
#
# The first time Razorpay blocks a payment on the old site,
# this is recorded in the shared database and from then on
# every visitor to the old site is sent to the new one.
# (Leave SWITCH_TO_URL empty on the new site.)
# ============================================================

SWITCH_TO_URL = (os.getenv("SWITCH_TO_URL") or "").rstrip("/")

# Paths that must keep working on the old site even after the
# switch (payments already in progress, Razorpay callbacks).
NEVER_REDIRECT = {"/place-order", "/razorpay-webhook", "/api/payment-failed", "/health"}

_switch_cache = {"value": False, "checked_at": 0.0}


def blocked_key(host):
    return "website_blocked:" + host


def record_if_website_blocked(payment):
    """
    If Razorpay blocked this payment because the website isn't
    approved, remember which website it came from.

    Everything is checked against Razorpay's own records, so a
    fake report can't trigger the switch.
    """

    if razorpay_client is None or not payment.get("id"):
        return None

    # Always re-fetch from Razorpay instead of trusting the caller.

    payment = razorpay_client.payment.fetch(payment["id"])

    description = (payment.get("error_description") or "").lower()

    if payment.get("status") != "failed" or "website" not in description:
        return None

    order_id = payment.get("order_id")

    if not order_id:
        return None

    site = (razorpay_client.order.fetch(order_id).get("notes") or {}).get("site")

    if not site:
        return None

    if get_state(blocked_key(site)) is None:
        set_state(blocked_key(site), datetime.now(IST).isoformat())
        print("🔀 Razorpay now blocks payments from", site)

    return site


def switched_to_new_site():
    """True when this (old) site should send visitors to SWITCH_TO_URL."""

    if not SWITCH_TO_URL:
        return False

    # Once switched, it stays switched. Otherwise re-check the
    # database at most every 30 seconds.

    now = time.time()

    if not _switch_cache["value"] and now - _switch_cache["checked_at"] > 30:
        _switch_cache["checked_at"] = now
        _switch_cache["value"] = get_state(blocked_key(request.host)) is not None

    return _switch_cache["value"]


@app.before_request
def redirect_old_site():

    if request.path in NEVER_REDIRECT:
        return None

    if switched_to_new_site():
        return redirect(SWITCH_TO_URL + request.full_path.rstrip("?"), code=302)

    return None


@app.route("/api/payment-failed", methods=["POST"])
def payment_failed():
    """
    Called by the checkout page when Razorpay reports a failed
    payment. If the old site has just lost approval, tell the
    browser where to continue.
    """

    data = request.get_json(silent=True) or {}

    payment_id = str(data.get("razorpay_payment_id") or "").strip()

    if not payment_id or not SWITCH_TO_URL:
        return jsonify({"success": True, "redirect": None})

    try:
        site = record_if_website_blocked({"id": payment_id})
    except Exception as e:
        print("❌ payment-failed check error:", str(e))
        return jsonify({"success": True, "redirect": None})

    if site == request.host:
        _switch_cache["value"] = True
        return jsonify({"success": True, "redirect": SWITCH_TO_URL})

    return jsonify({"success": True, "redirect": None})


# ============================================================
# ADMIN PAGE
# ============================================================

@app.route("/admin")
@admin_required
def admin():
    return render_template("admin.html")


# ============================================================
# GET ALL PAID ORDERS (newest first)
# ============================================================

@app.route("/api/orders")
@admin_required
def get_orders():

    rows = run_query(
        """
        SELECT * FROM orders
        WHERE payment_status = 'Paid'
        ORDER BY created_at DESC
        """,
        fetch="all"
    )

    return jsonify({
        "success": True,
        "orders": [order_to_json(row) for row in rows]
    })


# ============================================================
# UPDATE ORDER STATUS
# ============================================================

@app.route("/api/orders/<order_id>/status", methods=["POST"])
@admin_required
def update_order_status(order_id):

    data = request.get_json(silent=True) or {}

    new_status = str(data.get("status", "")).strip()

    allowed_statuses = [
        "Confirmed",
        "Preparing",
        "Ready",
        "Completed",
        "Cancelled"
    ]

    if new_status not in allowed_statuses:
        return jsonify({
            "success": False,
            "message": "Invalid order status."
        }), 400

    updated = run_query(
        "UPDATE orders SET status = ? WHERE order_id = ? AND payment_status = 'Paid'",
        (new_status, order_id)
    )

    if not updated:
        return jsonify({
            "success": False,
            "message": "Order not found."
        }), 404

    row = run_query(
        "SELECT * FROM orders WHERE order_id = ?",
        (order_id,),
        fetch="one"
    )

    return jsonify({
        "success": True,
        "message": "Order status updated.",
        "order": order_to_json(row)
    })


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return jsonify({
        "success": True,
        "message": "Back Benchers Food Stall server is running.",
        "payment": "Razorpay",
        "razorpay": razorpay_client is not None,
        "database": "postgres" if DATABASE_URL else "sqlite",
        "adminLocked": not ADMIN_PASSWORD,
        "switchToUrl": SWITCH_TO_URL or None,
        "switchedToNewSite": switched_to_new_site()
    })


# ============================================================
# ERROR HANDLERS
#
# If an API endpoint fails, return JSON instead of HTML.
# This prevents "Unexpected token '<'" in the frontend.
# ============================================================

def is_api_request():
    return request.path.startswith("/api/") or request.path in [
        "/create-order",
        "/place-order"
    ]


@app.errorhandler(404)
def page_not_found(error):

    if is_api_request():
        return jsonify({
            "success": False,
            "message": "API endpoint not found.",
            "path": request.path
        }), 404

    return error


@app.errorhandler(500)
def internal_server_error(error):

    if is_api_request():
        return jsonify({
            "success": False,
            "message": "Internal server error."
        }), 500

    return error


# ============================================================
# RUN APPLICATION (local only — Render uses gunicorn)
# ============================================================

if __name__ == "__main__":

    print()
    print("==============================================")
    print("🍔 BACK BENCHERS FOOD STALL")
    print("==============================================")
    print("🚀 Flask server starting...")
    print("🌐 http://localhost:5000")
    print()
    print("💳 Razorpay:", "✅ configured" if razorpay_client else "❌ NOT configured")
    print("🗄️ Database:", "Postgres (DATABASE_URL)" if DATABASE_URL else "SQLite (database.db)")
    print("🔐 Admin:", "✅ password set" if ADMIN_PASSWORD else "❌ locked — set ADMIN_PASSWORD")
    print("🔔 Admin page: http://localhost:5000/admin")
    print("==============================================")
    print()

    # Debug mode lets anyone on the network run code through the
    # error page, so it's only on when FLASK_DEBUG=1 is set.

    app.run(
        debug=os.getenv("FLASK_DEBUG") == "1",
        host="0.0.0.0",
        port=5000
    )
