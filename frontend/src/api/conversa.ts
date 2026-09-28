import { api } from './client'

export interface Participante {
  idusuario: number
  nome: string
  foto_url: string | null
  ultimo_acesso_em: string | null
}

export interface Mensagem {
  idmensagem: number
  idconversa: number
  idautor: number
  /** "evento" = registro automático (proposta enviada, plano confirmado…). */
  tipo: 'texto' | 'evento'
  texto: string
  criado_em: string
}

export interface Conversa {
  idconversa: number
  /** Papel de quem está vendo: "cliente" iniciou o contato; "prestador" foi procurado. */
  papel: 'cliente' | 'prestador'
  outra_parte: Participante
  ultima_mensagem: Mensagem | null
  criado_em: string
  atualizado_em: string
}

export interface PaginaMensagens {
  /** Ordem cronológica (mais antiga primeiro). */
  itens: Mensagem[]
  tem_mais_antigas: boolean
}

export const TAMANHO_MAXIMO_MENSAGEM = 2000

export const conversaApi = {
  /** Inicia contato com um prestador (ou reaproveita a conversa existente). */
  iniciar: (idprestador: number, texto: string) =>
    api.post<Conversa>('/conversas', { idprestador, texto }).then((r) => r.data),

  listar: () => api.get<Conversa[]>('/conversas').then((r) => r.data),

  obter: (idconversa: number) =>
    api.get<Conversa>(`/conversas/${idconversa}`).then((r) => r.data),

  /** Sem cursores: as mais recentes. `antesDe`: página anterior. `depoisDe`: só as novas. */
  mensagens: (idconversa: number, cursores: { antesDe?: number; depoisDe?: number } = {}) =>
    api
      .get<PaginaMensagens>(`/conversas/${idconversa}/mensagens`, {
        params: { antes_de: cursores.antesDe, depois_de: cursores.depoisDe },
      })
      .then((r) => r.data),

  enviar: (idconversa: number, texto: string) =>
    api.post<Mensagem>(`/conversas/${idconversa}/mensagens`, { texto }).then((r) => r.data),
}

const CINCO_MINUTOS_MS = 5 * 60 * 1000

/** "Online" = acessou nos últimos 5 minutos (mesmo intervalo em que o acesso é gravado). */
export function estaOnline(participante: Participante, agora = new Date()): boolean {
  if (!participante.ultimo_acesso_em) return false
  return agora.getTime() - new Date(participante.ultimo_acesso_em).getTime() <= CINCO_MINUTOS_MS
}
