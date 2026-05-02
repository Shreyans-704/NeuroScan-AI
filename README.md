# 🧠 NeuroScan AI — Alzheimer Detection System

An end-to-end AI-assisted Alzheimer's disease detection web application for healthcare professionals. Upload MRI/PET brain scans and receive instant AI-powered predictions, confidence visualizations, intelligent validation feedback, and downloadable medical-grade reports.

```bash
NeuroScan-AI/
│
├── backend/
│   ├── app.py                  # Flask API (prediction + report)
│   ├── report_generator.py     # PDF generation (ReportLab)
│   ├── requirements.txt        # Python dependencies
│   ├── models/
│   │   ├── .gitkeep            # Keeps folder tracked
│   │   └── README.md           # Model download instructions
│   ├── utils/
│   │   └── image_processing.py # (optional)
│   ├── config.py
│   └── .env.example
│
├── frontend/
│   ├── public/
│   │   └── index.html
│   ├── src/
│   │   ├── App.jsx
│   │   ├── main.jsx
│   │   ├── index.css
│   │   ├── api.js
│   │   ├── components/
│   │   │   ├── Navbar.jsx
│   │   │   ├── UploadZone.jsx
│   │   │   ├── AnalyzingSpinner.jsx
│   │   │   ├── ConfidenceChart.jsx
│   │   │   └── ResultsPanel.jsx
│   │   └── assets/
│   └── package.json
│
├── docs/
│   ├── screenshots/
│   │   ├── upload.png
│   │   ├── result.png
│   │   └── report.png
│   └── architecture.md
│
├── .gitignore
├── README.md
└── LICENSE
```

## 🛠 Prerequisites

| Tool    | Version |
| ------- | ------- |
| Node.js | ≥ 18.x  |
| Python  | ≥ 3.10  |
| pip     | latest  |

---

## 🚀 Running Locally

## PREVIEW : -
<img width="1915" height="878" alt="image" src="https://github.com/user-attachments/assets/fedc0539-7092-4aaa-b6ee-930708212015" />
<img width="1224" height="795" alt="image" src="https://github.com/user-attachments/assets/b282f634-ffd3-40b3-8dfe-92086ebe7925" />
<img width="1107" height="542" alt="image" src="https://github.com/user-attachments/assets/ccf80adf-e129-4fb6-b53b-c855538d9193" />
<img width="1919" height="832" alt="image" src="https://github.com/user-attachments/assets/64bfd01f-9aeb-4599-92a3-7d903c189258" />



## REPORT PREVIEW : - 
<img width="659" height="743" alt="image" src="https://github.com/user-attachments/assets/d4e09ce7-4d3f-487d-a31e-8954ecd6325a" />
<img width="651" height="421" alt="image" src="https://github.com/user-attachments/assets/ab1586e8-b74d-4ed5-826e-924ed36c2835" />




## 🔗 API Reference

### ✅ `GET /`

Health check

```json
{
  "status": "ok",
  "service": "Alzheimer Detection API",
  "version": "1.0.0"
}
```

---

### 🧠 `POST /predict`

Upload MRI/PET scan for analysis.

**Request:** `multipart/form-data`

| Field | Type       | Required |
| ----- | ---------- | -------- |
| scan  | Image file | ✅        |

---

### 🔍 Smart Validation Layer (NEW 🔥)

Before model inference, the backend now performs:

* ✅ Resolution check
* ✅ Grayscale consistency check
* ✅ Edge density analysis (reject graphs/screenshots)
* ✅ Noise/variance check

👉 Invalid images return:

```json
{
  "error": "Invalid scan — please upload a proper MRI brain image"
}
```

---

### ✅ Successful Response

```json
{
  "scan_id": "A1B2C3D4",
  "timestamp": "2026-04-26T18:30:00",
  "alzheimer_detected": true,
  "prediction": "Mild Demented",
  "confidence": {
    "Non-Demented": 2.1,
    "Very Mild Demented": 5.3,
    "Mild Demented": 89.4,
    "Moderate Demented": 3.2
  },
  "top_confidence": 89.4,
  "image_b64": "<base64>"
}
```

---

### 📄 `POST /report`

Generate downloadable medical report.

**Input:** Same JSON as `/predict`

**Output:** PDF file download

---

## 📄 PDF Report Features (UPDATED)

* 🏥 Clinical-style formatting
* 📊 Confidence distribution visualization
* 🧠 Prediction summary
* 📸 Embedded MRI scan
* 📋 Scan metadata (ID, timestamp)
* 💊 Clinical recommendations (stage-based)
* ⚠️ Medical disclaimer

---

## 🧠 Classification Stages

| Stage              | Meaning                 | Indicator |
| ------------------ | ----------------------- | --------- |
| Non-Demented       | No Alzheimer’s detected | 🟢        |
| Very Mild Demented | Early signs             | 🟡        |
| Mild Demented      | Cognitive impairment    | 🟠        |
| Moderate Demented  | Advanced stage          | 🔴        |

---

## ⚠️ Error Handling (NEW)

| Scenario       | Response               |
| -------------- | ---------------------- |
| Invalid image  | 400 + validation error |
| Model offline  | 503                    |
| Timeout        | 504                    |
| Internal error | 500                    |

👉 No more blank screens — frontend shows proper messages.

---

## 🧩 Technologies

| Layer    | Stack                  |
| -------- | ---------------------- |
| Frontend | React (Vite), Chart.js |
| Backend  | Flask, Pillow, OpenCV  |
| PDF      | reportlab              |
| API      | axios                  |

---

## ⚠️ Disclaimer

> This system is an AI-assisted clinical support tool.
> It must NOT be used for final diagnosis.
> Always consult a certified neurologist.

---

## 🚀 Key Features (FINAL)

* 🧠 AI-based Alzheimer detection
* 📤 Drag-and-drop scan upload
* ⚡ Real-time analysis pipeline
* 🛡️ Smart MRI validation (prevents fake inputs)
* 📊 Confidence visualization
* 📄 Medical-grade PDF report
* ❌ Robust error handling (no crashes)

---

## 🧠 Future Improvements

* CNN-based MRI validation (instead of rule-based)
* Cloud deployment (AWS / Render / Vercel)
* Patient history tracking
* Multi-scan comparison

---

## 👨‍💻 Author

Shreyans Jaiswal (23124103) 
<br>
Abhinoor Tayal (23124003)
<br>
Parav Sharma (23124072)

---

## ⭐ If you like this project

Give it a ⭐ on GitHub and use it in your portfolio!

#Frontend
cd "c:\Users\shrey\OneDrive\Desktop\CODING\NeuroScan AI\frontend"
npm run dev

#Backend
cd "c:\Users\shrey\OneDrive\Desktop\CODING\NeuroScan AI\backend"
python app.py

