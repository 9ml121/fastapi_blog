/**
 * useSelection 单元测试
 *
 * 测试目标：
 * 1. 验证 getAbsoluteOffset() 的位置计算逻辑
 * 2. 验证 getSelectionInfo() 的正向和反向选中处理
 * 3. 验证 setCursor() 和 selectRange() 的 DOM 操作
 *
 * 测试策略：
 * - 使用 JSDOM 模拟浏览器环境
 * - 手动创建 DOM 结构来测试
 * - Mock window.getSelection() 来模拟用户选中
 */

import { describe, it, expect, beforeEach, afterEach } from 'vitest'
import { ref } from 'vue'
import { useSelection } from '../composables/useSelection'
import type { EditorState } from '../types/editor'

// ============================================================================
// 测试辅助函数
// ============================================================================

/**
 * 创建一个模拟的 EditorState
 */
function createMockEditorState(): EditorState {
  return {
    title: '',
    content: '',
    transactions: [],
    currentIndex: -1,
    selection: {
      start: 0,
      end: 0,
      selectedText: '',
      isEmpty: true,
    },
    isSaving: false,
    isDirty: false,
    isFocused: false,
    hasError: false,
    canUndo: false,
    canRedo: false,
  }
}

/**
 * 创建一个简单的编辑器 DOM 元素
 *
 * @param html - 编辑器的 HTML 内容
 * @returns HTMLDivElement
 */
function createEditorElement(html: string): HTMLDivElement {
  const editor = document.createElement('div')
  editor.setAttribute('contenteditable', 'true')
  editor.innerHTML = html
  document.body.appendChild(editor)
  return editor
}

/**
 * 模拟用户选中文本
 *
 * @param anchorNode - 起点节点
 * @param anchorOffset - 起点偏移
 * @param focusNode - 终点节点
 * @param focusOffset - 终点偏移
 */
function mockSelection(
  anchorNode: Node,
  anchorOffset: number,
  focusNode: Node,
  focusOffset: number,
): void {
  const selection = window.getSelection()
  if (selection) {
    // setBaseAndExtent 是现代且正确的方式来编程式地创建选区，
    // 它能保留方向（anchor vs focus）。
    // 这对于测试正向和反向选择至关重要。
    // Vitest 使用的 JSDOM 支持此 API。
    selection.setBaseAndExtent(anchorNode, anchorOffset, focusNode, focusOffset)
  }
}

// ============================================================================
// 测试套件
// ============================================================================

