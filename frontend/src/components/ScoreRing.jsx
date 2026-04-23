import React, { useEffect, useRef } from 'react'
import './ScoreRing.css'

const RADIUS = 72
const STROKE = 10
const CIRCUMFERENCE = 2 * Math.PI * RADIUS

function scoreColor(score) {
  if (score >= 80) return ['#22d3a5', '#4f8ef7']
  if (score >= 60) return ['#4f8ef7', '#9b6dff']
  if (score >= 40) return ['#f5a623', '#4f8ef7']
  return ['#ff5370', '#f5a623']
}

function scoreLabel(score) {
  if (score >= 85) return 'Excellent'
  if (score >= 70) return 'Strong'
  if (score >= 55) return 'Moderate'
  if (score >= 40) return 'Weak'
  return 'Poor'
}

export default function ScoreRing({ score, animate = true }) {
  const progressRef = useRef(null)
  const offset = CIRCUMFERENCE - (score / 100) * CIRCUMFERENCE
  const [c1, c2] = scoreColor(score)
  const gradId = `ring-grad-${score}`

  useEffect(() => {
    if (!animate || !progressRef.current) return
    progressRef.current.style.strokeDashoffset = CIRCUMFERENCE
    const t = setTimeout(() => {
      if (progressRef.current)
        progressRef.current.style.strokeDashoffset = offset
    }, 80)
    return () => clearTimeout(t)
  }, [score, offset, animate])

  return (
    <div className="score-ring-wrap">
      <svg width="180" height="180" viewBox="0 0 180 180" className="score-ring-svg">
        <defs>
          <linearGradient id={gradId} x1="0%" y1="0%" x2="100%" y2="100%">
            <stop offset="0%" stopColor={c1} />
            <stop offset="100%" stopColor={c2} />
          </linearGradient>
        </defs>
        {/* Track */}
        <circle cx="90" cy="90" r={RADIUS} fill="none"
          stroke="rgba(255,255,255,0.06)" strokeWidth={STROKE} />
        {/* Glow */}
        <circle cx="90" cy="90" r={RADIUS} fill="none"
          stroke={c1} strokeWidth={STROKE + 8} strokeOpacity="0.08"
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={offset}
          strokeLinecap="round"
          transform="rotate(-90 90 90)"
          style={{ filter: `blur(6px)` }}
        />
        {/* Progress arc */}
        <circle
          ref={progressRef} cx="90" cy="90" r={RADIUS} fill="none"
          stroke={`url(#${gradId})`} strokeWidth={STROKE}
          strokeDasharray={CIRCUMFERENCE}
          strokeDashoffset={CIRCUMFERENCE}
          strokeLinecap="round"
          transform="rotate(-90 90 90)"
          style={{ transition: 'stroke-dashoffset 1.4s cubic-bezier(0.4,0,0.2,1)' }}
        />
      </svg>

      <div className="score-ring-center">
        <div className="score-number">{score}</div>
        <div className="score-denom">/100</div>
        <div className="score-label" style={{ color: c1 }}>{scoreLabel(score)}</div>
      </div>
    </div>
  )
}
