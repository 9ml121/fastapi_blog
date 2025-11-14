<template>
  <header class="bg-linear-to-r from-blue-600 to-blue-800 text-white shadow-lg">
    <!-- 导航栏容器 -->
    <div class="max-w-6xl mx-auto px-2 py-2 flex items-center justify-between">
      <!-- 左侧：Logo + 标题 -->
      <div class="flex items-center gap-3">
        <div class="text-2xl font-bold">📚</div>
        <h1 class="text-2xl font-bold">{{ appTitle }}</h1>
      </div>

      <!-- 中间：导航链接 -->
      <nav class="flex gap-6">
        <a
          v-for="link in navLinks"
          :key="link.name"
          :href="link.href"
          class="hover:text-blue-200 transition-colors"
        >
          {{ link.name }}
        </a>
      </nav>

      <!-- 右侧：用户菜单 -->
      <div class="flex items-center gap-4">
        <!-- 登录状态 -->
        <div v-if="isLoggedIn" class="flex items-center gap-2">
          <span>欢迎，{{ userName }}</span>
          <button
            @click="handleLogout"
            class="bg-red-500 hover:bg-red-600 px-4 py-2 rounded transition-colors"
          >
            退出
          </button>
        </div>

        <!-- 未登录状态 -->
        <div v-else class="flex gap-2">
          <button
            @click="handleLoginClick"
            class="bg-white text-blue-600 hover:bg-blue-50 px-4 py-2 rounded font-semibold transition-colors"
          >
            登录
          </button>
          <button
            @click="handleRegisterClick"
            class="border-2 border-white hover:bg-white hover:text-blue-600 px-4 py-2 rounded transition-colors"
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

// ============ 数据定义 ============

// 应用标题（Props 可以接收，这里用响应式数据演示）
const appTitle = ref('FastAPI 博客')

// 用户登录状态（后面会从全局状态替换）
const isLoggedIn = ref(false)
const userName = ref('')

// 导航链接列表
const navLinks = ref([
  { name: '首页', href: '/' },
  { name: '文章', href: '/posts' },
  { name: '标签', href: '/tags' },
  { name: '关于', href: '/about' },
])

// ============ 计算属性 ============

// 演示：根据登录状态计算显示的按钮文本
const buttonText = computed(() => {
  return isLoggedIn.value ? '已登录' : '未登录'
})

// ============ 事件处理 ============

const handleLoginClick = () => {
  // 后面会改成导航到登录页
  console.log('点击了登录按钮')
  alert('点击登录（后期会导航到登录页）')
}

const handleRegisterClick = () => {
  // 后面会改成导航到注册页
  console.log('点击了注册按钮')
  alert('点击注册（后期会导航到注册页）')
}

const handleLogout = () => {
  isLoggedIn.value = false
  userName.value = ''
  console.log('用户已退出')
}

// ============ 演示：模拟登录 ============
// 这只是为了演示组件效果，后期会被真实的 API 调用替换

const simulateLogin = () => {
  isLoggedIn.value = true
  userName.value = 'Alice'
}

// 页面加载时，自动模拟一个已登录状态（用于看效果）
// 后期删除这行，改用真实 API
simulateLogin()
</script>

<style scoped></style>
