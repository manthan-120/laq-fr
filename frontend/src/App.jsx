import { BrowserRouter as Router, Routes, Route } from 'react-router-dom'
import Layout from './components/layout/Layout'
import Dashboard from './pages/Dashboard'
import Search from './pages/Search'
import Chat from './pages/Chat'
import Upload from './pages/Upload'
import Database from './pages/Database'
import Validation from './pages/Validation'

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/search" element={<Search />} />
          <Route path="/chat" element={<Chat />} />
          <Route path="/upload" element={<Upload />} />
          <Route path="/database" element={<Database />} />
          <Route path="/validation" element={<Validation />} />
        </Routes>
      </Layout>
    </Router>
  )
}

export default App
