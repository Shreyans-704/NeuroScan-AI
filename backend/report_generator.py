import io
import os
import base64
import tempfile
from datetime import datetime

from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    Image, HRFlowable,
)
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.units import inch


# ── Default confidence fallback ───────────────────────────────
_DEFAULT_CONFIDENCE = {
    "Non-Demented": 0.0,
    "Very Mild Demented": 0.0,
    "Mild Demented": 0.0,
    "Moderate Demented": 0.0,
}

# ── Stage-keyed clinical content ──────────────────────────────
_IMPRESSIONS = {
    "non-demented": (
        "No imaging features suggestive of Alzheimer's disease identified. "
        "Scan within normal limits."
    ),
    "very mild": (
        "Subtle cortical changes noted, possibly indicative of very early cognitive decline. "
        "Correlation with clinical assessment recommended."
    ),
    "mild": (
        "Mild cerebral atrophy and hippocampal volume loss consistent with early-stage "
        "Alzheimer's disease. Neurological review advised."
    ),
    "moderate": (
        "Moderate neurodegenerative changes with significant hippocampal atrophy. "
        "Findings consistent with moderate Alzheimer's disease. Urgent specialist referral required."
    ),
}

_RECOMMENDATIONS = {
    "non-demented": [
        "Continue routine cognitive screening (MMSE/MoCA) annually.",
        "Maintain cardiovascular health and cognitive engagement.",
        "No pharmacological intervention indicated at this time.",
    ],
    "very mild": [
        "Repeat cognitive assessment (MMSE, MoCA) within 6 months.",
        "Lifestyle modification: regular aerobic exercise, sleep hygiene, Mediterranean diet.",
        "Follow-up MRI in 12 months to monitor progression.",
    ],
    "mild": [
        "Neurologist referral for comprehensive evaluation.",
        "Consider cholinesterase inhibitor therapy (e.g., donepezil) under specialist guidance.",
        "Initiate cognitive rehabilitation and caregiver education.",
    ],
    "moderate": [
        "Urgent neurology referral and multidisciplinary care planning.",
        "Review and optimise pharmacological management (AChEI / memantine).",
        "Caregiver support services and home safety assessment essential.",
        "Consider social services involvement and advance care planning.",
    ],
}


def _resolve_stage_key(stage_lower: str) -> str:
    """Map a lowercase prediction string to a _IMPRESSIONS/_RECOMMENDATIONS key."""
    if "very mild" in stage_lower:
        return "very mild"
    if "moderate" in stage_lower:
        return "moderate"
    if "mild" in stage_lower:
        return "mild"
    return "non-demented"


