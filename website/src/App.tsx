import { Suspense, lazy } from 'react'
import { Routes, Route } from 'react-router-dom'
import Layout from './components/Layout'

const LandingPage = lazy(() => import('./pages/LandingPage'))
const DataQualityPage = lazy(() => import('./pages/DataQualityPage'))
const SignalAnalysisPage = lazy(() => import('./pages/SignalAnalysisPage'))
const TimeTrendsPage = lazy(() => import('./pages/TimeTrendsPage'))
const TechnicalPage = lazy(() => import('./pages/TechnicalPage'))
const ModelingPage = lazy(() => import('./pages/ModelingPage'))

function App() {
  return (
    <Layout>
      <Suspense fallback={<div className="p-8 text-white/70">Loading dashboard section...</div>}>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/data-quality" element={<DataQualityPage />} />
          <Route path="/signal-analysis" element={<SignalAnalysisPage />} />
          <Route path="/time-trends" element={<TimeTrendsPage />} />
          <Route path="/modeling" element={<ModelingPage />} />
          <Route path="/technical" element={<TechnicalPage />} />
        </Routes>
      </Suspense>
    </Layout>
  )
}

export default App
