<script lang="ts" setup>
import BrandLogo from '@/components/BrandLogo.vue'
import FormInput from '@/components/FormInput.vue'
import { useAuthStore } from '@/stores/auth.store'

import { ArrowRight, Eye, EyeOff, Loader2, LockKeyhole, Mail } from 'lucide-vue-next'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

// ========== 状态初始化 ==========
const authStore = useAuthStore()
const router = useRouter()

// 表单数据
const username = ref('')
const password = ref('')

// 密码可见性状态
const showPassword = ref(false)

// 加载状态
const isLoading = ref(false)

// 记住我状态
const rememberMe = ref(false)

// 错误提示信息
const errorMessage = ref('')

// ========== 方法定义 ==========
// 切换密码可见性
const togglePassword = () => {
  showPassword.value = !showPassword.value
}

// 登录处理
const handleLogin = async () => {
  errorMessage.value = ''
  isLoading.value = true

  try {
    await authStore.login({
      username: username.value,
      password: password.value,
      remember: rememberMe.value,
    })
    // 登录成功，跳转到首页
    router.push('/')
  } catch (error) {
    errorMessage.value = '用户名或密码错误'
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="auth-container">
    <div class="top-toolbar">top-toolbar</div>

    <div class="auth-card">
      <div class="auth-header">
        <div class="auth-logo">
          <BrandLogo size="medium" :showName="true" direction="vertical" />
        </div>
        <h1 class="auth-title">登录账户</h1>
        <p class="auth-subtitle">请输入您的凭证继续</p>
      </div>

      <form class="auth-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="email"><b>邮箱</b></label>
          <FormInput
            v-model="username"
            id="email"
            type="email"
            placeholder="请输入邮箱地址"
            autocomplete="email"
            required
          >
            <template v-slot:prefix>
              <Mail :size="20" />
            </template>
          </FormInput>
        </div>

        <div class="form-group">
          <label for="password"><b>密码</b></label>
          <FormInput
            v-model="password"
            id="password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="请输入密码"
            autocomplete="current-password"
            required
          >
            <template #prefix>
              <LockKeyhole :size="20" />
            </template>
            <template #suffix>
              <Eye v-if="showPassword" :size="20" @click="togglePassword" class="toggle-icon"></Eye>
              <EyeOff v-else :size="20" @click="togglePassword" class="toggle-icon"></EyeOff>
            </template>
          </FormInput>
        </div>

        <!-- 记住我 & 忘记密码 -->
        <div class="form-options">
          <label class="remember-me">
            <input type="checkbox" v-model="rememberMe" />
            <span>记住我</span>
          </label>
          <router-link to="/forget-password" class="forget-password">忘记密码?</router-link>
        </div>

        <!-- 错误提示信息 -->
        <div v-if="errorMessage" class="error-message">{{ errorMessage }}</div>
        <!-- 登录按钮 -->
        <button class="btn btn-primary btn-block" type="submit" :disabled="isLoading">
          <Loader2 v-if="isLoading" :size="20" class="loading-icon"></Loader2>
          <span>{{ isLoading ? '登录中...' : '登 录' }}</span>
          <ArrowRight v-if="!isLoading" :size="20" />
        </button>
      </form>

      <!-- 注册链接 -->
      <div class="auth-footer">
        <div class="auth-divider">
          <span>还没有账户？</span>
        </div>

        <router-link to="/register" class="btn btn-secondary btn-block">创建账户</router-link>
      </div>
    </div>
  </div>

  <div class="toast-container"></div>
</template>

<style scoped>
/* 登录页面容器 - 占满整个视口 */
.auth-container {
  min-height: 100vh;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
}

/* 主内容区 - Flexbox 垂直水平居中 */
.auth-card {
  width: 100%;
  max-width: 420px;
  background: var(--color-bg-card);
  border-radius: 16px;
  box-shadow: 0 10px 30px var(--color-shadow);
  padding: 2.5rem;
  border: 1px solid rgba(53, 92, 194, 0.1);
}

.auth-header {
  text-align: center;
  margin-bottom: 2rem;
}

/* 登录卡片容器 - 白色圆角卡片 */
.auth-logo {
  margin-bottom: 1.5rem;
  text-align: center;
}

.auth-title {
  font-size: var(--font-size-xl);
  font-weight: 700;
  color: var(--color-text-primary);
  margin-bottom: 0.5rem;
}

.auth-subtitle {
  font-size: var(--font-size-sm);
  color: var(--color-text-secondary);
}

.auth-form {
  margin-bottom: 1.5rem;
}

.form-group {
  margin-bottom: 1.5rem;
}

.toggle-icon {
  cursor: pointer; /* 密码切换图标 - 可点击 */
}

.toggle-icon:hover {
  color: #3b82f6; /* 鼠标悬停时变色 */
}

/* 记住我 & 忘记密码 容器 */
.form-options {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1.5rem;
  font-size: var(--font-size-sm);
}

.remember-me {
  display: flex;
  align-items: center;
  gap: 8px;
  color: #6b7280;
  cursor: pointer;
}

.remember-me input[type='checkbox'] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.forget-password {
  color: #3b82f6;
  text-decoration: none;
}

.forget-password:hover {
  text-decoration: underline;
}

/* 加载图标旋转动画 */
.loading-icon {
  animation: spin 1s linear infinite;
}
@keyframes spin {
  from {
    transform: rotate(0deg);
  }
  to {
    transform: rotate(360deg);
  }
}

.error-message {
  color: var(--color-error);
  font-size: var(--font-size-sm);
  text-align: center;
  margin-bottom: 1rem;
  padding: 0.5rem;
  background-color: var(--color-bg-error);
  border-radius: 8px;
}

/* 注册链接 */
.auth-footer {
  text-align: center;
  font-size: 14px;
  color: #6b7280;
}

.auth-divider {
  display: flex;
  align-items: center;
  margin: 1.5rem 0;
}

.auth-divider::before,
.auth-divider::after {
  content: '';
  flex: 1;
  height: 1px;
  background-color: var(--color-border);
}

.auth-divider span {
  padding: 0 1rem;
  color: var(--color-text-secondary);
  font-size: var(--font-size-sm);
}
</style>
