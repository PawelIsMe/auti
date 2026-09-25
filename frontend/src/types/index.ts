export interface User {
  id: number
  username: string
  role: 'admin' | 'user'
  preferred_name: string
  date_of_birth: string
  gemini_api_key?: string | null
  info_for_ai?: string | null
}

export interface AuthResponse {
  access_token: string
  refresh_token?: string | null
  token_type: string
}

export interface ChatMessage {
  id: string
  role: 'user' | 'assistant'
  content: string
  time: Date
  imageUrl?: string
}

export interface InviteResponse {
  code: string
  is_used: boolean
}
