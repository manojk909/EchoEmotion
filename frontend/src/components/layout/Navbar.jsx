import { Link, useLocation } from 'react-router-dom'
import { motion } from 'framer-motion'
import { MicrophoneIcon, ChartBarIcon, HomeIcon, Cog6ToothIcon } from '@heroicons/react/24/outline'
import { useAuthStore } from '../../store/auth'

const NAV_LINKS = [
  { to: '/',          label: 'Home',      Icon: HomeIcon },
  { to: '/predict',   label: 'Predict',   Icon: MicrophoneIcon },
  { to: '/dashboard', label: 'Dashboard', Icon: ChartBarIcon },
  { to: '/model',     label: 'Model',     Icon: Cog6ToothIcon },
]

export default function Navbar() {
  const { pathname } = useLocation()
  const { isAuthed, logout } = useAuthStore()

  return (
    <nav className="fixed top-0 left-0 right-0 z-50 border-b border-surface-border bg-surface/80 backdrop-blur-md">
      <div className="max-w-7xl mx-auto px-4 h-16 flex items-center justify-between">
        {/* Logo */}
        <Link to="/" className="flex items-center gap-2.5 group">
          <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center">
            <MicrophoneIcon className="w-4 h-4 text-white" />
          </div>
          <span className="font-display font-bold text-lg text-white">Echo<span className="text-brand-400">Emotion</span></span>
        </Link>

        {/* Links */}
        <div className="hidden md:flex items-center gap-1">
          {NAV_LINKS.map(({ to, label, Icon }) => {
            const active = pathname === to
            return (
              <Link key={to} to={to} className={`relative flex items-center gap-2 px-4 py-2 rounded-xl text-sm font-medium transition-colors duration-200 ${active ? 'text-white' : 'text-slate-400 hover:text-white'}`}>
                {active && (
                  <motion.div
                    layoutId="nav-pill"
                    className="absolute inset-0 bg-white/8 rounded-xl"
                    transition={{ type: 'spring', stiffness: 400, damping: 30 }}
                  />
                )}
                <Icon className="w-4 h-4" />
                <span className="relative">{label}</span>
              </Link>
            )
          })}
        </div>

        {/* Auth */}
        <div className="flex items-center gap-3">
          {isAuthed ? (
            <button onClick={logout} className="btn-ghost text-sm">Log out</button>
          ) : (
            <>
              <Link to="/login"    className="btn-ghost text-sm">Log in</Link>
              <Link to="/register" className="btn-primary text-sm py-2">Sign up</Link>
            </>
          )}
        </div>
      </div>
    </nav>
  )
}
