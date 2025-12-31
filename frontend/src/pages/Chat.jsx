import { useState } from 'react'
import { HiDocumentText, HiUser, HiCalendar } from 'react-icons/hi'
import { chatWithLAQs } from '../services/api'
import './Chat.css'

function Chat() {
  const [query, setQuery] = useState('')
  const [result, setResult] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    try {
      const response = await chatWithLAQs(query)
      setResult(response)
    } catch (err) {
      console.error(err)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="chat-page">
      <form onSubmit={handleSubmit} className="chat-form">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter an LAQ or policy-related query..."
        />
        <button type="submit" disabled={loading}>
          {loading ? 'Processing...' : 'Submit'}
        </button>
      </form>

      {result && (
        <div className="assistant-result">
          <h3>System Response</h3>
          <p className="answer-text">{result.answer}</p>

          {result.sources && result.sources.length > 0 && (
            <div className="source-details">
              <h4>LAQ Details</h4>
              {(() => {
                const src = result.sources[0];
                return (
                  <div className="source-card">
                    <div className="source-header">
                      <div className="source-info">
                        <div className="source-laq">LAQ No: {src.metadata.laq_num}</div>
                        <div className="source-meta">
                          {src.metadata.minister && (
                            <span>
                              <HiUser /> {src.metadata.minister}
                            </span>
                          )}
                          {src.metadata.date && (
                            <span>
                              <HiCalendar /> {src.metadata.date}
                            </span>
                          )}
                        </div>
                      </div>
                    </div>
                    
                    <div className="source-q-a">
                      <div className="source-question">
                        <strong>Q:</strong> {src.question}
                      </div>
                      <div className="source-answer">
                        <strong>A:</strong> {src.answer}
                      </div>
                    </div>

                    {/* Display annexures if present */}
                    {src.annexures && src.annexures.length > 0 && (
                      <div className="source-annexures">
                        <div className="annexure-header">
                          <HiDocumentText />
                          <span>Attached Annexures</span>
                        </div>
                        {src.annexures.map((annexure, annexIdx) => (
                          <div key={annexIdx} className="annexure-item">
                            <div className="annexure-label">
                              <strong>Annexure {annexure.label}:</strong>
                            </div>
                            {annexure.metadata && annexure.metadata.annexure_file && (
                              <div className="annexure-meta">
                                Annexure File: {annexure.metadata.annexure_file}
                              </div>
                            )}
                            <div className="annexure-content">
                              <pre>{annexure.content}</pre>
                            </div>
                          </div>
                        ))}
                      </div>
                    )}
                  </div>
                );
              })()}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default Chat