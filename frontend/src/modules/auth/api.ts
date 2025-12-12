/**
 * Auth 模块 API
 * 封装 Axios 实例和认证相关请求
 */
import axios from 'axios'
import { getToken, removeToken } from './token'

// 创建 Axios 实例
const api = axios.create({
  baseURL: '/api/v1', // 基础路径（后续可从环境变量读取）
  timeout: 10000, // 超时时间 10s
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器: 自动添加 Token
api.interceptors.request.use(
  (config) => {
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => Promise.reject(error),
)

// 响应拦截器: 统一错误处理
api.interceptors.response.use(
  (response) => response,
  (error) => {
    // Token 过期或无效
    if (error.response?.status === 401) {
      removeToken()
      // 可选： 跳转登录页
      window.location.href = '/login'
    }
    return Promise.reject(error)
  },
)

// ========== Auth API ==========
export interface LoginParams {
  username: string
  password: string
}

export interface LoginResponse {
  access_token: string
  token_type: string
}

export async function loginApi(params: LoginParams): Promise<LoginResponse> {
  // OAuth2 要求 Form Data 格式
  const formData = new URLSearchParams()
  formData.append('username', params.username)
  formData.append('password', params.password)

  const response = await api.post('/auth/login', formData, {
    headers: {
      'Content-Type': 'application/x-www-form-urlencoded',
    },
  })
  return response.data
}

export default api
