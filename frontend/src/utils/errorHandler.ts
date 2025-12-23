/**
 * 错误处理工具函数（备用方案）
 *
 * 当前项目使用拦截器处理错误，此文件暂未使用。
 * 保留用于：
 * 1. 非 API 请求的错误处理（如 WebSocket）
 * 2. 需要自定义错误处理逻辑的场景
 * 3. 单元测试
 */

import type { AxiosError } from 'axios'

// 后端错误响应类型
export interface BackendError {
  code: string
  message: string
  details?: Record<string, any>
}

export interface BackendErrorResponse {
  error: BackendError
}

// 类型守卫：判断是否为 AxiosError
export function isAxiosError(error: unknown): error is AxiosError {
  return (error as AxiosError).isAxiosError === true
}

// 类型守卫：判断是否为后端错误响应
export function isBackendErrorResponse(data: unknown): data is BackendErrorResponse {
  return (
    typeof data === 'object' &&
    data !== null &&
    'error' in data &&
    typeof (data as any).error === 'object' &&
    'code' in (data as any).error &&
    'message' in (data as any).error
  )
}

// 提取错误信息（完全类型安全）
export function getErrorMessage(error: unknown): string {
  if (!isAxiosError(error)) {
    return '网络请求失败'
  }

  const responseData = error.response?.data

  if (isBackendErrorResponse(responseData)) {
    return responseData.error.message
  }

  // 处理其他情况...
  return '未知错误'
}