describe('useSelection', () => {
  let editorElement: HTMLDivElement
  let state: EditorState

  // 每个测试前：创建新的编辑器元素和状态
  beforeEach(() => {
    state = createMockEditorState()
  })

  // 每个测试后：清理 DOM
  afterEach(() => {
    if (editorElement && editorElement.parentNode) {
      editorElement.parentNode.removeChild(editorElement)
    }
    // 清空 selection
    const selection = window.getSelection()
    if (selection) {
      selection.removeAllRanges()
    }
  })

  // --------------------------------------------------------------------------
  // 测试组 1: getSelection() - 基本功能
  // --------------------------------------------------------------------------
  describe('getSelection() - 基本功能', () => {
    it('当没有选中时，应该返回空的 SelectionInfo', () => {
      // 准备：创建一个简单的编辑器
      editorElement = createEditorElement('Hello World')
      const { getSelectionInfo } = useSelection(ref(editorElement), state)

      // 执行：获取选中信息（此时没有选中任何文本）
      const result = getSelectionInfo()

      // 验证：应该返回空选中
      expect(result.start).toBe(0)
      expect(result.end).toBe(0)
      expect(result.selectedText).toBe('')
      expect(result.isEmpty).toBe(true)
    })

    it('当选中简单文本时，应该正确返回位置和文本', () => {
      // 准备：创建编辑器，内容是 "Hello World"
      editorElement = createEditorElement('Hello World')
      const { getSelectionInfo } = useSelection(ref(editorElement), state)

      // 模拟选中 "World"（位置 6-11）
      const textNode = editorElement.firstChild as Text
      mockSelection(textNode, 6, textNode, 11)

      // 执行
      const result = getSelectionInfo()

      // 验证
      expect(result.start).toBe(6)
      expect(result.end).toBe(11)
      expect(result.selectedText).toBe('World')
      expect(result.isEmpty).toBe(false)
    })
  })

  // --------------------------------------------------------------------------
  // 测试组 2: getSelectionInfo() - 跨节点选中
  // --------------------------------------------------------------------------
  describe('getSelectionInfo() - 跨节点选中', () => {
    it('当选中跨越多个节点时，应该正确计算全局位置', () => {
      // 准备：创建带有嵌套元素的编辑器
      // DOM 结构：
      //   <div>
      //     TextNode("Hello ")
      //     <b>
      //       TextNode("World")
      //     </b>
      //   </div>
      editorElement = createEditorElement('Hello <b>World</b>')
      const { getSelectionInfo } = useSelection(ref(editorElement), state)

      // 模拟选中 "World"
      // 注意：World 在 <b> 元素内部
      const bElement = editorElement.querySelector('b') as HTMLElement
      const worldNode = bElement.firstChild as Text
      mockSelection(worldNode, 0, worldNode, 5)

      // 执行
      const result = getSelectionInfo()

      // 验证："Hello " 有 6 个字符，所以 "World" 的全局位置是 6-11
      expect(result.start).toBe(6)
      expect(result.end).toBe(11)
      expect(result.selectedText).toBe('World')
      expect(result.isEmpty).toBe(false)
    })

    it('当选中从一个节点跨越到另一个节点时，应该正确处理', () => {
      // 准备：创建 "Hello <b>World</b>"
      editorElement = createEditorElement('Hello <b>World</b>')
      const { getSelectionInfo } = useSelection(ref(editorElement), state)

      // 模拟选中 "o Wor"（从 "Hello" 的 'o' 到 "World" 的 'r'）
      const helloNode = editorElement.firstChild as Text
      const bElement = editorElement.querySelector('b') as HTMLElement
      const worldNode = bElement.firstChild as Text

      // 从 helloNode 位置 4 到 worldNode 位置 3
      mockSelection(helloNode, 4, worldNode, 3)

      // 执行
      const result = getSelectionInfo()

      // 验证：start=4（"Hell|o "），end=9（"Wor|ld"），selectedText="o Wor"
      expect(result.start).toBe(4)
      expect(result.end).toBe(9)
      expect(result.selectedText).toBe('o Wor')
      expect(result.isEmpty).toBe(false)
    })
  })

  // --------------------------------------------------------------------------
  // 测试组 3: getSelectionInfo() - 反向选中
  // --------------------------------------------------------------------------
  describe('getSelectionInfo() - 反向选中', () => {
    it('当用户从右往左反向选中时，应该确保 start < end', () => {
      // 准备
      editorElement = createEditorElement('Hello World')
      const { getSelectionInfo } = useSelection(ref(editorElement), state)

      // 模拟反向选中：从位置 11 选到位置 6（从右往左）
      const textNode = editorElement.firstChild as Text
      // 注意：anchor 是用户开始选中的位置，focus 是结束位置
      // 反向选中时，anchor > focus
      mockSelection(textNode, 11, textNode, 6)

      // 执行
      const result = getSelectionInfo()

      // 验证：即使反向选中（11→6），返回的 start 也应该 < end
      expect(result.start).toBe(6)
      expect(result.end).toBe(11)
      expect(result.selectedText).toBe('World')
      expect(result.isEmpty).toBe(false)
    })
  })

  // --------------------------------------------------------------------------
  // 测试组 4: hasSelection()
  // --------------------------------------------------------------------------
  describe('hasSelection()', () => {
    it('当有文本被选中时，应该返回 true', () => {
      editorElement = createEditorElement('Hello World')
      const { hasSelection } = useSelection(ref(editorElement), state)

      // 模拟选中 "World"
      const textNode = editorElement.firstChild as Text
      mockSelection(textNode, 6, textNode, 11)

      // 验证：有文本选中时应返回 true
      expect(hasSelection()).toBe(true)
    })

    it('当没有文本被选中时（只有光标），应该返回 false', () => {
      editorElement = createEditorElement('Hello World')
      const { hasSelection } = useSelection(ref(editorElement), state)

      // 模拟光标（start === end）
      const textNode = editorElement.firstChild as Text
      mockSelection(textNode, 5, textNode, 5)

      // 验证：只有光标时应返回 false
      expect(hasSelection()).toBe(false)
    })
  })

  // --------------------------------------------------------------------------
  // 测试组 5: getCurrentLineInfo()
  // --------------------------------------------------------------------------
  describe('getCurrentLineInfo()', () => {
    it('应该返回光标所在行的内容', () => {
      // 准备：创建多行文本
      editorElement = createEditorElement('Hello World\nThis is line 2\nLine 3')
      const { getCurrentLineInfo, getSelectionInfo } = useSelection(ref(editorElement), state)

      // 模拟光标在第二行
      const textNode = editorElement.firstChild as Text
      // "Hello World\n" 有 12 个字符，所以第二行从位置 12 开始
      mockSelection(textNode, 15, textNode, 15) // 在 "This" 后面

      // 执行
      const line = getCurrentLineInfo()

      // 验证：应该返回光标所在行的内容
      expect(line).toBe('This is line 2')
      expect(getSelectionInfo().selectedText).toBe('')
    })
  })

  // --------------------------------------------------------------------------
  // 额外练习：测试中文字符和跨节点选中
  // --------------------------------------------------------------------------
  describe('自定义测试 - 中文字符处理', () => {
    it('应该正确处理中文字符的选中和跨节点边界', () => {
      editorElement = createEditorElement(' 你好！<b>中国</b>')
      const { getSelectionInfo } = useSelection(ref(editorElement), state)
      const textNode = editorElement.firstChild as Text

      // 测试场景1: 反向选中中文文本
      mockSelection(textNode, 4, textNode, 1)
      const result = getSelectionInfo()
      expect(result.selectedText).toBe('你好！')

      // 测试场景2: 选中嵌套节点内的中文字符
      const bElement = editorElement.querySelector('b') as HTMLElement
      const chineseNode = bElement.firstChild as Text
      mockSelection(chineseNode, 0, chineseNode, 2)
      const result2 = getSelectionInfo()
      expect(result2.selectedText).toBe('中国')
    })
  })
})
