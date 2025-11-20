/**
 * useSelection - 文本选中和光标管理 Composable
 *
 * 职责：
 * - 管理编辑器中的光标位置和文本选中状态
 * - 提供获取、设置、修改选中文本的能力
 * - 与浏览器 Selection API 交互
 *
 * 关键设计：
 * - 所有操作都基于字符位置索引（相对于 contentEditable div）
 * - 不依赖 DOM 节点结构，便于测试
 * - 返回的 SelectionInfo 供其他 Composable 使用
 */

import type { EditorState, SelectionInfo } from '../types/editor'

/**
 * 辅助函数：获取 contenteditable 中的绝对字符位置
 *
 * 背景：浏览器的 Selection API 返回的是 DOM 节点位置，
 * 我们需要将其转换为相对于整个文本内容的绝对位置（字符索引）
 *
 * 示例：
 * ```
 * <div contenteditable>
 *   Hello <b>World</b>
 * </div>
 *
 * 如果选中 "World"，Selection API 会给出：
 *   - anchorNode: <b> 元素的文本节点
 *   - anchorOffset: 0
 * 我们需要转换为：
 *   - start: 6 (相对于整个文本 "Hello World")
 *   - end: 11
 * ```
 */
function getAbsoluteOffset(node: Node, offset: number, root: HTMLElement): number {
  let absoluteOffset = 0
  let found = false

  /**
   * 深度优先遍历 DOM 树，计算到目标节点的字符累计
   */
  function traverse(currentNode: Node) {
    if (found) return

    // 如果到达了目标节点，记录偏移量
    if (currentNode === node) {
      absoluteOffset += offset
      found = true
      return
    }

    // 遍历子节点
    if (currentNode.nodeType === Node.ELEMENT_NODE) {
      for (const child of currentNode.childNodes) {
        traverse(child)
        if (found) return
      }
    } else if (currentNode.nodeType === Node.TEXT_NODE) {
      // 对于文本节点，累计字符数
      absoluteOffset += currentNode.textContent?.length ?? 0
    }
  }

  traverse(root)
  return absoluteOffset
}

/**
 * 辅助函数：将绝对字符位置转换为 (node, offset) 组合
 *
 * 这是 getAbsoluteOffset 的逆向操作
 */
function getNodeAndOffset(
  absoluteOffset: number,
  root: HTMLElement,
): { node: Node; offset: number } | null {
  let currentOffset = 0

  function traverse(node: Node): { node: Node; offset: number } | null {
    if (node.nodeType === Node.TEXT_NODE) {
      const textLength = node.textContent?.length ?? 0
      if (currentOffset + textLength >= absoluteOffset) {
        // 找到了目标节点
        return {
          node: node,
          offset: absoluteOffset - currentOffset,
        }
      }
      currentOffset += textLength
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      for (const child of node.childNodes) {
        const result = traverse(child)
        if (result) return result
      }
    }

    return null
  }

  return traverse(root)
}

/**
 * useSelection Composable
 *
 * @param editorElement - contenteditable div 的模板引用
 * @param state - 编辑器状态（用于更新 selection 信息）
 */
