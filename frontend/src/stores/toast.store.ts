import { defineStore } from 'pinia'
import { ref } from 'vue'

// Toast 类型
export type ToastType = 'success' | 'error' | 'warning' | 'info'

// 单条 Toast 数据结构
export interface Toast {
  id: number
  type: ToastType
  message: string
}

export const useToastStore = defineStore('toast', () => {
  // ========== State ==========
  const toasts = ref<Toast[]>([])
  let nextId = 1

  // ========== Actions ==========
  function addToast(type: ToastType, message: string, duration = 3000) {
    const id = nextId++
    toasts.value.push({ id, type, message })

    // 自动移除 Toast
    setTimeout(() => {
      removeToast(id)
    }, duration)
  }

  function removeToast(id: number) {
    const index = toasts.value.findIndex((toast) => toast.id === id)
    if (index !== -1) {
      toasts.value.splice(index, 1)
    }
  }

  // ========== 便捷方法 ==========
  const success = (message: string) => addToast('success', message)
  const error = (message: string) => addToast('error', message, 5000)
  const warning = (message: string) => addToast('warning', message)
  const info = (message: string) => addToast('info', message)

  return {
    toasts,
    addToast,
    removeToast,
    success,
    error,
    warning,
    info,
  }
})
