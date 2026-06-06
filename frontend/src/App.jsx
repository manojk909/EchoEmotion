import { Routes, Route } from 'react-router-dom'
import Navbar        from './components/layout/Navbar'
import LandingPage   from './pages/LandingPage'
import PredictPage   from './pages/PredictPage'
import DashboardPage from './pages/DashboardPage'
import ModelPage     from './pages/ModelPage'
import LoginPage     from './pages/LoginPage'
import RegisterPage  from './pages/RegisterPage'

export default function App() {
  return (
    <div className="min-h-screen">
      <Navbar />
      <Routes>
        <Route path="/"          element={<LandingPage />} />
        <Route path="/predict"   element={<PredictPage />} />
        <Route path="/dashboard" element={<DashboardPage />} />
        <Route path="/model"     element={<ModelPage />} />
        <Route path="/login"     element={<LoginPage />} />
        <Route path="/register"  element={<RegisterPage />} />
      </Routes>
    </div>
  )
}
