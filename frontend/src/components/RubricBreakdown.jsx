import React, { useEffect, useRef } from 'react'
import './RubricBreakdown.css'

const SECTIONS = [
  { key: 'skill_match',          label: 'Skill Match',          max: 25, color: '#4f8ef7' },
  { key: 'experience_depth',     label: 'Experience Depth',     max: 35, color: '#9b6dff' },
  { key: 'role_alignment',       label: 'Role Alignment',       max: 30, color: '#22d3a5' },
  { key: 'additional_strengths', label: 'Additional Strengths', max: 10, color: '#f5a623' },
]

function RubricBar({ section, data }) {
  const barRef = useRef(null)
  const pct = Math.round((data.score / section.max) * 100)

  useEffect(() => {
    const bar = barRef.current
    if (!bar) return
    bar.style.width = '0%'
    const t = setTimeout(() => { bar.style.width = pct + '%' }, 100)
    return () => clearTimeout(t)
  }, [pct])

  return (
    <div className="rubric-row">
      <div className="rubric-meta">
        <span className="rubric-label">{section.label}</span>
        <span className="rubric-score" style={{ color: section.color }}>
          {data.score}<span className="rubric-max">/{section.max}</span>
        </span>
      </div>

      <div className="rubric-track">
        <div
          ref={barRef}
          className="rubric-fill"
          style={{
            background: section.color,
            boxShadow: `0 0 12px ${section.color}60`,
            transition: 'width 1s cubic-bezier(0.4,0,0.2,1)',
          }}
        />
      </div>

      <p className="rubric-reasoning">{data.reasoning}</p>

      {data.evidence_quotes?.length > 0 && (
        <div className="rubric-quotes">
          {data.evidence_quotes.slice(0, 3).map((q, i) => (
            <div key={i} className="quote-block">"{q}"</div>
          ))}
        </div>
      )}

      {data.flagged_unverified && (
        <div className="rubric-flag">⚠ Some evidence quotes could not be verified in the resume text</div>
      )}
    </div>
  )
}

export default function RubricBreakdown({ evaluation }) {
  return (
    <div className="rubric-breakdown">
      <h3 className="rubric-title">Rubric Breakdown</h3>
      <div className="rubric-list">
        {SECTIONS.map(s => (
          <RubricBar key={s.key} section={s} data={evaluation[s.key]} />
        ))}
      </div>
    </div>
  )
}
