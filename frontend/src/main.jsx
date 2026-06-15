import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import { BrowserRouter, Routes, Route } from 'react-router-dom'
import RepositoryDashboard from './components/RepositoryDashboard.jsx'
import './index.css'
import App from './App.jsx'
import Landing from './Landing.jsx'
import axios from 'axios'

axios.defaults.withCredentials = true;

createRoot(document.getElementById('root')).render(
  <StrictMode>
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Landing />} />
        <Route path="/app" element={<App />} />
          <Route path="/repositories" element={<RepositoryDashboard />} />
      </Routes>
    </BrowserRouter>
  </StrictMode>,
)
