<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Menu } from 'lucide-vue-next'
import Sidebar from './components/Sidebar.vue'
import { useSidebar } from '@/composables'

// ============ Sidebar 管理 ============
const { isSidebarOpen, openSidebar } = useSidebar()

// 检测是否为移动设备
const isMobile = ref(false)

const checkMobile = (): void => {
  isMobile.value = window.innerWidth < 768
}

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})
</script>

<template>
  <div class="flex h-screen bg-gray-50">
    <!-- 侧边栏 -->
    <Sidebar />

    <!-- 主内容区域 -->
    <main class="flex-1 overflow-auto flex flex-col">
      <!-- 移动端菜单栏 -->
      <div v-if="isMobile" class="sticky top-0 bg-white border-b border-gray-200 px-4 py-3 z-30 flex items-center gap-3">
        <button
          @click="openSidebar"
          class="p-2 hover:bg-gray-100 rounded-lg transition-colors"
          title="打开菜单"
        >
          <Menu :size="24" class="text-gray-700" />
        </button>
        <h1 class="text-lg font-bold text-gray-900">Blog</h1>
      </div>

      <!-- 页面内容 -->
      <router-view />
    </main>
  </div>
</template>

<style scoped></style>
