/**
 * Sidebar navigation – Government Style
 */

import { Link, useLocation } from 'react-router-dom'
import './Sidebar.css'

function Sidebar() {
  const location = useLocation()

  const navItems = [
    { path: '/', label: 'Dashboard' },
    { path: '/search', label: 'Search LAQs' },
    { path: '/chat', label: 'LAQ Assistant' },
    { path: '/upload', label: 'LAQ Intake' },
    { path: '/database', label: 'LAQ Repository' },
    { path: '/validation', label: 'Validation' },
  ]

  return (
    <aside className="sidebar">
      <div className="logo">
        LAQ System
      </div>

      <nav className="nav-items">
        {navItems.map(item => (
          <Link
            key={item.path}
            to={item.path}
            className={`nav-item ${location.pathname === item.path ? 'active' : ''}`}
          >
            <span className="nav-item-label">{item.label}</span>
          </Link>
        ))}
      </nav>
    </aside>
  )
}

export default Sidebar
