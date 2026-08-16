import axios, { AxiosError } from 'axios'

export class ApiError extends Error {
  status: number
  detail: string
  constructor(status: number, detail: string) {
    super(detail)
    this.status = status
    this.detail = detail
  }
}

export const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
  withCredentials: true,
})

api.interceptors.response.use(
  (res) => res,
  (err: AxiosError<{ detail?: unknown }>) => {
    const status = err.response?.status ?? 0
    let detail = err.message

    const raw = err.response?.data?.detail
    if (typeof raw === 'string') detail = raw
    else if (Array.isArray(raw)) detail = raw.map((d: any) => d.msg).join('; ')

    return Promise.reject(new ApiError(status, detail))
  },
)
