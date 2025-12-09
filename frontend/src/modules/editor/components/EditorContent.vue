<script lang="ts" setup>
import { ref, watch, onUnmounted, onMounted } from 'vue'
import { useMarkdownEditor } from '../composables/useMarkdownEditor'

// =========== Props & Emits ============
const props = defineProps<{ modelValue?: string }>()
const emit = defineEmits<{
  'update:modelValue': [value: string] // 具名元组语法
}>()

// =========== 响应式数据 ================
const editorRef = ref<HTMLDivElement | null>(null)
const h1Warning = ref<string | null>(null)

// =========== 使用 useMarkdownEditor ============
const editorAPI = useMarkdownEditor(editorRef)

// =========== Live Preview 行类型更新 ============
// 输入防抖定时器（500ms）
let inputTimer: number | null = null
// Live Preview 定时器（200ms）
let livePreviewTimer: number | null = null

const checkH1 = () => {
  const result = editorAPI.checkH1Unique(editorRef.value)
  h1Warning.value = result.hasWarning ? (result.message ?? null) : null
}

// 防抖调用 updateLineTypes (200ms)
const debouncedUpdateLineTypes = () => {
  if (livePreviewTimer) {
    clearTimeout(livePreviewTimer)
  }

  livePreviewTimer = window.setTimeout(() => {
    editorAPI.updateLineTypes(editorRef.value)
    checkH1()
    livePreviewTimer = null
  }, 200) // 200ms 防抖
}

// =========== IME 组合输入处理 ============
// 输入法组合输入状态标志（中文输入法）
let isComposing = false

// 输入法组合开始（用户开始输入拼音）：不触发 input 事件
const handleCompositionStart = () => {
  isComposing = true
}

// 输入法组合结束(用户确认文字)：标记结束，并手动启动防抖
// 这样做是为了防止浏览器在 compositionend 后不触发 input 事件导致漏记
const handleCompositionEnd = () => {
  isComposing = false

  // ✅ 清除旧的计时器（避免拼音状态被记录）
  if (inputTimer) {
    clearTimeout(inputTimer)
    inputTimer = null
  }

  // ✅ 同步状态
  if (editorRef.value) {
    const newContent = editorRef.value.innerHTML
    editorAPI.syncState()
    emit('update:modelValue', newContent)
  }

  // IME 输入结束后更新行类型
  debouncedUpdateLineTypes()
}

// ============ 事件处理 ===========

const handleInput = () => {
  if (!editorRef.value) return
  if (isComposing) return

  // 同步内容
  const newContent = editorRef.value.innerHTML
  editorAPI.syncState()
  emit('update:modelValue', newContent)

  // 500ms 计时器防抖
  if (inputTimer) {
    clearTimeout(inputTimer)
  }

  inputTimer = window.setTimeout(() => {
    editorAPI.recordHistory('输入')
    inputTimer = null
  }, 500)

  // 更新行类型（200ms 防抖）
  debouncedUpdateLineTypes()
}

const handlePaste = (event: ClipboardEvent) => {
  event.preventDefault()
  const text = event.clipboardData?.getData('text/plain') || ''
  if (!text) return

  document.execCommand('insertText', false, text)
  editorAPI.recordHistory('粘贴')
  debouncedUpdateLineTypes()
}

const handleBlur = () => {
  // 失焦时强制记录
  if (inputTimer) {
    clearTimeout(inputTimer)
    inputTimer = null
  }

  if (editorRef.value) {
    editorAPI.recordHistory('输入')
  }
}

