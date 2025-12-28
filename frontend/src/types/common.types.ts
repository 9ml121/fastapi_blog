//  通用分页响应包装器,用于所有列表接口 (Post, Comment, etc.)
export interface PaginatedParams {
  page?: number
  size?: number
  sort?: string
  order?: 'asc' | 'desc'
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  size: number
  pages: number
}

// 后端错误响应类型, status_code 在 header 中返回
export interface BackendError {
  code: string
  message: string
  details?: Record<string, any>
}

export interface BackendErrorResponse {
  error: BackendError
}
