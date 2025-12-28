// 等价于 import api from '@/api/index'
import api from '@/api'
import type {
  AuthResponse,
  LoginParams,
  RegisterParams,
  ResetPasswordParams,
  User,
} from '@/types/user.types'

// ========== 登录 API ==========
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

// ========== 注册 API ==========
// --- 发送验证码 ---
export async function sendCodeApi(email: string): Promise<{ message: string }> {
  const response = await api.post('/auth/send-code', { email })
  return response.data
}

// --- 注册 --
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
export async function resetPasswordApi(params: ResetPasswordParams): Promise<{ message: string }> {
  const response = await api.post<{ message: string }>('/auth/reset-password', params)
  return response.data
}
