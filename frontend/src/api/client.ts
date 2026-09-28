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

export const api = axios.create({
  baseURL: '/api',
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
