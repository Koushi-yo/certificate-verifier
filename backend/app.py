from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import sqlite3
import uuid
import hashlib
import json
import os

app = Flask(__name__, template_folder="../frontend")
CORS(app)

DB_FILE = "certificates.db"
BASE_URL = "https://certificate-verifier-vasy.onrender.com"


# ---------- DATABASE ----------
def get_db():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            certificate_id TEXT PRIMARY KEY,
            payload TEXT,
            signature TEXT
        )
    """)
    conn.commit()
    conn.close()


init_db()


# ---------- UTIL ----------
def sign_payload(payload: dict) -> str:
    payload_str = json.dumps(payload, sort_keys=True)
    return hashlib.sha256(payload_str.encode()).hexdigest()


# ---------- ROUTES ----------

@app.route("/")
def home():
    return "Certificate Verification Backend is Live"


# ISSUE CERTIFICATE
@app.route("/api/issue", methods=["POST"])
def issue_certificate():
    data = request.json

    certificate_id = str(uuid.uuid4())
    payload = {
        "certificate_id": certificate_id,
        "name": data["name"],
        "university": data["university"],
        "degree": data["degree"],
        "branch": data["branch"],
        "year": data["year"],
        "cgpa": data["cgpa"]
    }

    signature = sign_payload(payload)

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO certificates VALUES (?, ?, ?)",
        (certificate_id, json.dumps(payload), signature)
    )
    conn.commit()
    conn.close()

    return jsonify({
        "certificate_id": certificate_id,
        "verify_url": f"{BASE_URL}/verify/{certificate_id}"
    })


# VERIFY API (JSON)
@app.route("/api/verify/<certificate_id>")
def verify_api(certificate_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT payload, signature FROM certificates WHERE certificate_id=?",
        (certificate_id,)
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return jsonify({"valid": False})

    payload = json.loads(row["payload"])
    expected_signature = sign_payload(payload)

    return jsonify({
        "valid": expected_signature == row["signature"],
        "data": payload
    })


# VERIFY PAGE (UI)
@app.route("/verify/<certificate_id>")
def verify_page(certificate_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT payload, signature FROM certificates WHERE certificate_id=?",
        (certificate_id,)
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return render_template("verify.html", valid=False)

    payload = json.loads(row["payload"])
    expected_signature = sign_payload(payload)
    valid = expected_signature == row["signature"]

    return render_template(
        "verify.html",
        valid=valid,
        cert=payload
    )


if __name__ == "__main__":
    app.run()
