import { useState } from 'react'
import { HiDocument, HiPaperClip, HiDownload } from 'react-icons/hi'
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

  const getFileIcon = (url) => {
    if (url.endsWith('.pdf')) return '📄'
    if (url.endsWith('.xlsx') || url.endsWith('.xls')) return '📊'
    if (url.endsWith('.docx') || url.endsWith('.doc')) return '📝'
    return '📎'
  }

  const getFileName = (url) => {
    const parts = url.split('/')
    return decodeURIComponent(parts[parts.length - 1])
  }

  return (
    <div className="chat-page">
      <div className="chat-header">
        <h2>Chat with LAQ Knowledge Base</h2>
        <p>Ask questions about legislative assembly proceedings and policies</p>
      </div>

      <form onSubmit={handleSubmit} className="chat-form">
        <textarea
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Enter an LAQ or policy-related query..."
          rows="4"
        />
        <button type="submit" disabled={loading} className="chat-submit-btn">
          {loading ? 'Processing...' : 'Submit Query'}
        </button>
      </form>

      {result && (
        <div className="assistant-result">
          <div className="answer-section">
            <h3>Response</h3>
            <div className="answer-text">{result.answer}</div>
          </div>

          {result.sources && result.sources.length > 0 && (
            <div className="sources-section">
              <h4>Referenced LAQs ({result.sources.length})</h4>
              
              {result.sources.map((src, i) => (
                <div key={i} className="source-card">
                  <div className="source-header">
                    <div className="source-meta">
                      <span className="source-number">LAQ #{src.metadata.laq_number}</span>
                      <span className="source-date">{src.metadata.date}</span>
                      <span className="source-similarity">{src.similarity_score.toFixed(1)}% match</span>
                    </div>
                  </div>

                  <div className="source-content">
                    <div className="source-question">
                      <strong>Q:</strong> {src.question}
                    </div>
                    <div className="source-answer">
                      <strong>A:</strong> {src.answer}
                    </div>
                  </div>

                  <div className="source-metadata">
                    <span><strong>Minister:</strong> {src.metadata.minister}</span>
                    {src.metadata.mla_name && src.metadata.mla_name !== 'N/A' && (
                      <span><strong>MLA:</strong> {src.metadata.mla_name}</span>
                    )}
                  </div>

                  {/* File Links Section */}
                  <div className="source-files">
                    {/* Reply Document Link */}
                    {src.reply_document_url && (
                      <div className="file-link-section">
                        <HiDocument className="file-section-icon" />
                        <span className="file-section-label">Reply Document:</span>
                        <a 
                          href={src.reply_document_url} 
                          target="_blank" 
                          rel="noopener noreferrer"
                          className="file-link reply-link"
                          download
                        >
                          {getFileIcon(src.reply_document_url)} {getFileName(src.reply_document_url)}
                          <HiDownload className="download-icon" />
                        </a>
                      </div>
                    )}

                    {/* Annexure Files Links */}
                    {src.attachment_urls && src.attachment_urls.length > 0 && (
                      <div className="file-link-section">
                        <HiPaperClip className="file-section-icon" />
                        <span className="file-section-label">Annexures ({src.attachment_urls.length}):</span>
                        <div className="annexure-links">
                          {src.attachment_urls.map((url, idx) => (
                            <a 
                              key={idx}
                              href={url} 
                              target="_blank" 
                              rel="noopener noreferrer"
                              className="file-link annexure-link"
                              download
                            >
                              {getFileIcon(url)} {getFileName(url)}
                              <HiDownload className="download-icon" />
                            </a>
                          ))}
                        </div>
                      </div>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default Chat