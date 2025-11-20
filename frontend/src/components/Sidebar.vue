<template>
  <div>
    <!-- 遮罩层（移动端）：点击关闭侧边栏 -->
    <Transition name="fade">
      <div
        v-if="isSidebarOpen && isMobile"
        class="fixed inset-0 bg-black bg-opacity-50 z-40 md:hidden"
        @click="closeSidebar"
      />
    </Transition>

    <!-- 侧边栏：可折叠的主导航栏 -->
    <Transition name="slide">
      <aside
        v-if="isSidebarOpen || !isMobile"
        class="fixed md:sticky top-0 left-0 h-screen md:h-screen border-r border-gray-200 bg-white z-50 md:z-0 flex flex-col overflow-hidden transition-all duration-300"
        :class="isMobile ? 'w-64' : (isCollapsed ? 'w-16' : 'w-64')"
      >
        <!-- ============ 顶部：折叠按钮、Logo、通知 ============ -->
        <div class="flex items-center justify-between h-16 px-4 border-b border-gray-200 shrink-0">
          <!-- 折叠/展开按钮（移动端为关闭） -->
          <button
            class="p-2 hover:bg-gray-100 rounded-lg transition-colors"
            @click="toggleCollapse"
            :title="isCollapsed ? '展开菜单' : '折叠菜单'"
          >
            <ChevronLeft
              :size="20"
              class="text-gray-700 transition-transform duration-300"
              :style="{
                transform: isMobile
                  ? 'rotate(0deg)'
                  : (isCollapsed ? 'rotate(90deg)' : 'rotate(0deg)')
              }"
            />
          </button>

          <!-- Logo（展开时显示） -->
          <div v-if="!isCollapsed" class="flex items-center gap-2 flex-1 justify-center">
            <BookOpen :size="20" class="text-gray-900 font-bold" />
            <span class="text-sm font-bold text-gray-900">Blog</span>
          </div>

          <!-- 占位符（折叠时） -->
          <div v-else class="flex-1" />

          <!-- 通知按钮（展开时显示） -->
          <button
            v-if="!isCollapsed"
            class="p-2 hover:bg-gray-100 rounded-lg transition-colors relative"
            aria-label="通知"
            title="通知"
          >
            <Bell :size="20" class="text-gray-700" />
            <!-- 通知红点 -->
            <span class="absolute top-1 right-1 w-2 h-2 bg-red-500 rounded-full" />
          </button>
        </div>

        <!-- ============ 中间：导航菜单 ============ -->
        <nav class="flex-1 p-2 space-y-1 overflow-y-auto">
          <a
            v-for="item in navItems"
            :key="item.id"
            :href="item.href"
            class="flex items-center gap-3 px-4 py-3 text-gray-700 rounded-lg hover:bg-gray-100 transition-colors cursor-pointer group"
            :title="item.label"
            @click="handleNavClick"
          >
            <component :is="item.icon" :size="20" class="shrink-0 text-gray-700 group-hover:text-gray-900" />
            <span v-if="!isCollapsed" class="font-medium group-hover:text-gray-900 whitespace-nowrap">
              {{ item.label }}
            </span>
          </a>
        </nav>

        <!-- ============ 底部：账户卡片（自然下沉到最底部） ============ -->
        <div class="p-2 border-t border-gray-200 bg-white shrink-0">
          <!-- 账户卡片 -->
          <div class="relative">
            <button
              class="w-full flex items-center gap-3 px-4 py-3 bg-gray-50 rounded-lg hover:bg-gray-100 transition-colors"
              @click="showAccountMenu = !showAccountMenu"
              :title="isCollapsed ? userName : '账户菜单'"
            >
              <!-- 用户头像 -->
              <img
                :src="userAvatar"
                :alt="userName"
                class="w-8 h-8 rounded-full object-cover shrink-0"
              />

              <!-- 用户信息（展开时显示） -->
              <div v-if="!isCollapsed" class="flex-1 text-left min-w-0">
                <p class="text-xs font-semibold text-gray-900 truncate">{{ userName }}</p>
                <p class="text-xs text-gray-500 truncate">{{ userEmail }}</p>
              </div>

              <!-- 下拉箭头（展开时显示） -->
              <ChevronDown
                v-if="!isCollapsed"
                :size="16"
                class="text-gray-700 shrink-0 transition-transform"
                :class="{ 'transform rotate-180': showAccountMenu }"
              />
            </button>

            <!-- 下拉菜单（展开时显示） -->
            <Transition
              enter-active-class="transition ease-out duration-100"
              enter-from-class="opacity-0 -translate-y-1"
              enter-to-class="opacity-100 translate-y-0"
              leave-active-class="transition ease-in duration-100"
              leave-from-class="opacity-100 translate-y-0"
              leave-to-class="opacity-0 -translate-y-1"
            >
              <div
                v-if="showAccountMenu && !isCollapsed"
                class="absolute bottom-full left-0 right-0 mb-2 bg-white border border-gray-200 rounded-lg shadow-lg z-10"
              >
                <a
                  href="#"
                  class="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors first:rounded-t-lg"
                  @click="showAccountMenu = false"
                >
                  <User :size="16" class="text-gray-600" />
                  我的资料
                </a>
                <a
                  href="#"
                  class="flex items-center gap-2 px-4 py-2 text-sm text-gray-700 hover:bg-gray-100 transition-colors"
                  @click="showAccountMenu = false"
                >
                  <Settings :size="16" class="text-gray-600" />
                  设置
                </a>
                <button
                  class="w-full flex items-center gap-2 text-left px-4 py-2 text-sm text-red-600 hover:bg-gray-100 transition-colors last:rounded-b-lg border-t border-gray-200"
                  @click="handleLogout"
                >
                  <LogOut :size="16" class="text-red-600" />
                  退出登录
                </button>
              </div>
            </Transition>
          </div>
        </div>
      </aside>
    </Transition>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useSidebar } from '@/composables'
