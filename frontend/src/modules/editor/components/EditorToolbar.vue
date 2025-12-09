<script lang="ts" setup>
import {
  Bold,
  Italic,
  Link,
  Code,
  Heading1,
  Heading2,
  Heading3,
  Quote,
  FileCode,
  Image,
  Table,
  Divide,
  Undo,
  Redo,
} from 'lucide-vue-next'
import type { InlineFormatType, ParagraphFormatType, BlockInsertType } from '../composables/editor.types'

// ==================== Props & Emits ====================
defineProps<{
  canUndo?: boolean
  canRedo?: boolean
}>()

interface Emits {
  (e: 'inline-format', action: InlineFormatType): void
  (e: 'paragraph-format', action: ParagraphFormatType): void
  (e: 'insert-block', action: BlockInsertType): void
  (e: 'undo'): void
  (e: 'redo'): void
}

const emit = defineEmits<Emits>()

// ==================== 方法 ====================
const handleFormat = (action: string) => {
  // 行内格式
  const inlineFormats: InlineFormatType[] = ['bold', 'italic', 'code',  'link']
  if (inlineFormats.includes(action as InlineFormatType)) {
    emit('inline-format', action as InlineFormatType)
    return
  }

  // 段落格式
  const paragraphFormats: ParagraphFormatType[] = ['heading1', 'heading2', 'heading3', 'quote']
  if (paragraphFormats.includes(action as ParagraphFormatType)) {
    emit('paragraph-format', action as ParagraphFormatType)
    return
  }
}

const handleInsert = (action: BlockInsertType) => {
  emit('insert-block', action)
}
</script>

<template>
  <div class="toolbar">
    <div class="toolbar-group">
      <button
        @click="emit('undo')"
        :disabled="!canUndo"
        title="撤销 (Ctrl+Z)"
        class="toolbar-btn"
      >
        <Undo :size="18" />
      </button>

      <button
        @click="emit('redo')"
        :disabled="!canRedo"
        title="重做 (Ctrl+Shift+Z)"
        class="toolbar-btn"
      >
        <Redo :size="18" />
      </button>
    </div>
    <div class="toolbar-divider"></div>

    <!-- 行内格式 -->
    <div class="toolbar-group">
      <button @click="handleFormat('bold')" title="加粗 (Ctrl+B)" class="toolbar-btn">
        <Bold :size="18" />
      </button>
      <button @click="handleFormat('italic')" title="斜体 (Ctrl+I)" class="toolbar-btn">
        <Italic :size="18" />
      </button>
      <button @click="handleFormat('code')" title="行内代码" class="toolbar-btn">
        <Code :size="18" />
      </button>
      <button @click="handleFormat('link')" title="插入链接 (Ctrl+K)" class="toolbar-btn">
        <Link :size="18" />
      </button>
    </div>

    <div class="toolbar-divider"></div>

    <!-- 段落格式 -->
    <div class="toolbar-group">
      <button @click="handleFormat('heading1')" title="一级标题" class="toolbar-btn">
        <Heading1 :size="18" />
      </button>
      <button @click="handleFormat('heading2')" title="二级标题" class="toolbar-btn">
        <Heading2 :size="18" />
      </button>
      <button @click="handleFormat('heading3')" title="三级标题" class="toolbar-btn">
        <Heading3 :size="18" />
      </button>
      <button @click="handleFormat('quote')" title="引用块" class="toolbar-btn">
        <Quote :size="18" />
      </button>
    </div>

    <!-- 分割线 -->
    <div class="toolbar-divider"></div>

    <!-- 插入块 -->
    <div class="toolbar-group">
      <button @click="handleInsert('divider')" title="分割线" class="toolbar-btn">
        <Divide :size="18" />
      </button>
      <button @click="handleInsert('codeBlock')" title="代码块" class="toolbar-btn">
        <FileCode :size="18" />
      </button>
      <button @click="handleInsert('image')" title="插入图片" class="toolbar-btn">
        <Image :size="18" />
      </button>
      <button @click="handleInsert('table')" title="插入表格" class="toolbar-btn">
        <Table :size="18" />
      </button>
    </div>
  </div>
</template>

<style scoped>
/* ========== 工具栏容器 ========== */
.toolbar {
  display: flex; /* 使用 flex 布局，让子元素横向排列 */
  gap: 8px; /* 子元素之间的间距 */
  padding: 8px 12px; /* 工具栏内边距（上下8px，左右12px）*/
  border-bottom: 1px solid #e5e7eb; /* 底部边框，分隔工具栏和编辑区 */
  background: #f9fafb; /* 浅灰色背景 */
}

/* ========== 按钮组 ========== */
.toolbar-group {
  display: flex; /* flex 布局，让按钮横向排列 */
  gap: 2px; /* 按钮之间的小间距 */
}

/* ========== 分割线 ========== */
.toolbar-divider {
  width: 1px; /* 分割线宽度 1px */
  background: #d1d5db; /* 灰色背景 */
  margin: 0 6px; /* 左右留6px间距 */
}

/* ========== 按钮基础样式 ========== */
.toolbar-btn {
  display: flex; /* flex 布局，用于居中图标 */
  align-items: center; /* 垂直居中 */
  justify-content: center; /* 水平居中 */
  padding: 6px; /* 按钮内边距 */
  border: none; /* 移除默认边框 */
  border-radius: 4px; /* 圆角 4px */
  background: transparent; /* 默认透明背景 */
  color: #6b7280; /* 灰色图标/文字 */
  cursor: pointer; /* 鼠标悬停时显示手型 */
  transition: all 0.15s; /* 所有属性变化都有 150ms 过渡动画 */
}

/* ========== 按钮悬停效果 ========== */
.toolbar-btn:hover {
  background: #e5e7eb; /* 悬停时浅灰色背景 */
  color: #1f2937; /* 悬停时深色图标/文字 */
}

/* ========== 按钮按下效果 ========== */
.toolbar-btn:active {
  background: #d1d5db; /* 按下时更深的灰色背景 */
}

/* ========== 禁用按钮样式 ========== */
.toolbar-btn:disabled {
  opacity: 0.4; /* 降低不透明度到40%，显示更明显的灰暗效果 */
  cursor: not-allowed; /* 鼠标悬停时显示禁止图标 */
  background-color: transparent; /* 禁用时保持透明背景 */
  color: #cbd5e1; /* 禁用时非常浅的灰色图标 */
  pointer-events: none; /* 禁用所有鼠标事件，包括点击 */
}

/* ========== 禁用按钮悬停时不变 ========== */
.toolbar-btn:disabled:hover {
  background-color: transparent; /* 禁用时悬停不改变背景（覆盖 .toolbar-btn:hover）*/
  color: #cbd5e1; /* 禁用时悬停保持浅灰色 */
  transform: none; /* 禁用时悬停不移动（如果有 transform 的话）*/
}

/* ========== 响应式设计 ========== */
@media (max-width: 768px) {
  .toolbar {
    overflow-x: auto; /* 小屏幕时允许水平滚动，避免按钮被遮挡 */
  }
}
</style>