# ──────────────────────────────────────────────────────────────
# Primary PDF builder
# ──────────────────────────────────────────────────────────────
def generate_alzheimer_report(output_path, image_path, data):
    """
    Build and write a PDF Alzheimer diagnostic report.

    Parameters
    ----------
    output_path : str | BytesIO
        Destination path or in-memory buffer.
    image_path  : str | None
        Absolute path to the MRI scan image, or None.
    data        : dict
        Keys: scan_id, date, findings (list), classification_data (list of lists),
              impression (str), recommendations (list).
    """
    base_styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "TitleStyle", parent=base_styles["Title"],
        alignment=TA_CENTER, spaceAfter=4,
    )
    subtitle_style = ParagraphStyle(
        "SubtitleStyle", parent=base_styles["Normal"],
        alignment=TA_CENTER, textColor=colors.grey, fontSize=10,
    )
    section_style = base_styles["Heading2"]
    body_style    = base_styles["Normal"]

    doc      = SimpleDocTemplate(output_path, pagesize=A4)
    elements = []

    # ── Header ────────────────────────────────────────────────
    elements.append(Paragraph("<b>NeuroScan AI Diagnostics</b>", title_style))
    elements.append(Paragraph("Department of Neurology &amp; Neuroimaging", subtitle_style))
    elements.append(Spacer(1, 6))
    elements.append(HRFlowable(width="100%", thickness=1))
    elements.append(Spacer(1, 12))

    # ── Scan Details ──────────────────────────────────────────
    elements.append(Paragraph("<b>Scan Details</b>", section_style))
    elements.append(Paragraph(f"Scan ID:  {data['scan_id']}", body_style))
    elements.append(Paragraph(f"Date:     {data['date']}", body_style))
    elements.append(Paragraph("Modality: MRI Brain — AI-Assisted Analysis", body_style))
    elements.append(Spacer(1, 12))

    # ── Scan Image ────────────────────────────────────────────
    if image_path:
        try:
            img = Image(image_path, width=4 * inch, height=3 * inch)
            img.hAlign = "CENTER"
            elements.append(img)
        except Exception:
            elements.append(Paragraph("Scan image unavailable.", body_style))
        elements.append(Spacer(1, 12))

    # ── Clinical Findings ─────────────────────────────────────
    elements.append(Paragraph("<b>Clinical Findings</b>", section_style))
    for item in data["findings"]:
        elements.append(Paragraph(f"• {item}", body_style))
    elements.append(Spacer(1, 12))

    # ── Classification Table ──────────────────────────────────
    elements.append(Paragraph("<b>AI Classification Analysis</b>", section_style))
    table_data = [["Stage", "Probability", "Result"]] + data["classification_data"]
    table = Table(table_data, hAlign="LEFT")
    table.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  colors.HexColor("#404040")),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  colors.white),
        ("FONTNAME",      (0, 0), (-1, 0),  "Helvetica-Bold"),
        ("ALIGN",         (0, 0), (-1, -1), "CENTER"),
        ("FONTSIZE",      (0, 0), (-1, -1), 9),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("GRID",          (0, 0), (-1, -1), 0.6, colors.HexColor("#CCCCCC")),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 15))

    # ── Impression (boxed) ────────────────────────────────────
    elements.append(Paragraph("<b>Impression</b>", section_style))
    impression_box = Table([[Paragraph(data["impression"], body_style)]])
    impression_box.setStyle(TableStyle([
        ("BOX",        (0, 0), (-1, -1), 1,  colors.HexColor("#888888")),
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#F9F9F9")),
        ("TOPPADDING",    (0, 0), (-1, -1), 10),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 10),
        ("LEFTPADDING",   (0, 0), (-1, -1), 12),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 12),
    ]))
    elements.append(impression_box)
    elements.append(Spacer(1, 12))

    # ── Recommendations ───────────────────────────────────────
    elements.append(Paragraph("<b>Recommendations</b>", section_style))
    for rec in data["recommendations"]:
        elements.append(Paragraph(f"• {rec}", body_style))
    elements.append(Spacer(1, 20))

    # ── Footer ────────────────────────────────────────────────
    def _footer(canvas, _doc):
        canvas.saveState()
        canvas.setFont("Helvetica", 8)
        canvas.drawString(40, 28, "AI-Assisted Report | Not a substitute for professional medical diagnosis")
        canvas.drawRightString(555, 28, f"Page {_doc.page}")
        canvas.restoreState()

    doc.build(elements, onFirstPage=_footer, onLaterPages=_footer)


# ──────────────────────────────────────────────────────────────
# Compatibility wrapper — called by app.py
# ──────────────────────────────────────────────────────────────
def generate_pdf_report(data: dict) -> bytes:
    """
    Accepts the prediction dict from /predict, converts it to the
    generate_alzheimer_report() data contract, and returns PDF bytes.
    """
    # ── Timestamp ─────────────────────────────────────────────
    timestamp = data.get("timestamp", datetime.now().isoformat())
    try:
        date_str = datetime.fromisoformat(timestamp).strftime("%d %B %Y, %H:%M")
    except Exception:
        date_str = timestamp

    # ── Core prediction fields ────────────────────────────────
    prediction     = data.get("prediction", "Unknown")
    top_confidence = data.get("top_confidence", 0.0)
    alzheimer      = data.get("alzheimer_detected", False)
    stage_key      = _resolve_stage_key(prediction.strip().lower())

    # ── Findings (concise, clinical) ──────────────────────────
    findings = [
        f"Diagnosis:  {prediction}",
        f"Confidence: {top_confidence:.1f}%",
        f"Alzheimer indicators: {'Present' if alzheimer else 'Absent'}",
    ]

    # ── Confidence / classification table ────────────────────
    confidence = data.get("confidence", {})
    if not isinstance(confidence, dict) or not confidence:
        confidence = _DEFAULT_CONFIDENCE.copy()

    classification_data = [
        [stage, f"{float(pct):.2f}%", "✓" if stage == prediction else "—"]
        for stage, pct in confidence.items()
    ]

    # ── Scan image: base64 → temp PNG ────────────────────────
    image_path = None
    tmp_path   = None
    image_b64  = data.get("image_b64")
    if image_b64:
        try:
            img_bytes = base64.b64decode(image_b64)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp.write(img_bytes)
                tmp_path = tmp.name
            image_path = tmp_path
        except Exception:
            image_path = None

    # ── Build and return PDF bytes ────────────────────────────
    buf = io.BytesIO()
    generate_alzheimer_report(buf, image_path, {
        "scan_id":             data.get("scan_id", "N/A"),
        "date":                date_str,
        "findings":            findings,
        "classification_data": classification_data,
        "impression":          _IMPRESSIONS[stage_key],
        "recommendations":     _RECOMMENDATIONS[stage_key],
    })

    if tmp_path and os.path.exists(tmp_path):
        os.unlink(tmp_path)

    buf.seek(0)
    return buf.read()