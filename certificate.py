
from pathlib import Path
from reportlab.lib.pagesizes import landscape, A4
from reportlab.pdfgen import canvas

OUTPUT_DIR = Path("certificates")
OUTPUT_DIR.mkdir(exist_ok=True)


def generate_certificate(
    certificate_id: str,
    recipient_name: str,
    event_name: str,
    issue_date: str
) -> str:
    file_path = OUTPUT_DIR / f"{certificate_id}.pdf"

    pdf = canvas.Canvas(str(file_path), pagesize=landscape(A4))
    width, height = landscape(A4)

    # Certificate border
    pdf.setLineWidth(3)
    pdf.rect(30, 30, width - 60, height - 60)

    # Certificate title
    pdf.setFont("Helvetica-Bold", 30)
    pdf.drawCentredString(
        width / 2, height - 120, "CERTIFICATE OF COMPLETION"
    )

    # Main text
    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(
        width / 2, height - 190, "This certificate is proudly presented to"
    )

    # Recipient name
    pdf.setFont("Helvetica-Bold", 26)
    pdf.drawCentredString(
        width / 2, height - 240, recipient_name
    )

    # Event name
    pdf.setFont("Helvetica", 16)
    pdf.drawCentredString(
        width / 2, height - 290, f"For completing {event_name}"
    )

    # Issue date
    pdf.setFont("Helvetica", 13)
    pdf.drawCentredString(
        width / 2, 100, f"Issue Date: {issue_date}"
    )

    pdf.save()
    return str(file_path)