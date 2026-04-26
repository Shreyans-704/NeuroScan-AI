"""
report_generator.py
====================
Generates a professional PDF report for Alzheimer's scan predictions.
Uses reportlab (pip install reportlab).
"""

import io
import base64
from datetime import datetime

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm, mm
from reportlab.lib.utils import ImageReader
from reportlab.platypus import (
    SimpleDocTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
    HRFlowable,
    KeepTogether,
)
from reportlab.graphics.shapes import Drawing, Rect, String
from reportlab.graphics.charts.barcharts import VerticalBarChart
from reportlab.graphics import renderPDF


# ──────────────────────────────────────────────────────────────
# Colour palette (medical blue theme)
# ──────────────────────────────────────────────────────────────
DEEP_BLUE    = colors.HexColor("#0A1628")
MID_BLUE     = colors.HexColor("#1E3A5F")
ACCENT_BLUE  = colors.HexColor("#2563EB")
LIGHT_BLUE   = colors.HexColor("#EFF6FF")
DANGER_RED   = colors.HexColor("#DC2626")
SUCCESS_GRN  = colors.HexColor("#16A34A")
TEXT_DARK    = colors.HexColor("#1E293B")
TEXT_GREY    = colors.HexColor("#64748B")
WHITE        = colors.white

CLASS_COLOURS = {
    "Non-Demented":       colors.HexColor("#22C55E"),
    "Very Mild Demented": colors.HexColor("#EAB308"),
    "Mild Demented":      colors.HexColor("#F97316"),
    "Moderate Demented":  colors.HexColor("#DC2626"),
}


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────
def _styles():
    """Return a dict of custom Paragraph styles."""
    base = getSampleStyleSheet()

    return {
        "title": ParagraphStyle(
            "ReportTitle",
            parent=base["Title"],
            fontSize=22,
            textColor=WHITE,
            fontName="Helvetica-Bold",
            leading=28,
            spaceAfter=4,
        ),
        "subtitle": ParagraphStyle(
            "ReportSubtitle",
            parent=base["Normal"],
            fontSize=11,
            textColor=colors.HexColor("#93C5FD"),
            fontName="Helvetica",
            leading=16,
        ),
        "section": ParagraphStyle(
            "SectionHeading",
            parent=base["Heading2"],
            fontSize=13,
            textColor=ACCENT_BLUE,
            fontName="Helvetica-Bold",
            spaceBefore=14,
            spaceAfter=6,
        ),
        "body": ParagraphStyle(
            "BodyText",
            parent=base["Normal"],
            fontSize=10,
            textColor=TEXT_DARK,
            fontName="Helvetica",
            leading=15,
        ),
        "disclaimer": ParagraphStyle(
            "DisclaimerText",
            parent=base["Normal"],
            fontSize=8.5,
            textColor=TEXT_GREY,
            fontName="Helvetica-Oblique",
            leading=13,
            borderPad=8,
        ),
        "result_positive": ParagraphStyle(
            "ResultPositive",
            parent=base["Normal"],
            fontSize=18,
            textColor=DANGER_RED,
            fontName="Helvetica-Bold",
            leading=24,
        ),
        "result_negative": ParagraphStyle(
            "ResultNegative",
            parent=base["Normal"],
            fontSize=18,
            textColor=SUCCESS_GRN,
            fontName="Helvetica-Bold",
            leading=24,
        ),
        "small": ParagraphStyle(
            "SmallText",
            parent=base["Normal"],
            fontSize=8,
            textColor=TEXT_GREY,
            fontName="Helvetica",
            leading=11,
        ),
    }


def _header_table(doc_data: dict, styles: dict) -> Table:
    """Build the dark header block with logo text + report meta."""
    title_para = Paragraph("NeuroScan AI Diagnostics", styles["title"])

    subtitle_para = Paragraph(
        "Department of Neurology & AI Imaging Analysis<br/>"
        "Alzheimer’s Disease Detection Unit",
        styles["subtitle"]
    )

    scan_id   = doc_data.get("scan_id", "N/A")
    timestamp = doc_data.get("timestamp", datetime.now().isoformat())
    try:
        dt = datetime.fromisoformat(timestamp)
        date_str = dt.strftime("%B %d, %Y")
        time_str = dt.strftime("%H:%M:%S")
    except Exception:
        date_str = timestamp
        time_str = ""

    meta_style = ParagraphStyle(
        "MetaText",
        fontSize=9,
        textColor=colors.HexColor("#CBD5E1"),
        fontName="Helvetica",
        leading=14,
    )
    meta_para = Paragraph(
        f"<b>Scan ID:</b> {scan_id}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"<b>Date:</b> {date_str}&nbsp;&nbsp;|&nbsp;&nbsp;"
        f"<b>Time:</b> {time_str}",
        meta_style,
    )

    data = [
        [title_para],
        [subtitle_para],
        [Spacer(1, 4)],
        [meta_para],
    ]
    t = Table(data, colWidths=["100%"])
    t.setStyle(TableStyle([
        ("BACKGROUND",  (0, 0), (-1, -1), DEEP_BLUE),
        ("TOPPADDING",  (0, 0), (-1, -1), 8),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 12),
        ("LEFTPADDING",  (0, 0), (-1, -1), 20),
        ("RIGHTPADDING", (0, 0), (-1, -1), 20),
    ]))
    return t


