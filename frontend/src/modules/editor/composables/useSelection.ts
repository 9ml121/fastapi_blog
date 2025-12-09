import type { SelectionInfo } from './editor.types'
import type { Ref } from 'vue'
import { getAbsoluteOffset, getNodeAndOffset, getTextContent } from '../utils/selection'

/**
 * useSelection - 底层 DOM 操作（光标、选区、行元素获取等）
 *
 * @description
 * 负责管理编辑器中的光标位置和文本选中状态。
 * 它充当 Vue 组件和底层 DOM Selection API 之间的桥梁。
 *
 * 核心职责：
 * - 提供获取、设置、修改选中文本的能力
 * - 处理 contenteditable 的光标位置计算
 *
 * 特性：
 * - ✅ SSR 友好：在服务器环境返回安全的默认值
 * todo Tree-shakable：使用具名导出
 *
 * @param editorElement - contenteditable div 的模板引用
 */
export function useSelection(editorElement: Ref<HTMLElement | null>) {
  // ==================== SSR 环境检测 ====================
  /**
   * 检测是否在浏览器环境
   * 在服务器端渲染（SSR）时，window 和 document 对象不存在
   */
  const isBrowser =
    typeof window !== 'undefined' && typeof document !== 'undefined' && window.getSelection

  /**
   * 默认选区信息（SSR 环境使用）
   */
  const DEFAULT_SELECTION: SelectionInfo = {
    start: 0,
    end: 0,
    selectedText: '',
    isEmpty: true,
  }

  /**
   * 获取当前选中的文本范围信息
   * @returns 包含 start, end, selectedText，isEmpty 的对象
   */
  const getSelectionInfo = (): SelectionInfo => {
    // 🔒 SSR 保护：服务器环境返回默认值
    if (!isBrowser) return DEFAULT_SELECTION

    // 1. 获取编辑器元素
    const ele = editorElement.value
    if (!ele) return DEFAULT_SELECTION

    // 2. 获取浏览器的 Selection 对象
    const sel = window.getSelection()
    if (!sel || sel.rangeCount === 0) return DEFAULT_SELECTION

    // 获取选中范围的起点和终点节点（anchorNode, focusNode）
    const anchorNode = sel.anchorNode
    const focusNode = sel.focusNode
    const anchorOffset = sel.anchorOffset
    const focusOffset = sel.focusOffset

    // 3. 使用 getAbsoluteOffset() 转换为绝对字符位置
    let start = getAbsoluteOffset(anchorNode as Node, anchorOffset, ele)
    let end = getAbsoluteOffset(focusNode as Node, focusOffset, ele)

    // 处理反向选中：确保 start < end
    if (start > end) {
      ;[start, end] = [end, start]
    }

    // 4. 修正：DOM元素的 innerText 会将包裹在DIV的BR转换为2个换行符，这里换成我们自定义的getTextContent
    const text = getTextContent(ele)
    const selectedText = text.substring(start, end) ?? ''
    return { start, end, selectedText, isEmpty: start === end }
  }

  /**
   * 将光标移动到指定的绝对字符索引位置
   * @param position - 光标位置（从 0 开始的字符索引）
   */
  const setCursor = (position: number): void => {
    // 🔒 SSR 保护：服务器环境直接返回
    if (!isBrowser) return

    // 1. 获取编辑器元素
    const ele = editorElement.value
    if (!ele) return

    // 2. 使用 getNodeAndOffset() 获取节点和偏移量
    const nodeAndOffset = getNodeAndOffset(position, ele)

    if (!nodeAndOffset) {
      console.warn(`无法找到位置 ${position}，设置光标到末尾`)

      // ⚡️ Fallback: 设置光标到末尾
      const range = document.createRange()
      ele.focus()
      range.selectNodeContents(ele)
      range.collapse(false) // 折叠到末尾

      const sel = window.getSelection()
      if (sel) {
        sel.removeAllRanges()
        sel.addRange(range)
      }
      return
    }

    // 3. 创建 Range 对象，设置光标起点
    const range = document.createRange()
    try {
      // 确保编辑器获得焦点，否则 selection 可能无效
      ele.focus()

      range.setStart(nodeAndOffset.node, nodeAndOffset.offset)
      range.collapse(true) // collapse 到起点，使光标不是选中范围

      const sel = window.getSelection()
      if (sel) {
        sel.removeAllRanges()
        sel.addRange(range)
      }
    } catch (error) {
      console.error('设置光标失败:', error)
    }
  }

  /**
   * 根据起始和结束的绝对字符索引，选中一段文本。
   * @param start - 开始位置 (绝对字符索引)
   * @param end - 结束位置 (绝对字符索引)
   */
  const selectRange = (start: number, end: number): void => {
    // 🔒 SSR 保护：服务器环境直接返回
    if (!isBrowser) return

    const ele = editorElement.value
    if (!ele) return

    const startNode = getNodeAndOffset(start, ele)
    const endNode = getNodeAndOffset(end, ele)

    if (!startNode || !endNode) {
      console.warn('无法选中范围')
      return
    }

    try {
      const range = document.createRange()
      range.setStart(startNode.node, startNode.offset)
      range.setEnd(endNode.node, endNode.offset)

      const sel = window.getSelection()
      if (sel) {
        sel.removeAllRanges()
        sel.addRange(range)
      }
    } catch (error) {
      console.error('选中范围失败:', error)
    }
  }

  /**
   * 替换指定范围的文本
   *
   * @param start - 开始位置（绝对字符索引）
   * @param end - 结束位置（绝对字符索引）
   * @param newText - 要插入的新文本
   * @param options - 控制行为的可选配置对象
   * @param options.moveCursorToEnd - 是否将光标移动到新文本末尾，默认 false
   * @param options.updateBrowserSelection - 是否更新浏览器的选区状态，默认 true
   *
   * @returns 是否成功
   */
  const replaceRange = (
    start: number,
    end: number,
    newText: string,
    options?: {
      moveCursorToEnd?: boolean
      updateBrowserSelection?: boolean
    },
  ): boolean => {
    // 🔒 SSR 保护：服务器环境直接返回 false
    if (!isBrowser) return false

    // 1. 解构options，设置默认值
    const { moveCursorToEnd = false, updateBrowserSelection = true } = options || {}

    // 2. 检查 editorElement 是否存在
    const ele = editorElement.value
    if (!ele) return false

    // 3. 获取起止位置的 DOM 节点和偏移量
    const startNode = getNodeAndOffset(start, ele)
    const endNode = getNodeAndOffset(end, ele)
    if (!startNode || !endNode) {
      console.warn('无法替换范围，位置无效')
      return false
    }

    // 4. 创建 Range 对象并设置范围
    const range = document.createRange()
    try {
      range.setStart(startNode.node, startNode.offset)
      range.setEnd(endNode.node, endNode.offset)
      // 5. 删除旧内容并插入新内容
      range.deleteContents()
      const textNode = document.createTextNode(newText)
      range.insertNode(textNode)

      // 6. 根据options.moveCursorToEnd决定是否移动光标
      if (moveCursorToEnd) {
        // ⚠️ 这里不能用 range.setStartAfter(textNode)，会导致光标偏移错误
        range.setStart(textNode, textNode.length)
        range.collapse(true)
      }

      // 7. 根据options.updateBrowserSelection决定是否更新浏览器选区
      if (updateBrowserSelection) {
        const sel = window.getSelection()
        if (sel) {
          sel.removeAllRanges()
          sel.addRange(range)
        }
      }

      return true
    } catch (error) {
      console.error('替换范围失败:', error)
      return false
    }
  }

  /**
   * 包裹选中文本（用于加粗、斜体等格式化操作）
   *
   * @param before - 前缀字符串（如 "**"）
   * @param after - 后缀字符串（如 "**"）
   */
  const wrapSelection = (before: string, after: string): void => {
    // 获取选中的文本
    const selection = getSelectionInfo()
    if (selection.isEmpty) {
      console.warn('没有选中文本，无法包裹')
      return
    }

    // 构建包裹后的文本
    const selectedText = selection.selectedText
    const wrappedText = before + selectedText + after

    // 替换选中的文本
    replaceRange(selection.start, selection.end, wrappedText, {
      moveCursorToEnd: false,
    })

    // 重新选中包裹后的文本
    selectRange(selection.start, selection.start + wrappedText.length)
  }

  /**
   * 在当前光标位置插入文本
   *
   * @description
   * - 如果有选中文本，会替换选中的内容
   * - 如果只有光标（无选中），会在光标位置插入
   * - 插入后光标会移动到插入文本的末尾
   *
   * @param text - 要插入的文本
   */
  const insertText = (text: string): void => {
    const { start, end } = getSelectionInfo()

    // 不管选区是否为空，都替换选区内容（相当于插入）
    replaceRange(start, end, text, {
      moveCursorToEnd: true,
    })
  }

  /**
   * 判断当前是否有文本被选中
   *
   * @returns {boolean} true 表示有文本被选中，false 表示仅有光标或无选中
   */
  const hasSelection = (): boolean => {
    const selection = getSelectionInfo()
    return !selection.isEmpty
  }

  /**
   * 获取光标所在行的内容
   *
   * @returns 当前行在文本中的起始位置、结束位置和文本内容
   */
  const getCurrentLineInfo = (): { lineStart: number; lineEnd: number; lineText: string } => {
    const ele = editorElement.value
    if (!ele) return { lineStart: 0, lineEnd: 0, lineText: '' }

    // 修正：使用 getTextContent 替代 innerText
    const text = getTextContent(ele)

    // 查找光标所在行的起始位置和结束位置
    const selection = getSelectionInfo()

    let lineStart = selection.start
    while (lineStart > 0 && text[lineStart - 1] !== '\n') {
      lineStart--
    }

    let lineEnd = selection.start
    while (lineEnd < text.length && text[lineEnd] !== '\n') {
      lineEnd++
    }

    return {
      lineStart,
      lineEnd,
      lineText: text.substring(lineStart, lineEnd),
    }
  }

  /**
   * 获取当前光标所在的行级 DOM 元素
   *
   * @returns 当前行的 HTMLElement，如果光标不在编辑器内则返回 null
   */
  const getActiveLineElement = (): HTMLElement | null => {
    const ele = editorElement.value
    if (!ele) return null

    const sel = window.getSelection()
    if (!sel || sel.rangeCount === 0) return null

    const range = sel.getRangeAt(0)
    let node = range.startContainer

    // 向上遍历找到行级 div (直接子元素)
    while (node && node.parentElement !== ele) {
      node = node.parentElement as Node
    }

    // 确认找到的是编辑器的直接子元素
    if(node && node.parentElement === ele) {
      return node as HTMLElement
    }
    return null
  }

  // 返回公开 API
  return {
    getSelectionInfo,
    setCursor,
    selectRange,
    wrapSelection,
    replaceRange,
    insertText,
    hasSelection,
    getCurrentLineInfo,
    getActiveLineElement,
  }
}

/**
 * 导出类型（供其他模块使用）
 */
export type UseSelectionReturn = ReturnType<typeof useSelection>
