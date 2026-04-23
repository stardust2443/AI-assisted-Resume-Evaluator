import React from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import ScoreRing from '../components/ScoreRing'
import RubricBreakdown from '../components/RubricBreakdown'
import SwotGrid from '../components/SwotGrid'
import './Results.css'

export default function Results() {
  const { state } = useLocation()
  const navigate  = useNavigate()
  const report    = state?.report

  if (!report) {
    return (
      <div className="container" style={{ padding: '80px 24px', textAlign: 'center' }}>
        <h2>No results found.</h2>
        <button className="btn btn-primary" style={{ marginTop: 24 }} onClick={() => navigate('/')}>← Back to Evaluator</button>
      </div>
    )
  }

  const { candidate_name, evaluation, swot, suggestions_for_improvement } = report

  return (
    <div className="results container">
      {/* Back */}
      <button className="btn btn-ghost back-btn" onClick={() => navigate('/')}>← New Evaluation</button>

      {/* Hero score card */}
      <div className="score-card card fade-up">
        <div className="score-left">
          <ScoreRing score={evaluation.total_score} />
        </div>
        <div className="score-right">
          <div className="candidate-name">{candidate_name}</div>
          <div className="score-sublabel">Overall Score</div>
          <div className="score-bars-mini">
            {[
              { label: 'Skill Match',    score: evaluation.skill_match.score,          max: 25, color: '#4f8ef7' },
              { label: 'Experience',     score: evaluation.experience_depth.score,      max: 35, color: '#9b6dff' },
              { label: 'Role Alignment', score: evaluation.role_alignment.score,        max: 30, color: '#22d3a5' },
              { label: 'Strengths',      score: evaluation.additional_strengths.score,  max: 10, color: '#f5a623' },
            ].map(s => (
              <div key={s.label} className="mini-bar-row">
                <span className="mini-bar-label">{s.label}</span>
                <div className="mini-track">
                  <div className="mini-fill" style={{ width: `${(s.score/s.max)*100}%`, background: s.color }} />
                </div>
                <span className="mini-score" style={{ color: s.color }}>{s.score}/{s.max}</span>
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Main 2-col layout */}
      <div className="results-grid fade-up" style={{ animationDelay: '0.1s' }}>
        {/* Left: Rubric detail */}
        <div className="card results-panel">
          <RubricBreakdown evaluation={evaluation} />
        </div>

        {/* Right: Suggestions */}
        <div className="card results-panel">
          <h3 className="panel-title">Improvement Suggestions</h3>
          <ol className="suggestions-list">
            {suggestions_for_improvement.map((s, i) => (
              <li key={i} className="suggestion-item">
                <span className="suggestion-num">{i + 1}</span>
                <p>{s}</p>
              </li>
            ))}
          </ol>
        </div>
      </div>

      {/* SWOT */}
      <div className="card swot-section fade-up" style={{ animationDelay: '0.2s' }}>
        <h3 className="panel-title">SWOT Analysis</h3>
        <SwotGrid swot={swot} />
      </div>
    </div>
  )
}
