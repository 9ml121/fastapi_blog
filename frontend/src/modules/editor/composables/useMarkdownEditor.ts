import { reactive, type Ref, readonly } from 'vue'
import type {
  BlockInsertType,
  EditorState,
  InlineFormatType,
  ParagraphFormatType,
} from './editor.types'
import { useSelection } from './useSelection'
import { useMarkdown } from './useMarkdown'
import { useHistory } from './useHistory'
import { useLivePreview} from './useLivePreview'
import { getTextContent as getTextContentUtil } from '../utils/selection'

/**
 * Markdown 编辑器整合层： 负责协调 DOM 操作和状态同步。
 *
 * @param editorElement - 编辑器 DOM 元素的 ref
 * @returns 统一的编辑器API
 */
export function useMarkdownEditor(editorElement: Ref<HTMLElement | null>) {
  // ============== 初始化底层 composables ============

  // 编辑器状态
  const editorState = reactive<EditorState>({
    content: '', // 保存的是编辑器 innerHtml
    isDirty: false,
  })

  // 初始化各个 composable
  const selectionAPI = useSelection(editorElement)
  const markdownAPI = useMarkdown(selectionAPI)
  const livePreviewAPI = useLivePreview(selectionAPI)
  const historyAPI = useHistory()

  // =============== 状态同步辅助函数  ==================
  /**
   * 将 DOM 内容同步到 Vue 状态
   * 必须在任何 DOM 修改操作（如格式化）后调用
   */
  const syncState = () => {
    if (editorElement.value) {
      const newContent = editorElement.value.innerHTML
      // 只有内容真的变了才更新，避免不必要的触发
      if (newContent !== editorState.content) {
        editorState.content = newContent
        editorState.isDirty = true
      }
    }
  }

  // =============== 内容管理 API ==================
  const getContent = () => editorElement.value?.innerHTML || '' // 返回 HTML

  const setContent = (content: string) => {
    // 设置 HTML
    if (editorElement.value) {
      editorElement.value.innerHTML = content
      editorState.content = content
    }
  }

  const clear = () => {
    setContent('<div><br /></div>')
  }

  const isEmpty = () => {
    const text = editorElement.value?.textContent?.trim() || ''
    return text.length === 0
  }

  // =============== 历史管理 API ==================
  const { canUndo, canRedo, historyState, clearHistory } = historyAPI

  const recordHistory = (label: string = '用户操作') => {
    if (editorElement.value) {
      const content = editorElement.value.innerHTML
      const cursorPos = selectionAPI.getSelectionInfo().end
      historyAPI.pushTransaction(content, label, cursorPos)
    }
  }

  const undo = () => {
    const previousState = historyAPI.undo()
    // 如果有可撤销的内容，且编辑器存在
    if (previousState && editorElement.value) {
      // 恢复内容
      editorElement.value.innerHTML = previousState.content
      editorState.content = previousState.content

      // 恢复光标
      if (previousState.cursorPosition !== undefined) {
        selectionAPI.setCursor(previousState.cursorPosition)
      } else {
        // fallback: 光标移到内容末尾
        selectionAPI.setCursor(previousState.content.length)
      }
      return true // true 表示撤销成功
    }
    return false // false 表示没有可撤销的内容
  }

  const redo = () => {
    const nextState = historyAPI.redo()
    if (nextState && editorElement.value) {
      // 恢复内容
      editorElement.value.innerHTML = nextState.content
      editorState.content = nextState.content

      // 恢复光标
      if (nextState.cursorPosition !== undefined) {
        selectionAPI.setCursor(nextState.cursorPosition)
      } else {
        selectionAPI.setCursor(nextState.content.length)
      }
      return true
    }
    return false
  }

  // =============== 格式化 API ==================
  // 格式化包装方法严格遵循：Action -> DOM -> Sync -> History

  const toggleInlineFormat = (action: InlineFormatType) => {
    // 1. 调用底层方法修改 DOM
    markdownAPI.toggleInlineFormat(action)
    // 2. 立即同步状态
    syncState()
    // 3. 记录历史
    recordHistory(`应用格式: ${action}`)
  }

  const toggleParagraphFormat = (action: ParagraphFormatType) => {
    markdownAPI.toggleParagraphFormat(action)
    syncState()
    recordHistory(`应用段落: ${action}`)
  }

  const insertBlock = (action: BlockInsertType) => {
    markdownAPI.insertBlock(action)
    syncState()
    recordHistory(`插入区块: ${action}`)
  }

  // =============== 选区管理 API ==================
  const focus = () => editorElement.value?.focus()
  const blur = () => editorElement.value?.blur()
  const setCursor = (position: number) => selectionAPI.setCursor(position)
  const selectRange = (start: number, end: number) => selectionAPI.selectRange(start, end)
  const getSelectionInfo = () => selectionAPI.getSelectionInfo()

  // =============== 工具方法 API ==================
  const getTextContent = (): string => {
    if (!editorElement.value) return ''
    return getTextContentUtil(editorElement.value)
  }

  const getWordCount = (): number => {
    const text = getTextContent().replace(/\s+/g, '')
    return text.length
  }

  const isDirty = () => editorState.isDirty
  const markClean = () => (editorState.isDirty = false)

  // =============== 生命周期 API ==================
  const destroy = () => {
    // 未来需要清理的资源（如果有）
    clearHistory()
  }


  // =============== 返回统一接口 ==================
  return {
    // 编辑器
    editorState: readonly(editorState),

    // 内容管理
    syncState,
    getContent,
    setContent,
    clear,
    isEmpty,

    // 格式化
    toggleInlineFormat,
    toggleParagraphFormat,
    insertBlock,

    // 历史管理
    historyState,
    recordHistory,
    undo,
    redo,
    canUndo,
    canRedo,
    clearHistory,

    // 选区管理
    focus,
    blur,
    setCursor,
    selectRange,
    getSelectionInfo,

    // 工具方法
    getTextContent,
    getWordCount,
    isDirty,
    markClean,

    // Live Preview
    updateLineTypes: livePreviewAPI.updateLineTypes,
    updateActiveLine: livePreviewAPI.updateActiveLine,
    checkH1Unique: livePreviewAPI.checkH1Unique,
    handleEnterKey: livePreviewAPI.handleEnterKey,

    // 生命周期
    destroy,
  }
}