export function useSelection(editorElement: HTMLDivElement | null, state: EditorState) {
  /**
   * 获取当前选中的文本范围信息
   *
   * 返回值示例：
   * {
   *   start: 5,
   *   end: 15,
   *   selectedText: "World is fun",
   *   isEmpty: false
   * }
   *
   * 关键点：
   * - Selection 的 anchor 和 focus 可能反向（从右往左选中）
   *   需要确保 start < end
   * - 需要检查选中范围是否在 contentEditable 容器内
   */
  const getSelection = (): SelectionInfo => {
    // 1. 获取浏览器的 Selection 对象（window.getSelection()）
    const browserSelection = window.getSelection()
    // 2. 如果没有选中，返回默认值（start=end，isEmpty=true）
    if (!browserSelection || browserSelection.rangeCount === 0) {
      return { start: 0, end: 0, selectedText: '', isEmpty: true }
    }
    // 3. 获取选中范围的起点和终点节点（anchorNode, focusNode）
    const anchorNode = browserSelection.anchorNode
    const focusNode = browserSelection.focusNode
    const anchorOffset = browserSelection.anchorOffset
    const focusOffset = browserSelection.focusOffset
    // 4. 使用 getAbsoluteOffset() 转换为绝对字符位置
    let start = getAbsoluteOffset(anchorNode as Node, anchorOffset, editorElement as HTMLElement)
    let end = getAbsoluteOffset(focusNode as Node, focusOffset, editorElement as HTMLElement)
    // ✅ 处理反向选中：确保 start < end
    if (start > end) {
      ;[start, end] = [end, start]
    }
    // 5. 从 editorElement.textContent 提取选中的文本
    const selectedText = editorElement?.textContent?.substring(start, end) ?? ''
    return { start, end, selectedText, isEmpty: start === end }
  }

  /**
   * 设置光标位置到指定位置
   *
   * @param position - 光标位置（从 0 开始的字符索引）
   *
   * 示例：
   * setCursor(5)  // 光标移到第 5 个字符之后
   */
  const setCursor = (position: number): void => {
    const range = document.createRange()
    const nodeAndOffset = getNodeAndOffset(position, editorElement as HTMLElement)

    if (!nodeAndOffset) {
      console.warn('无法设置光标位置')
      return
    }

    try {
      range.setStart(nodeAndOffset.node, nodeAndOffset.offset)
      range.collapse(true) // collapse 到起点，使光标不是选中范围

      const sel = window.getSelection()
      if (sel) {
        sel.removeAllRanges()
        sel.addRange(range)
      }

      // 更新状态
      updateSelection()
    } catch (error) {
      console.error('设置光标失败:', error)
    }
  }

  /**
   * 选中指定范围的文本
   *
   * @param start - 开始位置
   * @param end - 结束位置
   *
   * 示例：
   * selectRange(5, 10)  // 选中第 5 到 10 个字符
   */
  const selectRange = (start: number, end: number): void => {
    const startNode = getNodeAndOffset(start, editorElement as HTMLElement)
    const endNode = getNodeAndOffset(end, editorElement as HTMLElement)

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

      // 更新状态
      updateSelection()
    } catch (error) {
      console.error('选中范围失败:', error)
    }
  }

  /**
   * 包裹选中文本（用于加粗、斜体等格式化操作）
   *
   * @param before - 前缀（如 "**" 用于加粗）
   * @param after - 后缀（如 "**" 用于加粗）
   *
   * 示例：
   * wrapSelection("**", "**")  // 将选中文本变成粗体
   * wrapSelection("*", "*")    // 将选中文本变成斜体
   * wrapSelection("`", "`")    // 将选中文本变成行内代码
   */
  const wrapSelection = (before: string, after: string): void => {
    const sel = getSelection()
    if (sel.isEmpty) {
      console.warn('没有选中文本，无法包裹')
      return
    }

    // 获取选中的文本
    const selectedText = sel.selectedText
    const wrappedText = before + selectedText + after

    // 替换选中的文本
    const range = document.createRange()
    const startNode = getNodeAndOffset(sel.start, editorElement as HTMLElement)
    const endNode = getNodeAndOffset(sel.end, editorElement as HTMLElement)

    if (!startNode || !endNode) return

    try {
      range.setStart(startNode.node, startNode.offset)
      range.setEnd(endNode.node, endNode.offset)

      // 删除选中内容并插入新内容
      const fragment = document.createTextNode(wrappedText)
      range.deleteContents()
      range.insertNode(fragment)

      // 更新状态
      updateSelection()
    } catch (error) {
      console.error('包裹文本失败:', error)
    }
  }

  /**
   * 判断当前是否有文本被选中
   *
   * @returns true 如果有文本被选中，false 否则
   */
  const hasSelection = (): boolean => {
    const sel = getSelection()
    return !sel.isEmpty
  }

  /**
   * 获取光标所在行的内容
   *
   * 示例：
   * 如果编辑器内容是：
   * ```
   * Hello World
   * This is a test
   * ```
   * 当光标在第二行时，返回 "This is a test"
   */
  const getCurrentLine = (): string => {
    const sel = getSelection()
    const text = editorElement?.textContent ?? ''

    // 从光标位置向前找到行首
    let lineStart = sel.start
    while (lineStart > 0 && text[lineStart - 1] !== '\n') {
      lineStart--
    }

    // 从光标位置向后找到行尾
    let lineEnd = sel.start
    while (lineEnd < text.length && text[lineEnd] !== '\n') {
      lineEnd++
    }

    return text.substring(lineStart, lineEnd)
  }

  /**
   * 内部辅助函数：更新 state 中的 selection 信息
   *
   * 目的：保持 state.selection 与浏览器的实际选中状态同步
   */
  const updateSelection = (): void => {
    const sel = getSelection()
    state.selection = sel
  }

  /**
   * 监听选中变化事件
   *
   * 当用户用鼠标或键盘改变选中时，自动更新 state
   */
  const setupSelectionListener = (): void => {
    // 监听 mouseup 和 keyup 事件
    editorElement?.addEventListener('mouseup', updateSelection)
    editorElement?.addEventListener('keyup', updateSelection)

    // 监听 selectionchange 事件（全局）
    document.addEventListener('selectionchange', updateSelection)
  }

  /**
   * 清理事件监听器
   */
  const cleanupSelectionListener = (): void => {
    if (editorElement) {
      editorElement.removeEventListener('mouseup', updateSelection)
      editorElement.removeEventListener('keyup', updateSelection)
    }
    document.removeEventListener('selectionchange', updateSelection)
  }

  // 返回公开 API
  return {
    getSelection,
    setCursor,
    selectRange,
    wrapSelection,
    hasSelection,
    getCurrentLine,
    setupSelectionListener,
    cleanupSelectionListener,
  }
}

/**
 * 导出类型（供其他模块使用）
 */
export type UseSelectionReturn = ReturnType<typeof useSelection>
