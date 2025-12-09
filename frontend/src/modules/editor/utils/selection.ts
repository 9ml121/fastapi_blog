/**
 * 获取 DOM 节点相对于根元素的绝对字符偏移量
 *
 * @description
 * 浏览器的 Selection API 返回的是基于 DOM 节点的相对位置 (anchorNode, anchorOffset)。
 * 为了方便处理 Markdown 文本，我们需要将其转换为相对于编辑器根元素的绝对字符索引。
 *
 * @param node - 目标 DOM 节点 (通常是 selection.anchorNode 或 focusNode)
 * @param offset - 在目标节点内的偏移量
 * @param root - 编辑器的根元素 (contenteditable div)
 * @returns 相对于根元素的绝对字符索引 (从 0 开始)
 *
 * @example
 * ```html
 * <div contenteditable>
 *   Hello <b>World</b>
 * </div>
 * ```
 * 如果选中 "World" 的开头：
 * - 输入: node=textNode("World"), offset=0
 * - 输出: 6 ("Hello " 的长度)
 */
export function getAbsoluteOffset(node: Node, offset: number, root: HTMLElement): number {
  let absoluteOffset = 0
  let found = false

  /**
   * 深度优先遍历 DOM 树，计算到目标节点的字符累计
   */
  function traverse(currentNode: Node): void {
    if (found) return

    // 1. 找到目标节点：累加偏移量并结束
    if (currentNode === node) {
      absoluteOffset += offset
      found = true
      return
    }

    // 2. 处理元素节点
    if (currentNode.nodeType === Node.ELEMENT_NODE) {
      // 2.1 BR 标签：不产生任何偏移量
      if (currentNode.nodeName === 'BR') {
        // 不做任何操作
      } else {
        // 2.2 普通元素：递归遍历子节点
        for (const child of currentNode.childNodes) {
          traverse(child)
          if (found) return
        }

        // 2.3 块级元素边界：
        // 规则1: 目前设计只有 DIV 算作行容器
        // 规则2: 如果不是最后一行，算作 1 个换行符
        if (currentNode.nodeName === 'DIV' && currentNode !== root && currentNode.nextSibling) {
          absoluteOffset += 1
        }
      }
    }
    // 3. 处理文本节点
    else if (currentNode.nodeType === Node.TEXT_NODE) {
      absoluteOffset += currentNode.textContent?.length ?? 0
    }
  }

  traverse(root)
  return absoluteOffset
}

/**
 * 根据绝对字符偏移量获取对应的 DOM 节点和相对偏移量
 *
 * @description
 * 这是 `getAbsoluteOffset` 的逆运算。用于将逻辑上的字符位置（如光标位置 5）
 * 转换为浏览器 Range API 需要的 (node, offset) 格式。
 *
 * @param absoluteOffset - 绝对字符索引 (从 0 开始)
 * @param root - 编辑器的根元素
 * @returns 包含节点和偏移量的对象，如果未找到则返回 null
 *
 * @example
 * setCursor(6) -> 找到 "World" 文本节点，offset 为 0
 */
export function getNodeAndOffset(
  absoluteOffset: number,
  root: HTMLElement,
): { node: Node; offset: number } | null {
  // ⚠️ 特殊情况：编辑器完全为空
  if (absoluteOffset === 0 && root.childNodes.length === 0) {
    // 返回根元素本身，offset 为 0
    return { node: root, offset: 0 }
  }

  let currentOffset = 0

  function traverse(node: Node): { node: Node; offset: number } | null {
    // 1. 文本节点：直接比较偏移量
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
      // 2. 元素节点：递归遍历子节点
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      if (node.nodeName === 'BR') {
        // 2.1 光标在BR位置（⚠️BR标签目前不产生任何字符和任何offset,只有DIV边界产生换行符）
        if (currentOffset === absoluteOffset) {
          const parent = node.parentNode!
          const index = Array.from(parent.childNodes).indexOf(node as ChildNode)
          return { node: parent, offset: index }
        }
      } else {
        // 2.2 遍历子节点
        for (const child of node.childNodes) {
          const result = traverse(child)
          if (result) return result
        }
        // 2.3 块级元素边界：如果不是最后一行，算作 1 个换行符
        if (node.nodeName === 'DIV' && node !== root && node.nextSibling) {
          currentOffset += 1
        }
      }
    }

    return null
  }

  return traverse(root)
}

/**
 * 从DOM树获取文本内容（替代innerText）
 *
 * 规则：
 * - BR标签不产生字符
 * - 只有DIV边界产生换行符
 * - <div><br></div> 产生单个 \n
 *
 * @param root - contenteditable根元素
 * @returns 自定义替代innerText的文本内容
 */
export function getTextContent(root: HTMLElement): string {
  let text = ''

  function traverse(node: Node): void {
    if (node.nodeType === Node.TEXT_NODE) {
      text += node.textContent || ''
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      if (node.nodeName === 'BR') {
        // BR不产生字符
      } else {
        // 递归处理子节点
        for (const child of node.childNodes) {
          traverse(child)
        }
      }

      // DIV边界产生换行
      if (node.nodeName === 'DIV' && node !== root && node.nextSibling) {
        text += '\n'
      }
    }
  }

  traverse(root)
  return text
}
