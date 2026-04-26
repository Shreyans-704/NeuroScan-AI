/**
 * Navbar.jsx — Top navigation bar
 */

import React from 'react';

export default function Navbar() {
  return (
    <nav className="navbar">
      <div className="navbar-brand">
        <div className="navbar-logo" aria-hidden="true">🧠</div>
        <div>
          <div className="navbar-title">NeuroScan AI</div>
          <div className="navbar-subtitle">Alzheimer Detection System</div>
        </div>
      </div>

      <div className="navbar-badge">
        <span className="status-dot" />
        AI System Online
      </div>
    </nav>
  );
}
