// 等价于 import api from '@/api/index'
import api from '@/api'

// ========== 1. 定义数据模型 (与后端 Schema 对应) ==========
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

  last_login?: string | null // 后端是 datetime | None
  updated_at: string // 后端是 datetime
  created_at: string // ISO string
}

// 统一的认证响应 (注册/登录通用)
export interface AuthResponse {
  access_token: string
  token_type: string
  user: User
}

// ========== 2.登录 API ==========
// --- 登录 ---
export interface LoginParams {
  username: string
  password: string
  remember?: boolean
}

export async function loginApi(params: LoginParams): Promise<AuthResponse> {
  // OAuth2 要求 Form Data 格式
  const formData = new URLSearchParams()
  formData.append('username', params.username)
  formData.append('password', params.password)
  if (params.remember) formData.append('remember', 'true')

  const response = await api.post<AuthResponse>('/auth/login', formData, {
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  })
  return response.data
}

// ========== 2.注册 API ==========
// --- 发送验证码 ---
export async function sendCodeApi(email: string): Promise<{ message: string }> {
  const response = await api.post('/auth/send-code', { email })
  return response.data
}

// --- 注册 --
export interface RegisterParams {
  email: string
  password: string
  verification_code: string
}

export async function registerApi(params: RegisterParams): Promise<AuthResponse> {
  const response = await api.post<AuthResponse>('/auth/register', params)
  return response.data
}

// ========== 3.获取用户信息 API ==========
export async function getUserMeApi(): Promise<User> {
  const response = await api.get<User>('/users/me')
  return response.data
}

// ========== 4.忘记密码 API ==========
// 发送重置密码验证码
export async function forgotPasswordApi(email: string): Promise<{ message: string }> {
  const response = await api.post('/auth/forgot-password', { email })
  return response.data
}

// 重置密码
export interface ResetPasswordParams {
  email: string
  new_password: string
  verification_code: string
}

export async function resetPasswordApi(params: ResetPasswordParams): Promise<{ message: string }> {
  const response = await api.post<{ message: string }>('/auth/reset-password', params)
  return response.data
}
