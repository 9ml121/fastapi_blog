import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
  getUserMeApi,
  loginApi,
  registerApi,
  type LoginParams,
  type RegisterParams,
  type User,
} from '@/api/auth.api'
import { getToken, setToken, removeToken } from '@/utils/token'

export const useAuthStore = defineStore('auth', () => {
  // ========== State ==========
  const token = ref<string | null>(getToken())
  const user = ref<User | null>(null)

  // ========== Getters ==========
  // !! 双重否定，将 token 转为布尔值
  const isLoggedIn = computed(() => !!token.value)

  // ========== Actions ==========
  async function register(params: RegisterParams) {
    const response = await registerApi(params)
    // 保存 token 到 pinia state（响应式）+ localStorage(持久化)
    token.value = response.access_token
    setToken(response.access_token)

    // 保存用户信息
    user.value = response.user
  }

  async function login(params: LoginParams) {
    const response = await loginApi(params)
    // 保存 token 到 pinia state（响应式）+ localStorage(持久化)
    token.value = response.access_token
    setToken(response.access_token)

    // 保存用户信息
    user.value = response.user
  }

  function logout() {
    token.value = null
    user.value = null
    removeToken()
  }

  /**
   * 检查并恢复登录状态（页面刷新时从 localStorage 恢复状态）
   */
  async function checkAuth() {
    const savedToken = getToken()
    if (!savedToken) return

    token.value = savedToken

    try {
      // 调用后端接口获取用户信息
      user.value = await getUserMeApi()
    } catch (error) {
      // Token 失效，清除登录状态
      logout()
    }
  }

  return {
    // State
    token,
    user,
    // Getters
    isLoggedIn,
    // Actions
    checkAuth,
    login,
    logout,
    register,
  }
})
