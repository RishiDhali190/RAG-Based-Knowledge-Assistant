import { useState } from 'react'
import UploadPanel from './components/UploadPanel'
import ChatPanel from './components/ChatPanel'

/**
 * App – Root component that ties together:
 *   - UploadPanel (sidebar for document management)
 *   - ChatPanel (main chat area with query input)
 *   - Comparison toggle (RAG vs no-RAG hallucination demo)
 */

export default function App() {
  const [documents, setDocuments] = useState([])
  const [compareMode, setCompareMode] = useState(false)

  const hasDocuments = documents.some(d => d.status === 'success')

  return (
    <div className="app-container">
      {/* Sidebar */}
      <UploadPanel
        documents={documents}
        setDocuments={setDocuments}
      />

      {/* Main Area */}
      <div className="main-area">
        {/* Top Bar */}
        <div className="top-bar">
          <div className="top-bar-left">
            <h2>💬 Chat</h2>
            <span className="status-badge online">
              <span className="dot"></span>
              {hasDocuments
                ? `${documents.filter(d => d.status === 'success').length} doc(s) ready`
                : 'No documents loaded'}
            </span>
          </div>

          {/* Hallucination Demo Toggle */}
          <div className="comparison-toggle">
            <label htmlFor="compare-toggle">
              🔀 Compare RAG vs No-RAG
            </label>
            <label className="toggle-switch">
              <input
                id="compare-toggle"
                type="checkbox"
                checked={compareMode}
                onChange={(e) => setCompareMode(e.target.checked)}
              />
              <span className="toggle-slider"></span>
            </label>
          </div>
        </div>

        {/* Chat */}
        <ChatPanel
          compareMode={compareMode}
          hasDocuments={hasDocuments}
        />
      </div>
    </div>
  )
}
