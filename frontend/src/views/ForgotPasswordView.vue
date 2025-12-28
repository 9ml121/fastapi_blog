<script lang="ts" setup>
import { forgotPasswordApi, resetPasswordApi } from '@/api/auth.api'
import BrandLogo from '@/components/common/BrandLogo.vue'
import FormInput from '@/components/common/FormInput.vue'
import {
  validateCode,
  validateConfirmPassword,
  validateEmail,
  validatePassword,
} from '@/utils/validators'

import { useCountdown } from '@/composables/useCountdown'
import { useToastStore } from '@/stores/toast.store'
import {
  ArrowRight,
  Eye,
  EyeOff,
  KeyRound,
  Loader2,
  LockKeyhole,
  Mail,
  Send,
} from 'lucide-vue-next'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

// ========== 状态初始化 ==========
const router = useRouter()
const toastStore = useToastStore()
const { countdown, start: startCountdown } = useCountdown(60)

// 表单数据
const email = ref('')
const code = ref('')
const password = ref('')
const confirmPassword = ref('')

// 密码显隐状态
const showPassword = ref(false)
const showConfirmPassword = ref(false)

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
const isValidEmail = computed(() => validateEmail(email.value) === null)

// ========== 方法定义 ==========
const togglePasswordVisibility = (field: 'password' | 'confirmPassword') => {
  if (field === 'password') showPassword.value = !showPassword.value
  else showConfirmPassword.value = !showConfirmPassword.value
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

const validateForm = () => {
  errors.value.email = validateEmail(email.value) ?? ''
  errors.value.code = validateCode(code.value) ?? ''
  errors.value.password = validatePassword(password.value) ?? ''
  errors.value.confirmPassword =
    validateConfirmPassword(password.value, confirmPassword.value) ?? ''

  return !Object.values(errors.value).some((e) => e !== '')
}

const handleSendCode = async () => {
  // 1. 前置检查
  if (!isValidEmail.value) return

  try {
    // 2. 发送验证码
    await forgotPasswordApi(email.value)
    toastStore.success('验证码已发送，请查收邮件')

    // 3. 启动倒计时
    startCountdown()
  } catch (error: any) {
    // 忘记密码场景：邮箱必须已注册
    if (error.backendError?.code === 'RESOURCE_NOT_FOUND') {
      errors.value.email = '该邮箱未注册'
    }
  }
}

// 重置密码提交
const handleReset = async () => {
  if (!validateForm()) return
  isLoading.value = true

  try {
    await resetPasswordApi({
      email: email.value,
      new_password: password.value,
      verification_code: code.value,
    })

    toastStore.success('重置密码成功！')

    setTimeout(() => {
      router.push('/login')
    }, 1000)
  } catch (error: any) {
    if (error.backendError?.code === 'RESOURCE_NOT_FOUND') {
      errors.value.email = '该邮箱未注册'
    } else if (error.backendError?.code === 'INVALID_VERIFICATION_CODE') {
      errors.value.code = error.backendError.message
    }
  } finally {
    isLoading.value = false
  }
}
</script>

<template>
  <div class="auth-container">
    <div class="auth-card">
      <div class="auth-header">
        <h1 class="auth-title">重置密码</h1>
      </div>

      <form class="auth-form" @submit.prevent="handleReset">
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
          <label for="password" class="form-label">新密码</label>
          <span class="required">*</span>
          <FormInput
            v-model="password"
            @blur="onPasswordBlur"
            id="password"
            :type="showPassword ? 'text' : 'password'"
            placeholder="请输入新密码"
            autocomplete="new-password"
            required
          >
            <template #prefix>
              <LockKeyhole :size="20" />
            </template>
            <template #suffix>
              <Eye
                v-if="showPassword"
                :size="20"
                @click="togglePasswordVisibility('password')"
                class="toggle-icon"
              ></Eye>
              <EyeOff
                v-else
                :size="20"
                @click="togglePasswordVisibility('password')"
                class="toggle-icon"
              ></EyeOff>
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
                @click="togglePasswordVisibility('confirmPassword')"
                class="toggle-icon"
              ></Eye>
              <EyeOff
                v-else
                :size="20"
                @click="togglePasswordVisibility('confirmPassword')"
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

        <!-- 重置密码按钮 -->
        <button class="btn btn-primary btn-block" type="submit" :disabled="isLoading">
          <Loader2 v-if="isLoading" :size="20" class="loading-icon"></Loader2>
          <span>{{ isLoading ? '重置中...' : '重置密码' }}</span>
          <ArrowRight v-if="!isLoading" :size="20" />
        </button>
      </form>

      <!-- 返回登录 -->
      <div class="auth-footer">
        <div class="auth-divider">
          <span>想起密码？</span>
        </div>
        <router-link to="/login" class="btn btn-secondary btn-block">返回登录</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* ========== 验证码输入行 ========== */
.input-with-button {
  display: flex;
  align-items: stretch;
  height: 45px;
  gap: 4px;
}

/* 覆盖 FormInput 的容器样式 */
.input-with-button .input-wrapper {
  flex: 1; /* flex-grow: 1，占满剩余宽度 */
  width: auto; /* 覆盖原来的 width: 100% */
  min-width: 0; /* 默认情况下 flex 子项的 min-width 是 auto，会阻止元素收缩 */
}

/* ========== 发送验证码按钮 ========== */
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

.send-code-button:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 4px 10px rgba(0, 0, 0, 0.15);
}

.send-code-button:disabled {
  opacity: 0.6;
  cursor: not-allowed;
  transform: translateY(0);
}
</style>
