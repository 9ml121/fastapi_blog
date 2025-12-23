<script lang="ts" setup>
import { useToastStore } from '@/stores/toast.store'
import { CheckCircle, XCircle, AlertTriangle, Info, X } from 'lucide-vue-next'
import type { ToastType } from '@/stores/toast.store'

const toastStore = useToastStore()

// 图标映射
const iconMap = {
  success: CheckCircle,
  error: XCircle,
  warning: AlertTriangle,
  info: Info,
}

// 颜色映射（CSS 变量或直接颜色）
const colorMap = {
  success: '#10b981', // 绿色
  error: '#ef4444', // 红色
  warning: '#f59e0b', // 橙色
  info: '#3b82f6', // 蓝色
}

// 获取对应类型的图标组件
const getIcon = (type: ToastType) => iconMap[type]

// 获取对应类型的颜色
const getColor = (type: ToastType) => colorMap[type]
</script>

<template>
  <!-- Toast 容器 - 固定在右上角 -->
  <div class="toast-container">
    <!-- 使用 TransitionGroup 实现列表动画 -->
    <TransitionGroup name="toast">
      <div
        v-for="toast in toastStore.toasts"
        :key="toast.id"
        class="toast"
        :class="`toast-${toast.type}`"
        @click="toastStore.removeToast(toast.id)"
      >
        <!-- 图标 -->
        <component
          :is="getIcon(toast.type)"
          :size="20"
          :color="getColor(toast.type)"
          class="toast-icon"
        />

        <!-- 消息内容 -->
        <span class="toast-message">{{ toast.message }}</span>

        <!-- 关闭按钮 -->
        <button class="toast-close" @click.stop="toastStore.removeToast(toast.id)">
          <X :size="16" />
        </button>
      </div>
    </TransitionGroup>
  </div>
</template>

<style scoped>
/* ========== Toast 容器 ========== */
.toast-container {
  position: fixed;
  top: 20px;
  right: 20px;
  z-index: 9999; /* 确保在最上层 */
  display: flex;
  flex-direction: column;
  gap: 12px;
  pointer-events: none; /* 容器不阻止点击事件 */
}

/* ========== 单个 Toast 卡片 ========== */
.toast {
  pointer-events: auto; /* 卡片本身可点击 */

  display: flex;
  align-items: center;
  gap: 12px;

  min-width: 300px;
  max-width: 400px;
  padding: 16px;

  background: white;
  border-radius: 8px;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);

  cursor: pointer;
  transition: all 0.3s ease;
}

.toast:hover {
  transform: translateX(-4px);
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.2);
}

/* ========== 图标样式 ========== */
.toast-icon {
  flex-shrink: 0; /* 防止图标被压缩 */
}

/* ========== 消息文字 ========== */
.toast-message {
  flex: 1;
  font-size: 14px;
  color: #333;
  line-height: 1.5;
  word-break: break-word; /* 长单词自动换行 */
}

/* ========== 关闭按钮 ========== */
.toast-close {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;

  width: 24px;
  height: 24px;
  padding: 0;

  background: transparent;
  border: none;
  border-radius: 4px;
  color: #6b7280;

  cursor: pointer;
  transition: all 0.2s ease;
}

.toast-close:hover {
  background: rgba(0, 0, 0, 0.05);
  color: #333;
}

/* ========== 不同类型的左边框 ========== */
.toast-success {
  border-left: 4px solid #10b981;
}

.toast-error {
  border-left: 4px solid #ef4444;
}

.toast-warning {
  border-left: 4px solid #f59e0b;
}

.toast-info {
  border-left: 4px solid #3b82f6;
}

/* ========== 进入/退出动画 ========== */
/* 进入时：从右侧滑入 + 淡入 */
.toast-enter-active {
  animation: slideInRight 0.3s ease-out;
}

/* 退出时：向右滑出 + 淡出 */
.toast-leave-active {
  animation: slideOutRight 0.3s ease-in;
}

/* 移动动画（列表重新排列时） */
.toast-move {
  transition: transform 0.3s ease;
}

/* 关键帧动画：滑入 */
@keyframes slideInRight {
  from {
    transform: translateX(100%);
    opacity: 0;
  }
  to {
    transform: translateX(0);
    opacity: 1;
  }
}

/* 关键帧动画：滑出 */
@keyframes slideOutRight {
  from {
    transform: translateX(0);
    opacity: 1;
  }
  to {
    transform: translateX(100%);
    opacity: 0;
  }
}
</style>
