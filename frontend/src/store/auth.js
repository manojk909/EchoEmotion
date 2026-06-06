import { create } from 'zustand'

export const useAuthStore = create((set) => ({
  token:    localStorage.getItem('ser_token') || null,
  user:     null,
  isAuthed: !!localStorage.getItem('ser_token'),

  setAuth: (token, user) => {
    localStorage.setItem('ser_token', token)
    set({ token, user, isAuthed: true })
  },

  logout: () => {
    localStorage.removeItem('ser_token')
    set({ token: null, user: null, isAuthed: false })
  },
}))
