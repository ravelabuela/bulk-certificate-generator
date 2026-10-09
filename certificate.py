"""PDF rendering for the application's single certificate template."""

from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.pdfgen import canvas


OUTPUT_DIR = Path(__file__).resolve().parent / "certificates"
OUTPUT_DIR.mkdir(exist_ok=True)

NAVY = HexColor("#003C52")
GOLD = HexColor("#C99A32")
LIGHT_GOLD = HexColor("#F2C85C")
DARK_GOLD = HexColor("#8F651D")
CHARCOAL = HexColor("#313131")


def _polygon(pdf: canvas.Canvas, points: list[tuple[float, float]], color):
    """Draw a filled polygon using ReportLab's path primitives."""
    path = pdf.beginPath()
    path.moveTo(*points[0])
    for point in points[1:]:
        path.lineTo(*point)
    path.close()
    pdf.setFillColor(color)
    pdf.drawPath(path, fill=1, stroke=0)


def _draw_flourish(
    pdf: canvas.Canvas,
    x: float,
    y: float,
    scale: float = 1,
    flip: bool = False,
):
    """Draw a small vector ornamental flourish without external assets."""
    pdf.saveState()
    pdf.translate(x, y)
    pdf.scale(-scale if flip else scale, scale)
    pdf.setStrokeColor(GOLD)
    pdf.setFillColor(GOLD)
    pdf.setLineWidth(1.5)

    # Stem and curling tendrils.
    pdf.bezier(0, 0, 18, 8, 24, 36, 13, 54)
    pdf.bezier(13, 54, 3, 69, -8, 59, -2, 47)
    pdf.bezier(-2, 47, 2, 39, 10, 42, 8, 50)
    pdf.bezier(12, 24, 35, 18, 45, 30, 38, 42)
    pdf.bezier(38, 42, 31, 51, 23, 43, 30, 35)
    pdf.bezier(7, 20, -10, 26, -14, 13, -5, 7)
    pdf.bezier(-5, 7, 3, 2, 5, 12, -3, 14)

    # Leaves.
    for leaf_x, leaf_y, direction in ((10, 22, 1), (15, 37, -1), (3, 48, 1)):
        leaf = pdf.beginPath()
        leaf.moveTo(leaf_x, leaf_y)
        leaf.curveTo(
            leaf_x + 11 * direction,
            leaf_y + 2,
            leaf_x + 12 * direction,
            leaf_y + 11,
            leaf_x + 2 * direction,
            leaf_y + 10,
        )
        leaf.curveTo(
            leaf_x - 2 * direction,
            leaf_y + 7,
            leaf_x - 1 * direction,
            leaf_y + 2,
            leaf_x,
            leaf_y,
        )
        pdf.drawPath(leaf, fill=1, stroke=0)

    # A small flower at the end of the stem.
    for angle in range(0, 360, 60):
        pdf.saveState()
        pdf.translate(13, 54)
        pdf.rotate(angle)
        pdf.ellipse(-3, 2, 3, 12, fill=1, stroke=0)
        pdf.restoreState()
    pdf.setFillColor(DARK_GOLD)
    pdf.circle(13, 54, 2.5, fill=1, stroke=0)
    pdf.restoreState()


def _draw_spaced_text(
    pdf: canvas.Canvas,
    text: str,
    center_x: float,
    y: float,
    font: str,
    size: float,
    spacing: float,
):
    widths = [stringWidth(character, font, size) for character in text]
    total_width = sum(widths) + spacing * max(0, len(text) - 1)
    x = center_x - total_width / 2
    pdf.setFont(font, size)
    for character, width in zip(text, widths):
        pdf.drawString(x, y, character)
        x += width + spacing


def _draw_wrapped_centered(
    pdf: canvas.Canvas,
    text: str,
    center_x: float,
    y: float,
    maximum_width: float,
    font: str,
    size: float,
    leading: float,
):
    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for word in words:
        candidate = " ".join(current + [word])
        if current and stringWidth(candidate, font, size) > maximum_width:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))

    pdf.setFont(font, size)
    for index, line in enumerate(lines[:2]):
        pdf.drawCentredString(center_x, y - index * leading, line)


