import { ref, type Ref } from 'vue'

// 目录项接口
export interface TocItem {
  id: string
  text: string // 标题文本
  level: number // 层级（H2或H3）
  element: HTMLElement // 对应的 DOM 元素
}

/** 目录导航 Composable */
export function useTableOfContents(editorElement: Ref<HTMLElement | null>) {
  const tocItems = ref<TocItem[]>([])
  const activeId = ref<string | null>(null)
  // 保存 observer 实例的引用
  let observer: IntersectionObserver | null = null

  /**
   * 收集编辑器中的 H2/H3 标题
   */
  const collectHeadings = () => {
    const ele = editorElement.value
    if (!ele) return

    const headings = ele.querySelectorAll('[data-line-type="h2"], [data-line-type="h3"]')

    tocItems.value = Array.from(headings).map((el, index) => {
      const element = el as HTMLElement
      const level = element.getAttribute('data-line-type') === 'h2' ? 2 : 3
      const text = element.textContent?.replace(/^#{2,3}\s*/, '') || ''
      const id = `toc-${index}`
      return { id, text, level, element }
    })

    // 收集完标题后设置滚动监听
    setupScrollObserver()
  }

  /**
   * 滚动到指定标题
   */
  const scrollToHeading = (id: string) => {
    const item = tocItems.value.find((i) => i.id === id)
    if (item) {
      item.element.scrollIntoView({ behavior: 'smooth', block: 'start' })
      activeId.value = id
    }
  }

  /**
   * 设置滚动监听，自动高亮当前可见的标题
   */
  const setupScrollObserver = () => {
    if (observer) observer.disconnect()
    if (tocItems.value.length === 0) return

    const ele = editorElement.value
    if (!ele) return

    observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          // 只处理进入观察区域的元素
          if (entry.isIntersecting) {
            // 找到对应的 TOC 项
            const item = tocItems.value.find((i) => i.element === entry.target)
            if (item) {
              activeId.value = item.id
            }
          }
        })
      },
      {
        // 观察区域配置：只关注视口顶部 10%~20% 的区域
        rootMargin: '-10% 0px -80% 0px',
        threshold: 0,
      },
    )

    // 让 observer 观察每个标题元素
    tocItems.value.forEach((item) => {
      observer!.observe(item.element)
    })
  }

  /**
   * 清除观察器， 防止内存泄露
   */
  const cleanupObserver = () => {
    if (observer) {
      observer.disconnect()
      observer = null
    }
  }

  return {
    tocItems,
    activeId,
    collectHeadings,
    scrollToHeading,
    cleanupObserver,
  }
}
