from flask import Flask, render_template, request, jsonify
from datetime import datetime
import uuid


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)


# ============================================================
# TEMPORARY ORDER STORAGE
#
# IMPORTANT:
# Orders will disappear when Flask restarts.
# For your current college/demo project this is okay.
# ============================================================

orders = []


# ============================================================
# YOUR UPI DETAILS
#
# Change these if required.
# ============================================================

UPI_ID = "8374857347@axl"
UPI_NAME = "Back Benchers Food Stall"


# ============================================================
# HOME
# ============================================================

@app.route("/")
def home():
    return render_template("index.html")


# ============================================================
# MENU
# ============================================================

@app.route("/menu")
def menu():
    return render_template("menu.html")


# ============================================================
# CART
# ============================================================

@app.route("/cart")
def cart():
    return render_template("cart.html")


# ============================================================
# CHECKOUT
# ============================================================

@app.route("/checkout")
def checkout():
    return render_template("checkout.html")


# ============================================================
# SUCCESS
# ============================================================

@app.route("/success")
def success():
    return render_template("success.html")


# ============================================================
# PLACE ORDER
#
# FLOW:
#
# Customer selects food
#       ↓
# Checkout
#       ↓
# Customer sees UPI ID / QR
#       ↓
# Customer pays using UPI
#       ↓
# Customer enters UTR
#       ↓
# Order is stored as:
# "Verification Pending"
#       ↓
# Admin checks actual UPI payment
#       ↓
# Admin verifies payment
#       ↓
# Order becomes "Confirmed"
#
# Razorpay is NOT used.
# ============================================================

@app.route("/place-order", methods=["POST"])
def place_order():

    try:

        # ====================================================
        # GET JSON DATA
        # ====================================================

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "message": "No order data received."
            }), 400


        # ====================================================
        # CUSTOMER NAME
        # ====================================================

        customer_name = str(
            data.get("customerName", "")
        ).strip()

        if not customer_name:

            return jsonify({
                "success": False,
                "message": "Please enter your name."
            }), 400


        # ====================================================
        # PHONE
        # ====================================================

        phone = str(
            data.get("phone", "")
        ).strip()

        if not phone.isdigit() or len(phone) != 10:

            return jsonify({
                "success": False,
                "message":
                    "Enter a valid 10-digit mobile number."
            }), 400


        # ====================================================
        # TABLE
        # ====================================================

        table = str(
            data.get("table", "Pre-Booking")
        ).strip()

        if not table:

            table = "Pre-Booking"


        # ====================================================
        # UTR
        # ====================================================

        utr = str(
            data.get("utr", "")
        ).strip()

        if not utr:

            return jsonify({
                "success": False,
                "message": "Please enter the UTR number."
            }), 400


        if len(utr) < 6:

            return jsonify({
                "success": False,
                "message":
                    "Please enter a valid UTR number."
            }), 400


        # ====================================================
        # CHECK DUPLICATE UTR
        #
        # Prevent same UTR from being submitted for
        # multiple orders.
        # ====================================================

        for existing_order in orders:

            if existing_order.get("utr") == utr:

                return jsonify({
                    "success": False,
                    "message":
                        "This UTR has already been used."
                }), 400


        # ====================================================
        # ITEMS
        # ====================================================

        items = data.get("items", [])

        if not isinstance(items, list) or not items:

            return jsonify({
                "success": False,
                "message": "Cart is empty."
            }), 400


        # ====================================================
        # TOTAL
        # ====================================================

        try:

            total = float(
                data.get("total", 0)
            )

        except (TypeError, ValueError):

            return jsonify({
                "success": False,
                "message": "Invalid order amount."
            }), 400


        if total <= 0:

            return jsonify({
                "success": False,
                "message": "Invalid order amount."
            }), 400


        # ====================================================
        # ROUND TOTAL
        # ====================================================

        total = round(total, 2)


        # ====================================================
        # GENERATE ORDER ID
        # ====================================================

        order_id = (
            "BB"
            + uuid.uuid4().hex[:6].upper()
        )


        # ====================================================
        # CREATE ORDER
        # ====================================================

        order = {

            "orderId":
                order_id,

            "customerName":
                customer_name,

            "phone":
                phone,

            "table":
                table,

            # PAYMENT INFORMATION
            "payment":
                "Direct UPI",

            "paymentStatus":
                "Verification Pending",

            "upiId":
                UPI_ID,

            "upiName":
                UPI_NAME,

            "utr":
                utr,

            # ORDER INFORMATION
            "items":
                items,

            "total":
                total,

            "createdAt":
                datetime.now().strftime(
                    "%d-%m-%Y %I:%M %p"
                ),

            # ORDER STATUS
            "status":
                "Payment Verification Pending"

        }


        # ====================================================
        # SAVE ORDER
        # ====================================================

        orders.append(order)


        # ====================================================
        # TERMINAL LOG
        # ====================================================

        print()
        print("==============================================")
        print("🔔 NEW ORDER RECEIVED")
        print("==============================================")

        print(
            "Order ID:",
            order["orderId"]
        )

        print(
            "Customer:",
            order["customerName"]
        )

        print(
            "Phone:",
            order["phone"]
        )

        print(
            "Table:",
            order["table"]
        )

        print(
            "Payment:",
            "DIRECT UPI"
        )

        print(
            "UPI ID:",
            order["upiId"]
        )

        print(
            "UTR:",
            order["utr"]
        )

        print(
            "Payment Status:",
            order["paymentStatus"]
        )

        print(
            "Total: ₹",
            order["total"]
        )

        print("----------------------------------------------")

        print("Items:")

        for item in items:

            print(
                " -",
                item.get("name"),
                "| Qty:",
                item.get("quantity"),
                "| ₹",
                item.get("price")
            )

        print("----------------------------------------------")

        print(
            "⚠️ ADMIN MUST VERIFY PAYMENT"
        )

        print("==============================================")
        print()


        # ====================================================
        # RESPONSE
        # ====================================================

        return jsonify({

            "success":
                True,

            "message":
                "Order received. Payment verification is pending.",

            "orderId":
                order_id,

            "paymentStatus":
                "Verification Pending",

            "order":
                order

        }), 200


    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as e:

        print()
        print("❌ ORDER ERROR:")
        print(e)
        print()

        return jsonify({

            "success":
                False,

            "message":
                "Something went wrong while placing the order."

        }), 500


