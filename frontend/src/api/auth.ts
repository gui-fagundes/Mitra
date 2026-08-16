import { api } from './client'

export interface Usuario {
  idusuario: number
  nome: string
  email: string
  ativo: boolean
  data_criacao: string
}

export const authApi = {
  signup: (nome: string, email: string, senha: string) =>
    api.post<Usuario>('/auth/signup', { nome, email, senha }).then((r) => r.data),

  login: (email: string, senha: string) =>
    api.post<Usuario>('/auth/login', { email, senha }).then((r) => r.data),

  logout: () => api.post<void>('/auth/logout').then(() => undefined),

  me: () => api.get<Usuario>('/auth/me').then((r) => r.data),
}
