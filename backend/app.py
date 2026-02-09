from flask import Flask, request, jsonify, send_from_directory, render_template_string
from flask_cors import CORS
import sqlite3
import uuid
import json
import datetime
import os
import hashlib

# ---------------- BASIC SETUP ----------------
app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "certificates.db")
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")

VERIFY_BASE_URL = "https://certificate-verifier-vasy.onrender.com/verify"

# ---------------- DATABASE ----------------
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
            certificate_json TEXT NOT NULL,
            signature TEXT NOT NULL,
            issued_at TEXT NOT NULL,
            status TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

init_db()

# ---------------- UTIL ----------------
def sign_certificate(cert_json: dict) -> str:
    """
    Simple deterministic signature (demo-safe).
    Replace with private-key crypto later if needed.
    """
    payload = json.dumps(cert_json, sort_keys=True)
    return hashlib.sha256(payload.encode()).hexdigest()

# ---------------- HEALTH ----------------
@app.route("/")
def home():
    return "Certificate Verification Backend Running"

# ---------------- ISSUE CERTIFICATE ----------------
@app.route("/api/issue", methods=["POST"])
def issue_certificate():
    data = request.get_json()
    if not data:
        return jsonify({"error": "Invalid JSON"}), 400

    cert_id = str(uuid.uuid4())
    issued_at = datetime.datetime.utcnow().isoformat()

    signature = sign_certificate(data)

    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO certificates (id, certificate_json, signature, issued_at, status)
        VALUES (?, ?, ?, ?, ?)
    """, (
        cert_id,
        json.dumps(data),
        signature,
        issued_at,
        "VALID"
    ))
    conn.commit()
    conn.close()

    return jsonify({
        "certificate_id": cert_id,
        "verify_url": f"{VERIFY_BASE_URL}/{cert_id}",
        "signature": signature
    })

# ---------------- VERIFY (AUTO VIA QR) ----------------
@app.route("/verify/<cert_id>")
def verify_certificate(cert_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM certificates WHERE id = ?", (cert_id,))
    row = cur.fetchone()
    conn.close()

    if not row:
        return render_template_string("""
            <h1 style="color:red;">❌ INVALID CERTIFICATE</h1>
            <p>Certificate not found.</p>
        """)

    cert_data = json.loads(row["certificate_json"])
    expected_sig = row["signature"]
    actual_sig = sign_certificate(cert_data)

    valid = expected_sig == actual_sig and row["status"] == "VALID"

    color = "green" if valid else "red"
    status_text = "VALID CERTIFICATE ✅" if valid else "INVALID CERTIFICATE ❌"

    html = f"""
    <html>
    <head>
        <title>Certificate Verification</title>
        <style>
            body {{ font-family: Arial; background:#f5f5f5; padding:40px; }}
            .card {{ background:white; padding:30px; border-radius:8px; max-width:600px; margin:auto; }}
            h1 {{ color:{color}; }}
            table {{ width:100%; border-collapse: collapse; }}
            td {{ padding:8px; border-bottom:1px solid #ddd; }}
        </style>
    </head>
    <body>
        <div class="card">
            <h1>{status_text}</h1>
            <h3>Certificate Details</h3>
            <table>
                {''.join(f"<tr><td><b>{k}</b></td><td>{v}</td></tr>" for k,v in cert_data.items())}
            </table>
            <p><small>Issued at: {row["issued_at"]}</small></p>
        </div>
    </body>
    </html>
    """
    return html

# ---------------- FRONTEND PAGES (OPTIONAL) ----------------
@app.route("/issue-page")
def issue_page():
    return send_from_directory(FRONTEND_DIR, "issue.html")

@app.route("/scan-page")
def scan_page():
    return send_from_directory(FRONTEND_DIR, "scan.html")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
