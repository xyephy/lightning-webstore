#!/usr/bin/env python3
"""
Lightning Webstore - Bootcamp Day 4
A Flask web application that accepts Lightning payments via LND.
"""

import json
import os
import io
import base64

import qrcode
from flask import Flask, render_template, jsonify, request

from polar_detect import auto_detect, find_polar_node
from lnd_client import LNDClient

# ===========================================
# CONFIGURATION
# ===========================================
app = Flask(__name__)

# Load product catalog
PRODUCTS_FILE = os.path.join(os.path.dirname(__file__), "products.json")
with open(PRODUCTS_FILE) as f:
    PRODUCTS = json.load(f)

# Auto-detect LND from Polar, or use manual defaults
LND_DIR, REST_HOST = auto_detect("bob")
if not LND_DIR:
    LND_DIR = os.path.expanduser("~/bootcamp-code/day3/bob")
if not REST_HOST:
    REST_HOST = "https://localhost:8082"

lnd = LNDClient(lnd_dir=LND_DIR, rest_host=REST_HOST)


# ===========================================
# HELPER FUNCTIONS
# ===========================================
def get_product(product_id):
    """Find a product by its ID."""
    for product in PRODUCTS:
        if product["id"] == product_id:
            return product
    return None


def generate_qr_base64(data):
    """Generate a QR code and return as base64-encoded PNG."""
    qr = qrcode.QRCode(version=1, box_size=8, border=2)
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


# ===========================================
# ROUTES
# ===========================================
@app.route("/")
def index():
    """Display the product catalog."""
    return render_template("index.html", products=PRODUCTS)


@app.route("/checkout/<product_id>")
def checkout(product_id):
    """Create a Lightning invoice and show QR code for payment."""
    product = get_product(product_id)
    if not product:
        return "Product not found", 404

    try:
        # Create a Lightning invoice via LND
        memo = f"Webstore: {product['name']}"
        result = lnd.add_invoice(amount=product["price"], memo=memo)

        payment_request = result["payment_request"]
        r_hash = base64.b64decode(result["r_hash"]).hex()

        # Generate QR code
        qr_base64 = generate_qr_base64(payment_request.upper())

        return render_template(
            "checkout.html",
            product=product,
            payment_request=payment_request,
            r_hash=r_hash,
            qr_base64=qr_base64,
        )
    except Exception as e:
        return render_template(
            "error.html",
            error=str(e),
            product=product,
        )


@app.route("/api/check_payment/<r_hash>")
def check_payment(r_hash):
    """API endpoint to check if an invoice has been paid."""
    try:
        invoice = lnd.lookup_invoice(r_hash)
        settled = invoice.get("settled", False)
        return jsonify({"settled": settled})
    except Exception as e:
        return jsonify({"settled": False, "error": str(e)})


@app.route("/success/<product_id>")
def success(product_id):
    """Display payment success page."""
    product = get_product(product_id)
    if not product:
        return "Product not found", 404
    return render_template("success.html", product=product)


@app.route("/api/node_info")
def node_info():
    """API endpoint to get LND node information."""
    try:
        info = lnd.get_info()
        balance = lnd.channel_balance()
        return jsonify({
            "alias": info.get("alias", "unknown"),
            "pubkey": info.get("identity_pubkey", "unknown"),
            "channels": info.get("num_active_channels", 0),
            "synced": info.get("synced_to_chain", False),
            "balance": balance.get("local_balance", balance.get("balance", "0")),
        })
    except Exception as e:
        return jsonify({"error": str(e)})


# ===========================================
# MAIN
# ===========================================
if __name__ == "__main__":
    print("=" * 50)
    print("    LIGHTNING WEBSTORE - Bootcamp Day 4")
    print("=" * 50)
    print()

    # Show Polar detection info
    polar = find_polar_node("bob")
    if polar:
        print(f"Polar: Connected to node '{polar['name']}' in network "
              f"'{polar['network_name']}' (REST port {polar['rest_port']})")
        print(f"  LND dir:   {polar['lnd_dir']}")
        print(f"  REST host: {polar['rest_host']}")
    else:
        print("Polar not detected -- using manual configuration.")
        print(f"  LND dir:   {LND_DIR}")
        print(f"  REST host: {REST_HOST}")
        print()
        print("To fix: set LND_DIR and REST_HOST environment variables,")
        print("or make sure Polar is running with an LND node named 'bob'.")
    print()

    try:
        info = lnd.get_info()
        print(f"Connected to LND node: {info.get('alias', 'unknown')}")
        print(f"Channels: {info.get('num_active_channels', 0)}")
        print()
    except Exception as e:
        print(f"Warning: Could not connect to LND: {e}")
        print("Make sure your LND node is running!")
        print()

    print("Starting webstore at http://127.0.0.1:5000")
    print("Press Ctrl+C to stop")
    print()
    app.run(debug=True, host="127.0.0.1", port=5000)
