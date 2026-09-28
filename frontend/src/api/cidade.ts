import { api } from './client'

export interface Cidade {
  idcidade: number
  nome: string
  uf: string
}

export const cidadeApi = {
  listar: () => api.get<Cidade[]>('/cidades').then((r) => r.data),
}

export function rotuloCidade(cidade: Cidade): string {
  return `${cidade.nome}, ${cidade.uf}`
}
