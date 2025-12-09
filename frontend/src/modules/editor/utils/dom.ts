/**
 * 规范化 contenteditable 的 DOM 结构
 *
 * 确保contenteditable 根元素的所有子节点文本内容都被 <div> 包裹，避免裸露的文本节点
 *
 * @param root - contenteditable 根元素
 * @returns 是否进行了修改
 *
 * @example
 * ```html
 * <!-- 修复前 -->
 * <div contenteditable>
 *   hello  <!-- ⚠️ 裸露文本节点 -->
 * </div>
 *
 * <!-- 修复后 -->
 * <div contenteditable>
 *   <div>hello</div>  <!-- ✅ 被 div 包裹 -->
 * </div>
 * ```
 */
export function normalizeDOM(root: HTMLElement): boolean {
  const children = Array.from(root.childNodes) // ✅ 创建静态数组，不受 DOM 变化影响
  let modified = false

  for (const child of children) {
    // ✅ 只遍历直接子节点
    // 跳过已有的 DIV
    if (child.nodeName === 'DIV') {
      continue
    }

    // 文本节点或者其他需要包裹的节点
    if (child.nodeType === Node.TEXT_NODE || child.nodeName === 'BR') {
      const text = child.textContent?.trim()

      // 跳过纯空白文本节点
      if (child.nodeType === Node.TEXT_NODE && !text) {
        root.removeChild(child)
        modified = true
        continue
      }

      // 将裸露的文本节点或 BR 标签包裹到 <div> 中
      const div = document.createElement('div')
      root.insertBefore(div, child)
      div.appendChild(child) // ⚠️ appendChild 会移动节点（不是复制）
      modified = true
    }
  }

  return modified
}

/**
 * 检查 DOM 是否需要规范化
 *
 * @param root - contenteditable 根元素
 * @returns 是否需要规范化
 */
export function needsNormalization(root: HTMLElement): boolean {
  for (const child of root.childNodes) {
    // 发现裸露的文本节点（非空白）
    if (child.nodeType === Node.TEXT_NODE && child.textContent?.trim()) {
      return true
    }

    // 发现裸露的 BR 标签
    if (child.nodeName === 'BR') {
      return true
    }
  }
  return false
}
