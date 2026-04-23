import React, { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import UploadZone from '../components/UploadZone'
import LoadingScreen from '../components/LoadingScreen'
import { evaluateSingle, compareMultiple } from '../api/client'
import './Home.css'

export default function Home() {
  const navigate = useNavigate()
  const [mode, setMode] = useState('single')       // 'single' | 'compare'
  const [resumes, setResumes] = useState([])
  const [jdFile, setJdFile]   = useState([])
  const [jdText, setJdText]   = useState('')
  const [jdMode, setJdMode]   = useState('file')   // 'file' | 'text'
  const [loading, setLoading] = useState(false)
  const [loadStep, setLoadStep] = useState(0)
  const [error, setError]     = useState('')

  const canSubmit = resumes.length > 0 && (jdFile.length > 0 || jdText.trim())

  const tick = (n) => setLoadStep(n)

  const handleEvaluate = async () => {
    setError(''); setLoading(true); setLoadStep(0)
    try {
      tick(1); await new Promise(r => setTimeout(r, 400))
      tick(2); await new Promise(r => setTimeout(r, 400))
      tick(3)
      if (mode === 'single') {
        const report = await evaluateSingle(
          resumes[0],
          jdMode === 'file' ? jdFile[0] : null,
          jdMode === 'text' ? jdText    : null
        )
        tick(5)
        navigate('/results', { state: { report } })
      } else {
        const result = await compareMultiple(
          resumes,
          jdMode === 'file' ? jdFile[0] : null,
          jdMode === 'text' ? jdText    : null
        )
        tick(5)
        navigate('/compare', { state: { result } })
      }
    } catch (e) {
      const msg = e.response?.data?.detail || e.message || 'Evaluation failed.'
      setError(msg)
      setLoading(false)
    }
  }

  if (loading) return <LoadingScreen step={loadStep} />

  return (
    <div className="home container">
      {/* Hero */}
      <div className="hero fade-up">
        <div className="hero-badge badge badge-purple">AI-Powered · Evidence-Based</div>
        <h1>
          Evaluate Resumes<br/>
          <span className="grad-text">with Precision</span>
        </h1>
        <p className="hero-sub">
          Every score is backed by a direct quote from the resume.
          No black-box scoring. No keyword games.
        </p>
      </div>

      {/* Mode tabs */}
      <div className="mode-tabs fade-up" style={{ animationDelay: '0.1s' }}>
        <div className="tab-bar">
          <button className={`tab-btn ${mode === 'single' ? 'active' : ''}`} onClick={() => { setMode('single'); setResumes([]) }}>
            👤 Single Candidate
          </button>
          <button className={`tab-btn ${mode === 'compare' ? 'active' : ''}`} onClick={() => { setMode('compare'); setResumes([]) }}>
            👥 Compare &amp; Rank
          </button>
        </div>
      </div>

      {/* Upload panel */}
      <div className="upload-panel card fade-up" style={{ animationDelay: '0.18s' }}>
        <div className="upload-grid">
          {/* Resume upload */}
          <div className="upload-col">
            <div className="upload-col-label">
              {mode === 'single' ? 'Resume' : 'Resumes'}
              {mode === 'compare' && <span className="badge badge-blue" style={{ marginLeft: 8 }}>Multiple</span>}
            </div>
            <UploadZone
              label={mode === 'single' ? 'Drop Resume here' : 'Drop Resumes here (multiple)'}
              files={resumes}
              multiple={mode === 'compare'}
              onChange={setResumes}
              icon="📄"
            />
          </div>

          {/* JD upload/text */}
          <div className="upload-col">
            <div className="upload-col-label">
              Job Description
              <div className="jd-toggle">
                <button className={`jd-toggle-btn ${jdMode === 'file' ? 'active' : ''}`} onClick={() => setJdMode('file')}>File</button>
                <button className={`jd-toggle-btn ${jdMode === 'text' ? 'active' : ''}`} onClick={() => setJdMode('text')}>Paste</button>
              </div>
            </div>
            {jdMode === 'file' ? (
              <UploadZone
                label="Drop Job Description here"
                files={jdFile}
                multiple={false}
                onChange={setJdFile}
                icon="📋"
              />
            ) : (
              <textarea
                className="jd-textarea"
                placeholder="Paste the job description here..."
                value={jdText}
                onChange={e => setJdText(e.target.value)}
                rows={9}
              />
            )}
          </div>
        </div>

        {error && <div className="error-banner">⚠ {error}</div>}

        <div className="submit-row">
          <div className="submit-hint">
            {mode === 'single'
              ? 'Scoring: Skills 25 · Experience 35 · Alignment 30 · Strengths 10'
              : `${resumes.length} resume${resumes.length !== 1 ? 's' : ''} queued · will return ranked list with percentiles`}
          </div>
          <button className="btn btn-primary" disabled={!canSubmit} onClick={handleEvaluate} id="evaluate-btn">
            {mode === 'single' ? '⚡ Evaluate' : '⚡ Compare & Rank'}
          </button>
        </div>
      </div>

      {/* Feature pills */}
      <div className="feature-pills fade-up" style={{ animationDelay: '0.28s' }}>
        {['Quote-verified scores', 'SWOT analysis', 'Improvement tips', 'Anti keyword-stuffing', 'Batch ranking'].map(f => (
          <span key={f} className="badge badge-blue">{f}</span>
        ))}
      </div>
    </div>
  )
}
