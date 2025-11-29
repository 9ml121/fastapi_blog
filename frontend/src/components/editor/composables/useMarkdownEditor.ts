import { reactive, ref } from 'vue'
import type { EditorConfig, EditorState } from '../types/editor'
import { useSelection } from './useSelection'
import { useMarkdown } from './useMarkdown'
import { getTextContent } from '../utils/selection'

/**
 * useMarkdownEditor - 编辑器核心控制器 Composable
 *
 * @description
 * 这是编辑器的"大脑"，负责协调各个子模块（Selection, History, Parser）协同工作。
 * 它对外提供统一的 API，对内管理复杂的状态流转。
 *
 * 核心职责：
 * 1. **状态管理**：维护 Content, UI, History 等核心状态
 * 2. **DOM 管理**：持有 contenteditable 元素的引用
 * 3. **输入处理**：拦截 input 事件，调用 Parser 进行 Hybrid 渲染
 * 4. **模块协调**：集成 useSelection 等子模块
 *
 * @param config - 编辑器初始化配置
 * @returns 编辑器实例 API
 */
export function useMarkdownEditor(config: EditorConfig) {
  // ========================================================================
  // 1. editorState Initialization (状态初始化)
  // ========================================================================

  /**
   * 编辑器全局状态
   * 使用 reactive 确保深层响应性
   */
  const editorState = reactive<EditorState>({
    // Content Layer
    title: config.title ?? '',
    content: config.content ?? '',

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

  /**
   * 编辑器 DOM 引用
   * 必须绑定到 contenteditable="true" 的元素上
   */
  const editorRef = ref<HTMLDivElement | null>(null)

  // ========================================================================
  // 2. Sub-Composables Integration (子模块集成)
  // ========================================================================
  const selectionModule = useSelection(editorRef, editorState)
  const markdownModule = useMarkdown(editorState, selectionModule)

  // TODO: 集成 History 模块 (Task 2.3)
  // const historyModule = useHistory(state, config)

  // ========================================================================
  // 3. Core Methods (核心方法)
  // ========================================================================

  /**
   * 处理输入事件 (Input Event)
   *
   * @description
   * 当用户在编辑器中输入时触发。
   * 负责获取原始内容，调用 Markdown 解析器，并更新视图。
   *
   * @param e - 原生 InputEvent
   */
  const onInput = (e: InputEvent) => {
    const target = e.target as HTMLElement
    // 1. 从DOM获取原始文本内容
    // 修正：使用 getTextContent 替代 innerText
    const currentText = getTextContent(target)

    // 2. 与上次保存的内容对比，检查是否真的有变化
    if (currentText === editorState.content) {
      // 内容没变，可能只是光标移动，直接返回，提高性能
      return
    }

    // 3.更新状态，不修改 DOM
    editorState.content = currentText
    editorState.isDirty = true
    config.callbacks?.onContentChange?.(editorState.content)
  }

  /**
   * 处理获得焦点事件
   */
  const onFocus = () => {
    editorState.isFocused = true
  }

  /**
   * 处理失去焦点事件
   */
  const onBlur = () => {
    editorState.isFocused = false
    // 失去焦点时，可能需要保存一下选区状态，或者触发自动保存
  }

  /**
   * 手动设置编辑器内容
   *
   * @description
   * 用于外部控制（如加载草稿、重置内容）。
   * 会同时更新 state 和 DOM。
   *
   * @param newContent - 新的 Markdown 内容
   */
  const setContent = (newContent: string) => {
    editorState.content = newContent
    if (editorRef.value) {
      editorRef.value.innerText = newContent
    }
  }

  // ========================================================================
  // 4. Public API (对外暴露的接口)
  // ========================================================================
  return {
    // 状态和引用
    state: editorState,
    editorRef,

    // 核心事件处理
    onInput,
    onFocus,
    onBlur,

    // 基础操作
    setContent,

    // 导出子模块的能力 (Proxy)
    // ... 是 JS 的 展开运算符，类似于python的字典解包
    ...selectionModule,
    ...markdownModule,
  }
}
