import { useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { useMutation } from '@tanstack/react-query'
import toast from 'react-hot-toast'
import { MicrophoneIcon } from '@heroicons/react/24/outline'
import { register, login } from '../services/api'
import { useAuthStore } from '../store/auth'

export default function RegisterPage() {
  const [form, setForm] = useState({ email: '', username: '', password: '' })
  const navigate        = useNavigate()
  const setAuth         = useAuthStore((s) => s.setAuth)

  const set = (k) => (e) => setForm((f) => ({ ...f, [k]: e.target.value }))

  const mutation = useMutation({
    mutationFn: async () => {
      await register(form.email, form.username, form.password)
      // Auto-login after register
      const res = await login(form.email, form.password)
      return res
    },
    onSuccess: (res) => {
      setAuth(res.data.access_token, { username: res.data.username })
      toast.success(`Account created! Welcome, ${res.data.username}!`)
      navigate('/predict')
    },
    onError: (err) => {
      toast.error(err.response?.data?.detail || 'Registration failed.')
    },
  })

  const valid = form.email && form.username.length >= 3 && form.password.length >= 8

  return (
    <div className="min-h-screen gradient-mesh flex items-center justify-center px-4">
      <motion.div
        initial={{ opacity: 0, y: 24 }}
        animate={{ opacity: 1, y: 0 }}
        className="card w-full max-w-md"
      >
        <div className="flex items-center gap-2 mb-8">
          <div className="w-8 h-8 rounded-lg bg-brand-500 flex items-center justify-center">
            <MicrophoneIcon className="w-4 h-4 text-white" />
          </div>
          <span className="font-display font-bold text-lg text-white">
            Echo<span className="text-brand-400">Emotion</span>
          </span>
        </div>

        <h1 className="font-display text-2xl font-bold text-white mb-1">Create account</h1>
        <p className="text-slate-400 text-sm mb-8">Join EchoEmotion to save your prediction history.</p>

        <div className="space-y-4">
          {[
            { key: 'email',    label: 'Email',    type: 'email',    placeholder: 'you@example.com' },
            { key: 'username', label: 'Username', type: 'text',     placeholder: 'yourname' },
            { key: 'password', label: 'Password', type: 'password', placeholder: '8+ characters' },
          ].map(({ key, label, type, placeholder }) => (
            <div key={key}>
              <label className="text-slate-400 text-sm mb-1.5 block">{label}</label>
              <input
                type={type}
                value={form[key]}
                onChange={set(key)}
                placeholder={placeholder}
                className="input"
              />
            </div>
          ))}

          <button
            onClick={() => mutation.mutate()}
            disabled={!valid || mutation.isPending}
            className="btn-primary w-full"
          >
            {mutation.isPending ? (
              <span className="flex items-center justify-center gap-2">
                <span className="w-4 h-4 border-2 border-white/30 border-t-white rounded-full animate-spin" />
                Creating account…
              </span>
            ) : 'Sign up'}
          </button>
        </div>

        <p className="text-slate-500 text-sm text-center mt-6">
          Already have an account?{' '}
          <Link to="/login" className="text-brand-400 hover:text-brand-300 transition-colors">
            Log in
          </Link>
        </p>
      </motion.div>
    </div>
  )
}