# ============================================================
# ADMIN PAGE
# ============================================================

@app.route("/admin")
def admin():

    return render_template("admin.html")


# ============================================================
# GET ALL ORDERS
# ============================================================

@app.route("/api/orders")
def get_orders():

    return jsonify({

        "success":
            True,

        "orders":
            orders

    })


# ============================================================
# VERIFY PAYMENT
#
# Admin checks the actual UPI transaction first.
#
# Then admin clicks:
# VERIFY PAYMENT
#
# Order becomes:
#
# paymentStatus = Paid
# status = Confirmed
# ============================================================

@app.route(
    "/api/orders/<order_id>/verify-payment",
    methods=["POST"]
)
def verify_payment(order_id):

    for order in orders:

        if order["orderId"] == order_id:

            # ----------------------------------------------
            # CHECK IF ALREADY VERIFIED
            # ----------------------------------------------

            if order["paymentStatus"] == "Paid":

                return jsonify({

                    "success":
                        False,

                    "message":
                        "Payment is already verified.",

                    "order":
                        order

                }), 400


            # ----------------------------------------------
            # UPDATE PAYMENT
            # ----------------------------------------------

            order["paymentStatus"] = "Paid"

            order["status"] = "Confirmed"

            order["verifiedAt"] = (
                datetime.now().strftime(
                    "%d-%m-%Y %I:%M %p"
                )
            )


            # ----------------------------------------------
            # TERMINAL
            # ----------------------------------------------

            print()
            print("==============================================")
            print("✅ PAYMENT VERIFIED")
            print("==============================================")

            print(
                "Order ID:",
                order["orderId"]
            )

            print(
                "UTR:",
                order["utr"]
            )

            print(
                "Amount: ₹",
                order["total"]
            )

            print(
                "Status:",
                "CONFIRMED"
            )

            print("==============================================")
            print()


            return jsonify({

                "success":
                    True,

                "message":
                    "Payment verified successfully.",

                "order":
                    order

            })


    # ========================================================
    # ORDER NOT FOUND
    # ========================================================

    return jsonify({

        "success":
            False,

        "message":
            "Order not found."

    }), 404


