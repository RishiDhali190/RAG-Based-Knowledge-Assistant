import { useState, useRef } from 'react'

/**
 * UploadPanel – Sidebar component for uploading and managing documents.
 * 
 * Features:
 *  - Drag & drop or click to upload PDF, DOCX, TXT files
 *  - Shows upload progress
 *  - Lists uploaded documents with status
 *  - Clear all button
 */

const API_BASE = 'http://localhost:8000'

function getDocIcon(filename) {
  const ext = filename.split('.').pop().toLowerCase()
  if (ext === 'pdf') return '📕'
  if (ext === 'docx') return '📘'
  return '📄'
}

export default function UploadPanel({ documents, setDocuments, onUploadComplete }) {
  const [dragging, setDragging] = useState(false)
  const [uploading, setUploading] = useState(false)
  const [uploadProgress, setUploadProgress] = useState(0)
  const [uploadResults, setUploadResults] = useState([])
  const fileInputRef = useRef(null)

  const handleFiles = async (files) => {
    if (!files.length) return

    setUploading(true)
    setUploadProgress(10)

    const formData = new FormData()
    for (const file of files) {
      formData.append('files', file)
    }

    try {
      setUploadProgress(30)

      const response = await fetch(`${API_BASE}/upload`, {
        method: 'POST',
        body: formData
      })

      setUploadProgress(80)

      const data = await response.json()
      setUploadResults(data.results || [])

      // Update document list
      const successDocs = (data.results || [])
        .filter(r => r.status === 'success')
        .map(r => ({
          name: r.filename,
          chunks: r.chunks_created,
          status: 'success'
        }))

      const errorDocs = (data.results || [])
        .filter(r => r.status === 'error')
        .map(r => ({
          name: r.filename,
          error: r.message,
          status: 'error'
        }))

      setDocuments(prev => [...prev, ...successDocs, ...errorDocs])
      setUploadProgress(100)

      if (onUploadComplete) onUploadComplete()

      // Reset progress after a delay
      setTimeout(() => {
        setUploading(false)
        setUploadProgress(0)
      }, 1500)

    } catch (error) {
      console.error('Upload failed:', error)
      setUploadResults([{ filename: 'Upload', status: 'error', message: error.message }])
      setUploading(false)
    }
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const files = Array.from(e.dataTransfer.files)
    handleFiles(files)
  }

  const handleDragOver = (e) => {
    e.preventDefault()
    setDragging(true)
  }

  const handleDragLeave = () => {
    setDragging(false)
  }

  const handleClick = () => {
    fileInputRef.current?.click()
  }

  const handleFileSelect = (e) => {
    const files = Array.from(e.target.files)
    handleFiles(files)
    e.target.value = '' // reset so same file can be re-uploaded
  }

  const handleClear = async () => {
    try {
      await fetch(`${API_BASE}/clear`, { method: 'DELETE' })
      setDocuments([])
      setUploadResults([])
    } catch (error) {
      console.error('Clear failed:', error)
    }
  }

  return (
    <div className="sidebar">
      <div className="sidebar-header">
        <h1>🧠 RAG Knowledge Assistant</h1>
        <p>Chat with your company documents</p>
      </div>

      <div className="sidebar-content">
        {/* Upload Zone */}
        <div
          className={`upload-zone ${dragging ? 'dragging' : ''}`}
          onDrop={handleDrop}
          onDragOver={handleDragOver}
          onDragLeave={handleDragLeave}
          onClick={handleClick}
        >
          <div className="upload-icon">📂</div>
          <h3>Upload Documents</h3>
          <p>Drag & drop or click to browse<br />PDF, DOCX, TXT</p>
          <input
            ref={fileInputRef}
            type="file"
            className="upload-input"
            multiple
            accept=".pdf,.docx,.txt"
            onChange={handleFileSelect}
          />
        </div>

        {/* Upload Progress */}
        {uploading && (
          <div className="upload-progress">
            <span>Processing documents...</span>
            <div className="upload-progress-bar">
              <div
                className="upload-progress-fill"
                style={{ width: `${uploadProgress}%` }}
              />
            </div>
          </div>
        )}

        {/* Document List */}
        {documents.length > 0 && (
          <div className="document-list">
            <h3>📚 Uploaded Documents ({documents.length})</h3>
            {documents.map((doc, index) => (
              <div key={index} className="document-item">
                <span className="doc-icon">{getDocIcon(doc.name)}</span>
                <div className="doc-info">
                  <div className="doc-name">{doc.name}</div>
                  <div className="doc-meta">
                    {doc.status === 'success'
                      ? `${doc.chunks} chunks indexed`
                      : doc.error || 'Error processing'}
                  </div>
                </div>
                <span className={`doc-status ${doc.status}`}>
                  {doc.status === 'success' ? '✓' : '✕'}
                </span>
              </div>
            ))}

            <button className="clear-button" onClick={handleClear}>
              🗑️ Clear All Documents
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
