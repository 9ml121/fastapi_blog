import type {
  EditorState,
  FormatState,
  SelectionInfo,
  EditTransaction,
  InlineFormatType, // 行内格式类型
  BlockInsertType,
  ParagraphFormatType, // 块级插入类型
} from '../types/editor'

import type { UseSelectionReturn } from './useSelection'
import type { UseHistoryReturn } from './useHistory'

/**
 * useMarkdown - Markdown 格式化逻辑 Composable
 *
 * @description
 * 负责处理具体的 Markdown 格式化操作，如加粗、斜体、插入标题等。
 * 它依赖 useSelection 来获取当前选区，并调用 useSelection 的方法来修改文本。
 *
 * @param state - 编辑器状态
 * @param selectionModule - useSelection 模块实例
 * @param historyModule - useHistory 模块实例
 */
export function useMarkdown(
  state: EditorState,
  selectionModule: UseSelectionReturn,
  // historyModule: UseHistoryReturn,
) {
  const { getSelectionInfo, replaceRange, insertText, setCursor, selectRange, getCurrentLineInfo } =
    selectionModule

  /**
   * 对选中文本应用行内格式 (Bold, Italic, Code, highlight, Link)
   *
   * @param action - 格式类型
   */
  const applyInlineFormat = (action: InlineFormatType): void => {
    // 根据操作类型确定 Markdown 语法（行内格式需要前后包裹）
    const formatMap: Record<InlineFormatType, { before: string; after: string }> = {
      bold: { before: '**', after: '**' },
      italic: { before: '*', after: '*' },
      code: { before: '`', after: '`' },
      highlight: { before: '==', after: '==' },
      link: { before: '[', after: '](url)' },
    }

    const { start, end, selectedText, isEmpty } = getSelectionInfo()

    // === Link 格式需要特殊处理 ===
    if (action === 'link') {
      handleLinkFormat(start, end, selectedText, isEmpty)
      return
    }

    const { before, after } = formatMap[action]

    // === 场景1：空选区 → 插入标记，光标在中间 ===
    if (isEmpty) {
      insertText(before + after)
      setCursor(start + before.length)
      return
    }

    // === 场景2：有选中 ===
    // 检查是否完全格式化
    const isFullyFormatted =
      selectedText.startsWith(before) &&
      selectedText.endsWith(after) &&
      selectedText.length > before.length + after.length

    let newText: string

    if (isFullyFormatted) {
      // Toggle off：移除格式
      newText = selectedText.slice(before.length, -after.length)
    } else if (selectedText.includes(before)) {
      // 包含部分标记：清理后重新格式化
      const cleanText = removeAllFormatMarkers(selectedText, before, after)
      newText = before + cleanText + after
    } else {
      // 无标记：直接格式化
      newText = before + selectedText + after
    }

    replaceRange(start, end, newText)

    // 重新选中格式化后的文本
    selectRange(start, start + newText.length)
    // todo: 记录到历史栈
  }

  const removeAllFormatMarkers = (text: string, before: string, after: string): string => {
    const escapedBefore = before.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const escapedAfter = after.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')
    const regex = new RegExp(`${escapedBefore}(.*?)${escapedAfter}`, 'g')
    return text.replace(regex, '$1')
  }

  const handleLinkFormat = (
    start: number,
    end: number,
    selectedText: string,
    isEmpty: boolean,
  ): void => {
    if (isEmpty) {
      // 空选区，插入链接模板，光标在 [] 中间
      insertText('[](url)')
      setCursor(start + 1)
      return
    }

    // 检查是否已经是链接格式
    const linkRegex = /^\[(.*?)\]\((.*?)\)$/
    const match = selectedText.match(linkRegex)
    if (match) {
      // 已经是链接格式，移除链接格式,保留文本
      const linkedText = match[1]
      replaceRange(start, end, linkedText!)
    } else {
      // 不是链接格式，添加链接格式
      const linkedText = `[${selectedText}](url)`
      replaceRange(start, end, linkedText)

      // 将光标移动到 URL 部分
      const urlStart = start + 1 + selectedText.length + 2
      selectRange(urlStart, urlStart + 3)
    }
  }

  /**
   * 应用段落格式 (Heading1, Heading2, Heading3, Quote)
   *
   * 段落格式只需要在行首添加前缀，不需要包裹文本
   * 例如：将 "文字" 转换为 "# 文字"
   *
   * @param action - 段落格式类型
   */
  const applyParagraphFormat = (action: ParagraphFormatType): void => {
    // 1. 定义前缀映射表
    const prefixMap: Record<ParagraphFormatType, string> = {
      heading1: '# ',
      heading2: '## ',
      heading3: '### ',
      quote: '> ',
    }
    const prefix = prefixMap[action]

    // 2. 获取当前光标行信息
    const { lineStart, lineEnd, lineText } = getCurrentLineInfo()

    // 3. 检查当前行是否已经有该前缀（Toggle 逻辑）
    const hasPrefix = lineText.startsWith(prefix)

    // 4. 根据 Toggle 逻辑生成新文本
    let newLine: string
    if (hasPrefix) {
      // 移除前缀：从 currentLine 中去掉前缀部分
      newLine = lineText.slice(prefix.length)
    } else {
      // 添加前缀：在 currentLine 前面加上前缀
      newLine = prefix + lineText
    }

    // 5. 必须在 replaceRange 之前计算新光标位置
    const { start: oldCursorPos } = getSelectionInfo()
    const newCursorPos = hasPrefix
      ? // 移除前缀后，光标需要向前移动 prefix.length 个字符
        Math.max(lineStart, oldCursorPos - prefix.length)
      : // 添加前缀后，光标需要向后移动 prefix.length 个字符
        lineStart + oldCursorPos + prefix.length

    // 6. 替换当前行
    replaceRange(lineStart, lineEnd, newLine)

    // 7. 设置新光标位置
    setCursor(newCursorPos)
  }

  /**
   * 插入块级元素 (CodeBlock, Image, Table, Video, EmbedLink, Divider)
   * - ⚠️块级元素只能在空行插入
   *
   * @param action - 块级插入类型
   */
  const insertBlock = (action: BlockInsertType): void => {
    // 1. 获取当前行信息
    let { lineStart, lineEnd, lineText } = getCurrentLineInfo()
    console.log(`[insertBlock] lineStart=${lineStart}, lineEnd=${lineEnd}, lineText="${lineText}"`)

    // 2. 检查是否为空行（去除所有空白字符、零宽字符、不间断空格）
    if (lineText.replace(/[\s\u200B\u00A0\uFEFF]/g, '') !== '') {
      // 当前行非空，自动在行尾插入换行符
      console.log('[insertBlock] 当前行非空，自动换行')
      replaceRange(lineEnd, lineEnd, '\n')
      // 将光标移动到新行的起始位置
      setCursor(lineEnd + 1)
      // 重新获取新行信息（此时应为空行）
      const newInfo = getCurrentLineInfo()
      lineStart = newInfo.lineStart
      lineEnd = newInfo.lineEnd
      lineText = newInfo.lineText
      console.log(
        `[insertBlock] 换行后 lineStart=${lineStart}, lineEnd=${lineEnd}, lineText="${lineText}"`,
      )
    }

    // 3. 定义块模版
    const blockTemplates: Record<BlockInsertType, string> = {
      codeBlock: '```python\n\n```\n',
      image: '![图片描述](图片URL)\n',
      table: '| 列1 | 列2 | 列3 |\n| --- | --- | --- |\n| 单元格 | 单元格 | 单元格 |\n',
      video: '<video src="视频URL" controls></video>\n',
      embedLink: '[嵌入链接标题](URL)\n',
      divider: '---\n',
    }
    const template = blockTemplates[action]

    // 4. ⚠️ 在 replaceRange 之前计算光标位置（避免 DOM 更新后 lineStart 失效）
    let cursorPosition: number | null = null
    let selectionStart: number | null = null
    let selectionEnd: number | null = null

    switch (action) {
      case 'divider':
        // 光标放在分隔线末尾
        cursorPosition = lineStart + template.length
        break

      case 'codeBlock':
        // 光标放在代码区域内（第一行 ``` 后面）
        cursorPosition = lineStart + '```python\n'.length
        break

      case 'image':
        // 选中 URL 部分
        selectionStart = lineStart + '![图片描述]('.length
        selectionEnd = selectionStart + '图片URL'.length
        break

      case 'video':
        // 选中 URL 部分
        selectionStart = lineStart + '<video src="'.length
        selectionEnd = selectionStart + '视频URL'.length
        break

      case 'embedLink':
        // 选中 URL 部分
        selectionStart = lineStart + '[嵌入链接标题]('.length
        selectionEnd = selectionStart + 'URL'.length
        break

      case 'table':
        // 光标放在第一个单元格
        const headerAndSeparator = '| 列1 | 列2 | 列3 |\n| --- | --- | --- |\n| '
        cursorPosition = lineStart + headerAndSeparator.length
        break
    }

    // 5. 替换空行
    replaceRange(lineStart, lineEnd, template)

    // 6. 设置光标或选区
    if (selectionStart !== null && selectionEnd !== null) {
      // 需要选中范围（如 image, video, embedLink）
      selectRange(selectionStart, selectionEnd)
    } else if (cursorPosition !== null) {
      // 需要设置光标位置（如 divider, codeBlock, table）
      setCursor(cursorPosition)
    }
  }

  return {
    applyInlineFormat,
    applyParagraphFormat,
    insertBlock,
  }
}

// 导出类型供其他模块使用
export type UseMarkdownReturn = ReturnType<typeof useMarkdown>
