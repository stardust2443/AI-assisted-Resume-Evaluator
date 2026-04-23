import React from 'react'
import './SwotGrid.css'

const QUADRANTS = [
  { key: 'strengths',    label: 'Strengths',    icon: '💪', cls: 'swot-s', accent: '#22d3a5' },
  { key: 'weaknesses',   label: 'Weaknesses',   icon: '⚠️', cls: 'swot-w', accent: '#ff5370' },
  { key: 'opportunities',label: 'Opportunities',icon: '🚀', cls: 'swot-o', accent: '#4f8ef7' },
  { key: 'threats',      label: 'Threats',      icon: '🛡️', cls: 'swot-t', accent: '#f5a623' },
]

export default function SwotGrid({ swot }) {
  return (
    <div className="swot-grid">
      {QUADRANTS.map(q => (
        <div key={q.key} className={`swot-cell ${q.cls}`}>
          <div className="swot-header">
            <span className="swot-icon">{q.icon}</span>
            <span className="swot-label" style={{ color: q.accent }}>{q.label}</span>
          </div>
          <ul className="swot-list">
            {(swot[q.key] || []).map((item, i) => (
              <li key={i} className="swot-item">
                <span className="swot-bullet" style={{ background: q.accent }} />
                {item}
              </li>
            ))}
          </ul>
        </div>
      ))}
    </div>
  )
}
