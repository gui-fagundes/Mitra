import { defineStore } from 'pinia'
import type { Usuario } from '../api/auth'

const USER_KEY = 'user'

function loadUser(): Usuario | null {
  const raw = localStorage.getItem(USER_KEY)
  if (!raw) return null
  try {
    return JSON.parse(raw) as Usuario
  } catch {
    return null
  }
}

export const useAuthStore = defineStore('auth', {
  state: () => ({
    user: loadUser() as Usuario | null,
  }),

  getters: {
    isLogged: (state) => !!state.user,
  },

  actions: {
    setUser(user: Usuario) {
      this.user = user
      localStorage.setItem(USER_KEY, JSON.stringify(user))
    },

    clearUser() {
      this.user = null
      localStorage.removeItem(USER_KEY)
    },
  },
})
