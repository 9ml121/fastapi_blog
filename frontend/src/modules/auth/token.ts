/**
 * Token 管理工具
 * 统一管理 JWT Token 的读写和清除操作
 */

const TOKEN_KEY = 'auth_token'

/**
 * 获取 Token
 * @returns Token 字符串，或 null
 */
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

/**
 * 保存 Token
 * @param token JWT Token 字符串
 */
export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

/**
 * 清除 Token(退出登录时调用)
 */
export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}
