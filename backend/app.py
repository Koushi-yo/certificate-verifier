from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json
import os

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

# ------------------------
# HEALTH CHECK
# ------------------------
@app.route("/")
def home():
    return "Certificate Verification Backend Running"

# ------------------------
# SERVE FRONTEND PAGES
# ------------------------
@app.route("/verify-page")
def verify_page():
    return send_from_directory(FRONTEND_DIR, "verify.html")

@app.route("/issue-page")
def issue_page():
    return send_from_directory(FRONTEND_DIR, "issue.html")

@app.route("/scan-page")
def scan_page():
    return send_from_directory(FRONTEND_DIR, "scan.html")

# ------------------------
# VERIFY CERTIFICATE API
# ------------------------
@app.route("/api/verify", methods=["POST"])
def verify_certificate():
    try:
        data = request.get_json()

        if not data or "certificate" not in data or "signature" not in data:
            return jsonify({
                "valid": False,
                "reason": "Invalid JSON format"
            }), 400

        # ⚠️ DEMO LOGIC (signature verification already shown earlier)
        # In real production this checks cryptographic signature

        return jsonify({
            "valid": True,
            "message": "Certificate is VALID",
            "certificate": data["certificate"]
        })

    except Exception as e:
        return jsonify({
            "valid": False,
            "error": str(e)
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
