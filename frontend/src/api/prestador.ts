import { api } from './client'
import type { Cidade } from './cidade'
import type { Servico } from './taxonomia'

/** A vitrine do próprio prestador (área logada). */
export interface Vitrine {
  idprestadorperfil: number
  bio: string | null
  preco_min: number | null
  preco_max: number | null
  disponibilidade: string | null
  servicos: Servico[]
  cnpj_validado: boolean
  criado_em: string
  atualizado_em: string
}

/** Campos ausentes não mudam; `servicos` substitui a lista inteira (até 3 ids). */
export interface VitrineAtualizacao {
  bio?: string | null
  preco_min?: number | null
  preco_max?: number | null
  disponibilidade?: string | null
  servicos?: number[]
}

export interface CategoriaResumo {
  idcategoria: number
  nome: string
  slug: string
}

/** Perfil público de um prestador. */
export interface PrestadorPublico {
  idusuario: number
  nome: string
  foto_url: string | null
  cidade: Cidade | null
  bio: string | null
  preco_min: number | null
  preco_max: number | null
  disponibilidade: string | null
  cnpj_validado: boolean
  prestador_desde: string
  ultimo_acesso_em: string | null
  categorias: CategoriaResumo[]
  servicos: Servico[]
  servicos_concluidos: number
  nota_media: number | null
  qtd_avaliacoes: number
}

export const LIMITE_SERVICOS = 3

export const prestadorApi = {
  obterVitrine: () => api.get<Vitrine>('/conta/vitrine').then((r) => r.data),

  criarVitrine: (dados: VitrineAtualizacao = {}) =>
    api.post<Vitrine>('/conta/vitrine', dados).then((r) => r.data),

  atualizarVitrine: (dados: VitrineAtualizacao) =>
    api.patch<Vitrine>('/conta/vitrine', dados).then((r) => r.data),

  obterPublico: (idusuario: number) =>
    api.get<PrestadorPublico>(`/prestadores/${idusuario}`).then((r) => r.data),
}
