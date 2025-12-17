

import { useEffect, useState } from 'react'
import { getDatabaseInfo } from '../services/api'
import './Dashboard.css'

function Dashboard() {
  const [stats, setStats] = useState(null)

  useEffect(() => {
    const fetchStats = async () => {
      try {
        const data = await getDatabaseInfo()
        setStats(data)
      } catch (err) {
        console.error(err)
      }
    }
    fetchStats()
  }, [])

  return (
    <div className="dashboard">
      <div className="stats-grid">

        <div className="stat-card">
          <div className="stat-label">Total LAQs</div>
          <div className="stat-value">{stats?.total_documents || 0}</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Starred Questions</div>
          <div className="stat-value">{stats?.starred || '—'}</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Unstarred Questions</div>
          <div className="stat-value">{stats?.unstarred || '—'}</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Departments Covered</div>
          <div className="stat-value">{stats?.departments || '—'}</div>
        </div>

      </div>

      <section className="section">
        <h2 className="section-title">System Purpose</h2>
        <p>
          This system assists the Legislative Assembly Secretariat and
          Departments in processing, classifying, and responding to
          Legislative Assembly Questions (LAQs) efficiently by maintaining
          structured historical data and decision-support tools.
        </p>
      </section>
    </div>
  )
}

export default Dashboard