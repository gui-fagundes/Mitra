import { api } from './client'
import type { Cidade } from './cidade'

export interface Usuario {
  idusuario: number
  nome: string
  email: string
  telefone: string | null
  foto_url: string | null
  cidade: Cidade | null
  aceite_termos_em: string | null
  notificar_email: boolean
  busca_somente_cnpj: boolean
  ativo: boolean
  criado_em: string
}

export interface CadastroEntrada {
  nome: string
  email: string
  senha: string
  aceite_termos: boolean
  idcidade?: number | null
  telefone?: string | null
}

/** Campos ausentes não mudam; `null` limpa cidade, telefone e foto. */
export interface ContaAtualizacao {
  nome?: string
  idcidade?: number | null
  telefone?: string | null
  notificar_email?: boolean
  busca_somente_cnpj?: boolean
}

export const contaApi = {
  cadastrar: (dados: CadastroEntrada) =>
    api.post<Usuario>('/conta/cadastro', dados).then((r) => r.data),

  entrar: (email: string, senha: string) =>
    api.post<Usuario>('/conta/entrar', { email, senha }).then((r) => r.data),

  sair: () => api.post<void>('/conta/sair').then(() => undefined),

  obter: () => api.get<Usuario>('/conta').then((r) => r.data),

  atualizar: (dados: ContaAtualizacao) =>
    api.patch<Usuario>('/conta', dados).then((r) => r.data),

  /** JPG, PNG ou WebP de até 5 MB. */
  enviarFoto: (arquivo: File) => {
    const formulario = new FormData()
    formulario.append('arquivo', arquivo)
    // Sobrescreve o JSON padrão do cliente; o navegador completa o boundary.
    return api
      .put<Usuario>('/conta/foto', formulario, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data)
  },

  removerFoto: () => api.delete<Usuario>('/conta/foto').then((r) => r.data),

  /** Sempre resolve (204), exista ou não conta com o e-mail. */
  esqueciSenha: (email: string) =>
    api.post<void>('/conta/senha/esqueci', { email }).then(() => undefined),

  redefinirSenha: (token: string, novaSenha: string) =>
    api
      .post<void>('/conta/senha/redefinir', { token, nova_senha: novaSenha })
      .then(() => undefined),
}
