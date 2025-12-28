import { useToastStore } from '@/stores/toast.store'
import type { BackendError } from '@/types/common.types'
import { getToken, removeToken } from '@/utils/token'
import axios, { AxiosError } from 'axios'

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
  (error: AxiosError) => {
    const toastStore = useToastStore()

    // 1. 后端返回的错误
    if (error.response) {
      const data = error.response.data as any

      // 自定义错误格式
      if (data?.error) {
        const { code, message } = data.error
        switch (code) {
          // 1.1 401 错误: 未授权或 Token 过期
          case 'INVALID_CREDENTIALS':
          case 'UNAUTHORIZED':
            // 判断是不是登录接口
            const isAuthRequest = ['/auth/login', '/auth/register'].some((path) =>
              error.config?.url?.endsWith(path),
            )

            // 不是登录接口 → Token 过期 → 重定向
            if (!isAuthRequest) {
              removeToken()
              toastStore.error('登录已过期，请重新登录')
              setTimeout(() => {
                window.location.href = '/login'
              }, 1500)
            }
            break

          // 1.2 表单错误：表单下方显示，业务代码自行处理, 不用 Toast
          case 'EMAIL_ALREADY_EXISTS':
          case 'INVALID_VERIFICATION_CODE':
          case 'RESOURCE_NOT_FOUND':
            break

          // 1.3 其他错误统一用 Toast 提示
          default:
            toastStore.error(message)
        }

        // 将后端错误信息附加到 error 对象，方便业务代码访问
        error.backendError = data.error
      } else {
        toastStore.error(data?.detail || '服务器错误，请稍后重试')
      }
    }

    // 2. 网络错误
    else if (error.request) {
      toastStore.error('网络请求失败，请检查网络')
    }

    // 3. 其他错误
    else {
      toastStore.error('请求失败，请稍后重试')
    }

    return Promise.reject(error)
  },
)

// 声明类型扩展（TypeScript），将后端错误信息添加到 AxiosError 类型中
declare module 'axios' {
  export interface AxiosError {
    backendError?: BackendError
  }
}

// 默认导出，导入的时候不需要加花括号，名字可以自定。
// ! 一个文件只能有一个默认导出
export default api

// 导出业务模块, 方便统一从 api 目录下导入
export * from './auth.api'
