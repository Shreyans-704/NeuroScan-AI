"""
AI-Based Alzheimer Detection System — Flask Backend
=====================================================
Routes:
  GET  /           → Health check
  POST /predict    → Forward image to external model API, return prediction
  POST /report     → Generate PDF report from prediction data
"""
import cv2
import os
import io
import uuid
import base64
import logging
import requests
import numpy as np
from datetime import datetime

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from PIL import Image

from report_generator import generate_pdf_report

# ──────────────────────────────────────────────────────────────
# App setup
# ──────────────────────────────────────────────────────────────
app = Flask(__name__)

# Allow cross-origin requests from the React frontend
CORS(app, origins=["http://localhost:3000", "http://127.0.0.1:3000"])

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Configuration — set your deployed model URL here (or via env)
# ──────────────────────────────────────────────────────────────
EXTERNAL_MODEL_API_URL = os.getenv(
    "MODEL_API_URL",
    "http://localhost:8001/predict",   # ← replace with your real endpoint
)

# Allowed file extensions
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "tiff", "webp"}


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    """Return True if the filename has a permitted extension."""
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def basic_mri_check(img) -> bool:
    try:
        import cv2  # safe import

        np_img = np.array(img)

        # 1. Resolution check
        h, w = np_img.shape[:2]
        if h < 100 or w < 100:
            return False

        # 2. Reject colored images
        if len(np_img.shape) == 3:
            r, g, b = np_img[:,:,0], np_img[:,:,1], np_img[:,:,2]

            if np.mean(np.abs(r - g)) > 5 or np.mean(np.abs(r - b)) > 5:
                return False

       # 3. Edge detection (graphs = high edges)
        gray = cv2.cvtColor(np_img, cv2.COLOR_RGB2GRAY) if len(np_img.shape)==3 else np_img

        # ✅ ADD THIS
        if np.std(gray) < 10:
            return False

        edges = cv2.Canny(gray, 50, 150)

        edge_density = np.sum(edges > 0) / (h * w)

        if edge_density > 0.20:
            return False

        return True

    except Exception as e:
        print("MRI CHECK ERROR:", e)
        return False

def preprocess_image(file_obj) -> tuple[bytes, str]:
    """
    Optionally resize / normalise the uploaded image.
    Returns (raw_bytes, mime_type).
    """
    img = Image.open(file_obj).convert("RGB")

    # Resize to 224×224 (common CNN input) — keeps aspect via thumbnail
    img.thumbnail((224, 224), Image.LANCZOS)

    buf = io.BytesIO()
    img.save(buf, format="PNG")
    buf.seek(0)
    return buf.read(), "image/png"


def encode_image_base64(image_bytes: bytes) -> str:
    """Return base64-encoded string of raw image bytes."""
    return base64.b64encode(image_bytes).decode("utf-8")


# ──────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────
@app.get("/")
def health():
    """Health-check endpoint."""
    return jsonify({"status": "ok", "service": "Alzheimer Detection API", "version": "1.0.0"})


@app.post("/predict")
def predict():
    """
    Receive an MRI/PET scan, forward it to the external model API,
    and return a structured prediction response.

    Expected form-data:
        scan (file) — JPEG or PNG image
    """
    # ── 1. Validate request ───────────────────────────────────
    if "scan" not in request.files:
        return jsonify({"error": "No file part named 'scan' in request."}), 400

    file = request.files["scan"]

    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    if not allowed_file(file.filename):
        return jsonify(
            {"error": f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}
        ), 415

    try:
        # ── 2. Pre-process and early validation ──────────────
        pil_img = Image.open(file)
        
        # Smart validation layer
        if not basic_mri_check(pil_img):
            return jsonify({
                "error": "Invalid scan — please upload a proper MRI brain image"
            }), 400

        # Reset file pointer after PIL reading
        file.seek(0)

        image_bytes, mime_type = preprocess_image(file)
        image_b64 = encode_image_base64(image_bytes)

        scan_id = str(uuid.uuid4())[:8].upper()
        logger.info("Received scan — ID: %s, size: %d bytes", scan_id, len(image_bytes))

        # ── 3. Call external model API ────────────────────────
        response = requests.post(
            EXTERNAL_MODEL_API_URL,
            files={"image": ("scan.png", io.BytesIO(image_bytes), mime_type)},
            timeout=30,
        )
        response.raise_for_status()
        model_data = response.json()

        # ── 4. Parse and validate model response ─────────────
        prediction = model_data.get("prediction", "Unknown")
        confidence = model_data.get("confidence", {})

        # Ensure all four classes are present
        all_classes = ["Non-Demented", "Very Mild Demented", "Mild Demented", "Moderate Demented"]
        for cls in all_classes:
            confidence.setdefault(cls, 0.0)

        top_confidence = confidence.get(prediction, 0.0)
        alzheimer_detected = prediction.lower() != "non-demented"

        # ── 5. Build structured response ─────────────────────
        result = {
            "scan_id": scan_id,
            "timestamp": datetime.now().isoformat(),
            "alzheimer_detected": alzheimer_detected,
            "prediction": prediction,
            "confidence": confidence,
            "top_confidence": round(top_confidence, 2),
            "image_b64": image_b64,          # for frontend preview & PDF
        }

        logger.info(
            "Prediction complete — ID: %s | Result: %s | Confidence: %.1f%%",
            scan_id, prediction, top_confidence,
        )
        return jsonify(result), 200

    except requests.exceptions.ConnectionError:
        logger.error("Cannot reach external model API at %s", EXTERNAL_MODEL_API_URL)
        return jsonify(
            {
                "error": "External model API is unreachable. Please ensure your model server is running.",
                "model_url": EXTERNAL_MODEL_API_URL,
            }
        ), 503

    except requests.exceptions.Timeout:
        logger.error("External model API timed out.")
        return jsonify({"error": "Model API request timed out. Please retry."}), 504

    except requests.exceptions.HTTPError as exc:
        logger.error("Model API returned error: %s", exc)
        return jsonify({"error": f"Model API error: {exc}"}), 502

    except Exception as exc:
        logger.exception("Unexpected error in /predict: %s", exc)
        return jsonify({"error": f"Internal server error: {str(exc)}"}), 500


@app.post("/report")
def report():
    """
    Generate a PDF report from prediction data.

    Expected JSON body:
        {
            "scan_id": "...",
            "timestamp": "...",
            "prediction": "...",
            "confidence": { ... },
            "top_confidence": 94.2,
            "alzheimer_detected": true,
            "image_b64": "..."  (optional)
        }
    """
    data = request.get_json(silent=True)
    if not data:
        return jsonify({"error": "JSON body required."}), 400

    required = ["scan_id", "prediction", "confidence", "top_confidence"]
    missing = [k for k in required if k not in data]
    if missing:
        return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

    try:
        pdf_bytes = generate_pdf_report(data)
        filename = f"AlzheimerReport_{data['scan_id']}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    except Exception as exc:
        logger.exception("Error generating PDF: %s", exc)
        return jsonify({"error": f"PDF generation failed: {str(exc)}"}), 500


# ──────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logger.info("Starting Alzheimer Detection Backend on port %d", port)
    app.run(host="0.0.0.0", port=port, debug=True)