def _result_table(doc_data: dict, styles: dict) -> Table:
    """Build the primary result summary box."""
    alzheimer_detected = doc_data.get("alzheimer_detected", False)
    prediction         = doc_data.get("prediction", "Unknown")
    top_confidence     = doc_data.get("top_confidence", 0.0)

    detected_label = "⚠ ALZHEIMER'S INDICATORS DETECTED" if alzheimer_detected else "✓ NO ALZHEIMER'S INDICATORS"
    detected_style = styles["result_positive"] if alzheimer_detected else styles["result_negative"]
    bg_colour      = colors.HexColor("#FEF2F2") if alzheimer_detected else colors.HexColor("#F0FDF4")

    detected_para = Paragraph(detected_label, detected_style)
    stage_para    = Paragraph(
        f"<b>Stage Classification:</b> {prediction}", styles["body"]
    )
    conf_para     = Paragraph(
        f"<b>Confidence Score:</b> {top_confidence:.1f}%", styles["body"]
    )

    data = [
        [detected_para],
        [stage_para],
        [conf_para],
    ]
    t = Table(data, colWidths=["100%"])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), bg_colour),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, -1), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 16),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 16),
        ("ROUNDEDCORNERS", [6]),
        ("BOX", (0, 0), (-1, -1), 1.5,
         DANGER_RED if alzheimer_detected else SUCCESS_GRN),
    ]))
    return t


def _confidence_bar_chart(confidence: dict) -> Drawing:
    """Draw a horizontal-style bar chart using reportlab graphics."""
    labels  = list(confidence.keys())
    values = []
    for v in confidence.values():
        try:
            values.append(float(v))
        except:
            values.append(0)
    bar_colours = [CLASS_COLOURS.get(lbl, ACCENT_BLUE) for lbl in labels]

    drawing = Drawing(440, 180)

    chart = VerticalBarChart()
    chart.x           = 60
    chart.y           = 20
    chart.width       = 360
    chart.height      = 140
    chart.data        = [values]
    chart.strokeColor = None
    chart.fillColor   = None

    chart.valueAxis.valueMin    = 0
    chart.valueAxis.valueMax    = 100
    chart.valueAxis.valueStep   = 20
    chart.valueAxis.labelTextFormat = "%.0f%%"
    chart.valueAxis.labels.fontSize  = 8
    chart.valueAxis.labels.textColor = TEXT_GREY

    chart.categoryAxis.categoryNames = labels
    chart.categoryAxis.labels.fontSize        = 8
    chart.categoryAxis.labels.textColor       = TEXT_DARK
    chart.categoryAxis.labels.angle           = 0
    chart.categoryAxis.labels.dy              = -8
    chart.categoryAxis.labels.maxWidth        = 80

    chart.bars[0].fillColor   = ACCENT_BLUE
    chart.bars[0].strokeColor = None

    # Apply individual bar colours
    for i, col in enumerate(bar_colours):
        chart.bars[(0, i)].fillColor = col

    chart.barWidth = 40
    chart.groupSpacing = 10

    drawing.add(chart)

    # Value labels on top of bars
    for i, (val, col) in enumerate(zip(values, bar_colours)):
        x_pos = chart.x + chart.groupSpacing + i * (chart.barWidth + chart.groupSpacing) + chart.barWidth / 2
        y_pos = chart.y + (val / 100) * chart.height + 4
        label = String(x_pos, y_pos, f"{val:.1f}%",
                       fontSize=7.5, fillColor=col, textAnchor="middle",
                       fontName="Helvetica-Bold")
        drawing.add(label)

    return drawing


def _scan_image_table(image_b64: str | None) -> Table | None:
    """Build a table cell containing the uploaded scan thumbnail."""
    if not image_b64:
        return None
    try:
        img_bytes = base64.b64decode(image_b64)
        img_reader = ImageReader(io.BytesIO(img_bytes))
        from reportlab.platypus import Image as RLImage

        img_flowable = RLImage(io.BytesIO(img_bytes), width=6 * cm, height=6 * cm)
        data = [[img_flowable]]
        t = Table(data, colWidths=[7 * cm])
        t.setStyle(TableStyle([
            ("ALIGN",   (0, 0), (-1, -1), "CENTER"),
            ("VALIGN",  (0, 0), (-1, -1), "MIDDLE"),
            ("BOX",     (0, 0), (-1, -1), 0.5, TEXT_GREY),
            ("BACKGROUND", (0, 0), (-1, -1), LIGHT_BLUE),
            ("TOPPADDING", (0, 0), (-1, -1), 6),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ]))
        return t
    except Exception:
        return None


