import axios, { AxiosError } from 'axios'

export class ErroApi extends Error {
  status: number
  detalhe: string
  constructor(status: number, detalhe: string) {
    super(detalhe)
    this.status = status
    this.detalhe = detalhe
  }
}

export const BASE_API = '/api'

export const api = axios.create({
  baseURL: BASE_API,
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

// O FastAPI devolve erros em `detail` (nome fixo do framework): string para
// HTTPException, lista de erros de validação para 422.
api.interceptors.response.use(
  (res) => res,
  (err: AxiosError<{ detail?: unknown }>) => {
    const status = err.response?.status ?? 0
    let detalhe = err.message

    const bruto = err.response?.data?.detail
    if (typeof bruto === 'string') detalhe = bruto
    else if (Array.isArray(bruto)) detalhe = bruto.map((d: any) => d.msg).join('; ')

    return Promise.reject(new ErroApi(status, detalhe))
  },
)

/**
 * URL para exibir um arquivo enviado (foto, portfólio). A API guarda o caminho
 * público ("/arquivos/fotos/x.jpg"), servido por ela mesma — então passa pelo
 * mesmo prefixo das chamadas. URLs absolutas (storage externo no futuro) passam direto.
 */
export function urlArquivo(caminho: string | null | undefined): string | null {
  if (!caminho) return null
  return /^https?:\/\//.test(caminho) ? caminho : `${BASE_API}${caminho}`
}
