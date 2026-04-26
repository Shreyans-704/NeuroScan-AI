/**
 * App.jsx — FIXED VERSION (VALIDATION + CORRECT ERRORS)
 */

import React, { useState, useCallback } from 'react';
import Navbar from './components/Navbar';
import UploadZone from './components/UploadZone';
import AnalyzingSpinner from './components/AnalyzingSpinner';
import ResultsPanel from './components/ResultsPanel';
import { analyzeScan } from './api';

const PHASE = {
  UPLOAD: 'upload',
  LOADING: 'loading',
  RESULTS: 'results',
};

export default function App() {
  const [phase, setPhase] = useState(PHASE.UPLOAD);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  // ✅ MRI VALIDATION FUNCTION
  const isValidScan = (file) => {
    if (!file) return false;

    const validTypes = ["image/jpeg", "image/png", "image/jpg"];
    if (!validTypes.includes(file.type)) return false;

    // reject very small/random files
    if (file.size < 5000) return false;

    return true;
  };

  // ── Analyze scan ──────────────────────────────────────────
  const handleAnalyze = useCallback(async (file) => {
    setError(null);

    // ✅ VALIDATION FIRST
    if (!isValidScan(file)) {
      setError("⚠️ Please upload a valid MRI/PET scan image (JPG/PNG only)");
      return;
    }

    setPhase(PHASE.LOADING);

    try {
      const data = await analyzeScan(file);
      setResult(data);
      setPhase(PHASE.RESULTS);
    } catch (err) {
      // ✅ PROPER ERROR HANDLING
      let message = "⚠️ Something went wrong";

      if (err.response) {
        // backend responded
        message = err.response.data?.error || "⚠️ Invalid scan or server error";
      } else if (err.request) {
        // no response from backend
        message = "⚠️ Cannot connect to backend server (check Flask)";
      } else {
        message = err.message;
      }

      setError(message);
      setPhase(PHASE.UPLOAD);
    }
  }, []);

  // ── Reset ────────────────────────────────────────────────
  const handleReset = useCallback(() => {
    setResult(null);
    setError(null);
    setPhase(PHASE.UPLOAD);
  }, []);

  return (
    <div className="app-wrapper">
      <Navbar />

      <main className="main-content">

        {/* HERO */}
        {phase === PHASE.UPLOAD && (
          <section className="hero-section fade-in">
            <h1 className="hero-title">
              AI-Powered Alzheimer's Detection System
            </h1>
            <p className="hero-description">
              Upload MRI/PET scan for instant AI analysis
            </p>
          </section>
        )}

        {/* ERROR */}
        {error && phase === PHASE.UPLOAD && (
          <div className="error-box">
            <div className="error-title">⚠️ Analysis Failed</div>
            <div className="error-message">{error}</div>
          </div>
        )}

        {/* UPLOAD */}
        {phase === PHASE.UPLOAD && (
          <UploadZone onAnalyze={handleAnalyze} />
        )}

        {/* LOADING */}
        {phase === PHASE.LOADING && <AnalyzingSpinner />}

        {/* RESULTS */}
        {phase === PHASE.RESULTS && (
          <ResultsPanel result={result} onReset={handleReset} />
        )}

      </main>

      <footer className="app-footer">
        <p>
          NeuroScan AI · For research and clinical support use only
        </p>
      </footer>
    </div>
  );
}