def _class_detail_table(confidence: dict, prediction: str, styles: dict) -> Table:
    """Tabular breakdown of all class probabilities."""
    header = ["Classification Stage", "Probability (%)", "Status"]
    rows   = [header]
    for cls, pct in confidence.items():
        is_predicted = cls == prediction
        status = "✓ Predicted" if is_predicted else "—"
        rows.append([cls, f"{float(pct):.2f}%", status])

    t = Table(rows, colWidths=[220, 120, 100])
    style = TableStyle([
        # Header
        ("BACKGROUND",    (0, 0), (-1, 0), MID_BLUE),
        ("TEXTCOLOR",     (0, 0), (-1, 0), WHITE),
        ("FONTNAME",      (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE",      (0, 0), (-1, 0), 10),
        ("ALIGN",         (0, 0), (-1, 0), "CENTER"),
        ("TOPPADDING",    (0, 0), (-1, 0), 8),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 8),
        # Rows
        ("FONTNAME",  (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE",  (0, 1), (-1, -1), 9),
        ("ALIGN",     (1, 1), (-1, -1), "CENTER"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [WHITE, LIGHT_BLUE]),
        ("TOPPADDING",    (0, 1), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 10),
        # Grid
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#CBD5E1")),
    ])

    # Highlight predicted row
    for i, cls in enumerate(confidence.keys(), start=1):
        if cls == prediction:
            style.add("BACKGROUND", (0, i), (-1, i), colors.HexColor("#DBEAFE"))
            style.add("FONTNAME",   (2, i), (2, i), "Helvetica-Bold")
            style.add("TEXTCOLOR",  (2, i), (2, i), SUCCESS_GRN)

    t.setStyle(style)
    return t

def _recommendation_section(prediction, styles):
    prediction = prediction.strip().lower()

    if prediction == "non-demented":
        text = """
        <b>Clinical Recommendation:</b><br/>
        • No signs of Alzheimer’s detected.<br/>
        • Maintain healthy lifestyle and regular monitoring.<br/>
        • Periodic cognitive screening is advised.
        """

    elif prediction in ["very mild demented", "very mild dementia"]:
        text = """
        <b>Clinical Recommendation:</b><br/>
        • Very early signs detected — monitor closely.<br/>
        • Perform cognitive screening tests (MMSE, MoCA).<br/>
        • Lifestyle improvements strongly recommended.<br/>
        • Follow-up scans suggested.
        """

    elif prediction in ["mild demented", "mild dementia"]:
        text = """
        <b>Clinical Recommendation:</b><br/>
        • Mild stage Alzheimer’s detected.<br/>
        • Neurologist consultation recommended.<br/>
        • Start cognitive therapy and lifestyle adjustments.<br/>
        • Pharmacological treatment (e.g., cholinesterase inhibitors) may be considered under medical supervision.
        """

    elif prediction in ["moderate demented", "moderate dementia"]:
        text = """
        <b>Clinical Recommendation:</b><br/>
        • Moderate stage Alzheimer’s detected.<br/>
        • Immediate clinical attention required.<br/>
        • Medication and structured care plan needed.<br/>
        • Caregiver support is essential.
        """

    else:
        text = """
        <b>Clinical Recommendation:</b><br/>
        • Unable to determine condition clearly.<br/>
        • Further clinical evaluation is recommended.
        """

    return Paragraph(text, styles["body"])


def _disclaimer_box(styles: dict) -> Table:
    """Return a styled disclaimer paragraph."""
    disclaimer_text = (
        "<b>⚠ Medical Disclaimer:</b> This report is generated by an AI-assisted "
        "analysis system and is intended to support — not replace — professional "
        "medical diagnosis. All findings should be reviewed and confirmed by a "
        "qualified neurologist or healthcare professional before any clinical "
        "decision is made. The AI system may produce false positives or false "
        "negatives. This report does not constitute medical advice."
    )
    para = Paragraph(disclaimer_text, styles["disclaimer"])
    t = Table([[para]], colWidths=["100%"])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#FFFBEB")),
        ("BOX",           (0, 0), (-1, -1), 1, colors.HexColor("#F59E0B")),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
    ]))
    return t


