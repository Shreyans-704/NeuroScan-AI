"""
mock_model_server.py
═════════════════════
A lightweight Flask mock server that simulates your deployed
deep learning model API for local development/testing purposes.

Accepts: POST /predict  (multipart/form-data with `image` field)
Returns: JSON prediction response

Run with:
    python mock_model_server.py
"""

import io
import random
from flask import Flask, request, jsonify

app = Flask(__name__)

CLASSES = ["Non-Demented", "Very Mild Demented", "Mild Demented", "Moderate Demented"]


@app.post("/predict")
def predict():
    if "image" not in request.files:
        return jsonify({"error": "No image provided"}), 400

    # Simulate random prediction (replace with real model call)
    # In production this would run your PyTorch / TensorFlow model
    weights = [random.random() for _ in CLASSES]
    total   = sum(weights)
    probs   = {cls: round((w / total) * 100, 2) for cls, w in zip(CLASSES, weights)}

    predicted = max(probs, key=probs.get)

    return jsonify({
        "prediction": predicted,
        "confidence": probs,
    })


if __name__ == "__main__":
    print("=" * 55)
    print("  Mock Alzheimer Model Server")
    print("  Listening on http://localhost:8001")
    print("=" * 55)
    app.run(host="0.0.0.0", port=8001, debug=False)
