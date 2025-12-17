/**
 * Header component – Government Style
 */

import { useLocation } from 'react-router-dom'
import './Header.css'

function Header() {
  const location = useLocation()

  const getPageTitle = () => {
    const titles = {
      '/': 'Legislative Assembly Questions Dashboard',
      '/search': 'Search & Filter LAQs',
      '/chat': 'LAQ Decision Support Assistant',
      '/upload': 'LAQ Document Intake',
      '/database': 'Legislative Question Repository',
    }
    return titles[location.pathname] || 'Legislative Assembly Questions System'
  }

  return (
    <header className="header">
      <h1 className="header-title">{getPageTitle()}</h1>
      <div className="header-actions">
        {/* Reserved for future official actions */}
      </div>
    </header>
  )
}

export default Header