import React, { useCallback, useState } from 'react'
import './UploadZone.css'

const ACCEPTED = '.pdf,.docx,.txt'
const ACCEPT_LABEL = 'PDF, DOCX, or TXT'

function FileChip({ file, onRemove }) {
  const ext = file.name.split('.').pop().toUpperCase()
  const size = (file.size / 1024).toFixed(0)
  return (
    <div className="file-chip">
      <span className="file-ext">{ext}</span>
      <span className="file-name">{file.name}</span>
      <span className="file-size">{size} KB</span>
      {onRemove && (
        <button className="file-remove" onClick={() => onRemove(file)} title="Remove">✕</button>
      )}
    </div>
  )
}

export default function UploadZone({ label, files, multiple, onChange, icon }) {
  const [dragging, setDragging] = useState(false)

  const handleDrop = useCallback(e => {
    e.preventDefault(); setDragging(false)
    const dropped = Array.from(e.dataTransfer.files)
    const valid = dropped.filter(f => /\.(pdf|docx|txt)$/i.test(f.name))
    if (!valid.length) return
    onChange(multiple ? [...(files || []), ...valid] : [valid[0]])
  }, [files, multiple, onChange])

  const handleInput = e => {
    const picked = Array.from(e.target.files)
    onChange(multiple ? [...(files || []), ...picked] : [picked[0]])
    e.target.value = ''
  }

  const remove = (f) => onChange((files || []).filter(x => x !== f))

  const hasFiles = files && files.length > 0

  return (
    <div className={`upload-zone ${dragging ? 'dragging' : ''} ${hasFiles ? 'has-files' : ''}`}
      onDragOver={e => { e.preventDefault(); setDragging(true) }}
      onDragLeave={() => setDragging(false)}
      onDrop={handleDrop}
    >
      <label className="upload-label" htmlFor={`upload-${label}`}>
        {!hasFiles ? (
          <div className="upload-empty">
            <div className="upload-icon">{icon || '📄'}</div>
            <div className="upload-title">{label}</div>
            <div className="upload-hint">
              Drag & drop or <span className="upload-browse">browse</span>
            </div>
            <div className="upload-types">{ACCEPT_LABEL}</div>
          </div>
        ) : (
          <div className="upload-files">
            <div className="upload-files-header">
              <span>{label}</span>
              <span className="upload-change">+ Add more</span>
            </div>
            <div className="file-chips">
              {files.map((f, i) => (
                <FileChip key={i} file={f} onRemove={multiple ? remove : null} />
              ))}
            </div>
          </div>
        )}
      </label>
      <input
        id={`upload-${label}`} type="file" hidden
        accept={ACCEPTED} multiple={multiple} onChange={handleInput}
      />
    </div>
  )
}
