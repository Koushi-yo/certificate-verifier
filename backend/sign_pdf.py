from pyhanko.sign import signers
from pyhanko.sign.fields import SigFieldSpec
from pyhanko.pdf_utils.incremental_writer import IncrementalPdfFileWriter

INPUT_PDF = "marksheet_with_qr.pdf"
OUTPUT_PDF = "marksheet_signed.pdf"

KEY_FILE = "issuer.key"
CERT_FILE = "issuer.crt"

with open(KEY_FILE, "rb") as kf, open(CERT_FILE, "rb") as cf:
    signer = signers.SimpleSigner(
        signing_cert=cf.read(),
        signing_key=kf.read(),
        cert_registry=None
    )

with open(INPUT_PDF, "rb") as inf:
    writer = IncrementalPdfFileWriter(inf)
    signers.sign_pdf(
        writer,
        signature_meta=signers.PdfSignatureMetadata(
            field_name="Signature1"
        ),
        signer=signer,
        new_field_spec=SigFieldSpec(sig_field_name="Signature1"),
        output=OUTPUT_PDF
    )

print("PDF digitally signed successfully")
