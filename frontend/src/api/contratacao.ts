import { api } from './client'
import type { Participante } from './conversa'
import type { Servico } from './taxonomia'

export type EstadoContratacao = 'proposta' | 'combinado' | 'concluido' | 'cancelado'

export interface Contratacao {
  idcontratacao: number
  idconversa: number
  /** Papel de quem está vendo. */
  papel: 'cliente' | 'prestador'
  outra_parte: Participante
  idproponente: number
  servico: Servico
  descricao: string
  local: string | null
  /** "2026-10-05" (data, sem hora). */
  data_prevista: string | null
  valor_estimado: number | null
  estado: EstadoContratacao
  aceite_cliente_em: string | null
  aceite_prestador_em: string | null
  combinado_em: string | null
  valor_final: number | null
  conclusao_cliente_em: string | null
  conclusao_prestador_em: string | null
  concluido_em: string | null
  cancelado_em: string | null
  idcancelado_por: number | null
  motivo_cancelamento: string | null
  /** Há algo para quem está vendo fazer (aceitar ou confirmar a conclusão). */
  aguardando_voce: boolean
  criado_em: string
  atualizado_em: string
}

export interface PropostaEntrada {
  idservico: number
  descricao: string
  local?: string | null
  data_prevista?: string | null
  valor_estimado?: number | null
}

export const contratacaoApi = {
  propor: (idconversa: number, dados: PropostaEntrada) =>
    api
      .post<Contratacao>(`/conversas/${idconversa}/contratacoes`, dados)
      .then((r) => r.data),

  /** Mais recente primeiro. */
  daConversa: (idconversa: number) =>
    api.get<Contratacao[]>(`/conversas/${idconversa}/contratacoes`).then((r) => r.data),

  minhas: (filtros: { papel?: 'cliente' | 'prestador'; estado?: EstadoContratacao } = {}) =>
    api.get<Contratacao[]>('/contratacoes', { params: filtros }).then((r) => r.data),

  obter: (idcontratacao: number) =>
    api.get<Contratacao>(`/contratacoes/${idcontratacao}`).then((r) => r.data),

  /** Quem edita já aceita a nova versão; o aceite do outro cai. */
  editar: (idcontratacao: number, dados: Partial<PropostaEntrada>) =>
    api.patch<Contratacao>(`/contratacoes/${idcontratacao}`, dados).then((r) => r.data),

  aceitar: (idcontratacao: number) =>
    api.post<Contratacao>(`/contratacoes/${idcontratacao}/aceitar`).then((r) => r.data),

  /** `valorFinal` = preço cobrado; obrigatório se ninguém informou ainda. */
  confirmarConclusao: (idcontratacao: number, valorFinal?: number) =>
    api
      .post<Contratacao>(
        `/contratacoes/${idcontratacao}/concluir`,
        valorFinal === undefined ? {} : { valor_final: valorFinal },
      )
      .then((r) => r.data),

  cancelar: (idcontratacao: number, motivo?: string) =>
    api
      .post<Contratacao>(`/contratacoes/${idcontratacao}/cancelar`, { motivo: motivo || null })
      .then((r) => r.data),
}

export const ROTULO_ESTADO: Record<EstadoContratacao, string> = {
  proposta: 'Proposta em negociação',
  combinado: 'Combinado',
  concluido: 'Concluído',
  cancelado: 'Cancelado',
}

export function estaAberta(c: Contratacao): boolean {
  return c.estado === 'proposta' || c.estado === 'combinado'
}

/** Momento em que quem está vendo e a outra parte agiram na fase atual. */
export function marcasDaFase(c: Contratacao): { minha: string | null; dela: string | null } {
  const prefixo = c.estado === 'proposta' ? 'aceite' : 'conclusao'
  const minha = c[`${prefixo}_${c.papel}_em` as keyof Contratacao] as string | null
  const outro = c.papel === 'cliente' ? 'prestador' : 'cliente'
  const dela = c[`${prefixo}_${outro}_em` as keyof Contratacao] as string | null
  return { minha, dela }
}

/** Frase curta do que falta: "Aguardando você aceitar", "Aguardando Pedro confirmar"… */
export function situacao(c: Contratacao): string {
  if (c.estado === 'concluido') return 'Concluído pelos dois lados'
  if (c.estado === 'cancelado') return 'Cancelado'
  const { minha } = marcasDaFase(c)
  const verbo = c.estado === 'proposta' ? 'aceitar a proposta' : 'confirmar a conclusão'
  return minha ? `Aguardando ${c.outra_parte.nome} ${verbo}` : `Aguardando você ${verbo}`
}
