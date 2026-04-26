/**
 * AnalyzingSpinner.jsx
 * ────────────────────
 * Animated loading overlay shown during AI inference.
 * Cycles through descriptive step labels for transparency.
 */

import React, { useEffect, useState } from 'react';

const STEPS = [
  { label: 'Uploading scan to server…',       duration: 2000 },
  { label: 'Preprocessing image…',            duration: 1500 },
  { label: 'Sending to AI model API…',        duration: 3000 },
  { label: 'Running neural network inference…', duration: 4000 },
  { label: 'Calculating confidence scores…',  duration: 2000 },
  { label: 'Preparing results…',              duration: 1000 },
];

export default function AnalyzingSpinner() {
  const [currentStep, setCurrentStep] = useState(0);

  useEffect(() => {
    let step  = 0;
    let timer = null;

    const advance = () => {
      step++;
      if (step < STEPS.length) {
        setCurrentStep(step);
        timer = setTimeout(advance, STEPS[step].duration);
      }
    };

    timer = setTimeout(advance, STEPS[0].duration);
    return () => clearTimeout(timer);
  }, []);

  return (
    <div className="card fade-in">
      <div className="spinner-overlay">

        {/* Pulsing ring */}
        <div style={{ position: 'relative', width: 80, height: 80 }}>
          {/* Outer pulse rings */}
          <div style={{
            position: 'absolute', inset: 0, borderRadius: '50%',
            border: '2px solid var(--color-accent)',
            animation: 'pulse-ring 1.8s ease-out infinite',
          }} />
          <div style={{
            position: 'absolute', inset: 0, borderRadius: '50%',
            border: '2px solid var(--color-accent)',
            animation: 'pulse-ring 1.8s ease-out 0.6s infinite',
          }} />
          {/* Spinning inner loader */}
          <div className="spinner-ring" style={{
            position: 'absolute', inset: 8, width: 'auto', height: 'auto',
          }} />
          {/* Brain icon */}
          <div style={{
            position: 'absolute', inset: 0,
            display: 'flex', alignItems: 'center', justifyContent: 'center',
            fontSize: 22,
          }}>
            🧠
          </div>
        </div>

        {/* Headline */}
        <div style={{ textAlign: 'center' }}>
          <div style={{
            fontFamily: 'var(--font-display)',
            fontSize: '1.15rem',
            fontWeight: 700,
            color: 'var(--text-primary)',
            marginBottom: 4,
          }}>
            AI Analysis in Progress
          </div>
          <div style={{ fontSize: '0.85rem', color: 'var(--text-muted)' }}>
            Please wait — do not close this window
          </div>
        </div>

        {/* Step list */}
        <div className="spinner-steps">
          {STEPS.map((step, i) => (
            <div
              key={step.label}
              className={`spinner-step${i <= currentStep ? ' active' : ''}`}
            >
              <div className="spinner-step-dot" />
              <span style={{ opacity: i > currentStep ? 0.35 : 1 }}>
                {i < currentStep ? '✓ ' : ''}{step.label}
              </span>
            </div>
          ))}
        </div>

      </div>
    </div>
  );
}
