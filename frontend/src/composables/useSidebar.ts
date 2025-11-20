import { ref, watch } from 'vue'
import type { Ref } from 'vue'

/**
 * Sidebar 全局状态（在函数外部定义）
 * 关键：只初始化一次，所有 useSidebar() 调用都会返回同一个 ref
 * 这样 App.vue 和 Sidebar.vue 就能共享状态
 */
let globalSidebarRef: Ref<boolean> | null = null

const initState = (): boolean => {
  const version = localStorage.getItem('sidebar-version')
  if (version !== '1') {
    localStorage.removeItem('sidebar-open')
    localStorage.setItem('sidebar-version', '1')
  }

  const saved = localStorage.getItem('sidebar-open')
  return saved !== null ? JSON.parse(saved) : true
}

/**
 * Sidebar 状态管理 Composable
 *
 * 功能：
 * - 管理 sidebar 打开/关闭状态
 * - 持久化用户偏好到 localStorage
 * - 提供切换、打开、关闭方法
 *
 * 使用示例：
 * ```ts
 * const { isSidebarOpen, toggleSidebar, closeSidebar } = useSidebar()
 * ```
 */
export const useSidebar = () => {
  // 第一次调用时创建 ref，后续调用都返回同一个 ref
  if (!globalSidebarRef) {
    globalSidebarRef = ref<boolean>(initState())

    // 监听状态变化，持久化到 localStorage
    watch(
      globalSidebarRef,
      (newValue) => {
        localStorage.setItem('sidebar-open', JSON.stringify(newValue))
      },
      { immediate: false },
    )
  }

  const isSidebarOpen = globalSidebarRef

  /**
   * 切换 sidebar 状态
   */
  const toggleSidebar = (): void => {
    isSidebarOpen.value = !isSidebarOpen.value
  }

  /**
   * 关闭 sidebar
   */
  const closeSidebar = (): void => {
    isSidebarOpen.value = false
  }

  /**
   * 打开 sidebar
   */
  const openSidebar = (): void => {
    isSidebarOpen.value = true
  }

  return {
    isSidebarOpen,
    toggleSidebar,
    closeSidebar,
    openSidebar,
  }
}
