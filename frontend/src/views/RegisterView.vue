<script lang="ts" setup>
import BrandLogo from '@/components/BrandLogo.vue'
import FormInput from '@/components/FormInput.vue'
import { useAuthStore } from '@/stores/auth.store'
import {
  validateEmail,
  validateCode,
  validatePassword,
  validateConfirmPassword,
} from '@/utils/validators'
import { sendCodeApi } from '@/api'

import {
  ArrowRight,
  Eye,
  EyeOff,
  Loader2,
  LockKeyhole,
  Mail,
  KeyRound,
  Send,
} from 'lucide-vue-next'
import { computed, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'

// ========== 状态初始化 ==========
const authStore = useAuthStore()
const router = useRouter()

// 表单数据
const email = ref('')
const code = ref('')
const password = ref('')
const confirmPassword = ref('')

// 密码显隐状态
const showPassword = ref(false)
const showConfirmPassword = ref(false)

// 倒计时状态
const countdown = ref(0)
let timer: number | null = null

// 加载状态
const isLoading = ref(false)

// 错误信息
const errors = ref({
  email: '',
  code: '',
  password: '',
  confirmPassword: '',
})

// ========== 计算属性 ==========
// 邮箱格式验证
const isValidEmail = computed(() => !validateEmail(email.value))

// ========== 方法定义 ==========
// 切换密码可见性
const togglePassword = () => {
  showPassword.value = !showPassword.value
}

const onEmailBlur = () => {
  errors.value.email = validateEmail(email.value) ?? ''
}

const onPasswordBlur = () => {
  errors.value.password = validatePassword(password.value) ?? ''
}

const onConfirmPasswordBlur = () => {
  errors.value.confirmPassword =
    validateConfirmPassword(password.value, confirmPassword.value) ?? ''
}

const onCodeBlur = () => {
  errors.value.code = validateCode(code.value) ?? ''
}

// 提交时检验全部
const validateForm = () => {
  errors.value.email = validateEmail(email.value) ?? ''
  errors.value.code = validateCode(code.value) ?? ''
  errors.value.password = validatePassword(password.value) ?? ''
  errors.value.confirmPassword =
    validateConfirmPassword(password.value, confirmPassword.value) ?? ''

  // 有错误返回 false，无错误返回 true
  return !Object.values(errors.value).some((e) => e !== '')
}

// 发送验证码
const handleSendCode = async () => {
  // 1. 前置检查
  if (!isValidEmail.value) return

  try {
    // 2. 发送验证码
    await sendCodeApi(email.value)
    // fix 封转 Toast 组件后这里改为调用 Toast 的方法
    console.log('✅ 验证码发送成功至:', email.value)

    // 3. 设置倒计时
    countdown.value = 60 // 设置初始值
    timer = window.setInterval(() => {
      countdown.value-- // 每秒减 1
      if (countdown.value <= 0) {
        if (timer) {
          clearInterval(timer) // 清除定时器
          timer = null
        }
      }
    }, 1000) // 每 1000ms (1秒) 执行一次
  } catch (error: any) {
    console.error('验证码发送失败:', error)
    // 如果后端返回了错误信息，显示给用户
    if (error.response?.data?.detail) {
      errors.value.email = error.response.data.detail // 将后端错误显示在输入框下方
    } else {
      alert('发送验证码失败，请稍后重试')
    }
  }
}

// 注册提交
const handleRegister = async () => {
  // 1. 表单验证
  if (!validateForm()) return

  // 2. 开始注册
  isLoading.value = true

  try {
    await authStore.register({
      email: email.value,
      password: password.value,
      verification_code: code.value,
    })
    console.log('✅ 注册并自动登录成功')

    // 3. 跳转首页
    router.push('/')
  } catch (error: any) {
    console.error('注册失败:', error)
    // 处理注册失败，比如验证码错误
    if (error.response?.data?.detail) {
      // 这里的 detail 可能是字符串，也可能是对象，简单处理直接弹窗或显示
      alert(error.response.data.detail)
    }
  } finally {
    isLoading.value = false
  }
}

// ========== 生命周期 ==========
onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>

<template>
  <div class="auth-container">
    <div class="top-toolbar">top-toolbar</div>

    <div class="auth-card">
      <div class="auth-header">
        <div class="auth-logo">
          <BrandLogo size="medium" :showName="true" direction="vertical" />
        </div>
        <h1 class="auth-title">创建账户</h1>
        <p class="auth-subtitle">填写信息完成注册</p>
      </div>

      <form class="auth-form" @submit.prevent="handleRegister">
        <div class="form-group">
          <label for="email" class="form-label">邮箱</label>
          <span class="required">*</span>
          <FormInput
            v-model="email"
            @blur="onEmailBlur"
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
          <div v-if="errors.email" class="error-message">{{ errors.email }}</div>
        </div>

        <div class="form-group">
          <label for="password" class="form-label">密码</label>
          <span class="required">*</span>
          <FormInput
            v-model="password"
            @blur="onPasswordBlur"
            id="password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="请输入密码"
            autocomplete="new-password"
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
          <div v-if="errors.password" class="error-message">{{ errors.password }}</div>
        </div>

        <div class="form-group">
          <label for="confirmPassword" class="form-label">确认密码</label>
          <span class="required">*</span>
          <FormInput
            v-model="confirmPassword"
            @blur="onConfirmPasswordBlur"
            id="confirmPassword"
            :type="showConfirmPassword ? 'text' : 'password'"
            placeholder="请再次输入新密码"
            autocomplete="new-password"
            required
          >
            <template #prefix>
              <LockKeyhole :size="20" />
            </template>
            <template #suffix>
              <Eye
                v-if="showConfirmPassword"
                :size="20"
                @click="showConfirmPassword = !showConfirmPassword"
                class="toggle-icon"
              ></Eye>
              <EyeOff
                v-else
                :size="20"
                @click="showConfirmPassword = !showConfirmPassword"
                class="toggle-icon"
              ></EyeOff>
            </template>
          </FormInput>
          <div v-if="errors.confirmPassword" class="error-message">
            {{ errors.confirmPassword }}
          </div>
        </div>

        <div class="form-group">
          <label for="verificationCode" class="form-label">邮箱验证码</label>
          <span class="required">*</span>
          <div class="input-with-button">
            <FormInput
              v-model="code"
              @blur="onCodeBlur"
              id="verificationCode"
              type="text"
              placeholder="请输入验证码"
              autocomplete="one-time-code"
              required
            >
              <template v-slot:prefix>
                <KeyRound :size="20" />
              </template>
            </FormInput>

            <button
              type="button"
              class="send-code-button"
              :disabled="countdown > 0 || !isValidEmail"
              @click="handleSendCode"
            >
              <Send :size="20" />
              {{ countdown > 0 ? `${countdown}s` : '获取验证码' }}
            </button>
          </div>
          <div v-if="errors.code" class="error-message">{{ errors.code }}</div>
        </div>

        <!-- 注册按钮 -->
        <button class="btn btn-primary btn-block" type="submit" :disabled="isLoading">
          <Loader2 v-if="isLoading" :size="20" class="loading-icon"></Loader2>
          <span>{{ isLoading ? '注册中...' : '创建账户' }}</span>
          <ArrowRight v-if="!isLoading" :size="20" />
        </button>
      </form>

      <!-- 登录链接 -->
      <div class="auth-footer">
        <div class="auth-divider">
          <span>已有账户？</span>
        </div>

        <router-link to="/login" class="btn btn-secondary btn-block">登 录</router-link>
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

.form-label {
  margin-bottom: 0.5rem;
  font-weight: 500;
}

.required {
  color: var(--color-error);
  margin-left: 4px;
  font-size: var(--font-size-base);
  vertical-align: middle; /* 图标与文字垂直居中对齐 */
}

/* ============================================
   验证码输入行：输入框 + 发送按钮 并排布局
   ============================================ */
.input-with-button {
  display: flex;
  align-items: stretch; /* 子元素高度一致 */
  height: 45px;
  gap: 4px;
}

/* 覆盖 FormInput 的容器样式 */
.input-with-button .input-wrapper {
  flex: 1; /* flex-grow: 1，占满剩余宽度 */
  width: auto; /* 覆盖原来的 width: 100% */
  min-width: 0; /* 默认情况下 flex 子项的 min-width 是 auto，会阻止元素收缩 */
}
/* ============================================
   发送验证码按钮样式
   ============================================ */
.send-code-button {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 6px;

  /* 尺寸 */
  min-width: 100px; /* 最小宽度，防止倒计时时按钮变窄 */
  padding: 0 15px; /* 水平内边距 */

  /* 文字 */
  font-size: var(--font-size-sm);
  font-weight: 500;
  white-space: nowrap; /* 文字不换行 */

  /* 边框圆角 */
  border-radius: 8px;

  /* 颜色 */
  background-color: var(--color-primary);
  border: none;
  color: #fff;

  /* 过渡动画 */
  cursor: pointer;
  transition: all 0.3s ease;
}
/* Hover 效果：填充背景色 */
.send-code-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
}
/* 禁用状态（倒计时中） */
.send-code-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: translateY(0);
}

.toggle-icon {
  cursor: pointer; /* 密码切换图标 - 可点击 */
}

.toggle-icon:hover {
  color: #3b82f6; /* 鼠标悬停时变色 */
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
  text-align: left;
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
