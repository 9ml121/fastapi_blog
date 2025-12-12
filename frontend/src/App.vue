<script setup lang="ts">
import { onMounted } from 'vue'
import { useAuthStore } from '@/modules/auth/auth.store'

// 激活 store
const authStore = useAuthStore()

onMounted(async () => {
  console.log('=== 登录测试 ===')
  try {
    await authStore.login({
      username: 'admin@example.com', // 替换
      password: 'admin123', // 替换
    })
    console.log('✅ 登录成功!')
    console.log('Token:', authStore.token)
    console.log('isLoggedIn:', authStore.isLoggedIn)
  } catch (error) {
    console.log('❌ 登录失败:', error)
  }
})
</script>

<template>
  <div class="app-container">
    <!-- 侧边栏 -->
    <!-- <Sidebar /> -->

    <!-- 主内容区域 -->
    <main class="main-content">
      <!-- 页面内容 -->
      <router-view />
    </main>
  </div>
</template>

<style scoped>
/* =============================================================================
   应用根容器
   ============================================================================= */
.app-container {
  /* 启用 Flexbox 布局 - 让子元素（侧边栏和主内容区）可以水平排列 */
  display: flex;

  /* 高度占满整个视口 - 100vh = 100% 视口高度 */
  height: 100vh;
}

/* =============================================================================
   主内容区域
   ============================================================================= */
.main-content {
  /*
   * flex: 1 1 0% 是 flex-grow flex-shrink flex-basis 的简写
   * - flex-grow: 1    → 允许元素占据剩余空间（如果有侧边栏，会填充剩余宽度）
   * - flex-shrink: 1  → 允许元素在空间不足时收缩
   * - flex-basis: 0%  → 初始大小为 0，完全由 flex-grow 决定最终大小
   */
  flex: 1 1 0%;

  /* 当内容超出容器高度时，自动显示滚动条,如果内容没超出，不显示滚动条 */
  overflow: auto;

  /* 作为 Flex 容器，为内部的 <router-view> 提供 Flex 布局环境 */
  display: flex;

  /* 子元素按列（垂直）排列 */
  flex-direction: column;
}
</style>
