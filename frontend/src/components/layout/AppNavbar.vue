<script lang="ts" setup>
import BrandLogo from '@/components/common/BrandLogo.vue'
import { Moon, Search, Sun, User } from 'lucide-vue-next'

import { useAuthStore } from '@/stores/auth.store'
import { onMounted, ref } from 'vue'

// 个人中心
const authStore = useAuthStore()
const isLoggedIn = ref(authStore.isLoggedIn)
const user = ref(authStore.user)
const isUserMenuOpen = ref(false)

// 主题切换
const isDark = ref(false)
function toggleTheme() {
  isDark.value = !isDark.value
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
  localStorage.setItem('theme', isDark.value ? 'dark' : 'light')
}

onMounted(() => {
  isDark.value = localStorage.getItem('theme') === 'dark'
  document.documentElement.setAttribute('data-theme', isDark.value ? 'dark' : 'light')
})

// 登出
async function logout() {
  await authStore.logout()
  isLoggedIn.value = false
  user.value = null
  isUserMenuOpen.value = false
}

// 下拉菜单
function toggleUserMenu() {
  isUserMenuOpen.value = !isUserMenuOpen.value
}
</script>

<template>
  <nav class="navbar">
    <div class="navbar-container">
      <!-- 左侧：Logo -->
      <div class="navbar-logo">
        <router-link to="/">
          <BrandLogo size="small" :showName="true" :gap="8" direction="horizontal" />
        </router-link>
      </div>

      <!-- 中间：导航菜单 -->
      <ul class="navbar-menu">
        <li><router-link to="/posts">博文</router-link></li>
        <li><router-link to="/projects">项目</router-link></li>
        <li><router-link to="/picks">好物</router-link></li>
      </ul>

      <!-- 右侧：工具区 -->
      <div class="navbar-actions">
        <button class="icon-btn" title="搜索">
          <Search :size="20" />
        </button>

        <button class="icon-btn" @click="toggleTheme" title="切换主题">
          <Sun v-if="isDark" :size="20" />
          <Moon v-else :size="20" />
        </button>

        <!-- 用户状态 -->
        <router-link v-if="!isLoggedIn" to="/login" class="login-btn">登录</router-link>
        <!-- 已登录状态：包含头像和下拉菜单的容器 -->
        <div v-else class="user-dropdown-container" @click="toggleUserMenu">
          <img v-if="user?.avatar" :src="user.avatar" class="user-avatar" />
          <button v-else class="icon-btn" title="个人中心">
            <User :size="20" />
          </button>
          <!-- 下拉菜单 -->
          <div v-if="isUserMenuOpen" class="dropdown-menu">
            <div class="menu-head">
              <span class="username">{{ user?.nickname || user?.username }}</span>
            </div>
            <ul class="menu-list">
              <li><router-link to="/profile">个人中心</router-link></li>
              <li class="divider"></li>
              <li @click="logout" class="danger">退出登录</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<style scoped>
/* ========== 布局方案 ==========*/
.navbar {
  position: sticky;
  top: 0;
  z-index: 100;
  height: 64px;
  background: rgba(255, 255, 255, 0.8);
  backdrop-filter: blur(8px); /* 毛玻璃模糊效果 */
  border-bottom: 1px solid var(--color-border);
}

.navbar-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 24px;
  height: 100%;
  display: flex;
  align-items: center;
  justify-content: space-between;
}

.navbar-logo a {
  text-decoration: none;
}

.navbar-menu {
  display: flex;
  gap: 32px;
  list-style: none;
  margin: 0;
  padding: 0;
}

.navbar-actions {
  display: flex;
  align-items: center;
  gap: 16px;
}

/* ========== 菜单项样式 ==========*/
.navbar-menu a {
  color: var(--color-text-primary);
  text-decoration: none;
  font-weight: 500;
  padding: 8px 0;
  transition: color 0.2s ease;
}

.navbar-menu a:hover {
  color: var(--color-primary);
}

/* 当前页面高亮 */
/* ! Vue Router 会自动给当前匹配路由的 <a> 标签添加 router-link-active 类。 */
.navbar-menu a.router-link-active {
  color: var(--color-primary);
  position: relative; /* 设置相对定位，作为下方伪元素（下划线）的定位基准 */
}

.navbar-menu a.router-link-active::after {
  content: ''; /* 伪元素必须属性，内容为空 */
  position: absolute; /* 绝对定位 */
  bottom: -1px; /* 定位在文字下方 1px 处 */
  left: 0; /* 左对齐 */
  right: 0; /* 右对齐（配合 left:0 撑满宽度） */
  height: 2px; /* 下划线高度 */
  background: var(--color-primary); /* 下划线颜色跟随品牌主色 */
  border-radius: 1px; /* 下划线两端圆角 */
}

/* ========== 按钮样式 ==========*/
.icon-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: transparent; /* 幽灵按钮 */
  border-radius: 20px;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: background 0.2s ease;
}

.icon-btn:hover {
  background: var(--color-bg-hover);
  transform: translateY(-1px); /* 悬停上浮 */
  box-shadow: 0 4px 8px rgba(0, 0, 0, 0.12); /* 阴影加深 */
}

.login-btn {
  padding: 8px 16px;
  background: var(--color-primary);
  color: white;
  border-radius: 8px;
  text-decoration: none;
  font-weight: 500;
  transition: opacity 0.2s ease;
}

.login-btn:hover {
  opacity: 0.9;
}

.user-avatar {
  width: 36px;
  height: 36px;
  border-radius: 50%; /* 圆形头像 */
  cursor: pointer;
  object-fit: cover; /* 防止图片变形 */
  border: 2px solid transparent;
  transition: all 0.2s ease;
}
.user-avatar:hover {
  border-color: var(--color-primary);
  transform: scale(1.05);
}

.user-dropdown-container {
  position: relative; /* 核心：为下拉菜单提供定位参考 */
  display: flex;
  align-items: center;
}

.dropdown-menu {
  position: absolute;
  top: calc(100% + 12px); /* 位于容器下方 12px 处 */
  right: 0;
  width: 160px;
  background: var(--color-bg-card);
  border: 1px solid var(--color-border);
  border-radius: 12px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  z-index: 1000;
  overflow: hidden; /* 确保内部元素的背景色不会超出圆角边框 */

  /* 入场动画 */
  transform-origin: top right; /* 动画从右上角开始缩放 */
  animation: menuAppear 0.2s ease-out;
}

@keyframes menuAppear {
  from {
    opacity: 0;
    transform: scale(0.95);
  }
  to {
    opacity: 1;
    transform: scale(1);
  }
}

.menu-head {
  padding: 12px 16px;
  border-bottom: 1px solid var(--color-border);
  background: var(--color-bg-hover);
}

.username {
  display: block;
  font-weight: 600;
  color: var(--color-text-primary);
  font-size: var(--font-size-sm);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.divider {
  height: 1px;
  background: var(--color-border);
  margin:4px 0;
}

.menu-list {
  list-style: none;
  padding: 4px 0;
  margin: 0;
}

.menu-list li a,
.menu-list li.danger {
  padding: 10px 16px;
  display: flex;
  align-items: center;
  color: var(--color-text-primary);
  text-decoration: none;
  cursor: pointer;
  transition: background 0.2s;
}

.menu-list li a:hover {
  background: var(--color-bg-hover);
}

.menu-list li.danger:hover {
  background: var(--color-bg-error);
}
</style>
