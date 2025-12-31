import { useState } from 'react'
import { HiSearch, HiExclamation, HiUser, HiCalendar, HiTag, HiDocumentText } from 'react-icons/hi'
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
                      LAQ: {result.metadata.laq_num}
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

                  {/* Display annexure content if present */}
                  {result.annexures && result.annexures.length > 0 && (
                    <div className="result-annexures">
                      <div className="annexure-header">
                        <HiDocumentText />
                        <span>Attached Annexures</span>
                      </div>
                      {result.annexures.map((annexure, annexIdx) => (
                        <div key={annexIdx} className="annexure-item">
                          <div className="annexure-label">
                            <strong>Annexure {annexure.label}:</strong>
                          </div>
                          {annexure.metadata && (
                            <div className="annexure-meta">
                              Annexure File: {annexure.metadata.annexure_file || 'N/A'}
                            </div>
                          )}
                          <div className="annexure-content">
                            {/* Display as formatted table/text */}
                            <pre>{annexure.content}</pre>
                          </div>
                        </div>
                      ))}
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
