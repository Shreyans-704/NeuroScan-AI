/**
 * ResultsPanel.jsx
 * ────────────────
 * A highly professional, stable, and production-ready medical dashboard UI
 * built specifically for AI-assisted Alzheimer's scanning.
 */

import React, { useEffect, useRef, useState } from 'react';
import { downloadReport } from '../api';

const STAGE_THEMES = {
  'Non-Demented': {
    color: '#34d399',      // Emerald 400
    bg: 'rgba(52, 211, 153, 0.1)',
    border: 'rgba(52, 211, 153, 0.3)',
    icon: '🟢',
    label: 'Normal findings. No significant indications of Alzheimer\'s disease detected.'
  },
  'Very Mild Demented': {
    color: '#fbbf24',      // Amber 400
    bg: 'rgba(251, 191, 36, 0.1)',
    border: 'rgba(251, 191, 36, 0.3)',
    icon: '🟡',
    label: 'Very mild cognitive impairment. Suggests early-stage monitoring is recommended.'
  },
  'Mild Demented': {
    color: '#f97316',      // Orange 500
    bg: 'rgba(249, 115, 22, 0.1)',
    border: 'rgba(249, 115, 22, 0.3)',
    icon: '🟠',
    label: 'Mild cognitive impairment. Clinical evaluation is highly recommended.'
  },
  'Moderate Demented': {
    color: '#f87171',      // Red 400
    bg: 'rgba(248, 113, 113, 0.1)',
    border: 'rgba(248, 113, 113, 0.3)',
    icon: '🔴',
    label: 'Moderate indications of Alzheimer\'s disease detected. Immediate clinical review required.'
  },
  'Unknown': {
    color: '#94a3b8',
    bg: 'rgba(148, 163, 184, 0.1)',
    border: 'rgba(148, 163, 184, 0.3)',
    icon: '❓',
    label: 'Inconclusive scan. Please process a clearer image.'
  }
};

