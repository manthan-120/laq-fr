import { useState } from 'react'
import { HiSearch, HiExclamation, HiUser, HiCalendar, HiTag, HiDocument, HiPaperClip, HiDownload } from 'react-icons/hi'
import { searchLAQs } from '../services/api'
import './Search.css'

function Search() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleSearch = async (e) => {
    e.preventDefault()
    if (!query.trim()) return

    setLoading(true)
    setError(null)

    try {
      const data = await searchLAQs(query)
      setResults(data.results)
    } catch (err) {
      setError(err.message || 'Search failed')
      console.error('Search error:', err)
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
    <div className="search-page">
      <form onSubmit={handleSearch} className="search-form">
        <input
          type="text"
          className="search-input"
          placeholder="Search LAQs..."
          value={query}
          onChange={(e) => setQuery(e.target.value)}
        />
        <button type="submit" className="search-button" disabled={loading}>
          <HiSearch />
          <span>{loading ? 'Searching...' : 'Search'}</span>
        </button>
      </form>

      {error && (
        <div className="error-message">
          <HiExclamation />
          <span>{error}</span>
        </div>
      )}

      {results.length > 0 && (
        <div className="results-container">
          <div className="results-header">
            <h2>Found {results.length} results</h2>
          </div>

          <div className="results-list">
            {results.map((result, index) => (
              <div key={index} className="result-card">
                <div className="result-score">
                  {result.similarity_score.toFixed(1)}%
                </div>
                <div className="result-content">
                  <div className="result-question">
                    <strong>Q:</strong> {result.question}
                  </div>
                  <div className="result-answer">
                    <strong>A:</strong> {result.answer}
                  </div>
                  <div className="result-metadata">
                    <span>
                      <HiTag />
                      LAQ: {result.metadata.laq_number}
                    </span>
                    <span>
                      <HiUser />
                      Minister: {result.metadata.minister}
                    </span>
                    <span>
                      <HiCalendar />
                      Date: {result.metadata.date}
                    </span>
                  </div>

                  {/* File Links */}
                  {(result.reply_document_url || (result.attachment_urls && result.attachment_urls.length > 0)) && (
                    <div className="result-files">
                      {result.reply_document_url && (
                        <div className="file-link-section">
                          <HiDocument className="file-section-icon" />
                          <a 
                            href={result.reply_document_url} 
                            target="_blank" 
                            rel="noopener noreferrer"
                            className="file-link"
                            download
                          >
                            {getFileIcon(result.reply_document_url)} {getFileName(result.reply_document_url)}
                            <HiDownload className="download-icon" />
                          </a>
                        </div>
                      )}

                      {result.attachment_urls && result.attachment_urls.length > 0 && (
                        <div className="file-link-section">
                          <HiPaperClip className="file-section-icon" />
                          <span className="annexure-label">Annexures:</span>
                          <div className="annexure-links-inline">
                            {result.attachment_urls.map((url, idx) => (
                              <a 
                                key={idx}
                                href={url} 
                                target="_blank" 
                                rel="noopener noreferrer"
                                className="file-link"
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
                  )}
                </div>
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

export default Search