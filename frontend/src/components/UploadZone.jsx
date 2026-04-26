/**
 * UploadZone.jsx
 * ─────────────
 * Drag-and-drop + click-to-browse file upload zone.
 * Previews the image, validates format, triggers analysis.
 */

import React, { useCallback, useRef, useState } from 'react';

// Accepted MIME types
const ACCEPTED_TYPES = ['image/jpeg', 'image/png', 'image/bmp', 'image/tiff', 'image/webp'];
const ACCEPTED_EXT   = '.jpg, .jpeg, .png, .bmp, .tiff, .webp';

export default function UploadZone({ onAnalyze, isLoading }) {
  const [file, setFile]         = useState(null);
  const [preview, setPreview]   = useState(null);
  const [dragActive, setDrag]   = useState(false);
  const [fileError, setError]   = useState(null);
  const inputRef                = useRef(null);

  // ── Validate & load file ──────────────────────────────────
  const handleFile = useCallback((incoming) => {
    setError(null);

    if (!incoming) return;

    if (!ACCEPTED_TYPES.includes(incoming.type)) {
      setError(`Unsupported file type: ${incoming.type || 'unknown'}. Please upload JPEG or PNG.`);
      return;
    }

    if (incoming.size > 20 * 1024 * 1024) {
      setError('File too large. Maximum size is 20 MB.');
      return;
    }

    setFile(incoming);

    // Generate preview URL
    const url = URL.createObjectURL(incoming);
    setPreview(url);
  }, []);

  // ── Input change ──────────────────────────────────────────
  const handleInputChange = (e) => {
    handleFile(e.target.files?.[0] ?? null);
  };

  // ── Drag events ───────────────────────────────────────────
  const handleDragOver  = (e) => { e.preventDefault(); setDrag(true); };
  const handleDragLeave = (e) => { e.preventDefault(); setDrag(false); };
  const handleDrop      = (e) => {
    e.preventDefault();
    setDrag(false);
    handleFile(e.dataTransfer.files?.[0] ?? null);
  };

  // ── Reset ─────────────────────────────────────────────────
  const handleReset = () => {
    setFile(null);
    if (preview) URL.revokeObjectURL(preview);
    setPreview(null);
    setError(null);
    if (inputRef.current) inputRef.current.value = '';
  };

  const fileSizeLabel = file
    ? file.size > 1024 * 1024
      ? `${(file.size / 1024 / 1024).toFixed(1)} MB`
      : `${(file.size / 1024).toFixed(0)} KB`
    : '';

  return (
    <div className="card fade-in">
      {/* Card header */}
      <div className="card-header">
        <div className="card-icon">📤</div>
        <div>
          <div className="card-title">Upload MRI / PET Scan</div>
        </div>
      </div>

      <div className="card-body" style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-lg)' }}>

        {/* ── Upload zone (shown when no file) ─── */}
        {!preview && (
          <div
            className={`upload-zone${dragActive ? ' drag-active' : ''}`}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            onClick={() => inputRef.current?.click()}
            role="button"
            tabIndex={0}
            aria-label="Upload MRI or PET scan image"
            onKeyDown={(e) => e.key === 'Enter' && inputRef.current?.click()}
          >
            <div className="upload-icon-ring">🧠</div>
            <div className="upload-heading">Drop your scan here</div>
            <div className="upload-sub">or click to browse your files</div>
            <div className="upload-formats">
              {['JPG', 'PNG', 'BMP', 'TIFF', 'WebP'].map((fmt) => (
                <span key={fmt} className="format-badge">{fmt}</span>
              ))}
            </div>
            <input
              ref={inputRef}
              type="file"
              accept={ACCEPTED_EXT}
              onChange={handleInputChange}
              style={{ display: 'none' }}
              id="scan-upload-input"
              aria-hidden="true"
            />
          </div>
        )}

        {/* ── Error message ─── */}
        {fileError && (
          <div className="error-box">
            <span className="error-icon">⚠️</span>
            <div>
              <div className="error-title">Upload Error</div>
              <div className="error-message">{fileError}</div>
            </div>
          </div>
        )}

        {/* ── Preview ─── */}
        {preview && (
          <div className="fade-in">
            <div className="preview-container">
              <img
                src={preview}
                alt="Uploaded MRI scan preview"
                className="preview-image"
              />
              <div className="preview-overlay">
                <span className="preview-badge">{file?.name}</span>
                <span className="preview-badge">{fileSizeLabel}</span>
              </div>
            </div>

            {/* Action buttons */}
            <div style={{
              display: 'flex',
              gap: 'var(--spacing-md)',
              marginTop: 'var(--spacing-lg)',
              flexWrap: 'wrap',
            }}>
              <button
                id="analyze-btn"
                className="btn btn-primary btn-lg"
                style={{ flex: 1, minWidth: 160 }}
                onClick={() => onAnalyze(file)}
                disabled={isLoading}
                aria-label="Analyze uploaded scan with AI"
              >
                {isLoading ? (
                  <>
                    <span className="spinner-ring" style={{ width: 20, height: 20, borderWidth: 2 }} />
                    Analyzing…
                  </>
                ) : (
                  <>🔍 Analyze Scan</>
                )}
              </button>

              <button
                id="reset-btn"
                className="btn btn-danger"
                onClick={handleReset}
                disabled={isLoading}
                aria-label="Remove selected scan"
              >
                ✕ Remove
              </button>

              <button
                id="change-scan-btn"
                className="btn btn-secondary"
                onClick={() => inputRef.current?.click()}
                disabled={isLoading}
                aria-label="Choose a different scan"
              >
                ↑ Change
                <input
                  ref={inputRef}
                  type="file"
                  accept={ACCEPTED_EXT}
                  onChange={handleInputChange}
                  style={{ display: 'none' }}
                  aria-hidden="true"
                />
              </button>
            </div>
          </div>
        )}

        {/* ── Info note ─── */}
        <div style={{
          display: 'flex',
          alignItems: 'center',
          gap: 'var(--spacing-sm)',
          padding: 'var(--spacing-sm) var(--spacing-md)',
          background: 'var(--color-bg-secondary)',
          borderRadius: 'var(--radius-sm)',
          border: '1px solid var(--color-border-subtle)',
        }}>
          <span style={{ fontSize: 14 }}>🔒</span>
          <span style={{ fontSize: '0.78rem', color: 'var(--text-muted)' }}>
            Scans are processed securely and not stored permanently.
          </span>
        </div>

      </div>
    </div>
  );
}
