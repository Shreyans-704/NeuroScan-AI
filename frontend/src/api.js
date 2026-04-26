/**
 * api.js — Centralised API client for the Alzheimer Detection backend
 * Base URL is handled by Vite proxy in dev (vite.config.js)
 * or via VITE_API_URL environment variable (production).
 */

import axios from 'axios';

// Base URL: empty string lets Vite's proxy forward /predict and /report to Flask
const BASE_URL = "http://127.0.0.1:5000";

const apiClient = axios.create({
  baseURL: BASE_URL,
  timeout: 60000, // 60s — model inference can be slow
});

/**
 * Upload an MRI/PET scan and get AI prediction.
 * @param {File} file — The image file to analyze.
 * @param {function} onProgress — Optional upload progress callback (0–100).
 * @returns {Promise<Object>} Prediction result JSON.
 */
export async function analyzeScan(file, onProgress) {
  const formData = new FormData();
  formData.append('scan', file);

  const response = await apiClient.post('/predict', formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    onUploadProgress: (evt) => {
      if (onProgress && evt.total) {
        onProgress(Math.round((evt.loaded / evt.total) * 100));
      }
    },
  });

  return response.data;
}

/**
 * Download a PDF report for a given prediction result.
 * Triggers a browser download automatically.
 * @param {Object} predictionData — The full prediction result from analyzeScan().
 */
export async function downloadReport(predictionData) {
  const response = await apiClient.post('/report', predictionData, {
    responseType: 'blob',
  });

  // Construct filename from content-disposition header or fallback
  const contentDisposition = response.headers['content-disposition'] || '';
  const nameMatch = contentDisposition.match(/filename="?([^";\n]+)"?/);
  const fileName = nameMatch ? nameMatch[1] : `AlzheimerReport_${predictionData.scan_id}.pdf`;

  // Trigger browser download
  const url = window.URL.createObjectURL(new Blob([response.data], { type: 'application/pdf' }));
  const link = document.createElement('a');
  link.href = url;
  link.setAttribute('download', fileName);
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(url);
}