# ──────────────────────────────────────────────────────────────
# Main generator
# ──────────────────────────────────────────────────────────────
def generate_pdf_report(data: dict) -> bytes:
    """
    Build and return a PDF report as raw bytes.

    Parameters
    ----------
    data : dict
        Prediction result dict from /predict endpoint.
    """
    buf = io.BytesIO()
    styles = _styles()

    doc = SimpleDocTemplate(
        buf,
        pagesize=A4,
        leftMargin=2 * cm,
        rightMargin=2 * cm,
        topMargin=1.5 * cm,
        bottomMargin=2 * cm,
        title=f"Alzheimer Detection Report — {data.get('scan_id', '')}",
        author="AI Alzheimer Detection System",
    )

    story = []

    # ── Header ───────────────────────────────────────────────
    story.append(_header_table(data, styles))
    story.append(Spacer(1, 16))

    # ── Primary result ────────────────────────────────────────
    story.append(Paragraph("Primary Diagnosis Result", styles["section"]))
    story.append(_result_table(data, styles))
    story.append(Spacer(1, 14))

    prediction = data.get("prediction", "")

    color = SUCCESS_GRN
    if "Very Mild" in prediction:
        color = colors.HexColor("#EAB308")
    elif "Mild" in prediction:
        color = colors.HexColor("#F97316")
    elif "Moderate" in prediction:
        color = DANGER_RED

    severity_box = Table(
        [[Paragraph(f"<b>Severity Level: {prediction}</b>", styles["body"])]],
        colWidths=["100%"]
    )

    severity_box.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,-1), LIGHT_BLUE),
        ("BOX", (0,0), (-1,-1), 2, color),
        ("LEFTPADDING", (0,0), (-1,-1), 12),
        ("TOPPADDING", (0,0), (-1,-1), 8),
        ("BOTTOMPADDING", (0,0), (-1,-1), 8),
    ]))

    story.append(severity_box)
    story.append(Spacer(1, 12))

    # ── Scan image (if provided) ──────────────────────────────
    image_b64 = data.get("image_b64")
    if image_b64:
        story.append(Paragraph("Uploaded Scan Image", styles["section"]))
        img_table = _scan_image_table(image_b64)
        if img_table:
            story.append(img_table)
            story.append(Spacer(1, 14))

    # ── Confidence bar chart ──────────────────────────────────
    confidence = data.get("confidence", {})

    # fallback if empty or broken
    if not isinstance(confidence, dict) or len(confidence) == 0:
        confidence = {
            "Non-Demented": 0,
            "Very Mild Demented": 0,
            "Mild Demented": 0,
            "Moderate Demented": 0
        }

    # chart
    try:
        chart_drawing = _confidence_bar_chart(confidence)
        story.append(chart_drawing)
        story.append(Spacer(1, 12))
    except Exception:
        pass

    # ── Detailed table ────────────────────────────────────────
    story.append(Paragraph("Detailed Classification Breakdown", styles["section"]))
    story.append(_class_detail_table(confidence, data.get("prediction", "Unknown"), styles))
    story.append(Spacer(1, 20))

    # ── Clinical Recommendations ─────────────────────────────
    story.append(Paragraph("Clinical Recommendations", styles["section"]))
    story.append(_recommendation_section(data.get("prediction", ""), styles))
    story.append(Spacer(1, 20))

    # ── Doctor Verification ─────────────────────────────
    story.append(Paragraph("Medical Review & Authorization", styles["section"]))
    doctor_text = """
    <b>Reviewed By:</b> Dr. AI Neuro System<br/>
    <b>Designation:</b> AI-Assisted Diagnostic Engine<br/>
    <b>Status:</b> Preliminary Automated Report<br/><br/>
    <i>This report must be reviewed and validated by a certified neurologist.</i>
    """
    story.append(Paragraph(doctor_text, styles["body"]))
    story.append(Spacer(1, 20))

    # ── Disclaimer ────────────────────────────────────────────
    story.append(HRFlowable(width="100%", thickness=0.5, color=TEXT_GREY))
    story.append(Spacer(1, 10))
    story.append(_disclaimer_box(styles))
    story.append(Spacer(1, 10))

    # ── Footer note ───────────────────────────────────────────
    footer_text = (
        f"Report ID: {data.get('scan_id', 'N/A')} | "
        f"Generated: {datetime.now().strftime('%d-%m-%Y %H:%M')} | "
        f"System Version: NeuroScan AI v1.0"
    )
    story.append(Paragraph(footer_text, styles["small"]))

    def add_watermark(canvas, doc):
        canvas.saveState()
        canvas.setFont("Helvetica-Bold", 40)
        canvas.setFillColorRGB(0.9, 0.9, 0.9)
        canvas.drawCentredString(300, 400, "NeuroScan AI")
        canvas.restoreState()

    doc.build(story, onFirstPage=add_watermark, onLaterPages=add_watermark)

    buf.seek(0)
    return buf.read()
