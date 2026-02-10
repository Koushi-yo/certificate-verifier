from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3
import uuid
import hashlib
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
FRONTEND_DIR = os.path.join(BASE_DIR, "frontend")
DB_PATH = os.path.join(os.path.dirname(__file__), "certificates.db")

app = Flask(__name__)
CORS(app)

# -----------------------------
# DATABASE INIT
# -----------------------------
def init_db():
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS certificates (
                certificate_id TEXT PRIMARY KEY,
                signature TEXT NOT NULL
            )
        """)
        conn.commit()

init_db()

# -----------------------------
# HOME
# -----------------------------
@app.route("/")
def home():
    return "<h2>Certificate Verification Service is LIVE</h2>"

# -----------------------------
# FRONTEND ROUTES
# -----------------------------
@app.route("/issue")
def issue_page():
    return send_from_directory(FRONTEND_DIR, "issue.html")

@app.route("/scan")
def scan_page():
    return send_from_directory(FRONTEND_DIR, "scan.html")

@app.route("/verify-page")
def verify_page():
    return send_from_directory(FRONTEND_DIR, "verify.html")

# -----------------------------
# API: ISSUE CERTIFICATE
# -----------------------------
@app.route("/api/issue", methods=["POST"])
def issue_certificate():
    data = request.json

    payload = (
        data.get("name", "") +
        data.get("university", "") +
        data.get("degree", "") +
        data.get("branch", "") +
        data.get("year", "") +
        data.get("cgpa", "")
    )

    certificate_id = str(uuid.uuid4())
    signature = hashlib.sha256(payload.encode()).hexdigest()

    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "INSERT INTO certificates (certificate_id, signature) VALUES (?, ?)",
            (certificate_id, signature)
        )
        conn.commit()

    verify_url = f"{request.host_url}verify/{certificate_id}"

    return jsonify({
        "certificate_id": certificate_id,
        "verify_url": verify_url
    })

# -----------------------------
# VERIFY CERTIFICATE
# -----------------------------
@app.route("/verify/<certificate_id>")
def verify_certificate(certificate_id):
    with sqlite3.connect(DB_PATH) as conn:
        cur = conn.cursor()
        cur.execute(
            "SELECT certificate_id FROM certificates WHERE certificate_id = ?",
            (certificate_id,)
        )
        row = cur.fetchone()

    if row:
        return send_from_directory(FRONTEND_DIR, "valid.html")
    else:
        return send_from_directory(FRONTEND_DIR, "invalid.html")

# -----------------------------
# START
# -----------------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
