import { useState, useRef, useEffect } from 'react'

/**
 * ChatPanel – Main chat interface for asking questions.
 * 
 * Features:
 *  - Message history with user/assistant bubbles
 *  - Source chunks display (shows which document parts were used)
 *  - Loading indicator while waiting for response
 *  - Auto-scroll to latest message
 *  - Enter to send, Shift+Enter for new line
 */

const API_BASE = 'http://localhost:8000'

export default function ChatPanel({ compareMode, hasDocuments }) {
  const [messages, setMessages] = useState([])
  const [input, setInput] = useState('')
  const [loading, setLoading] = useState(false)
  const [expandedSources, setExpandedSources] = useState({})
  const chatEndRef = useRef(null)
  const textareaRef = useRef(null)

  // Auto-scroll to bottom when new messages arrive
  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: 'smooth' })
  }, [messages, loading])

  // Auto-resize textarea
  useEffect(() => {
    if (textareaRef.current) {
      textareaRef.current.style.height = 'auto'
      textareaRef.current.style.height = textareaRef.current.scrollHeight + 'px'
    }
  }, [input])

  const toggleSources = (messageIndex) => {
    setExpandedSources(prev => ({
      ...prev,
      [messageIndex]: !prev[messageIndex]
    }))
  }

  const sendMessage = async () => {
    const question = input.trim()
    if (!question || loading) return

    // Add user message
    const userMessage = { role: 'user', content: question }
    setMessages(prev => [...prev, userMessage])
    setInput('')
    setLoading(true)

    try {
      if (compareMode) {
        // Fetch both RAG and no-RAG responses in parallel
        const [ragRes, noRagRes] = await Promise.all([
          fetch(`${API_BASE}/query`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question, top_k: 5 })
          }),
          fetch(`${API_BASE}/query-no-rag`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ question })
          })
        ])

        const ragData = await ragRes.json()
        const noRagData = await noRagRes.json()

        setMessages(prev => [...prev, {
          role: 'comparison',
          rag: ragData,
          noRag: noRagData
        }])

      } else {
        // Standard RAG query
        const response = await fetch(`${API_BASE}/query`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ question, top_k: 5 })
        })

        const data = await response.json()
        setMessages(prev => [...prev, {
          role: 'assistant',
          content: data.answer,
          sources: data.sources || []
        }])
      }

    } catch (error) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: `❌ Error: ${error.message}. Make sure the backend is running on port 8000.`,
        sources: []
      }])
    }

    setLoading(false)
  }

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault()
      sendMessage()
    }
  }

  return (
    <>
      {/* Chat Messages */}
      <div className="chat-area">
        {messages.length === 0 && !loading && (
          <div className="welcome-state">
            <div className="welcome-icon">🤖</div>
            <h2>RAG Knowledge Assistant</h2>
            <p>
              Upload your company documents and start asking questions.
              Get accurate, grounded answers from your own data.
            </p>
            <div className="welcome-steps">
              <div className="welcome-step">
                <div className="welcome-step-icon">📄</div>
                <div className="welcome-step-text">Upload Documents</div>
              </div>
              <div className="welcome-step">
                <div className="welcome-step-icon">🔍</div>
                <div className="welcome-step-text">Ask Questions</div>
              </div>
              <div className="welcome-step">
                <div className="welcome-step-icon">✅</div>
                <div className="welcome-step-text">Get Accurate Answers</div>
              </div>
            </div>
          </div>
        )}

        {messages.map((msg, index) => {
          if (msg.role === 'user') {
            return (
              <div key={index} className="message user">
                <div className="message-avatar">👤</div>
                <div className="message-content">
                  <span className="message-label">You</span>
                  <div className="message-bubble">{msg.content}</div>
                </div>
              </div>
            )
          }

          if (msg.role === 'comparison') {
            return (
              <div key={index} className="comparison-container">
                <div className="comparison-card rag">
                  <div className="comparison-card-header">
                    ✅ With RAG (Document-Grounded)
                  </div>
                  <div className="comparison-card-body">
                    {msg.rag.answer}
                    {msg.rag.sources && msg.rag.sources.length > 0 && (
                      <div className="sources-detail" style={{ marginTop: '12px' }}>
                        <div
                          className="sources-toggle"
                          onClick={() => toggleSources(`rag-${index}`)}
                        >
                          📚 {msg.rag.sources.length} source(s) used
                          <span>{expandedSources[`rag-${index}`] ? '▲' : '▼'}</span>
                        </div>
                        {expandedSources[`rag-${index}`] && (
                          <div className="sources-list">
                            {msg.rag.sources.map((src, i) => (
                              <div key={i} className="source-item">
                                <div className="source-item-header">
                                  📄 {src.source}
                                </div>
                                <div className="source-item-text">
                                  {src.text.substring(0, 200)}
                                  {src.text.length > 200 ? '...' : ''}
                                </div>
                              </div>
                            ))}
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                </div>
                <div className="comparison-card no-rag">
                  <div className="comparison-card-header">
                    ❌ Without RAG (May Hallucinate)
                  </div>
                  <div className="comparison-card-body">
                    {msg.noRag.answer}
                  </div>
                </div>
              </div>
            )
          }

          // Assistant message
          return (
            <div key={index} className="message assistant">
              <div className="message-avatar">🤖</div>
              <div className="message-content">
                <span className="message-label">Assistant (RAG)</span>
                <div className="message-bubble">{msg.content}</div>

                {/* Source chips */}
                {msg.sources && msg.sources.length > 0 && (
                  <>
                    <div className="source-chips">
                      {[...new Set(msg.sources.map(s => s.source))].map((src, i) => (
                        <span key={i} className="source-chip">📄 {src}</span>
                      ))}
                    </div>

                    <div className="sources-detail">
                      <div
                        className="sources-toggle"
                        onClick={() => toggleSources(index)}
                      >
                        📚 View {msg.sources.length} source chunk(s)
                        <span>{expandedSources[index] ? '▲' : '▼'}</span>
                      </div>
                      {expandedSources[index] && (
                        <div className="sources-list">
                          {msg.sources.map((src, i) => (
                            <div key={i} className="source-item">
                              <div className="source-item-header">
                                📄 {src.source} (relevance: {src.score?.toFixed(2)})
                              </div>
                              <div className="source-item-text">
                                {src.text.substring(0, 300)}
                                {src.text.length > 300 ? '...' : ''}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  </>
                )}
              </div>
            </div>
          )
        })}

        {/* Loading indicator */}
        {loading && (
          <div className="message assistant">
            <div className="message-avatar">🤖</div>
            <div className="message-content">
              <span className="message-label">Assistant</span>
              <div className="message-bubble">
                <div className="loading-dots">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              </div>
            </div>
          </div>
        )}

        <div ref={chatEndRef} />
      </div>

      {/* Input Area */}
      <div className="input-area">
        <div className="input-wrapper">
          <textarea
            ref={textareaRef}
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={
              hasDocuments
                ? "Ask a question about your documents..."
                : "Upload documents first, then ask questions here..."
            }
            rows={1}
          />
          <button
            className="send-button"
            onClick={sendMessage}
            disabled={!input.trim() || loading}
          >
            ➤
          </button>
        </div>
        <div className="input-hint">
          {compareMode
            ? '🔀 Comparison mode: see RAG vs non-RAG answers side by side'
            : 'Press Enter to send · Shift+Enter for new line'}
        </div>
      </div>
    </>
  )
}
