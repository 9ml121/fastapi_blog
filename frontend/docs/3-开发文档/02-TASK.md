## 要求1
你先认真分析一下 https://crelay.net/#/login 这个网站登录页面设计，我们登录页面就对标这个页面开发。然后更新一篇 登录页面UI设计文档，重点讲一下 这个页面的 UI 要求，以及实现的技术要点。
要求：
1. 基于我们前后端已有api功能
2. icon图标我们是用lucide-vue-next
3. 网页logo图片和网站名称你帮我设计一下，要求简洁大气


## 要求2
1. 前后端登录的 api 目前是已经完成了的，参考app/api/v1/endpoints/auth.py，frontend/src/modules/auth/api.ts；
2. 另外我们这个是学习项目，要参考项目要求规范 agent/rules/agent.md；
3. 我们目前为了方便学习，是采用模块化高内聚的开发模式，登录功能都在frontend/src/modules/auth，
4. 你这个设计文档比较全面，我们一下子可能吃不消，你按照教学友好的方式，分阶段分步骤指导我一步步实现，重点是要讲解每一步的技术要点。
5. 登录设计文档维护到 `2-设计文档/登录功能`

```vue
<template>
  <form class="login-form" @submit.prevent="handleSubmit">
    <!-- 标题 -->
    <div class="form-header">
      <h1 class="form-title">登录账户</h1>
      <p class="form-subtitle">请输入您的凭据继续</p>
    </div>

    <!-- 邮箱输入 -->
    <div class="form-group">
      <label class="form-label">
        邮箱 <span class="required">*</span>
      </label>
      <div class="input-wrapper">
        <span class="input-icon">📧</span>
        <input
          v-model="form.username"
          type="email"
          class="form-input"
          placeholder="请输入邮箱地址"
          :disabled="authStore.isLoading"
        />
      </div>
      <span v-if="errors.username" class="error-text">{{ errors.username }}</span>
    </div>

    <!-- 密码输入 -->
    <div class="form-group">
      <label class="form-label">
        密码 <span class="required">*</span>
      </label>
      <div class="input-wrapper">
        <span class="input-icon">🔒</span>
        <input
          v-model="form.password"
          :type="showPassword ? 'text' : 'password'"
          class="form-input"
          placeholder="请输入密码"
          :disabled="authStore.isLoading"
        />
        <button 
          type="button" 
          class="toggle-password"
          @click="showPassword = !showPassword"
        >
          {{ showPassword ? '🙈' : '👁' }}
        </button>
      </div>
      <span v-if="errors.password" class="error-text">{{ errors.password }}</span>
    </div>

    <!-- 错误提示 -->
    <div v-if="loginError" class="login-error">{{ loginError }}</div>

    <!-- 登录按钮 -->
    <button 
      type="submit" 
      class="submit-btn"
      :disabled="authStore.isLoading"
    >
      {{ authStore.isLoading ? '登录中...' : '登录' }}
      <span v-if="!authStore.isLoading" class="btn-arrow">→</span>
    </button>
  </form>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useAuthStore } from './auth.store'

const emit = defineEmits<{
  success: []
}>()

const authStore = useAuthStore()

// 表单数据
const form = reactive({
  username: '',
  password: '',
})

// 验证错误
const errors = reactive({
  username: '',
  password: '',
})

// 登录错误
const loginError = ref('')

// 密码显隐
const showPassword = ref(false)

// 表单验证
function validate(): boolean {
  let isValid = true
  errors.username = ''
  errors.password = ''

  if (!form.username.trim()) {
    errors.username = '请输入邮箱'
    isValid = false
  }

  if (!form.password) {
    errors.password = '请输入密码'
    isValid = false
  }

  return isValid
}

// 提交登录
async function handleSubmit() {
  loginError.value = ''
  
  if (!validate()) return

  try {
    await authStore.login(form)
    emit('success')
  } catch (error: any) {
    loginError.value = error.response?.data?.error?.message || '登录失败，请重试'
  }
}
</script>

<style scoped>
/* 表单容器 */
.login-form {
  width: 100%;
  max-width: 400px;
}

/* 标题区域 */
.form-header {
  text-align: center;
  margin-bottom: 32px;
}

.form-title {
  font-size: 24px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 8px 0;
}

.form-subtitle {
  font-size: 14px;
  color: #6b7280;
  margin: 0;
}

/* 表单组 */
.form-group {
  margin-bottom: 20px;
}

.form-label {
  display: block;
  font-size: 14px;
  font-weight: 500;
  color: #374151;
  margin-bottom: 8px;
}

.required {
  color: #ef4444;
}

/* 输入框包装器 */
.input-wrapper {
  position: relative;
  display: flex;
  align-items: center;
}

.input-icon {
  position: absolute;
  left: 12px;
  font-size: 16px;
  color: #9ca3af;
}

.form-input {
  width: 100%;
  padding: 12px 12px 12px 40px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  font-size: 14px;
  color: #1f2937;
  transition: border-color 0.2s, box-shadow 0.2s;
}

.form-input:focus {
  outline: none;
  border-color: #3b82f6;
  box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}

.form-input::placeholder {
  color: #9ca3af;
}

.form-input:disabled {
  background-color: #f3f4f6;
  cursor: not-allowed;
}

/* 密码显隐按钮 */
.toggle-password {
  position: absolute;
  right: 12px;
  background: none;
  border: none;
  font-size: 16px;
  cursor: pointer;
  color: #6b7280;
}

/* 错误提示 */
.error-text {
  display: block;
  margin-top: 4px;
  font-size: 12px;
  color: #ef4444;
}

.login-error {
  padding: 12px;
  background-color: #fef2f2;
  border: 1px solid #fecaca;
  border-radius: 8px;
  color: #dc2626;
  font-size: 14px;
  text-align: center;
  margin-bottom: 16px;
}

/* 登录按钮 */
.submit-btn {
  width: 100%;
  padding: 14px;
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
  gap: 8px;
  transition: background-color 0.2s;
}

.submit-btn:hover {
  background-color: #2563eb;
}

.submit-btn:disabled {
  background-color: #9ca3af;
  cursor: not-allowed;
}

.btn-arrow {
  font-size: 18px;
}
</style>

```