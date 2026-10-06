from flask import Flask, render_template, request, jsonify
from datetime import datetime
import uuid
import os
import razorpay


# ============================================================
# FLASK APP
# ============================================================

app = Flask(__name__)


# ============================================================
# RAZORPAY CONFIGURATION
#
# IMPORTANT:
# Do NOT put the actual Key ID / Secret directly in this file.
#
# Render Environment Variables:
#
# RAZORPAY_KEY_ID
# RAZORPAY_KEY_SECRET
#
# ============================================================

RAZORPAY_KEY_ID = os.getenv("RAZORPAY_KEY_ID")
RAZORPAY_KEY_SECRET = os.getenv("RAZORPAY_KEY_SECRET")


# ============================================================
# RAZORPAY CLIENT
# ============================================================

razorpay_client = None

if RAZORPAY_KEY_ID and RAZORPAY_KEY_SECRET:

    razorpay_client = razorpay.Client(
        auth=(
            RAZORPAY_KEY_ID,
            RAZORPAY_KEY_SECRET
        )
    )


# ============================================================
# TEMPORARY ORDER STORAGE
#
# IMPORTANT:
# Orders will disappear when Flask restarts.
#
# For your current college/demo project this is okay.
# ============================================================

orders = []


# ============================================================
# YOUR UPI DETAILS
#
# These are kept only as business information.
# Razorpay will handle the actual payment.
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
# CREATE RAZORPAY ORDER
#
# FLOW:
#
# Customer
#    ↓
# Checkout
#    ↓
# Click "PROCEED TO PAY"
#    ↓
# Frontend calls /create-order
#    ↓
# Flask creates Razorpay Order
#    ↓
# Razorpay Checkout opens
#
# ============================================================

@app.route("/create-order", methods=["POST"])
def create_order():

    try:

        # ----------------------------------------------------
        # CHECK RAZORPAY CONFIGURATION
        # ----------------------------------------------------

        if razorpay_client is None:

            return jsonify({

                "success": False,

                "message":
                    "Razorpay is not configured on the server."

            }), 500


        # ----------------------------------------------------
        # GET REQUEST DATA
        # ----------------------------------------------------

        data = request.get_json()

        if not data:

            return jsonify({

                "success": False,

                "message":
                    "No payment data received."

            }), 400


        # ----------------------------------------------------
        # GET AMOUNT
        # ----------------------------------------------------

        try:

            total = float(
                data.get("total", 0)
            )

        except (TypeError, ValueError):

            return jsonify({

                "success": False,

                "message":
                    "Invalid order amount."

            }), 400


        # ----------------------------------------------------
        # VALIDATE AMOUNT
        # ----------------------------------------------------

        if total <= 0:

            return jsonify({

                "success": False,

                "message":
                    "Order amount must be greater than ₹0."

            }), 400


        # ----------------------------------------------------
        # ROUND TOTAL
        # ----------------------------------------------------

        total = round(total, 2)


        # ----------------------------------------------------
        # CONVERT RUPEES TO PAISE
        #
        # Razorpay accepts amount in paise.
        #
        # Example:
        #
        # ₹100
        # ↓
        # 10000 paise
        #
        # ----------------------------------------------------

        amount_in_paise = int(
            round(total * 100)
        )


        # ----------------------------------------------------
        # GENERATE RECEIPT
        # ----------------------------------------------------

        receipt_id = (
            "BB_"
            + uuid.uuid4().hex[:10].upper()
        )


        # ----------------------------------------------------
        # CREATE RAZORPAY ORDER
        # ----------------------------------------------------

        razorpay_order = razorpay_client.order.create({

            "amount":
                amount_in_paise,

            "currency":
                "INR",

            "receipt":
                receipt_id,

            "notes": {

                "stall":
                    "Back Benchers Food Stall"

            }

        })


        # ----------------------------------------------------
        # LOG
        # ----------------------------------------------------

        print()
        print("==============================================")
        print("💳 RAZORPAY ORDER CREATED")
        print("==============================================")

        print(
            "Razorpay Order ID:",
            razorpay_order["id"]
        )

        print(
            "Amount: ₹",
            total
        )

        print(
            "Receipt:",
            receipt_id
        )

        print("==============================================")
        print()


        # ----------------------------------------------------
        # RESPONSE TO FRONTEND
        # ----------------------------------------------------

        return jsonify({

            "success":
                True,

            "message":
                "Razorpay order created successfully.",

            "key":
                RAZORPAY_KEY_ID,

            "orderId":
                razorpay_order["id"],

            "amount":
                amount_in_paise,

            "currency":
                "INR",

            "receipt":
                receipt_id

        }), 200


    except Exception as e:

        print()
        print("❌ RAZORPAY CREATE ORDER ERROR")
        print(e)
        print()

        return jsonify({

            "success":
                False,

            "message":
                "Unable to create Razorpay order."

        }), 500


