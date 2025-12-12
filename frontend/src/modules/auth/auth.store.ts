/**
 * Auth Store
 * 管理用户登录状态
 */

import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { loginApi, type LoginParams } from './api'
import { getToken, setToken, removeToken } from './token'

export const useAuthStore = defineStore('auth', () => {
  // ========== State ==========
  const token = ref<string | null>(getToken())
  const user = ref<{ username: string } | null>(null)
  const isLoading = ref(false)

  // ========== Getters ==========
  const isLoggedIn = computed(() => !!token.value)

  // ========== Actions ==========
  /**
   * 用户登录
   */
  async function login(params: LoginParams) {
    isLoading.value = true
    try {
      const response = await loginApi(params)
      token.value = response.access_token
      setToken(response.access_token)
      // 可选：从 token 解析用户信息，或调用 /me 接口
      user.value = { username: params.username }
    } finally {
      isLoading.value = false
    }
  }

  /**
   * 用户登出
   */
  function logout() {
    token.value = null
    user.value = null
    removeToken()
  }

  /**
   * 检查并恢复登录状态（页面刷新时从 localStorage 恢复状态）
   */
  function checkAuth() {
    const savedToken = getToken()
    if (savedToken) {
      token.value = savedToken
      // 可选：解析 token 或调用 /me 接口获取用户信息
    }
  }

  return {
    // State
    token,
    user,
    isLoading,
    // Getters
    isLoggedIn,
    // Actions
    checkAuth,
    login,
    logout,
  }
})
