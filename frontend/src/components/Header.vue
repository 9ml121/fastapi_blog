<template>
  <header class="sticky top-0 z-50 bg-white border-b border-gray-200">
    <!-- 导航栏容器 -->
    <div class="max-w-7xl mx-auto px-4 py-4 flex items-center justify-between">
      <!-- 左侧：汉堡菜单 + Logo + 标题 -->
      <div class="flex items-center gap-3 shrink-0">
        <!-- 汉堡菜单按钮（全屏幕显示，允许切换 sidebar） -->
        <button
          class="p-2 text-gray-700 hover:bg-gray-100 hover:text-gray-900 rounded-lg transition-colors"
          @click="handleMenuToggle"
          aria-label="切换导航菜单"
          title="切换侧边栏"
        >
          <Menu :size="24" class="text-gray-700" />
        </button>

        <div class="flex items-center gap-2">
          <div class="text-2xl font-bold">📚</div>
          <h1 class="text-xl font-bold text-gray-900">{{ appTitle }}</h1>
        </div>
      </div>

      <!-- 中间：导航链接（隐藏在手机上） -->
      <nav class="hidden md:flex gap-8 flex-1 justify-center">
        <a
          v-for="link in navLinks"
          :key="link.name"
          :href="link.href"
          class="text-gray-700 font-medium hover:text-gray-900 transition-colors"
        >
          {{ link.name }}
        </a>
      </nav>

      <!-- 搜索框（中等屏幕及以上显示） -->
      <div
        class="hidden sm:flex items-center bg-gray-100 rounded-full px-4 py-2 gap-2 grow mx-4 max-w-xs"
      >
        <span class="text-gray-400">🔍</span>
        <input
          type="text"
          placeholder="搜索文章、作者、标签..."
          class="bg-transparent outline-none text-sm text-gray-700 w-full placeholder-gray-400"
        />
      </div>

      <!-- 右侧：用户菜单 -->
      <div class="flex items-center gap-3 shrink-0">
        <!-- 登录状态 -->
        <div v-if="isLoggedIn" class="flex items-center gap-3">
          <div class="hidden sm:flex items-center gap-2">
            <img :src="userAvatar" :alt="userName" class="w-8 h-8 rounded-full object-cover" />
            <span class="text-sm font-medium text-gray-900">{{ userName }}</span>
          </div>
          <button
            @click="handleLogout"
            class="text-sm font-medium text-gray-700 hover:text-gray-900 transition-colors hover:bg-gray-100 px-3 py-2 rounded-full"
          >
            退出
          </button>
        </div>

        <!-- 未登录状态 -->
        <div v-else class="flex gap-2">
          <button
            @click="handleLoginClick"
            class="text-sm font-semibold text-gray-900 hover:bg-gray-100 px-4 py-2 rounded-full transition-colors"
          >
            登录
          </button>
          <button
            @click="handleRegisterClick"
            class="text-sm font-semibold text-white bg-gray-900 hover:bg-gray-800 px-4 py-2 rounded-full transition-colors"
          >
            注册
          </button>
        </div>
      </div>
    </div>
  </header>
</template>

<script lang="ts" setup>
import { ref, computed } from 'vue'
import { Menu } from 'lucide-vue-next'
import { useSidebar } from '@/composables'

// ============ Props & Emits ============

// 本组件不再通过 Props/Emits 管理 sidebar 状态
// 改用全局的 useSidebar Composable

// ============ Composables ============

// 获取全局的 sidebar 状态管理
const { isSidebarOpen, toggleSidebar } = useSidebar()

// ============ 数据定义 ============

// 应用标题（Props 可以接收，这里用响应式数据演示）
const appTitle = ref('FastAPI 博客')

// 用户登录状态（后面会从全局状态替换）
const isLoggedIn = ref(false)
const userName = ref('')
const userAvatar = ref('https://i.pravatar.cc/40?img=1')

// 导航链接列表
const navLinks = ref([
  { name: '个人空间', href: '/' },
  { name: '公共广场', href: '/posts' },
  { name: '互助问答', href: '/tags' },
])

// ============ 计算属性 ============

// 演示：根据登录状态计算显示的按钮文本
const buttonText = computed(() => {
  return isLoggedIn.value ? '已登录' : '未登录'
})

// ============ 事件处理 ============

/**
 * 切换侧边栏开关
 * 使用 useSidebar 提供的 toggleSidebar 方法
 */
const handleMenuToggle = (): void => {
  toggleSidebar()
}

const handleLoginClick = (): void => {
  // 后面会改成导航到登录页
  console.log('点击了登录按钮')
  alert('点击登录（后期会导航到登录页）')
}

const handleRegisterClick = (): void => {
  // 后面会改成导航到注册页
  console.log('点击了注册按钮')
  alert('点击注册（后期会导航到注册页）')
}

const handleLogout = (): void => {
  isLoggedIn.value = false
  userName.value = ''
  console.log('用户已退出')
}

// ============ 演示：模拟登录 ============
// 这只是为了演示组件效果，后期会被真实的 API 调用替换

const simulateLogin = (): void => {
  isLoggedIn.value = true
  userName.value = 'Alice'
}

// 页面加载时，自动模拟一个已登录状态（用于看效果）
// 后期删除这行，改用真实 API
simulateLogin()
</script>

<style scoped></style>