export default function ResultsPanel({ result, onReset }) {
  const [downloading, setDownloading] = useState(false);
  const [barsVisible, setBarsVisible] = useState(false);
  const wrapperRef = useRef(null);

  useEffect(() => {
    // Smoothly animate bars on load
    const timer = setTimeout(() => setBarsVisible(true), 150);
    wrapperRef.current?.scrollIntoView({ behavior: 'smooth', block: 'start' });
    return () => clearTimeout(timer);
  }, []);

  // 🛡️ CRASH SAFETY: 1. Strict Null check
  if (!result || typeof result !== "object") {
    return (
      <div className="card fade-in" style={{ padding: 'var(--spacing-2xl)', textAlign: 'center' }}>
        <h2 style={{ color: 'var(--text-muted)' }}>No valid scan data received.</h2>
        <button className="btn btn-primary mt-md" onClick={onReset}>Return to Upload</button>
      </div>
    );
  }

  // 🛡️ CRASH SAFETY: 2. Fallbacks & normalization for ALL accesses
  const rawPrediction = result.prediction?.toString() || 'Unknown';
  const prediction = STAGE_THEMES[rawPrediction] ? rawPrediction : 'Unknown';

  // Format Confidence mapping
  let normConf = {
    "Non-Demented": 0,
    "Very Mild Demented": 0,
    "Mild Demented": 0,
    "Moderate Demented": 0
  };

  if (result.confidence && typeof result.confidence === 'object') {
    normConf = { ...normConf, ...result.confidence };
  } else if (typeof result.confidence === 'number' || typeof result.confidence === 'string') {
    normConf[prediction] = parseFloat(result.confidence) || 0;
  }

  const topConf = parseFloat(result.top_confidence) || normConf[prediction] || 0;
  const image_b64 = result.image_b64 || null;
  const scan_id = result.scan_id || 'UNKNOWN';

  // Date formatting
  let displayDate = 'N/A';
  try {
    if (result.timestamp) {
      const dt = new Date(result.timestamp);
      if (!isNaN(dt.getTime())) {
        displayDate = dt.toLocaleString('en-GB', {
          day: '2-digit', month: 'short', year: 'numeric',
          hour: '2-digit', minute: '2-digit'
        });
      }
    }
  } catch (e) { }

  const theme = STAGE_THEMES[prediction];

  // ── Handlers ──
  const handleDownloadReport = async () => {
    setDownloading(true);
    try {
      // Compile normalized, validated payload for backend report generation
      const pdfPayload = {
        scan_id: result?.scan_id || "N/A",
        prediction: result?.prediction || "Unknown",
        confidence: result?.confidence || {},
        top_confidence: result?.top_confidence || 0,
        alzheimer_detected: result?.alzheimer_detected || false,
        image_b64: result?.image_b64 || null
      };

      await downloadReport(pdfPayload);
    } catch (err) {
      alert("Failed to download PDF report: " + (err.response?.data?.error || err.message));
    } finally {
      setDownloading(false);
    }
  };

  const maxConfidence = Math.max(0, ...Object.values(normConf));

  return (
    <div ref={wrapperRef} className="fade-in" style={{
      display: 'flex', flexDirection: 'column', gap: 'var(--spacing-xl)', animation: 'fadeSlideUp 0.6s ease'
    }}>

      {maxConfidence < 50 && (
        <div style={{
          background: 'rgba(239, 68, 68, 0.1)',
          border: '1px solid rgba(239, 68, 68, 0.4)',
          color: '#fca5a5',
          padding: 'var(--spacing-lg)',
          borderRadius: 'var(--radius-md)',
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-md)',
          fontWeight: 600,
          boxShadow: '0 4px 12px rgba(239, 68, 68, 0.1)'
        }}>
          <span style={{ fontSize: '1.5rem' }}>⚠️</span>
          Low confidence — image may not be a valid MRI scan. Please verify input.
        </div>
      )}

      {/* ── SECTION 1: PRIMARY DIAGNOSIS CARD ── */}
      <div style={{
        background: theme.bg,
        border: `1px solid ${theme.border}`,
        borderRadius: 'var(--radius-xl)',
        padding: 'var(--spacing-2xl)',
        boxShadow: `0 8px 32px ${theme.bg}`,
        position: 'relative',
        overflow: 'hidden'
      }}>
        <div style={{ position: 'relative', zIndex: 1, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--spacing-lg)' }}>

          {/* Main Title Area */}
          <div style={{ flex: 1, minWidth: 280 }}>
            <div style={{ display: 'inline-block', fontSize: '0.8rem', fontWeight: 600, letterSpacing: '0.1em', textTransform: 'uppercase', color: theme.color, marginBottom: 'var(--spacing-sm)' }}>
              {theme.icon} AI Assessment Result
            </div>
            <h1 style={{ fontFamily: 'var(--font-display)', fontSize: 'clamp(2rem, 4vw, 3rem)', fontWeight: 800, color: '#FFFFFF', lineHeight: 1.1, marginBottom: 'var(--spacing-md)' }}>
              {prediction}
            </h1>
            <p style={{ fontSize: '1rem', color: 'rgba(255,255,255,0.8)', maxWidth: 600, lineHeight: 1.6 }}>
              {theme.label}
            </p>
          </div>

          {/* Large Confidence Circle */}
          <div style={{
            display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center',
            width: 160, height: 160, borderRadius: '50%',
            background: `conic-gradient(${theme.color} ${(topConf / 100) * 360}deg, rgba(255,255,255,0.05) 0deg)`,
            boxShadow: `0 0 40px ${theme.border}`
          }}>
            <div style={{
              width: 130, height: 130, borderRadius: '50%', background: 'var(--color-bg-secondary)',
              display: 'flex', flexDirection: 'column', alignItems: 'center', justifyContent: 'center'
            }}>
              <span style={{ fontSize: '2.5rem', fontWeight: 800, color: '#FFF', fontFamily: 'var(--font-display)', lineHeight: 1 }}>
                {(parseFloat(topConf) || 0).toFixed(1)}<span style={{ fontSize: '1.2rem', color: 'var(--text-muted)' }}>%</span>
              </span>
              <span style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '2px', marginTop: 4 }}>Confidence</span>
            </div>
          </div>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))', gap: 'var(--spacing-xl)' }}>

        {/* ── SECTION 2: CONFIDENCE DISTRIBUTION ── */}
        <div className="card" style={{ padding: 'var(--spacing-xl)' }}>
          <h3 style={{ fontSize: '1.2rem', color: '#FFF', marginBottom: 'var(--spacing-lg)', display: 'flex', alignItems: 'center', gap: '8px' }}>
            <span>📊</span> Probability Distribution
          </h3>

          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' }}>
            {Object.entries(normConf || {}).map(([stageName, val]) => {
              const currentTheme = STAGE_THEMES[stageName];
              const pct = parseFloat(val) || 0;
              const isLead = stageName === prediction;

              return (
                <div key={stageName} style={{ position: 'relative' }}>
                  <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 6, fontSize: '0.85rem' }}>
                    <span style={{ color: isLead ? '#FFF' : 'var(--text-secondary)', fontWeight: isLead ? 600 : 400 }}>
                      {stageName}
                    </span>
                    <span style={{ color: isLead ? currentTheme.color : 'var(--text-muted)', fontWeight: 600, fontFamily: 'monospace' }}>
                      {pct.toFixed(2)}%
                    </span>
                  </div>

                  {/* Progress Bar Track */}
                  <div style={{ height: 10, width: '100%', background: 'var(--color-bg-elevated)', borderRadius: 10, overflow: 'hidden' }}>
                    {/* Progress Bar Fill */}
                    <div style={{
                      height: '100%',
                      background: currentTheme.color,
                      width: barsVisible ? `${pct}%` : '0%',
                      transition: 'width 1.2s cubic-bezier(0.16, 1, 0.3, 1)',
                      borderRadius: 10,
                      boxShadow: isLead ? `0 0 10px ${currentTheme.color}` : 'none'
                    }} />
                  </div>
                </div>
              );
            })}
          </div>
        </div>

        {/* ── SECTION 3: SCAN METADATA & IMAGE ── */}
        <div className="card" style={{ padding: 'var(--spacing-xl)', display: 'flex', flexDirection: 'column', justifyContent: 'space-between' }}>

          <div>
            <h3 style={{ fontSize: '1.2rem', color: '#FFF', marginBottom: 'var(--spacing-lg)', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <span>📷</span> Scan Reference
            </h3>

            {/* Image Box */}
            <div style={{
              background: 'var(--color-bg-elevated)', border: '1px solid var(--color-border)',
              borderRadius: 'var(--radius-md)', padding: 'var(--spacing-sm)',
              display: 'flex', justifyContent: 'center', alignItems: 'center', height: 200, marginBottom: 'var(--spacing-lg)'
            }}>
              {image_b64 ? (
                <img
                  src={`data:image/png;base64,${image_b64}`}
                  alt="Processed MRI/PET"
                  style={{ maxHeight: '100%', maxWidth: '100%', objectFit: 'contain', borderRadius: 4, mixBlendMode: 'screen' }}
                />
              ) : (
                <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem', fontStyle: 'italic' }}>
                  No source image provided by server
                </span>
              )}
            </div>

            {/* Meta tags */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-sm)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 8, borderBottom: '1px solid var(--color-border-subtle)' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Scan Registry ID</span>
                <span style={{ color: '#FFF', fontFamily: 'monospace', fontWeight: 600 }}>{scan_id}</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: 8, borderBottom: '1px solid var(--color-border-subtle)' }}>
                <span style={{ color: 'var(--text-muted)', fontSize: '0.85rem' }}>Processed On</span>
                <span style={{ color: '#FFF', fontSize: '0.85rem' }}>{displayDate}</span>
              </div>
            </div>
          </div>
        </div>
      </div>

      {/* ── SECTION 4: ACTIONS & DISCLAIMER ── */}
      <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-md)' }}>
        <div style={{ display: 'flex', gap: 'var(--spacing-md)', flexWrap: 'wrap' }}>

          <button onClick={handleDownloadReport} disabled={downloading} className="btn" style={{
            background: 'var(--color-bg-card)', border: '1px solid var(--color-border)', color: '#FFF',
            padding: '14px 28px', fontSize: '1rem', fontWeight: 600, flex: 1,
            transition: 'all 0.2s', boxShadow: '0 4px 12px rgba(0,0,0,0.2)'
          }}>
            {downloading ? '⏳ Generating Document...' : '⬇ Download PDF Report'}
          </button>

          <button onClick={onReset} className="btn" style={{
            background: 'linear-gradient(135deg, var(--color-accent), #1d4ed8)',
            color: '#FFF', border: 'none',
            padding: '14px 28px', fontSize: '1rem', fontWeight: 600, flex: 1,
            transition: 'all 0.2s', boxShadow: '0 4px 16px rgba(37,99,235,0.4)'
          }}>
            ↻ Process New Scan
          </button>
        </div>

        <div style={{ padding: '16px', background: 'rgba(239, 68, 68, 0.05)', border: '1px dashed rgba(239, 68, 68, 0.3)', borderRadius: 'var(--radius-md)', color: 'var(--text-secondary)', fontSize: '0.8rem', lineHeight: 1.5 }}>
          <strong style={{ color: '#f87171' }}>Disclaimer:</strong> This software is a supplemental AI analysis tool. It must <b>not</b> be used as a primary diagnostic platform. Always consult a certified neurological physician.
        </div>
      </div>

    </div>
  );
}
