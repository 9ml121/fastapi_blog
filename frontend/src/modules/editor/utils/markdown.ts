import { marked } from 'marked'
import DOMPurify from 'dompurify'

// 配置 marked（模块级别，只执行一次）
marked.use({
  gfm: true, // GitHub Flavored Markdown
  breaks: true, // 换行转 <br>
})

// 自定义 Renderer：外部链接新窗口打开
const renderer = new marked.Renderer()

renderer.link = function ({ href, title, tokens }) {
  // 解析 tokens 获取文本内容
  const text = this.parser.parseInline(tokens)

  // 判断是否为外部链接
  const isExternal = href.startsWith('http')

  const titleAttr = title ? ` title="${title}"` : ''
  const targetAttr = isExternal ? ' target="_blank" rel="noopener noreferrer"' : ''

  return `<a href="${href}"${titleAttr}${targetAttr}>${text}</a>`
}

marked.use({ renderer })

/**
 * 将 Markdown 转换为安全的 HTML
 *
 * @param markdown Markdown 文本
 * @returns 清理后的 HTML 字符串
 *
 * @example
 * const html = markdownToHtml('# Hello\n**Bold**')
 * // => '<h1>Hello</h1>\n<p><strong>Bold</strong></p>'
 */
export function markdownToHtml(markdown: string): string {
  // 1. Markdown → HTML
  const rawHtml = marked(markdown) as string

  // 2. 清理 HTML (防止XSS攻击)
  const cleanHtml = DOMPurify.sanitize(rawHtml, {
    ALLOWED_TAGS: [
      // 标题（只支持3级）
      'h1',
      'h2',
      'h3',
      // 段落和换行
      'p',
      'br',
      'hr',
      // 文本格式
      'strong',
      'em',
      'code',
      'pre',
      'del',
      // 引用
      'blockquote',
      // 列表
      'ul',
      'ol',
      'li',
      // 链接和图片
      'a',
      'img',
      // 表格
      'table',
      'thead',
      'tbody',
      'tr',
      'th',
      'td',
    ],
    ALLOWED_ATTR: ['href', 'src', 'alt', 'title', 'class', 'target', 'rel'],
  })

  return cleanHtml
}
