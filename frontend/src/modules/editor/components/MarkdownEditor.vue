<script lang="ts" setup>
import type { InlineFormatType, ParagraphFormatType, BlockInsertType } from '../composables/editor.types'
import EditorContent from './EditorContent.vue'
import EditorToolbar from './EditorToolbar.vue'
import TableOfContents from './TableOfContents.vue'
import { ref, watch, computed, nextTick, onUnmounted } from 'vue'
import { useTableOfContents } from '../composables/useTableOfContents'

// ==================== Props：声明接收父组件传来的数据（readonly） ====================
interface Props {
  modelValue?: string // 编辑器内容（HTML 格式）
  titleValue?: string // 文章标题
  showTitle?: boolean // 是否显示标题输入框
}

const props = withDefaults(defineProps<Props>(), {
  showTitle: true,
})

//  ==================== Emits：子向父发出的自定义事件 ====================
interface Emits {
  (e: 'update:modelValue', value: string): void // 内容变化时通知父组件（v-model）
  (e: 'update:titleValue', value: string): void // 标题变化时通知父组件（v-model:titleValue）
  (e: 'change', content: string, title: string): void // 内容或标题变化时的统一通知
}

const emit = defineEmits<Emits>()

// ==================== 数据 ====================
//  EditorContent 组件实例 和 DOM 元素（计算属性）
const editorContentRef = ref<InstanceType<typeof EditorContent> | null>(null)

// 编辑器内容的本地副本: 接收来自 EditorContent 的 v-model 更新
const content = ref(props.modelValue || '')

// 标题的本地副本: 与标题输入框双向绑定
const title = ref(props.titleValue || '')

// 目录数据
const editorElement = computed(() => editorContentRef.value?.editorRef ?? null)
const { tocItems, activeId, collectHeadings, scrollToHeading, cleanupObserver } =
  useTableOfContents(editorElement)

// ==================== 格式化方法 ====================
const handleInlineFormat = (action: InlineFormatType) => {
  editorContentRef.value?.toggleInlineFormat(action)
}

// 处理段落格式
const handleParagraphFormat = (action: ParagraphFormatType) => {
  editorContentRef.value?.toggleParagraphFormat(action)
}

// 处理块级插入
const handleInsertBlock = (action: BlockInsertType) => {
  editorContentRef.value?.insertBlock(action)
}

// ==================== 历史管理 ====================
const handleUndo = () => {
  editorContentRef.value?.undo()
}

const handleRedo = () => {
  editorContentRef.value?.redo()
}

// 历史状态计算属性: defineExpose 会自动解包 ref，所以直接访问即可
const canUndo = computed(() => editorContentRef.value?.canUndo ?? false)
const canRedo = computed(() => editorContentRef.value?.canRedo ?? false)

// ==================== 标题处理 ====================
const handleTitleChange = () => {
  emit('update:titleValue', title.value)
  emit('change', content.value, title.value)
}

// 标题输入框按 Enter 聚焦到编辑区
const focusEditor = (event: KeyboardEvent) => {
  // ⚠️ 阻止 Enter 键的默认行为，防止在标题输入框中插入换行符
  event.preventDefault()

  const editor = editorContentRef.value
  if (!editor) return

  // 聚焦编辑区
  editor.editorRef?.focus()

  // 将光标移动到编辑区的起始位置（位置 0）
  editor.setCursor(0)
}

// ==================== Props 监听 ====================
// 监听外部 Props 变化
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

// 监听本地 content 变化，向父组件发出事件
let tocTimer: number | null = null

watch(content, (newValue) => {
  emit('update:modelValue', newValue)
  emit('change', newValue, title.value)

  // 防抖收集标题
  if (tocTimer) clearTimeout(tocTimer)
  tocTimer = window.setTimeout(() => nextTick(collectHeadings), 300)
})

// ==================== 生命周期 ====================
// 监听组件卸载，清除观察器
onUnmounted(() => {
  cleanupObserver()
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
  // 暴露完整的编辑器 API
  editorContentRef,
})
</script>

<template>
  <div class="markdown-editor-wrapper">
    <!-- 编辑器主体 -->
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
        @undo="handleUndo"
        @redo="handleRedo"
        :canUndo
        :canRedo
      />

      <!-- 编辑区 -->
      <EditorContent ref="editorContentRef" v-model="content" />
    </div>

    <!-- 目录 -->
    <TableOfContents :items="tocItems" :activeId="activeId" @select="scrollToHeading" />
  </div>
</template>

<style scoped>
/* 外层包装器 */
.markdown-editor-wrapper {
  position: relative; /* 相对定位，作为子元素定位的参考 */
}

/* 主编辑器容器 */
.markdown-editor {
  max-width: 900px; /* 限制最大宽度，保证可读性 */
  min-height: calc(100vh - 100px); /* 视口高度减去顶部边距 */
  margin: 0 auto; /* 上下边距 0，左右自动（实现水平居中）*/
  border: 1px solid #e5e7eb; /* 浅灰色边框 */
  border-radius: 8px; /* 四个角的圆角半径 */
  overflow: hidden; /* 超出边界的内容被裁剪（配合圆角使用） */
  background: white; /* 白色背景 */
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.1); /* 阴影效果：水平偏移 0，垂直偏移 1px，模糊 3px，颜色黑色 10% 透明度 */
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