# ============================================================
# REJECT PAYMENT
#
# If UTR/payment is not found in your UPI account,
# admin can reject the payment.
# ============================================================

@app.route(
    "/api/orders/<order_id>/reject-payment",
    methods=["POST"]
)
def reject_payment(order_id):

    for order in orders:

        if order["orderId"] == order_id:

            order["paymentStatus"] = "Payment Rejected"

            order["status"] = "Payment Rejected"

            order["rejectedAt"] = (
                datetime.now().strftime(
                    "%d-%m-%Y %I:%M %p"
                )
            )


            print()
            print("==============================================")
            print("❌ PAYMENT REJECTED")
            print("==============================================")

            print(
                "Order ID:",
                order["orderId"]
            )

            print(
                "UTR:",
                order["utr"]
            )

            print(
                "Status:",
                "PAYMENT REJECTED"
            )

            print("==============================================")
            print()


            return jsonify({

                "success":
                    True,

                "message":
                    "Payment rejected.",

                "order":
                    order

            })


    return jsonify({

        "success":
            False,

        "message":
            "Order not found."

    }), 404


# ============================================================
# UPDATE ORDER STATUS
#
# Optional:
# Admin can change food order status.
#
# Example statuses:
#
# Confirmed
# Preparing
# Ready
# Completed
# Cancelled
# ============================================================

@app.route(
    "/api/orders/<order_id>/status",
    methods=["POST"]
)
def update_order_status(order_id):

    try:

        data = request.get_json()

        if not data:

            return jsonify({
                "success": False,
                "message": "No status received."
            }), 400


        new_status = str(
            data.get("status", "")
        ).strip()


        allowed_statuses = [

            "New",

            "Confirmed",

            "Preparing",

            "Ready",

            "Completed",

            "Cancelled",

            "Payment Verification Pending",

            "Payment Rejected"

        ]


        if new_status not in allowed_statuses:

            return jsonify({

                "success":
                    False,

                "message":
                    "Invalid order status."

            }), 400


        for order in orders:

            if order["orderId"] == order_id:

                order["status"] = new_status


                return jsonify({

                    "success":
                        True,

                    "message":
                        "Order status updated.",

                    "order":
                        order

                })


        return jsonify({

            "success":
                False,

            "message":
                "Order not found."

        }), 404


    except Exception as e:

        print(
            "❌ Status Update Error:",
            e
        )

        return jsonify({

            "success":
                False,

            "message":
                "Unable to update order status."

        }), 500


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route("/health")
def health():

    return jsonify({

        "success":
            True,

        "message":
            "Back Benchers Food Stall server is running.",

        "payment":
            "Direct UPI",

        "upiId":
            UPI_ID,

        "upiName":
            UPI_NAME,

        "razorpay":
            False,

        "totalOrders":
            len(orders)

    })


# ============================================================
# RUN APPLICATION
# ============================================================

if __name__ == "__main__":

    print()
    print("==============================================")
    print("🍔 BACK BENCHERS FOOD STALL")
    print("==============================================")

    print(
        "🚀 Flask server starting..."
    )

    print(
        "🌐 http://localhost:5000"
    )

    print()

    print(
        "💳 Payment Method: DIRECT UPI"
    )

    print(
        "📱 UPI ID:",
        UPI_ID
    )

    print(
        "👤 UPI Name:",
        UPI_NAME
    )

    print(
        "🚫 Razorpay: DISABLED"
    )

    print()

    print(
        "🔔 Admin:",
        "http://localhost:5000/admin"
    )

    print("==============================================")
    print()


    app.run(

        debug=True,

        host="0.0.0.0",

        port=5000

    )