def _draw_seal(pdf: canvas.Canvas, center_x: float, center_y: float):
    """Create a simple medal-like seal from concentric vector circles."""
    pdf.saveState()
    pdf.setFillColor(DARK_GOLD)
    pdf.circle(center_x, center_y, 37, fill=1, stroke=0)
    pdf.setFillColor(GOLD)
    pdf.circle(center_x, center_y, 33, fill=1, stroke=0)
    pdf.setFillColor(LIGHT_GOLD)
    pdf.circle(center_x, center_y + 2, 27, fill=1, stroke=0)
    pdf.setStrokeColor(DARK_GOLD)
    pdf.setLineWidth(1.2)
    pdf.circle(center_x, center_y, 27, fill=0, stroke=1)
    pdf.setFillColor(NAVY)
    pdf.setFont("Helvetica-Bold", 9)
    pdf.drawCentredString(center_x, center_y - 4, "AWARDED")
    pdf.restoreState()


def generate_certificate(
    certificate_id: str,
    recipient_name: str,
    event_name: str,
    issue_date: str,
) -> str:
    """Generate and return the path to an elegant participation certificate."""
    file_path = OUTPUT_DIR / f"{certificate_id}.pdf"
    width, height = landscape(A4)
    pdf = canvas.Canvas(str(file_path), pagesize=(width, height))
    pdf.setTitle("Certificate of Participation")

    # White paper with a thin gold frame.
    pdf.setFillColor(white)
    pdf.rect(0, 0, width, height, fill=1, stroke=0)
    pdf.setStrokeColor(DARK_GOLD)
    pdf.setLineWidth(1)
    pdf.rect(22, 22, width - 44, height - 44, fill=0, stroke=1)

    # Navy and gold corner ribbons inspired by the supplied reference.
    _polygon(pdf, [(0, height), (215, height), (0, height - 92)], NAVY)
    _polygon(pdf, [(width, height), (width - 150, height), (width, height - 175)], NAVY)
    _polygon(pdf, [(width, height - 70), (width - 65, height), (width, height - 250)], LIGHT_GOLD)
    _polygon(pdf, [(0, 0), (0, 95), (180, 0)], NAVY)
    _polygon(pdf, [(0, 0), (0, 155), (125, 0)], LIGHT_GOLD)

    _draw_flourish(pdf, 55, height - 172, 1.6)
    _draw_flourish(pdf, width - 95, 55, 1.55, flip=True)

    # Heading and medal.
    pdf.setFillColor(NAVY)
    _draw_spaced_text(
        pdf, "CERTIFICATE", width / 2, height - 108,
        "Times-Roman", 29, 9,
    )
    _draw_seal(pdf, width / 2, height - 178)

    pdf.setFillColor(CHARCOAL)
    _draw_spaced_text(
        pdf, "OF PARTICIPATION", width / 2, height - 252,
        "Times-Roman", 13, 2.5,
    )
    pdf.setFont("Times-Roman", 15)
    pdf.drawCentredString(width / 2, height - 291, "This certificate is presented to:")

    # Use the largest readable name size for both short and long recipients.
    name_size = 39
    while (
        name_size > 20
        and stringWidth(recipient_name, "Times-Italic", name_size) > width - 250
    ):
        name_size -= 1
    pdf.setFillColor(GOLD)
    pdf.setFont("Times-Italic", name_size)
    pdf.drawCentredString(width / 2, height - 367, recipient_name)
    pdf.setStrokeColor(HexColor("#584783"))
    pdf.setLineWidth(1.2)
    pdf.line(width / 2 - 158, height - 386, width / 2 + 158, height - 386)

    pdf.setFillColor(CHARCOAL)
    _draw_wrapped_centered(
        pdf,
        f"For successfully completing {event_name}",
        width / 2,
        height - 432,
        width - 280,
        "Times-Roman",
        15,
        21,
    )

    pdf.setFont("Times-Roman", 12)
    pdf.drawString(245, 82, "ISSUE DATE")
    pdf.setFont("Times-Bold", 14)
    pdf.drawString(245, 58, issue_date)
    pdf.setStrokeColor(GOLD)
    pdf.setLineWidth(0.7)
    pdf.line(235, 52, 375, 52)

    pdf.save()
    return str(file_path)
