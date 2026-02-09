from flask import Flask, request, jsonify, render_template_string
from flask_cors import CORS
import sqlite3
import uuid
import hashlib
import os

app = Flask(__name__)
CORS(app)

# ===============================
# DATABASE (ABSOLUTE, SAFE)
# ===============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "certificates.db")

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            id TEXT PRIMARY KEY,
            payload TEXT,
            signature TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ===============================
# UTIL
# ===============================
def sign_payload(payload: str) -> str:
    return hashlib.sha256(payload.encode()).hexdigest()

# ===============================
# ISSUE CERTIFICATE (API)
# ===============================
@app.route("/api/issue", methods=["POST"])
def issue_certificate():
    data = request.get_json(force=True)

    cert_id = str(uuid.uuid4())
    payload_str = str(sorted(data.items()))
    signature = sign_payload(payload_str)

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO certificates (id, payload, signature) VALUES (?, ?, ?)",
        (cert_id, payload_str, signature)
    )
    conn.commit()
    conn.close()

    verify_url = f"https://certificate-verifier-vasy.onrender.com/verify/{cert_id}"

    return jsonify({
        "certificate_id": cert_id,
        "signature": signature,
        "verify_url": verify_url
    })

# ===============================
# VERIFY PAGE (PROFESSIONAL)
# ===============================
VERIFY_HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Certificate Verification</title>
    <style>
        body { font-family: Arial; background:#f5f5f5; padding:40px }
        .box { background:white; padding:30px; border-radius:8px; max-width:600px; margin:auto }
        .ok { color:green; font-size:24px }
        .bad { color:red; font-size:24px }
        code { background:#eee; padding:5px }
    </style>
</head>
<body>
<div class="box">
    {% if valid %}
        <div class="ok">✔ CERTIFICATE IS VALID</div>
        <p><b>Certificate ID:</b> <code>{{ cert_id }}</code></p>
        <p><b>Signature:</b></p>
        <code>{{ signature }}</code>
    {% else %}
        <div class="bad">✖ INVALID CERTIFICATE</div>
        <p>Certificate not found.</p>
    {% endif %}
</div>
</body>
</html>
"""

@app.route("/verify/<cert_id>")
def verify(cert_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM certificates WHERE id = ?", (cert_id,))
    row = cur.fetchone()
    conn.close()

    if row:
        return render_template_string(
            VERIFY_HTML,
            valid=True,
            cert_id=row["id"],
            signature=row["signature"]
        )
    else:
        return render_template_string(
            VERIFY_HTML,
            valid=False
        )

# ===============================
# HOME
# ===============================
@app.route("/")
def home():
    return jsonify({"status": "Certificate Verifier API is running"})

# ===============================
# START
# ===============================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000)
