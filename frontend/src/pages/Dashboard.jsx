import { useEffect, useState } from 'react'
import './Dashboard.css'
import { getAllLAQs } from '../services/api'

function Dashboard() {
  const [laqs, setLaqs] = useState([])
  const [filteredLaqs, setFilteredLaqs] = useState([])

  const [filters, setFilters] = useState({
    year: '',
    mla_name: '',
    department: '',
    type: '',
    cutmotion: '',
  })

  // ✅ Load LAQs from backend
  useEffect(() => {
    const loadLAQs = async () => {
      try {
        const data = await getAllLAQs()
        setLaqs(data)
        setFilteredLaqs(data)
      } catch (err) {
        console.error('Failed to load LAQs', err)
      }
    }
    loadLAQs()
  }, [])

  // ✅ Apply filters
  useEffect(() => {
    let temp = [...laqs]

    if (filters.year)
      temp = temp.filter(l => String(l.year) === filters.year)

    if (filters.mla_name)
      temp = temp.filter(l => l.mla_name.includes(filters.mla_name))

    if (filters.department)
      temp = temp.filter(l => l.department.includes(filters.department))

    if (filters.type)
      temp = temp.filter(l => l.type === filters.type)

    if (filters.cutmotion)
      temp = temp.filter(l => l.cutmotion === filters.cutmotion)

    setFilteredLaqs(temp)
  }, [filters, laqs])

  // ✅ Stats
  const totalDocuments = laqs.length
  const starred = laqs.filter(l => l.type === 'Starred').length
  const unstarred = laqs.filter(l => l.type === 'Unstarred').length
  const departments = [...new Set(laqs.map(l => l.department))].length

  // ✅ Filter options
  const years = [...new Set(laqs.map(l => l.year))]
  const mlalist = [...new Set(laqs.map(l => l.mla_name))]
  const departmentsList = [...new Set(laqs.map(l => l.department))]
  const cutmotionsList = [...new Set(laqs.map(l => l.cutmotion))]

  return (
    <div className="dashboard">
      {/* Top Stats */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-label">Total LAQs</div>
          <div className="stat-value">{totalDocuments}</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Starred Questions</div>
          <div className="stat-value">{starred}</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Unstarred Questions</div>
          <div className="stat-value">{unstarred}</div>
        </div>

        <div className="stat-card">
          <div className="stat-label">Departments Covered</div>
          <div className="stat-value">{departments}</div>
        </div>
      </div>

      {/* Filters */}
      <h2 className="section-title">LAQ Questions Intake</h2>

      <div className="filters">
        <select value={filters.year}
          onChange={e => setFilters({ ...filters, year: e.target.value })}>
          <option value="">All Years</option>
          {years.map(y => <option key={y} value={y}>{y}</option>)}
        </select>

        <select value={filters.mla_name}
          onChange={e => setFilters({ ...filters, mla_name: e.target.value })}>
          <option value="">All MLAs</option>
          {mlalist.map(m => <option key={m} value={m}>{m}</option>)}
        </select>

        <select value={filters.department}
          onChange={e => setFilters({ ...filters, department: e.target.value })}>
          <option value="">All Departments</option>
          {departmentsList.map(d => <option key={d} value={d}>{d}</option>)}
        </select>

        <select value={filters.type}
          onChange={e => setFilters({ ...filters, type: e.target.value })}>
          <option value="">All Types</option>
          <option value="Starred">Starred</option>
          <option value="Unstarred">Unstarred</option>
        </select>

        <select value={filters.cutmotion}
          onChange={e => setFilters({ ...filters, cutmotion: e.target.value })}>
          <option value="">All Cut Motions</option>
          {cutmotionsList.map(c =>
            <option key={c} value={c}>{c}</option>
          )}
        </select>
      </div>

      {/* Table */}
      <div className="laq-table-container">
        <table className="laq-table">
          <thead>
            <tr>
              <th>LAQ No</th>
              <th>Year</th>
              <th>MLA Name</th>
              <th>Department</th>
              <th>Demand No</th>
              <th>Type</th>
              <th>Cut Motion</th>
              <th>Duplicate</th>
              <th>Date</th>
              <th>Question</th>
            </tr>
          </thead>
          <tbody>
            {filteredLaqs.map(l => (
              <tr key={l.laq_no}>
                <td>{l.laq_no}</td>
                <td>{l.year}</td>
                <td>{l.mla_name}</td>
                <td>{l.department}</td>
                <td>{l.demand_no}</td>
                <td>{l.type}</td>
                <td>{l.cutmotion}</td>
                <td>{l.duplicate ? 'Yes' : 'No'}</td>
                <td>{l.date}</td>
                <td>{l.question}</td>
              </tr>
            ))}

            {filteredLaqs.length === 0 && (
              <tr>
                <td colSpan="10" style={{ textAlign: 'center', padding: 12 }}>
                  No questions match the filter criteria.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
    </div>
  )
}

export default Dashboard