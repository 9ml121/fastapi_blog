import type { UseSelectionReturn } from './useSelection'

// 行类型枚举
export type LineType = 'h1' | 'h2' | 'h3' | 'ol' | 'ul' | 'quote' | 'code-block' | 'paragraph'

// 返回值接口
export interface LineTypeInfo {
  type: LineType
  level?: number // 标题层级（1-3）
  marker?: string // 列表标记（- 或 *）
  number?: number // 有序列表序号
  indent?: string // 缩进空格字符串
  indentLevel?: number // 缩进层级
  prefix?: string // 前缀字符串（用于 Enter 延续）
}


/**
 * 检测单行文本的 Markdown 类型
 * @param text 行文本内容
 * @returns 行类型信息
 */
export function detectLineType(text: string): LineTypeInfo {
  // 1. 标题检测（H1-H3，H4+ 忽略）
  const headingMatch = text.match(/^(#{1,3})\s/)
  if (headingMatch) {
    const level = headingMatch[1]?.length as 1 | 2 | 3
    return {
      type: `h${level}` as LineType,
      level,
      prefix: headingMatch[0],
    }
  }

  // 2. 无序列表检测（支持缩进）
  const unorderedMatch = text.match(/^(\s*)([-*])\s/)
  if (unorderedMatch) {
    return {
      type: 'ul',
      indent: unorderedMatch[1] || '',
      indentLevel: unorderedMatch[1]?.length,
      marker: unorderedMatch[2],
      prefix: unorderedMatch[0],
    }
  }

  // 3. 有序列表检测
  const orderedMatch = text.match(/^(\s*)(\d+)\.\s/)
  if (orderedMatch) {
    return {
      type: 'ol',
      number: parseInt(orderedMatch[2]!, 10),
      indent: orderedMatch[1] || '',
      indentLevel: orderedMatch[1]?.length,
      prefix: orderedMatch[0],
    }
  }

  // 4. 引用块检测(支持缩进，兼容嵌套引用 >>)
  const quoteMatch = text.match(/^(\s*>\s?)/)
  if (quoteMatch) {
    return {
      type: 'quote',
      prefix: quoteMatch[0],
    }
  }

  // 5. 代码块检测
  if (/^```/.test(text)) {
    return { type: 'code-block' }
  }

  // 6. 默认：普通段落
  return { type: 'paragraph' }
}

// ======== Composable（需要依赖 useSelection）========
export function useLivePreview(selectionAPI: UseSelectionReturn) {
  /**
   * 更新编辑器中带有md标识语法行的 data-line-type 属性（ol排除）
   * @param editorElement 编辑器容器元素（contenteditable 的 div）
   */
  const updateLineTypes = (editorElement: HTMLElement | null) => {
    if (!editorElement) return
    // 获取当前行（用于跳过包裹）
    const activeLine = selectionAPI.getActiveLineElement()

    // 获取所有直接子元素（每一行），设置data-line-type属性
    const lines = editorElement.children

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i] as HTMLElement
      // 跳过非元素节点（如文本节点）
      if (line.nodeType !== Node.ELEMENT_NODE) continue

      // 使用 textContent 获取纯文本（不含 HTML 标签）
      const text = line.textContent || ''
      // 检测行类型
      const typeInfo = detectLineType(text)

      // 包裹非当前行的符号
      if (line !== activeLine && typeInfo.prefix && typeInfo.type !== 'ol' && !line.querySelector('.md-token')) {
        const prefixLength = typeInfo.prefix.length
        const content = line.textContent || ''

        line.innerHTML =
          `<span class="md-token">${content.slice(0, prefixLength)}</span>` +
          content.slice(prefixLength)
      }

      // 设置 data-line-type 属性（只在值变化时更新，避免不必要的 DOM 操作）
      if (line.getAttribute('data-line-type') !== typeInfo.type) {
        line.setAttribute('data-line-type', typeInfo.type)
      }
    }
  }

  /**
   * 更新激活行状态（添加/移除 .line-active 类）
   */
  const updateActiveLine = (editorElement: HTMLElement | null) => {
    if (!editorElement) return
    const activeLine = selectionAPI.getActiveLineElement()

    // 移除所有行的 .line-active 类
    const lines = editorElement.querySelectorAll('.line-active')
    lines.forEach(line => line.classList.remove('line-active'))

    // 添加当前行的 .line-active 类
    if (activeLine) activeLine.classList.add('line-active')
  }

  const checkH1Unique = (editorElement: HTMLElement | null): {
    count: number
    hasWarning: boolean
    message?: string
  } => {
    if (!editorElement) return { count: 0, hasWarning: false }
    const h1Lines = editorElement.querySelectorAll('[data-line-type="h1"]')
    const count = h1Lines.length

    if (count > 1) {
      return { count, hasWarning: true, message: `检测到 ${count} 个一级标题，建议只使用一个` }
    }

    return { count, hasWarning: false }
  }

  /**
   * 处理Enter键自动延续格式(只对有序列表、无序列表、引用生效)
   */
  const handleEnterKey = (event: KeyboardEvent): boolean => {
    const { lineText } = selectionAPI.getCurrentLineInfo()
    const typeInfo = detectLineType(lineText)
    const allowedTypes = ['ul', 'ol', 'quote']
    if (!typeInfo.prefix || !allowedTypes.includes(typeInfo.type)) return false

    // 空行前缀: enter 键是删除当前行的前缀
    const contextAfterPrefix = lineText.slice(typeInfo.prefix.length).trim()
    if (contextAfterPrefix === '') {
      event.preventDefault()
      for (let i = 0; i < typeInfo.prefix.length; i++) {
        document.execCommand('delete')
      }
      return true
    }

    // 非空行前缀，enter 键是自动延续格式，执行新行插入
    event.preventDefault()
    let prefix = typeInfo.prefix
    if (typeInfo.type === 'ol' && typeInfo.number !== undefined) {
      // 有序列表：序号 + 1
      prefix = typeInfo.indent! + (typeInfo.number + 1) + '. '
    }
    document.execCommand('insertText', false, '\n' + prefix)
    return true
  }


  return {
    updateLineTypes,
    updateActiveLine,
    checkH1Unique,
    handleEnterKey,
  }
}
