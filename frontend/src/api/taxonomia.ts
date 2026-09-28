import { api } from './client'

export interface Servico {
  idservico: number
  idcategoria: number
  nome: string
  slug: string
}

export interface Categoria {
  idcategoria: number
  nome: string
  slug: string
  /** Classe do Font Awesome 4.7, ex.: "fa-wrench". */
  icone: string
  servicos: Servico[]
}

export const taxonomiaApi = {
  listarCategorias: () => api.get<Categoria[]>('/categorias').then((r) => r.data),

  listarServicos: (categoria?: string) =>
    api.get<Servico[]>('/servicos', { params: { categoria } }).then((r) => r.data),
}