# ============================================================
# PLACE ORDER / VERIFY RAZORPAY PAYMENT
#
# This endpoint is called AFTER successful Razorpay payment.
#
# Razorpay sends:
#
# razorpay_payment_id
# razorpay_order_id
# razorpay_signature
#
# Server verifies the signature before accepting the order.
#
# ============================================================

@app.route("/place-order", methods=["POST"])
def place_order():

    try:

        # ----------------------------------------------------
        # CHECK RAZORPAY
        # ----------------------------------------------------

        if razorpay_client is None:

            return jsonify({

                "success": False,

                "message":
                    "Razorpay is not configured."

            }), 500


        # ----------------------------------------------------
        # GET JSON DATA
        # ----------------------------------------------------

        data = request.get_json()

        if not data:

            return jsonify({

                "success": False,

                "message":
                    "No order data received."

            }), 400


        # ----------------------------------------------------
        # CUSTOMER NAME
        # ----------------------------------------------------

        customer_name = str(
            data.get("customerName", "")
        ).strip()

        if not customer_name:

            return jsonify({

                "success": False,

                "message":
                    "Please enter your name."

            }), 400


        # ----------------------------------------------------
        # PHONE
        # ----------------------------------------------------

        phone = str(
            data.get("phone", "")
        ).strip()

        if not phone.isdigit() or len(phone) != 10:

            return jsonify({

                "success": False,

                "message":
                    "Enter a valid 10-digit mobile number."

            }), 400


        # ----------------------------------------------------
        # TABLE
        # ----------------------------------------------------

        table = str(
            data.get("table", "Pre-Booking")
        ).strip()

        if not table:

            table = "Pre-Booking"


        # ----------------------------------------------------
        # CART ITEMS
        # ----------------------------------------------------

        items = data.get("items", [])

        if not isinstance(items, list) or not items:

            return jsonify({

                "success": False,

                "message":
                    "Cart is empty."

            }), 400


        # ----------------------------------------------------
        # TOTAL
        # ----------------------------------------------------

        try:

            total = float(
                data.get("total", 0)
            )

        except (TypeError, ValueError):

            return jsonify({

                "success": False,

                "message":
                    "Invalid order amount."

            }), 400


        if total <= 0:

            return jsonify({

                "success": False,

                "message":
                    "Invalid order amount."

            }), 400


        total = round(total, 2)


        # ----------------------------------------------------
        # RAZORPAY PAYMENT DETAILS
        # ----------------------------------------------------

        razorpay_payment_id = str(
            data.get(
                "razorpay_payment_id",
                ""
            )
        ).strip()

        razorpay_order_id = str(
            data.get(
                "razorpay_order_id",
                ""
            )
        ).strip()

        razorpay_signature = str(
            data.get(
                "razorpay_signature",
                ""
            )
        ).strip()


        # ----------------------------------------------------
        # CHECK PAYMENT DETAILS
        # ----------------------------------------------------

        if not razorpay_payment_id:

            return jsonify({

                "success": False,

                "message":
                    "Razorpay payment ID is missing."

            }), 400


        if not razorpay_order_id:

            return jsonify({

                "success": False,

                "message":
                    "Razorpay order ID is missing."

            }), 400


        if not razorpay_signature:

            return jsonify({

                "success": False,

                "message":
                    "Razorpay payment signature is missing."

            }), 400


        # ----------------------------------------------------
        # VERIFY RAZORPAY SIGNATURE
        #
        # IMPORTANT SECURITY STEP
        # ----------------------------------------------------

        try:

            razorpay_client.utility.verify_payment_signature({

                "razorpay_order_id":
                    razorpay_order_id,

                "razorpay_payment_id":
                    razorpay_payment_id,

                "razorpay_signature":
                    razorpay_signature

            })


        except razorpay.errors.SignatureVerificationError:

            print()
            print("❌ RAZORPAY SIGNATURE VERIFICATION FAILED")
            print(
                "Payment ID:",
                razorpay_payment_id
            )
            print(
                "Order ID:",
                razorpay_order_id
            )
            print()

            return jsonify({

                "success": False,

                "message":
                    "Payment verification failed."

            }), 400


        # ----------------------------------------------------
        # CHECK DUPLICATE PAYMENT
        # ----------------------------------------------------

        for existing_order in orders:

            if existing_order.get(
                "razorpayPaymentId"
            ) == razorpay_payment_id:

                return jsonify({

                    "success":
                        False,

                    "message":
                        "This payment has already been used."

                }), 400


        # ----------------------------------------------------
        # GENERATE OUR ORDER ID
        # ----------------------------------------------------

        order_id = (

            "BB"
            + uuid.uuid4().hex[:6].upper()

        )


        # ----------------------------------------------------
        # CREATE ORDER
        # ----------------------------------------------------

        order = {

            # ------------------------------------------------
            # ORDER INFORMATION
            # ------------------------------------------------

            "orderId":
                order_id,

            "customerName":
                customer_name,

            "phone":
                phone,

            "table":
                table,

            "items":
                items,

            "total":
                total,

            "createdAt":
                datetime.now().strftime(
                    "%d-%m-%Y %I:%M %p"
                ),


            # ------------------------------------------------
            # PAYMENT INFORMATION
            # ------------------------------------------------

            "payment":
                "Razorpay",

            "paymentStatus":
                "Paid",

            "razorpayPaymentId":
                razorpay_payment_id,

            "razorpayOrderId":
                razorpay_order_id,

            "razorpaySignature":
                razorpay_signature,


            # ------------------------------------------------
            # ORDER STATUS
            # ------------------------------------------------

            "status":
                "Confirmed"

        }


        # ----------------------------------------------------
        # SAVE ORDER
        # ----------------------------------------------------

        orders.append(order)


        # ----------------------------------------------------
        # TERMINAL LOG
        # ----------------------------------------------------

        print()
        print("==============================================")
        print("🔔 NEW PAID ORDER RECEIVED")
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
            "RAZORPAY"
        )

        print(
            "Razorpay Payment ID:",
            order["razorpayPaymentId"]
        )

        print(
            "Razorpay Order ID:",
            order["razorpayOrderId"]
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
            "✅ PAYMENT VERIFIED"
        )

        print(
            "✅ ORDER CONFIRMED"
        )

        print("==============================================")
        print()


        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return jsonify({

            "success":
                True,

            "message":
                "Payment successful. Order confirmed.",

            "orderId":
                order_id,

            "paymentStatus":
                "Paid",

            "status":
                "Confirmed",

            "order":
                order

        }), 200


    except Exception as e:

        print()
        print("❌ ORDER ERROR")
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
# UPDATE ORDER STATUS
#
# Admin can change:
#
# Confirmed
# Preparing
# Ready
# Completed
# Cancelled
#
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

                "message":
                    "No status received."

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

            "Cancelled"

        ]


        if new_status not in allowed_statuses:

            return jsonify({

                "success":
                    False,

                "message":
                    "Invalid order status."

            }), 400


        # ----------------------------------------------------
        # FIND ORDER
        # ----------------------------------------------------

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


        # ----------------------------------------------------
        # ORDER NOT FOUND
        # ----------------------------------------------------

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
            "Razorpay",

        "upiId":
            UPI_ID,

        "upiName":
            UPI_NAME,

        "razorpay":
            razorpay_client is not None,

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
        "💳 Payment Method: RAZORPAY"
    )

    print(
        "📱 UPI ID:",
        UPI_ID
    )

    print(
        "👤 UPI Name:",
        UPI_NAME
    )

    if razorpay_client:

        print(
            "✅ Razorpay: ENABLED"
        )

    else:

        print(
            "❌ Razorpay: NOT CONFIGURED"
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