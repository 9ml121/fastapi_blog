<script lang="ts" setup>
import BrandLogo from '@/components/common/BrandLogo.vue'
import FormInput from '@/components/common/FormInput.vue'
import { useAuthStore } from '@/stores/auth.store'

import { useToastStore } from '@/stores/toast.store'
import { ArrowRight, Eye, EyeOff, Loader2, LockKeyhole, Mail } from 'lucide-vue-next'
import { ref } from 'vue'
import { useRouter } from 'vue-router'

// ========== 状态初始化 ==========
const authStore = useAuthStore()
const toastStore = useToastStore()
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

// ========== 方法定义 ==========
// 切换密码可见性
const togglePassword = () => {
  showPassword.value = !showPassword.value
}

// 登录处理
const handleLogin = async () => {
  isLoading.value = true

  try {
    await authStore.login({
      username: username.value,
      password: password.value,
      remember: rememberMe.value,
    })
    // 登录成功，跳转到首页
    router.push('/')
  } catch (error: any) {
    toastStore.error(error.backendError?.message || '登录失败，请稍后重试')
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="auth-container">
    <div class="auth-card">
      <!-- Logo & 标题 -->
      <div class="auth-header">
        <h1 class="auth-title">登录</h1>
      </div>

      <!-- 登录表单 -->
      <form class="auth-form" @submit.prevent="handleLogin">
        <div class="form-group">
          <label for="email" class="form-label">邮箱</label>
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
          <label for="password" class="form-label">密码</label>
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
            <span>30天内免登录</span>
          </label>
          <router-link to="/forgot-password" class="forgot-password">忘记密码?</router-link>
        </div>

        <!-- 登录按钮 -->
        <button class="btn btn-primary btn-block" type="submit" :disabled="isLoading">
          <Loader2 v-if="isLoading" :size="20" class="loading-icon"></Loader2>
          <span>{{ isLoading ? '登录中...' : '登录' }}</span>
          <ArrowRight v-if="!isLoading" :size="20" />
        </button>
      </form>

      <!-- 注册链接 -->
      <div class="auth-footer">
        <div class="auth-divider">
          <span>还没有账户？</span>
        </div>
        <router-link to="/register" class="btn btn-secondary btn-block">注册</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ========== 记住我 & 忘记密码 ========== */
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
  color: var(--color-text-secondary);
  cursor: pointer;
}

.remember-me input[type='checkbox'] {
  width: 16px;
  height: 16px;
  cursor: pointer;
}

.forgot-password {
  color: var(--color-link);
  text-decoration: none;
}

.forgot-password:hover {
  text-decoration: underline;
}
</style>
