<script lang="ts" setup>
import BrandLogo from '@/components/BrandLogo.vue'
import LoginCard from '@/components/BaseCard.vue'
import FormInput from '@/components/FormInput.vue'

import { ref } from 'vue'
import { LockKeyhole, Mail, Eye, EyeOff, Loader2 } from 'lucide-vue-next'

// 表单数据
const username = ref('')
const password = ref('')

// 密码可见性状态
const showPassword = ref(false)

// 加载状态
const isLoading = ref(false)

// 记住我状态
const rememberMe = ref(false)

// 切换密码可见性
const togglePassword = () => {
  showPassword.value = !showPassword.value
}

// todo 登录处理（暂时模拟）
const handleLogin = async () => {
  isLoading.value = true

  // 模拟网络请求延迟
  await new Promise((resolve) => setTimeout(resolve, 2000))

  console.log('登录信息:', {
    username: username.value,
    password: password.value,
  })
  isLoading.value = false
}
</script>

<template>
  <div class="auth-container">
    <div class="top-toolbar">此处待开发暗色切换按钮和国际化？？</div>
    <div class="auth-card">
      <div class="auth-logo">
        <BrandLogo size="large" :showName="true" direction="vertical" />
      </div>

      <!-- 用户名输入框 -->
      <FormInput v-model="username" placeholder="请输入邮箱地址">
        <template v-slot:prefix>
          <Mail :size="20" />
        </template>
        <template v-slot:suffix></template>
      </FormInput>

      <!-- 密码输入框 -->
      <FormInput
        v-model="password"
        :type="showPassword ? 'text' : 'password'"
        placeholder="请输入密码"
      >
        <template #prefix>
          <LockKeyhole :size="20" />
        </template>
        <template #suffix>
          <Eye v-if="showPassword" :size="20" @click="togglePassword" class="toggle-icon"></Eye>
          <EyeOff v-else :size="20" @click="togglePassword" class="toggle-icon"></EyeOff>
        </template>
      </FormInput>

      <!-- 记住我 & 忘记密码 -->
      <div class="form-option">
        <label class="remember-me">
          <input type="checkbox" v-model="rememberMe" />
          <span>记住我</span>
        </label>
        <a href="#" class="forget-password">忘记密码?</a>
      </div>

      <!-- 登录按钮 -->
      <button class="login-btn" :disabled="isLoading" @click="handleLogin">
        <Loader2 v-if="isLoading" :size="20" class="loading-icon"></Loader2>
        <span>{{ isLoading ? '登录中...' : '登 录' }}</span>
      </button>

      <!-- 注册链接 -->
      <div class="register-link">
        <span>没有账号？</span>
        <router-link to="/register">立即注册</router-link>
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
  justify-content: center; /* 水平居中 */
  align-items: center; /* 垂直居中 */
  padding: 2rem 1rem;


  background-color: #f5f7fa; /* 只能设置纯色背景 */
}

/* 主内容区 - Flexbox 垂直水平居中 */
.auth-card {
  width: 100%;
  max-width: 420px;
  background: #ffffff; /* 简写属性，可设置颜色、图片、渐变等多种属性 */
  border-radius: 24px;
  box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
  backdrop-filter: blur(10px); /*让元素背后的内容变模糊（毛玻璃效果）*/
  border: 1px solid rgba(53, 92, 194, 0.1);
  gap: 20px; /* 子元素间距 20px */

}

/* 登录卡片容器 - 白色圆角卡片 */
.auth-logo {




  display: flex;


}

.toggle-icon {
  cursor: pointer; /* 密码切换图标 - 可点击 */
}

.toggle-icon:hover {
  color: #3b82f6; /* 鼠标悬停时变色 */
}

/* 记住我 & 忘记密码 容器 */
.form-option {
  display: flex;
  justify-content: space-between; /* 两端对齐 */
  align-items: center;
  font-size: 14px;
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

/* 登录按钮 */
.login-btn {
  width: 100%;
  height: 48px;
  margin-top: 24px;
  background-color: #3b82f6;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 16px;
  font-weight: 500;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  /* 子元素间距 8px（图标和文字之间） */
  gap: 8px;
  /* 效果：悬停时背景色变化会平滑过渡，而不是突然切换。 */
  transition: all 0.2s ease;
}
/* 悬停效果: 鼠标悬停时变深蓝色，但如果按钮是禁用状态，则不变色*/
.login-btn:hover:not(:disabled) {
  background-color: rgba(53, 92, 194, 0.85);
  transform: translateY(-1px);
  box-shadow: 0 4px 10px rgba(53, 92, 194, 0.3);
}
/* 禁用状态 */
.login-btn:disabled {
  background-color: #93c5fd;
  cursor: not-allowed;
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

/* 注册链接 */
.register-link {
  text-align: center;
  font-size: 14px;
  color: #6b7280;
}

.register-link a {
  color: #3b82f6;
  text-decoration: none;
  margin-left: 4px;
}

.register-link a:hover {
  text-decoration: underline;
}
</style>
