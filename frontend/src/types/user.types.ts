// 1. 核心实体：用户 (Entity), 与后端 Schema 对应
export interface User {
  id: string
  username: string
  email: string
  nickname?: string | null
  avatar?: string | null
  bio?: string | null
  role: string
  is_active: boolean
  is_verified: boolean
  last_login?: string | null
  updated_at: string
  created_at: string
}

// 2. 认证响应 DTO
export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

// 3. 业务操作参数 (Payloads)
export interface LoginParams {
  username: string
  password: string
  remember?: boolean
}

export interface RegisterParams {
  email: string
  password: string
  verification_code: string
}

export interface ResetPasswordParams {
  email: string
  new_password: string
  verification_code: string
}
