import { useState } from 'react'
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
          <p>{result.answer}</p>

          {result.sources && (
            <div>
              <h4>Referenced LAQs</h4>
              <ul>
                {result.sources.map((src, i) => (
                  <li key={i}>
                    LAQ No: {src.metadata.laq_number} – {src.metadata.department}
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export default Chat