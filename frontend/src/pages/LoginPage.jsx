import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { MicrophoneIcon } from '@heroicons/react/24/outline'
import { login } from '../services/api'
import { useAuthStore } from '../store/auth'

export default function LoginPage() {
  const [email, setEmail]       = useState('')
  const [password, setPassword] = useState('')
  const navigate                = useNavigate()
  const setAuth                 = useAuthStore((s) => s.setAuth)

  const mutation = useMutation({
    mutationFn: () => login(email, password),
    onSuccess: (res) => {
      setAuth(res.data.access_token, { username: res.data.username })
      toast.success(`Welcome back, ${res.data.username}!`)
      navigate('/predict')
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Login failed.')
    },
  })

  return (
    <div className="min-h-screen gradient-mesh flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        className="card w-full max-w-md"
      >
        {/* Logo */}
        <div className="flex items-center gap-2 mb-8">
          <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center">
            <MicrophoneIcon className="w-4 h-4 text-white" />
          </div>
          <span className="font-display font-bold text-lg text-white">
            Echo<span className="text-brand-400">Emotion</span>
          </span>
        </div>

        <h1 className="font-display text-2xl font-bold text-white mb-1">Welcome back</h1>
        <p className="text-slate-400 text-sm mb-8">Log in to access your dashboard and history.</p>

        <div className="space-y-4">
          <div>
            <label className="text-slate-400 text-sm mb-1.5 block">Email</label>
            <input
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="you@example.com"
              className="input"
            />
          </div>
          <div>
            <label className="text-slate-400 text-sm mb-1.5 block">Password</label>
            <input
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              className="input"
              onKeyDown={(e) => e.key === 'Enter' && mutation.mutate()}
            />
          </div>

          <button
            onClick={() => mutation.mutate()}
            disabled={!email || !password || mutation.isPending}
            className="btn-primary w-full"
          >
            {mutation.isPending ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Logging in…
              </span>
            ) : 'Log in'}
          </button>
        </div>

        <p className="text-slate-500 text-sm text-center mt-6">
          No account?{' '}
          <Link to="/register" className="text-brand-400 hover:text-brand-300 transition-colors">
            Sign up free
          </Link>
        </p>
      </motion.div>
    </div>
  )
}
