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
