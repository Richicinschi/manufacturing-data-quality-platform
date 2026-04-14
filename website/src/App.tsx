import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'
import LandingPage from './pages/LandingPage'
import DataQualityPage from './pages/DataQualityPage'
import SignalAnalysisPage from './pages/SignalAnalysisPage'
import TimeTrendsPage from './pages/TimeTrendsPage'
import TechnicalPage from './pages/TechnicalPage'

function App() {
  return (
    <Layout>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        <Route path="/data-quality" element={<DataQualityPage />} />
        <Route path="/signal-analysis" element={<SignalAnalysisPage />} />
        <Route path="/time-trends" element={<TimeTrendsPage />} />
        <Route path="/technical" element={<TechnicalPage />} />
      </Routes>
    </Layout>
  )
}

export default App
