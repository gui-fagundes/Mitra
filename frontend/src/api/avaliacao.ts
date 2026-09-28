import { api } from './client'

export interface Avaliacao {
  idavaliacao: number
  idcontratacao: number
  nota: number
  comentario: string | null
  /** Nome abreviado do cliente ("Cris S."). */
  autor: string
  servico: string
  criado_em: string
  resposta: string | null
  resposta_em: string | null
}

export interface PaginaAvaliacoes {
  total: number
  nota_media: number | null
  itens: Avaliacao[]
}

export const TAMANHO_MAXIMO_TEXTO_AVALIACAO = 1000

export const avaliacaoApi = {
  /** Só o cliente, com a contratação concluída, até 30 dias depois. Não é editável. */
  avaliar: (idcontratacao: number, nota: number, comentario?: string) =>
    api
      .post<Avaliacao>(`/contratacoes/${idcontratacao}/avaliacao`, {
        nota,
        comentario: comentario?.trim() || null,
      })
      .then((r) => r.data),

  /** Resposta pública do prestador avaliado, uma vez. */
  responder: (idavaliacao: number, texto: string) =>
    api.post<Avaliacao>(`/avaliacoes/${idavaliacao}/resposta`, { texto }).then((r) => r.data),

  doPrestador: (idusuario: number, paginacao: { limite?: number; deslocamento?: number } = {}) =>
    api
      .get<PaginaAvaliacoes>(`/prestadores/${idusuario}/avaliacoes`, { params: paginacao })
      .then((r) => r.data),
}

/** 4.5 → "4,5". */
export function formatarNota(nota: number): string {
  return nota.toFixed(1).replace('.', ',')
}