import {
  BookOpen,
  Globe,
  User,
  BarChart3,
  Settings,
  LogOut,
  Bell,
  ChevronDown,
  ChevronLeft,
} from 'lucide-vue-next'

// ============ Composables ============

const { isSidebarOpen, closeSidebar } = useSidebar()

// ============ 状态管理 ============

/**
 * Sidebar 是否折叠
 * true: 折叠（只显示图标，w-20）
 * false: 展开（显示完整菜单，w-64）
 */
const isCollapsed = ref(false)

/**
 * 是否为移动设备
 */
const isMobile = ref(false)

/**
 * 账户下拉菜单是否显示
 */
const showAccountMenu = ref(false)

// ============ 用户信息（后期从全局状态读取） ============

const userName = ref('Alice Chen')
const userEmail = ref('alice@example.com')
const userAvatar = ref('https://i.pravatar.cc/40?img=1')

// ============ 菜单数据 ============

/**
 * 导航菜单项
 * 公共、个人、统计
 */
const navItems = ref([
  { id: 1, label: '公共', href: '/', icon: Globe },
  { id: 2, label: '个人', href: '/personal', icon: User },
  { id: 3, label: '统计', href: '/stats', icon: BarChart3 },
])

// ============ 事件处理 ============

/**
 * 切换折叠状态
 */
const toggleCollapse = (): void => {
  if (isMobile.value) {
    // 移动设备：点击折叠按钮应该关闭侧边栏
    closeSidebar()
  } else {
    // 桌面设备：在展开/折叠之间切换
    isCollapsed.value = !isCollapsed.value
  }
  // 关闭账户菜单
  showAccountMenu.value = false
}

/**
 * 处理导航点击（移动端自动关闭侧边栏）
 */
const handleNavClick = (): void => {
  if (isMobile.value) {
    closeSidebar()
  }
  showAccountMenu.value = false
}

/**
 * 处理退出登录
 */
const handleLogout = (): void => {
  console.log('用户退出登录')
  // 后期调用退出 API 和导航到登录页
  showAccountMenu.value = false
}

// ============ 检测屏幕大小 ============

/**
 * 检测是否为移动设备
 */
const checkMobile = (): void => {
  isMobile.value = window.innerWidth < 768
}

// ============ 生命周期 ============

import { onMounted, onUnmounted } from 'vue'

onMounted(() => {
  checkMobile()
  window.addEventListener('resize', checkMobile)
})

onUnmounted(() => {
  window.removeEventListener('resize', checkMobile)
})
</script>

<style scoped>
/* 遮罩层淡入淡出 */
.fade-enter-active,
.fade-leave-active {
  transition: opacity 0.3s ease;
}

.fade-enter-from,
.fade-leave-to {
  opacity: 0;
}

/* 侧边栏从左侧滑入/滑出 */
.slide-enter-active,
.slide-leave-active {
  transition: transform 0.3s ease;
}

.slide-enter-from,
.slide-leave-to {
  transform: translateX(-100%);
}
</style>
