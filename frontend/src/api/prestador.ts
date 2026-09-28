import { api } from './client'
import type { Cidade } from './cidade'
import type { Servico } from './taxonomia'

export interface ItemPortfolio {
  idprestadorportfolio: number
  /** Caminho público; exibir com urlArquivo(). */
  imagem_url: string
  legenda: string | null
  ordem: number
}

export const LIMITE_PORTFOLIO = 10

/** A vitrine do próprio prestador (área logada). */
export interface Vitrine {
  idprestadorperfil: number
  bio: string | null
  preco_min: number | null
  preco_max: number | null
  disponibilidade: string | null
  servicos: Servico[]
  portfolio: ItemPortfolio[]
  /** Sem máscara; só o próprio prestador vê. Ter CNPJ = ter o selo. */
  cnpj: string | null
  cnpj_validado: boolean
  cnpj_validado_em: string | null
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
  portfolio: ItemPortfolio[]
  servicos_concluidos: number
  nota_media: number | null
  qtd_avaliacoes: number
}

export const LIMITE_SERVICOS = 3

/** Card de um prestador no resultado da busca. */
export interface CartaoPrestador {
  idusuario: number
  nome: string
  foto_url: string | null
  cidade: Cidade | null
  bio: string | null
  preco_min: number | null
  preco_max: number | null
  cnpj_validado: boolean
  servicos: Servico[]
  ultimo_acesso_em: string | null
  nota_media: number | null
  qtd_avaliacoes: number
}

export interface ResultadoBusca {
  total: number
  itens: CartaoPrestador[]
}

export type OrdemBusca = 'reputacao' | 'melhor' | 'muitas' | 'recentes'

export interface FiltrosBusca {
  termo?: string
  /** Prioriza (não filtra) prestadores desta cidade. */
  idcidade?: number
  categoria?: string
  servicos?: number[]
  somente_cnpj?: boolean
  preco_min?: number
  preco_max?: number
  nota_min?: number
  ordem?: OrdemBusca
  limite?: number
  deslocamento?: number
}

export const TAMANHO_PAGINA = 20

export const prestadorApi = {
  obterVitrine: () => api.get<Vitrine>('/conta/vitrine').then((r) => r.data),

  criarVitrine: (dados: VitrineAtualizacao = {}) =>
    api.post<Vitrine>('/conta/vitrine', dados).then((r) => r.data),

  atualizarVitrine: (dados: VitrineAtualizacao) =>
    api.patch<Vitrine>('/conta/vitrine', dados).then((r) => r.data),

  /** Só grava se a Receita (via BrasilAPI) confirmar que está ativo. Aceita com ou sem máscara. */
  cadastrarCnpj: (cnpj: string) =>
    api.put<Vitrine>('/conta/vitrine/cnpj', { cnpj }).then((r) => r.data),

  removerCnpj: () => api.delete<Vitrine>('/conta/vitrine/cnpj').then((r) => r.data),

  adicionarAoPortfolio: (arquivo: File, legenda?: string) => {
    const formulario = new FormData()
    formulario.append('arquivo', arquivo)
    if (legenda) formulario.append('legenda', legenda)
    return api
      .post<ItemPortfolio>('/conta/vitrine/portfolio', formulario, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      .then((r) => r.data)
  },

  editarLegenda: (idprestadorportfolio: number, legenda: string | null) =>
    api
      .patch<ItemPortfolio>(`/conta/vitrine/portfolio/${idprestadorportfolio}`, { legenda })
      .then((r) => r.data),

  removerDoPortfolio: (idprestadorportfolio: number) =>
    api.delete<void>(`/conta/vitrine/portfolio/${idprestadorportfolio}`).then(() => undefined),

  /** Todos os ids do portfólio, na nova ordem. */
  reordenarPortfolio: (ids: number[]) =>
    api.put<ItemPortfolio[]>('/conta/vitrine/portfolio/ordem', { ids }).then((r) => r.data),

  /** Busca pública com ordenação orgânica (sem posições pagas). */
  buscar: (filtros: FiltrosBusca) =>
    api
      .get<ResultadoBusca>('/prestadores', {
        params: filtros,
        // servicos=1&servicos=2 (formato que o FastAPI espera), sem colchetes.
        paramsSerializer: { indexes: null },
      })
      .then((r) => r.data),

  obterPublico: (idusuario: number) =>
    api.get<PrestadorPublico>(`/prestadores/${idusuario}`).then((r) => r.data),
}
