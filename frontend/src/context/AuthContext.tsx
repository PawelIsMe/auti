import { createContext, useCallback, useContext, useEffect, useMemo, useRef, useState, type ReactNode } from 'react'
import { api, clearTokens, getAccessToken, saveTokens } from '../services/api'
import type { AuthResponse, ChatMessage, User } from '../types'

interface AuthValue {
  user: User | null
  loading: boolean
  initialized: boolean | null
  signIn: (username: string, password: string, remember: boolean) => Promise<void>
  signUp: (payload: Record<string, unknown>) => Promise<void>
  finishSetup: (payload: Record<string, unknown>) => Promise<void>
  signOut: () => Promise<void>
  reloadUser: () => Promise<void>
  chatMessages: ChatMessage[]
  addChatMessage: (message: ChatMessage) => void
  clearChatHistory: () => void
}

const AuthContext = createContext<AuthValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [initialized, setInitialized] = useState<boolean | null>(null)
  const [chatMessages, setChatMessages] = useState<ChatMessage[]>([])
  const chatImageUrls = useRef(new Set<string>())

  const reloadUser = useCallback(async () => setUser(await api.me()), [])
  const addChatMessage = useCallback((message: ChatMessage) => {
    if (message.imageUrl?.startsWith('blob:')) chatImageUrls.current.add(message.imageUrl)
    setChatMessages((messages) => [...messages, message])
  }, [])
  const clearChatHistory = useCallback(() => {
    chatImageUrls.current.forEach((url) => URL.revokeObjectURL(url))
    chatImageUrls.current.clear()
    setChatMessages([])
  }, [])
  const accept = useCallback(async (tokens: AuthResponse, remember: boolean) => {
    saveTokens(tokens, remember)
    await reloadUser()
  }, [reloadUser])

  useEffect(() => {
    let live = true
    Promise.all([
      api.setupStatus().then((result) => { if (live) setInitialized(result.is_initialized) }),
      getAccessToken() ? api.me().then((profile) => { if (live) setUser(profile) }).catch(() => { clearTokens() }) : Promise.resolve(),
    ]).catch(() => { if (live && initialized === null) setInitialized(true) })
      .finally(() => { if (live) setLoading(false) })
    return () => { live = false }
  }, [])

  useEffect(() => () => {
    chatImageUrls.current.forEach((url) => URL.revokeObjectURL(url))
    chatImageUrls.current.clear()
  }, [])

  const signIn = useCallback(async (username: string, password: string, remember: boolean) => {
    await accept(await api.login(username, password, remember), remember)
  }, [accept])
  const signUp = useCallback(async (payload: Record<string, unknown>) => {
    await accept(await api.register(payload), false)
  }, [accept])
  const finishSetup = useCallback(async (payload: Record<string, unknown>) => {
    await accept(await api.firstSetup(payload), false)
    setInitialized(true)
  }, [accept])
  const signOut = useCallback(async () => {
    try { if (getAccessToken()) await api.logout() } catch { /* Local sign-out must work even if the API is unavailable. */ }
    finally { clearTokens(); setUser(null); clearChatHistory() }
  }, [clearChatHistory])

  const value = useMemo(() => ({ user, loading, initialized, signIn, signUp, finishSetup, signOut, reloadUser, chatMessages, addChatMessage, clearChatHistory }),
    [user, loading, initialized, signIn, signUp, finishSetup, signOut, reloadUser, chatMessages, addChatMessage, clearChatHistory])
  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>
}

export function useAuth() {
  const context = useContext(AuthContext)
  if (!context) throw new Error('useAuth musi być użyte wewnątrz AuthProvider.')
  return context
}
