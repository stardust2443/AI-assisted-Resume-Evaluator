import React, { useState } from 'react'
import { useLocation, useNavigate } from 'react-router-dom'
import ScoreRing from '../components/ScoreRing'
import SwotGrid from '../components/SwotGrid'
import RubricBreakdown from '../components/RubricBreakdown'
import './Compare.css'

function medal(rank) {
  if (rank === 1) return '🥇'
  if (rank === 2) return '🥈'
  if (rank === 3) return '🥉'
  return `#${rank}`
}

export default function Compare() {
  const { state }  = useLocation()
  const navigate   = useNavigate()
  const [expanded, setExpanded] = useState(null)

  const result = state?.result
  if (!result) {
    return (
      <div className="container" style={{ padding: '80px 24px', textAlign: 'center' }}>
        <h2>No comparison results.</h2>
        <button className="btn btn-primary" style={{ marginTop: 24 }} onClick={() => navigate('/')}>← Back</button>
      </div>
    )
  }

  const { total_candidates, ranked } = result

  return (
    <div className="compare container">
      <button className="btn btn-ghost back-btn" onClick={() => navigate('/')}>← New Evaluation</button>

      <div className="compare-header fade-up">
        <h2>{total_candidates} Candidates Ranked</h2>
        <p>Sorted by total score · Includes relative percentile within this batch</p>
      </div>

      {/* Leaderboard */}
      <div className="leaderboard fade-up" style={{ animationDelay: '0.1s' }}>
        {ranked.map((rc, idx) => {
          const { rank, percentile, report } = rc
          const ev = report.evaluation
          const isOpen = expanded === idx
          return (
            <div key={idx} className={`candidate-row card ${rank === 1 ? 'top-rank' : ''}`}>
              <div className="candidate-summary" onClick={() => setExpanded(isOpen ? null : idx)}>
                <div className="rank-badge">{medal(rank)}</div>

                <div className="candidate-info">
                  <div className="candidate-name-row">
                    <span className="cname">{report.candidate_name}</span>
                    <span className={`badge ${rank === 1 ? 'badge-green' : rank === 2 ? 'badge-blue' : 'badge-purple'}`}>
                      Top {100 - percentile < 1 ? '<1' : Math.round(100 - percentile)}%
                    </span>
                  </div>
                  <div className="candidate-mini-bars">
                    {[
                      { score: ev.skill_match.score,          max: 25, color: '#4f8ef7' },
                      { score: ev.experience_depth.score,      max: 35, color: '#9b6dff' },
                      { score: ev.role_alignment.score,        max: 30, color: '#22d3a5' },
                      { score: ev.additional_strengths.score,  max: 10, color: '#f5a623' },
                    ].map((s, i) => (
                      <div key={i} className="cm-track">
                        <div className="cm-fill" style={{ width: `${(s.score / s.max) * 100}%`, background: s.color }} />
                      </div>
                    ))}
                  </div>
                </div>

                <div className="candidate-score-col">
                  <div className="c-total-score">{ev.total_score}</div>
                  <div className="c-total-label">/100</div>
                  <div className="c-percentile">p{percentile}</div>
                </div>

                <div className="expand-toggle">{isOpen ? '▲' : '▼'}</div>
              </div>

              {isOpen && (
                <div className="candidate-detail fade-in">
                  <div className="detail-grid">
                    <div>
                      <RubricBreakdown evaluation={ev} />
                    </div>
                    <div>
                      <h4 className="panel-title">SWOT</h4>
                      <SwotGrid swot={report.swot} />
                      <div className="divider" />
                      <h4 className="panel-title">Top Suggestions</h4>
                      <ol className="mini-suggestions">
                        {report.suggestions_for_improvement.slice(0, 4).map((s, i) => (
                          <li key={i}>{s}</li>
                        ))}
                      </ol>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
