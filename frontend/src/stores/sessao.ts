import { defineStore } from 'pinia'
import type { Usuario } from '../api/conta'

const CHAVE_USUARIO = 'usuario'

function carregarUsuario(): Usuario | null {
  try {
    const bruto = localStorage.getItem(CHAVE_USUARIO)
    return bruto ? (JSON.parse(bruto) as Usuario) : null
  } catch {
    return null
  }
}

export const useSessaoStore = defineStore('sessao', {
  state: () => ({
    usuario: carregarUsuario() as Usuario | null,
  }),

  getters: {
    logado: (state) => !!state.usuario,
  },

  actions: {
    definirUsuario(usuario: Usuario) {
      this.usuario = usuario
      localStorage.setItem(CHAVE_USUARIO, JSON.stringify(usuario))
    },

    limparUsuario() {
      this.usuario = null
      localStorage.removeItem(CHAVE_USUARIO)
    },
  },
})
