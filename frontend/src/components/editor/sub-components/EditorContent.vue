<script lang="ts" setup>
import { ref, reactive, watch } from 'vue'
import type { EditorState } from '../types/editor'
import { useSelection } from '../composables/useSelection'
import { useMarkdown } from '../composables/useMarkdown'
import { useHistory } from '../composables/useHistory'

// =========== Props & Emits ============
const props = defineProps<{ modelValue?: string }>()

const emit = defineEmits<{ (e: 'update:modelValue', value: string): void }>()

// =========== 响应式数据 ================
const editorRef = ref<HTMLDivElement | null>(null)

// 编辑器状态
const editorState = reactive<EditorState>({
  // Content Layer
  title: '',
  content: '',

  // History Layer (暂未实现)
  transactions: [],
  currentIndex: -1,

  // UI Layer
  selection: { start: 0, end: 0, selectedText: '', isEmpty: true },
  isSaving: false,
  isDirty: false,
  isFocused: false,

  // Error Layer
  hasError: false,

  // Computed Cache
  canUndo: false,
  canRedo: false,
})


// ============ 监听 Props（设置初始内容和后续更新）===========
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue !== undefined && editorRef.value && newValue !== editorState.content) {
      editorRef.value.innerHTML = newValue
      editorState.content = newValue
    }
  },
  { immediate: true }, // 组件挂载时立即执行
)

// ============ 监听 editorState.content（处理格式化操作）===========
watch(
  () => editorState.content,
  (newContent) => {
    // 格式化操作会更新 editorState.content，需要同步到父组件
    if (newContent && newContent !== props.modelValue) {
      emit('update:modelValue', newContent)
    }
  },
)

// ============ 方法 ===========
// 输入事件处理
const handleInput = () => {
  if (editorRef.value) {
    const newContent = editorRef.value.innerHTML
    emit('update:modelValue', newContent)
    editorState.content = newContent
    editorState.isDirty = true
  }
}

// 快捷键处理
const handleKeyDown = (event: KeyboardEvent) => {
  // 检测修饰键（支持 Windows/Linux 的 Ctrl 和 macOS 的 Cmd）
  const isMod = event.ctrlKey || event.metaKey

  // 撤销：Ctrl+Z / Cmd+Z
  if (isMod && event.key === 'z' && !event.shiftKey) {
    event.preventDefault() // ⚠️ 阻止浏览器默认撤销

    const previousContent = historyAPI.undo
    if (previousContent !== null && editorRef.value) {
      // 恢复内容到编辑区
      editorRef.value.innerHTML = previousContent
    }
  }
}

// ======== 初始化 composables =========
const selectionAPI = useSelection(editorRef, editorState)
const markdownAPI = useMarkdown(editorState, selectionAPI)
const historyAPI = useHistory(editorState)

// ======= 暴露 API 给父组件 =========
defineExpose({
  ...selectionAPI,
  ...markdownAPI,
  ...historyAPI,
  editorElement: editorRef,
  state: editorState,
})
</script>

<template>
  <div class="editor-content">
    <div ref="editorRef" class="editor-editable" contenteditable="true" @input="handleInput">
      <div><br></div>
    </div>
  </div>
</template>

<style scoped>
.editor-content {
  width: 100%;
  min-height: 400px;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 16px;
}

.editor-editable {
  min-height: 100%;
  outline: none;
  font-size: 16px;
  line-height: 1.75;
}

.editor-editable:empty::before {
  content: '开始编写...';
  color: #9ca3af;
}
</style>
