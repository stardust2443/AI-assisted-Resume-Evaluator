import React from 'react'
import './LoadingScreen.css'

const STEPS = [
  { label: 'Extracting text from document', icon: '📄' },
  { label: 'Parsing resume structure',      icon: '🔍' },
  { label: 'Analyzing job requirements',    icon: '📋' },
  { label: 'Scoring against rubric',        icon: '⚖️' },
  { label: 'Verifying evidence quotes',     icon: '✅' },
  { label: 'Generating SWOT & insights',    icon: '💡' },
]

export default function LoadingScreen({ step = 0 }) {
  return (
    <div className="loading-screen fade-in">
      <div className="loading-inner">
        <div className="loading-spinner">
          <svg width="64" height="64" viewBox="0 0 64 64" fill="none">
            <circle cx="32" cy="32" r="26" stroke="rgba(79,142,247,0.15)" strokeWidth="6"/>
            <path d="M32 6a26 26 0 0 1 26 26" stroke="url(#spin-grad)" strokeWidth="6" strokeLinecap="round"/>
            <defs>
              <linearGradient id="spin-grad" x1="0" y1="0" x2="64" y2="64" gradientUnits="userSpaceOnUse">
                <stop stopColor="#4f8ef7"/>
                <stop offset="1" stopColor="#9b6dff"/>
              </linearGradient>
            </defs>
          </svg>
        </div>
        <h2 className="loading-title">Evaluating Candidate</h2>
        <p className="loading-sub">Running AI analysis — this takes 30–60 seconds</p>

        <div className="loading-steps">
          {STEPS.map((s, i) => (
            <div key={i} className={`loading-step ${i < step ? 'done' : i === step ? 'active' : ''}`}>
              <span className="step-icon">{i < step ? '✓' : s.icon}</span>
              <span className="step-label">{s.label}</span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
