import qrcode
import sys
from PyPDF2 import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm

# -----------------------------
# INPUTS
# -----------------------------

certificate_id = sys.argv[1]

INPUT_PDF = "marksheet.pdf"
OUTPUT_PDF = "marksheet_with_qr.pdf"
TEMP_QR = "temp_qr.png"
QR_PAGE = "qr_page.pdf"

BASE_URL = "https://YOUR_RENDER_URL.onrender.com"
QR_DATA = f"{BASE_URL}/verify-page/{certificate_id}"

# -----------------------------
# GENERATE QR
# -----------------------------

qr = qrcode.make(QR_DATA)
qr.save(TEMP_QR)

# -----------------------------
# CREATE QR COVER PAGE
# -----------------------------

c = canvas.Canvas(QR_PAGE, pagesize=A4)
width, height = A4

qr_size = 90 * mm
x = (width - qr_size) / 2
y = (height - qr_size) / 2

c.setFont("Helvetica-Bold", 20)
c.drawCentredString(width / 2, height - 80, "Certificate Verification")

c.setFont("Helvetica", 12)
c.drawCentredString(width / 2, height - 110, "Scan the QR code below to verify")

c.drawImage(TEMP_QR, x, y, qr_size, qr_size)

c.setFont("Helvetica", 10)
c.drawCentredString(
    width / 2,
    y - 20,
    "This certificate is digitally signed. Any modification invalidates it."
)

c.showPage()
c.save()

# -----------------------------
# MERGE QR PAGE + CERTIFICATE
# -----------------------------

writer = PdfWriter()

qr_reader = PdfReader(QR_PAGE)
writer.add_page(qr_reader.pages[0])

original = PdfReader(INPUT_PDF)
for page in original.pages:
    writer.add_page(page)

with open(OUTPUT_PDF, "wb") as f:
    writer.write(f)

print("QR page added for certificate:", certificate_id)
