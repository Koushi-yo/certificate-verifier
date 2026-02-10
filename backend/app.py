from flask import Flask, request, jsonify, render_template, abort
import sqlite3
import uuid
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
FRONTEND_DIR = os.path.join(BASE_DIR, "..", "frontend")
DB_PATH = os.path.join(BASE_DIR, "certificates.db")

app = Flask(
    __name__,
    template_folder=FRONTEND_DIR
)

# -------------------------
# DATABASE INIT
# -------------------------
def init_db():
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            token TEXT PRIMARY KEY,
            issuer TEXT,
            doc_type TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

# -------------------------
# HOME
# -------------------------
@app.route("/")
def home():
    return "Certificate Verification Service is LIVE"

# -------------------------
# ISSUE PAGE (UNIVERSITY)
# -------------------------
@app.route("/issue", methods=["GET"])
def issue_page():
    return render_template("issue.html")

@app.route("/api/issue", methods=["POST"])
def issue_certificate():
    data = request.get_json()
    issuer = data.get("university", "Unknown University")
    doc_type = data.get("degree", "Academic Certificate")

    token = str(uuid.uuid4())

    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO certificates VALUES (?, ?, ?)",
        (token, issuer, doc_type)
    )
    conn.commit()
    conn.close()

    verify_url = f"https://certificate-verifier-vasy.onrender.com/verify/{token}"

    return jsonify({
        "verify_url": verify_url
    })

# -------------------------
# SCAN PAGE (OPTIONAL)
# -------------------------
@app.route("/scan")
def scan_page():
    return render_template("scan.html")

# -------------------------
# VERIFY VIA TOKEN (QR FLOW)
# -------------------------
@app.route("/verify/<token>")
def verify_token(token):
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute(
        "SELECT issuer, doc_type FROM certificates WHERE token=?",
        (token,)
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return render_template("invalid.html")

    issuer, doc_type = row
    return render_template(
        "valid.html",
        issuer=issuer,
        doc_type=doc_type
    )

# -------------------------
# MANUAL VERIFY PAGE (OPTIONAL)
# -------------------------
@app.route("/verify")
def verify_page():
    return render_template("verify.html")

# -------------------------
# RUN
# -------------------------
if __name__ == "__main__":
    app.run()
