import axios from 'axios'
import { getToken, removeToken } from '@/utils/token'

// Axios 实例
const api = axios.create({
  // 基础路径（优先从环境变量读取）
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 10000,
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
      // 判断是不是登录接口
      const isLoginRequest = error.config?.url?.includes('/auth/login')
      // 不是登录接口 → Token 过期 → 重定向
      if (!isLoginRequest) {
        removeToken()
        // 可选： 跳转登录页
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

// 默认导出，导入的时候不需要加花括号，名字可以自定。
// ! 一个文件只能有一个默认导出
export default api

// 导出业务模块, 方便统一从 api 目录下导入
export * from './auth.api'
