"""
app.py — NeuroScan AI Backend
==============================
Pipeline: Upload Image → ResNet-18 Prediction → PDF Report → Download

Routes:
  GET  /health   → Health check
  POST /predict  → Run model, generate and return PDF
"""

import io
import os
import uuid
import base64
import logging
from datetime import datetime

import torch
import torch.nn as nn
from torchvision import transforms, models
from PIL import Image

from flask import Flask, request, jsonify, send_file
from flask_cors import CORS

from report_generator import generate_pdf_report

# ──────────────────────────────────────────────────────────────
# Logging
# ──────────────────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

# ──────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────
CLASSES = ["Non-Demented", "Very Mild Demented", "Mild Demented", "Moderate Demented"]
MODEL_PATH = os.path.join(os.path.dirname(__file__), "models", "best_model.pth.tar")
ALLOWED_EXTENSIONS = {"jpg", "jpeg", "png", "bmp", "tiff", "webp"}

# ──────────────────────────────────────────────────────────────
# Model — loaded once at startup
# ──────────────────────────────────────────────────────────────
def _load_model() -> nn.Module:
    """Load ResNet-18 with custom 4-class head from a .pth.tar checkpoint."""
    model = models.resnet18(weights=None)

    # Rebuild the custom FC head that matches training architecture
    in_features = model.fc.in_features
    model.fc = nn.Sequential(
        nn.Linear(in_features, 512),
        nn.ReLU(),
        nn.Dropout(0.7),
        nn.Linear(512, len(CLASSES)),
    )

    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(
            f"Model weights not found at '{MODEL_PATH}'. "
            "Place best_model.pth.tar inside backend/models/."
        )

    checkpoint = torch.load(MODEL_PATH, map_location="cpu", weights_only=False)
    state_dict = checkpoint["state_dict"]

# Remove "model." prefix
    new_state_dict = {}
    for k, v in state_dict.items():
        new_key = k.replace("model.", "")
        new_state_dict[new_key] = v

    model.load_state_dict(new_state_dict)
    model.eval()
    logger.info("ResNet-18 checkpoint loaded from %s", MODEL_PATH)
    return model


try:
    MODEL = _load_model()
except FileNotFoundError as _err:
    logger.error("⚠  %s", _err)
    MODEL = None  # app still starts; /predict will return 503 gracefully


# ──────────────────────────────────────────────────────────────
# Preprocessing transform
# ──────────────────────────────────────────────────────────────
_TRANSFORM = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(
        mean=[0.485, 0.456, 0.406],
        std=[0.229, 0.224, 0.225]
    )
])

# ──────────────────────────────────────────────────────────────
# Flask app
# ──────────────────────────────────────────────────────────────
app = Flask(__name__)
CORS(app, origins=["http://localhost:3000", "http://localhost:5173",
                   "http://127.0.0.1:3000", "http://127.0.0.1:5173"])


# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────
def allowed_file(filename: str) -> bool:
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def preprocess(pil_image: Image.Image) -> torch.Tensor:
    """Convert a PIL image to a (1, 3, 224, 224) CPU tensor."""
    rgb = pil_image.convert("RGB")
    tensor = _TRANSFORM(rgb)          # (3, 224, 224)
    return tensor.unsqueeze(0)        # (1, 3, 224, 224)


def predict(tensor: torch.Tensor) -> tuple[str, float, dict]:
    """
    Run inference and return (predicted_class, confidence_pct, full_confidence_dict).
    """
    with torch.no_grad():
        logits = MODEL(tensor)                        # (1, 4)
        probs  = torch.softmax(logits, dim=1)[0]      # (4,)

    confidence = {cls: round(float(probs[i]) * 100, 2) for i, cls in enumerate(CLASSES)}
    predicted_class  = max(confidence, key=confidence.get)
    confidence_score = confidence[predicted_class]
    return predicted_class, confidence_score, confidence


def image_to_base64(pil_image: Image.Image) -> str:
    """Encode a PIL image as a base64 PNG string."""
    buf = io.BytesIO()
    pil_image.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    return base64.b64encode(buf.read()).decode("utf-8")

import numpy as np
import cv2

def is_valid_mri(image: Image.Image) -> bool:
    img = np.array(image.convert("L"))

    # Too bright → likely document/screenshot
    if np.mean(img) > 200:
        return False

    # Too dark
    if np.mean(img) < 20:
        return False

    # Edge density (MRI has structure)
    edges = cv2.Canny(img, 50, 150)
    edge_density = np.sum(edges > 0) / edges.size

    if edge_density < 0.02:
        return False

    # Low variation → reject
    if img.std() < 15:
        return False

    return True

# ──────────────────────────────────────────────────────────────
# Routes
# ──────────────────────────────────────────────────────────────
@app.get("/health")
def health():
    return jsonify({
        "status": "ok",
        "model_loaded": MODEL is not None,
        "service": "NeuroScan AI",
        "version": "2.0.0",
    })


@app.post("/predict")
def predict_route():
    """
    Accept an MRI image, run ResNet-18 inference,
    generate a PDF report, and return it as a download.
    """
    # ── 1. Model readiness ────────────────────────────────────
    if MODEL is None:
        return jsonify({"error": "Model not loaded. Place resnet18.pth in backend/models/."}), 503

    # ── 2. Validate upload ────────────────────────────────────
    if "scan" not in request.files:
        return jsonify({"error": "No file uploaded. Use field name 'scan'."}), 400

    file = request.files["scan"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": f"Unsupported file type. Allowed: {', '.join(ALLOWED_EXTENSIONS)}"}), 415

    try:
        # ── 3. Load image ─────────────────────────────────────
        pil_image = Image.open(file.stream)
        # 🚫 Reject non-MRI images
        if not is_valid_mri(pil_image):
            return jsonify({
                "error": "Invalid scan. Please upload a valid brain MRI image."
            }), 400

        # ── 4. Preprocess + inference ─────────────────────────
        tensor = preprocess(pil_image)
        predicted_class, confidence_score, confidence = predict(tensor)
        alzheimer_detected = predicted_class.lower() != "non-demented"

        scan_id = str(uuid.uuid4())[:8].upper()
        logger.info("Scan %s → %s (%.1f%%)", scan_id, predicted_class, confidence_score)

        # ── 5. Build data dict ────────────────────────────────
        data = {
            "scan_id":            scan_id,
            "timestamp":          datetime.now().isoformat(),
            "prediction":         predicted_class,
            "confidence":         confidence,
            "top_confidence":     confidence_score,
            "alzheimer_detected": alzheimer_detected,
            "image_b64":          image_to_base64(pil_image),
        }

        # ── 6. Generate PDF ───────────────────────────────────
        
        return jsonify(data)

        # ── 7. Return PDF as download ─────────────────────────
        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    except Exception as exc:
        logger.exception("Error in /predict: %s", exc)
        return jsonify({"error": f"Internal server error: {str(exc)}"}), 500


@app.post("/report")
def report_route():
    try:
        data = request.get_json()

        if not data:
            return jsonify({"error": "No data provided"}), 400

        pdf_bytes = generate_pdf_report(data)

        filename = f"NeuroScan_{data.get('scan_id', 'report')}.pdf"

        return send_file(
            io.BytesIO(pdf_bytes),
            mimetype="application/pdf",
            as_attachment=True,
            download_name=filename,
        )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ──────────────────────────────────────────────────────────────
# Entry point
# ──────────────────────────────────────────────────────────────
if __name__ == "__main__":
    port = int(os.getenv("PORT", 5000))
    logger.info("Starting NeuroScan AI backend on port %d", port)
    app.run(host="0.0.0.0", port=port, debug=True)
