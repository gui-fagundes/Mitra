const moeda = new Intl.NumberFormat('pt-BR', { maximumFractionDigits: 2 })

/** "R$ 80–150", "A partir de R$ 80", "Até R$ 150" ou "Sob consulta". */
export function formatarFaixaPreco(min: number | null, max: number | null): string {
  if (min != null && max != null) {
    return min === max ? `R$ ${moeda.format(min)}` : `R$ ${moeda.format(min)}–${moeda.format(max)}`
  }
  if (min != null) return `A partir de R$ ${moeda.format(min)}`
  if (max != null) return `Até R$ ${moeda.format(max)}`
  return 'Sob consulta'
}

const DIA_MS = 24 * 60 * 60 * 1000

/** Duração desde a data, para "atende há …": "3 meses", "2 anos", "menos de 1 mês". */
export function tempoDesde(dataIso: string, agora = new Date()): string {
  const dias = Math.floor((agora.getTime() - new Date(dataIso).getTime()) / DIA_MS)
  const meses = Math.floor(dias / 30)
  if (meses < 1) return 'menos de 1 mês'
  if (meses < 12) return meses === 1 ? '1 mês' : `${meses} meses`
  const anos = Math.floor(meses / 12)
  return anos === 1 ? '1 ano' : `${anos} anos`
}

/** Última atividade: "hoje", "ontem", "há 5 dias", "há 2 meses". */
export function atividadeRelativa(dataIso: string | null, agora = new Date()): string {
  if (!dataIso) return '—'
  const dias = Math.floor((agora.getTime() - new Date(dataIso).getTime()) / DIA_MS)
  if (dias <= 0) return 'hoje'
  if (dias === 1) return 'ontem'
  if (dias < 30) return `há ${dias} dias`
  const meses = Math.floor(dias / 30)
  return meses === 1 ? 'há 1 mês' : `há ${meses} meses`
}

/** "12345678000195" → "12.345.678/0001-95". Serve também para o CNPJ alfanumérico. */
export function formatarCnpj(cnpj: string): string {
  const c = cnpj.replace(/[^0-9A-Za-z]/g, '').toUpperCase()
  if (c.length !== 14) return cnpj
  return `${c.slice(0, 2)}.${c.slice(2, 5)}.${c.slice(5, 8)}/${c.slice(8, 12)}-${c.slice(12)}`
}

/** "2026-09-28T10:00:00" → "28/09/2026". */
export function formatarData(dataIso: string): string {
  return new Date(dataIso).toLocaleDateString('pt-BR')
}

/**
 * Destino seguro para depois do login: só caminhos internos do Mitra
 * ("/mensagens/3"), nunca outro site ("//malicioso.com", "https://…").
 */
export function destinoInterno(valor: unknown): string | null {
  const caminho = Array.isArray(valor) ? valor[0] : valor
  if (typeof caminho !== 'string') return null
  return caminho.startsWith('/') && !caminho.startsWith('//') ? caminho : null
}

function mesmoDia(a: Date, b: Date): boolean {
  return a.toDateString() === b.toDateString()
}

/** "14:32". */
export function formatarHora(dataIso: string): string {
  return new Date(dataIso).toLocaleTimeString('pt-BR', { hour: '2-digit', minute: '2-digit' })
}

/** Separador de dia no chat: "Hoje", "Ontem" ou "12/09/2026". */
export function rotuloDia(dataIso: string, agora = new Date()): string {
  const data = new Date(dataIso)
  if (mesmoDia(data, agora)) return 'Hoje'
  const ontem = new Date(agora)
  ontem.setDate(agora.getDate() - 1)
  if (mesmoDia(data, ontem)) return 'Ontem'
  return data.toLocaleDateString('pt-BR')
}

/** Horário compacto da lista de conversas: "14:32" (hoje), "Ontem" ou "12/09". */
export function quandoCurto(dataIso: string, agora = new Date()): string {
  const rotulo = rotuloDia(dataIso, agora)
  if (rotulo === 'Hoje') return formatarHora(dataIso)
  if (rotulo === 'Ontem') return rotulo
  return new Date(dataIso).toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' })
}
