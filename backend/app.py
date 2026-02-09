from flask import Flask, request, send_file
from flask_cors import CORS
import sqlite3
import uuid
import subprocess
from datetime import datetime
import os

app = Flask(__name__)
CORS(app)

DB_PATH = "database.db"

# --------------------------------------------------
# DATABASE UTILITIES
# --------------------------------------------------

def get_db():
    return sqlite3.connect(DB_PATH)

def init_db():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            id TEXT PRIMARY KEY,
            issuer TEXT,
            issued_at TEXT,
            revoked INTEGER
        )
    """)
    conn.commit()
    conn.close()

init_db()

# --------------------------------------------------
# HOME
# --------------------------------------------------

@app.route("/")
def home():
    return "Certificate Verification Backend Running"

# --------------------------------------------------
# ISSUE CERTIFICATE (UI + LOGIC)
# --------------------------------------------------

@app.route("/issue-page", methods=["GET", "POST"])
def issue_page():
    if request.method == "GET":
        return """
        <h2>Issue Certificate</h2>
        <form method="POST">
            Issuer:<br>
            <input name="issuer" required><br><br>

            Certificate Data (for record only):<br>
            <textarea name="certificate_data" required></textarea><br><br>

            <button type="submit">Issue Certificate</button>
        </form>
        """

    issuer = request.form.get("issuer")
    certificate_data = request.form.get("certificate_data")

    if not issuer or not certificate_data:
        return "<p style='color:red;'>Missing data</p>"

    certificate_id = str(uuid.uuid4())
    issued_at = datetime.utcnow().isoformat()

    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO certificates VALUES (?, ?, ?, ?)",
        (certificate_id, issuer, issued_at, 0)
    )
    conn.commit()
    conn.close()

    # --------------------------------------------------
    # GENERATE QR + PDF + SIGN
    # --------------------------------------------------

    subprocess.run(
        ["python", "embed_qr_into_pdf.py", certificate_id],
        check=True
    )

    subprocess.run(
        ["python", "sign_pdf.py"],
        check=True
    )

    return f"""
    <h3 style="color:green;">✅ Certificate Issued</h3>
    <p><b>Certificate ID:</b> {certificate_id}</p>
    <a href="/download">Download Signed Certificate</a>
    """

# --------------------------------------------------
# DOWNLOAD FINAL SIGNED PDF
# --------------------------------------------------

@app.route("/download")
def download():
    return send_file("marksheet_signed.pdf", as_attachment=True)

# --------------------------------------------------
# VERIFY CERTIFICATE (PUBLIC)
# --------------------------------------------------

@app.route("/verify-page/<certificate_id>")
def verify_page(certificate_id):
    conn = get_db()
    cur = conn.cursor()
    cur.execute(
        "SELECT issuer, issued_at, revoked FROM certificates WHERE id=?",
        (certificate_id,)
    )
    row = cur.fetchone()
    conn.close()

    if not row:
        return "<h2 style='color:red;'>❌ INVALID CERTIFICATE</h2>"

    issuer, issued_at, revoked = row

    if revoked:
        return "<h2 style='color:red;'>❌ CERTIFICATE REVOKED</h2>"

    return f"""
    <h2 style='color:green;'>✅ CERTIFICATE VALID</h2>
    <p><b>Issuer:</b> {issuer}</p>
    <p><b>Issued At:</b> {issued_at}</p>
    <p>This document is digitally signed. Any modification invalidates it.</p>
    """

# --------------------------------------------------
# RUN (RENDER + LOCAL COMPATIBLE)
# --------------------------------------------------

if __name__ == "__main__":
    print(">>> Certificate backend starting...")
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