const handleKeyDown = (event: KeyboardEvent) => {
  // Enter 键自动延续格式
  if (event.key === 'Enter' && !event.shiftKey && !isComposing) {
    if (editorAPI.handleEnterKey(event)) {
      // 已处理，更新行类型
      debouncedUpdateLineTypes()
      return
    }
  }

  // 检测修饰键（支持 Windows/Linux 的 Ctrl 和 macOS 的 Cmd）
  const isCtrlOrCmd = event.ctrlKey || event.metaKey
  const key = event.key.toLowerCase()

  // Ctrl/Cmd + Z: 撤销
  if (isCtrlOrCmd && key === 'z' && !event.shiftKey && !isComposing) {
    event.preventDefault() // ⚠️ 阻止浏览器默认撤销

    // ✅ 清除防抖并强制记录当前状态（确保不遗漏用户的输入）
    if (inputTimer) {
      clearTimeout(inputTimer)
      editorAPI.recordHistory('撤销')
      inputTimer = null
    }

    // 执行撤销
    editorAPI.undo()
    return
  }

  // Ctrl/Cmd + Shift + Z: 重做
  if (isCtrlOrCmd && key === 'z' && event.shiftKey && !isComposing) {
    event.preventDefault()

    // ✅ 清除防抖计时器，丢弃未保存的输入
    // 注意：重做时不应该记录历史，否则会创建新的历史记录，破坏 redo 逻辑
    if (inputTimer) {
      clearTimeout(inputTimer)
      inputTimer = null
    }

    // 执行重做
    editorAPI.redo()
    return
  }
}

const handleSelectionChange = () => {
  editorAPI.updateActiveLine(editorRef.value)
}

// ============ 监听 Props：外部更新同步 ===========
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue !== undefined && editorRef.value) {
      const currentContent = editorAPI.getContent()
      if (newValue !== currentContent) {
        editorRef.value.innerHTML = newValue
        editorAPI.setContent(newValue)

        // ✅ 新增：内容更新后立即更新行类型
        editorAPI.updateLineTypes(editorRef.value)

        // 如果历史为空，把初始内容存进去
        if (!editorAPI.canUndo.value && newValue) {
          editorAPI.recordHistory('初始内容')
        }
      }
    }
  },
  { immediate: true },
)

// ============ 监听 editorState：内部更新同步（如撤销/重做/格式化） ===========
// ✅ 恢复此监听，确保内部 API 操作能同步给父组件
watch(
  () => editorAPI.editorState.content,
  (newContent) => {
    if (newContent !== props.modelValue) {
      emit('update:modelValue', newContent)
    }
  },
)

// ============ 生命周期：清理资源 ===========
onMounted(() => {
  document.addEventListener('selectionchange', handleSelectionChange)
})

onUnmounted(() => {
  if (inputTimer) {
    clearTimeout(inputTimer)
    inputTimer = null
  }
  // ✅ 新增：清理 Live Preview 定时器
  if (livePreviewTimer) {
    clearTimeout(livePreviewTimer)
    livePreviewTimer = null
  }
  document.removeEventListener('selectionchange', handleSelectionChange)
  editorAPI.destroy()
})

// ======= 暴露 API 给父组件 =========
defineExpose({
  ...editorAPI,
  handleKeyDown,
  editorRef,
})
</script>

<template>
  <div v-if="h1Warning" class="editor-warning">⚠️ {{ h1Warning }}</div>
  <div class="editor-content">
    <div
      ref="editorRef"
      class="editor-editable"
      contenteditable="true"
      @input="handleInput"
      @keydown="handleKeyDown"
      @paste="handlePaste"
      @compositionstart="handleCompositionStart"
      @compositionend="handleCompositionEnd"
      @blur="handleBlur"
    ></div>
  </div>
</template>

<!-- 非 scoped 样式：Live Preview 样式 -->
<style>
@import '../styles/livePreview.css';
</style>

<!-- scoped 样式：组件私有样式 -->
<style scoped>
.editor-content {
  width: 100%;
}

.editor-editable {
  min-height: 100%;
  padding: 12px 16px 20vh; /*顶部内边距 12 像素， 左右两侧各 16 像素，底部内边距为视口高度的 20% */
  outline: none; /* 移除元素获得焦点时浏览器默认显示的轮廓线 */
  font-size: 16px;
  line-height: 1.75;
}

.editor-editable:empty::before {
  content: '开始编写...';
  color: #9ca3af;
}

.editor-warning {
  padding: 8px 12px;
  background-color: #fef3cd;
  border: 1px solid #ffc107;
  border-radius: 4px;
  color: #856404;
  font-size: 14px;
}
</style>
