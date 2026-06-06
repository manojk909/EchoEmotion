import axios from 'axios'

const BASE_URL = import.meta.env.VITE_API_URL || '/api/v1'

export const api = axios.create({
  baseURL: BASE_URL,
  timeout: 60_000,
})

// Attach JWT on every request
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('ser_token')
  if (token) config.headers.Authorization = `Bearer ${token}`
  return config
})

// ── Auth ───────────────────────────────────────────────────────────────────
export const login = (email, password) =>
  api.post('/auth/login', new URLSearchParams({ username: email, password }))

export const register = (email, username, password) =>
  api.post('/auth/register', { email, username, password })

export const getMe = () => api.get('/auth/me')

// ── Prediction ─────────────────────────────────────────────────────────────
export const predictAudio = (file) => {
  const form = new FormData()
  form.append('file', file)
  return api.post('/predict', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}

// ── Model ──────────────────────────────────────────────────────────────────
export const getModelInfo  = () => api.get('/model-info')
export const getMetrics    = () => api.get('/metrics')
export const trainModel    = (payload) => api.post('/train', payload)

// ── Dashboard ──────────────────────────────────────────────────────────────
export const getDashboard  = () => api.get('/dashboard')

// ── Misc ───────────────────────────────────────────────────────────────────
export const getEmotions   = () => api.get('/emotions')
export const healthCheck   = () => api.get('/health')
