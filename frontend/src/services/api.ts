import type { AuthResponse, InviteResponse, User } from '../types'

const API = '/api'
const ACCESS_KEY = 'auti.access'
const REFRESH_KEY = 'auti.refresh'
const PERSIST_KEY = 'auti.persist'

export function getAccessToken() {
  return localStorage.getItem(ACCESS_KEY) ?? sessionStorage.getItem(ACCESS_KEY)
}

export function saveTokens(tokens: AuthResponse, remember = false) {
  clearTokens()
  const store = remember ? localStorage : sessionStorage
  store.setItem(ACCESS_KEY, tokens.access_token)
  if (tokens.refresh_token) store.setItem(REFRESH_KEY, tokens.refresh_token)
  if (remember) localStorage.setItem(PERSIST_KEY, 'true')
}

export function clearTokens() {
  for (const store of [localStorage, sessionStorage]) {
    store.removeItem(ACCESS_KEY)
    store.removeItem(REFRESH_KEY)
  }
  localStorage.removeItem(PERSIST_KEY)
}

export function shouldRemember() {
  return localStorage.getItem(PERSIST_KEY) === 'true'
}

export class ApiError extends Error {
  status: number
  constructor(message: string, status: number) {
    super(message)
    this.name = 'ApiError'
    this.status = status
  }
}

async function authorizedFetch(path: string, init: RequestInit = {}, retry = true): Promise<Response> {
  const headers = new Headers(init.headers)
  if (init.body && !headers.has('Content-Type')) headers.set('Content-Type', 'application/json')
  const token = getAccessToken()
  if (token) headers.set('Authorization', `Bearer ${token}`)
  let response: Response
  try {
    response = await fetch(`${API}${path}`, { ...init, headers })
  } catch {
    throw new ApiError('Nie udało się połączyć z serwerem. Sprawdź połączenie i spróbuj ponownie.', 0)
  }
  if (response.status === 401 && retry && !path.startsWith('/auth/')) {
    const refresh = localStorage.getItem(REFRESH_KEY) ?? sessionStorage.getItem(REFRESH_KEY)
    if (refresh) {
      try {
        const renewed = await request<AuthResponse>('/auth/refresh', {
          method: 'POST', body: JSON.stringify({ refresh_token: refresh }),
        }, false)
        saveTokens(renewed, shouldRemember())
        return authorizedFetch(path, init, false)
      } catch {
        clearTokens()
      }
    }
  }
  return response
}

async function request<T>(path: string, init: RequestInit = {}, retry = true): Promise<T> {
  const response = await authorizedFetch(path, init, retry)
  if (!response.ok) {
    let message = `Błąd serwera (${response.status}).`
    try {
      const body = await response.json() as { detail?: string | { msg?: string }[] }
      if (typeof body.detail === 'string') message = body.detail
      else if (Array.isArray(body.detail)) message = body.detail.map((item) => item.msg).filter(Boolean).join(', ')
    } catch { /* Response did not contain JSON. */ }
    throw new ApiError(message, response.status)
  }
  if (response.status === 204) return undefined as T
  return response.json() as Promise<T>
}

function snapshotApiPath(imageUrl?: string) {
  if (!imageUrl) return '/static/snapshot'
  const url = new URL(imageUrl, window.location.origin)
  const path = url.pathname
  if (path === '/api/static/snapshot') return '/static/snapshot'
  if (path.startsWith('/api/')) return path.slice(4)
  return path
}

const json = (method: string, payload?: unknown): RequestInit => ({
  method,
  ...(payload === undefined ? {} : { body: JSON.stringify(payload) }),
})

export const api = {
  setupStatus: () => request<{ is_initialized: boolean }>('/setup/status'),
  firstSetup: (payload: Record<string, unknown>) => request<AuthResponse>('/setup/first', json('POST', payload)),
  login: (username: string, password: string, remember_me: boolean) =>
    request<AuthResponse>('/auth/login', json('POST', { username, password, remember_me })),
  register: (payload: Record<string, unknown>) => request<AuthResponse>('/auth/register', json('POST', payload)),
  logout: () => request<{ message: string }>('/auth/logout', json('POST')),
  me: () => request<User>('/users/me'),
  updateProfile: (payload: { gemini_api_key?: string | null; info_for_ai?: string | null }) =>
    Promise.all([
      payload.gemini_api_key === undefined ? Promise.resolve() : request('/users/me/gemini-key', json('PUT', { gemini_api_key: payload.gemini_api_key })),
      payload.info_for_ai === undefined ? Promise.resolve() : request('/users/me/info-for-ai', json('PUT', { info_for_ai: payload.info_for_ai })),
    ]),
  updateBirthDate: (date_of_birth: string) => request('/users/me/date-of-birth', json('PUT', { date_of_birth })),
  deleteAccount: () => request<void>('/users/me', json('DELETE')),
  chat: (message: string) => request<{ type: string; reply: string; img_url?: string }>('/chat/session', json('POST', { message })),
  snapshot: async (imageUrl?: string) => {
    const response = await authorizedFetch(snapshotApiPath(imageUrl), { method: 'POST' })
    if (!response.ok) {
      let message = 'Nie udało się pobrać zdjęcia z kamery.'
      try { const body = await response.json() as { detail?: string }; if (body.detail) message = body.detail } catch { /* Image endpoint may return a non-JSON error. */ }
      throw new ApiError(message, response.status)
    }
    return response.blob()
  },
  users: () => request<User[]>('/admin/users'),
  setRole: (id: number, role: User['role']) => request(`/admin/users/${id}/role`, json('PUT', { role })),
  deleteUser: (id: number) => request<void>(`/admin/users/${id}`, json('DELETE')),
  createInvite: () => request<InviteResponse>('/admin/invitations', json('POST')),
}
