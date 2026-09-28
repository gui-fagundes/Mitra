import { api } from './client'

export interface Usuario {
  idusuario: number
  nome: string
  email: string
  ativo: boolean
  criado_em: string
}

export const contaApi = {
  cadastrar: (nome: string, email: string, senha: string) =>
    api.post<Usuario>('/conta/cadastro', { nome, email, senha }).then((r) => r.data),

  entrar: (email: string, senha: string) =>
    api.post<Usuario>('/conta/entrar', { email, senha }).then((r) => r.data),

  sair: () => api.post<void>('/conta/sair').then(() => undefined),

  obter: () => api.get<Usuario>('/conta').then((r) => r.data),
}
