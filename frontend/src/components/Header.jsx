import React from 'react'
import './Header.css'

export default function Header() {
  return (
    <header className="header">
      <div className="container header-inner">
        <div className="header-brand">
          <div className="brand-icon">
            <svg width="22" height="22" viewBox="0 0 24 24" fill="none">
              <path d="M9 12l2 2 4-4" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"/>
              <path d="M21 12a9 9 0 11-18 0 9 9 0 0118 0z" stroke="currentColor" strokeWidth="2" strokeLinecap="round"/>
            </svg>
          </div>
          <span className="brand-name">ResumeAI <span className="brand-tag">Evaluator</span></span>
        </div>
        <div className="header-pill">
          <span className="status-dot" />
          Gemini 2.5 Flash
        </div>
      </div>
    </header>
  )
}
