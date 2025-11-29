<script lang="ts" setup>
import type { InlineFormatType, ParagraphFormatType, BlockInsertType } from '../types/editor'
import EditorContent from './EditorContent.vue'
import EditorToolbar from './EditorToolbar.vue'
import { ref, watch } from 'vue'

// ==================== Props：声明接收父组件传来的数据（readonly） ====================
interface Props {
  modelValue?: string
  titleValue?: string
  showTitle?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  showTitle: true,
})

//  ==================== Emits：子向父发出的自定义事件 ====================
interface Emits {
  (e: 'update:modelValue', value: string): void
  (e: 'update:titleValue', value: string): void
  (e: 'change', content: string, title: string): void
}

const emit = defineEmits<Emits>()

// ==================== ref: 模板引用 + 响应式数据 ====================
const editorContentRef = ref()
// 创建可修改的本地副本
const content = ref(props.modelValue || '')
const title = ref(props.titleValue || '')

// ==================== 方法 ====================
// 处理行内格式
const handleInlineFormat = (action: InlineFormatType) => {
  editorContentRef.value?.applyInlineFormat(action)
}

// 处理段落格式
const handleParagraphFormat = (action: ParagraphFormatType) => {
  editorContentRef.value?.applyParagraphFormat(action)
}

// 处理块级插入
const handleInsertBlock = (action: BlockInsertType) => {
  editorContentRef.value?.insertBlock(action)
}

// 处理编辑器内容更新
const handleTitleChange = () => {
  emit('update:titleValue', title.value)
  emit('change', content.value, title.value)
}

// 标题输入框按 Enter 聚焦到编辑区
const focusEditor = (event: KeyboardEvent) => {
  // ⚠️ 阻止 Enter 键的默认行为，防止在编辑区插入换行符
  event.preventDefault()

  const editor = editorContentRef.value
  if (!editor) return

  // 聚焦编辑区
  editor.editorElement.focus()

  // 将光标移动到编辑区的起始位置（位置 0）
  editor.setCursor(0)
}

// ==================== 监听 Props + content ====================
watch([() => props.modelValue, () => props.titleValue], ([newContent, newTitle]) => {
  // 处理 content 更新
  if (newContent !== undefined && newContent !== content.value) {
    content.value = newContent
  }

  // 处理 title 更新
  if (newTitle !== undefined && newTitle !== title.value) {
    title.value = newTitle
  }
})

// 监听 content 变化，向父组件发出事件
watch(content, (newValue) => {
  emit('update:modelValue', newValue)
  emit('change', newValue, title.value)
})

// ==================== 暴露 API ====================
defineExpose({
  // 暴露编辑器内容组件的所有方法
  getContent: () => content.value,
  setContent: (value: string) => {
    content.value = value
  },
  getTitle: () => title.value,
  setTitle: (value: string) => {
    title.value = value
  },
  // 直接暴露编辑器实例
  editorContent: editorContentRef,
})
</script>

<template>
  <div class="markdown-editor">
    <!-- 标题输入 -->
    <div v-if="showTitle" class="editor-title">
      <input
        type="text"
        v-model="title"
        placeholder="文章标题"
        class="title-input"
        @input="handleTitleChange"
        @keydown.enter="focusEditor"
      />
    </div>

    <!-- 工具栏 -->
    <EditorToolbar
      @inline-format="handleInlineFormat"
      @paragraph-format="handleParagraphFormat"
      @insert-block="handleInsertBlock"
    />

    <!-- 编辑区 -->
    <EditorContent ref="editorContentRef" v-model="content" />
  </div>
</template>

<style scoped>
/* 主编辑器容器 */
.markdown-editor {
  width: 100%; /* 占满父容器宽度 */
  max-width: 900px; /* 最大宽度900px（Medium最佳阅读宽度） */
  margin: 0 auto; /* 水平居中 */
  border: 1px solid #e5e7eb; /* 浅灰色边框 */
  border-radius: 8px; /* 圆角8px */
  overflow: hidden; /* 隐藏超出圆角的内容 */
  background: white; /* 白色背景 */
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); /* 轻微阴影 */
  transition: box-shadow 0.2s; /* 阴影过渡动画0.2秒 */
}

/* 编辑器获得焦点时的样式 */
.markdown-editor:focus-within {
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15); /* 更明显的阴影，突出焦点状态 */
}

/* 标题输入区域容器 */
.editor-title {
  border-bottom: 1px solid #e5e7eb; /* 底部分隔线 */
  padding: 16px 20px; /* 内边距：上下16px，左右20px */
}

/* 标题输入框 */
.title-input {
  width: 100%; /* 占满容器宽度 */
  border: none; /* 移除默认边框 */
  outline: none; /* 移除焦点轮廓 */
  font-size: 32px; /* 大字号 */
  font-weight: 600; /* 加粗 */
  color: #1f2937; /* 深灰色文字 */
}

/* 标题输入框占位符样式 */
.title-input::placeholder {
  color: #9ca3af; /* 浅灰色占位符文字 */
}

/* 移动端适配（屏幕宽度小于768px） */
@media (max-width: 768px) {
  .markdown-editor {
    max-width: 100%; /* 移动端占满屏幕宽度 */
    border-radius: 0; /* 移除圆角 */
    border-left: none; /* 移除左边框 */
    border-right: none; /* 移除右边框 */
  }

  .title-input {
    font-size: 24px; /* 移动端减小标题字号 */
  }
}
</style>
