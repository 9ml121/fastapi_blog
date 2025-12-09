# useMarkdown 实现概设

> **文档目的**：详细设计 useMarkdown Composable 的实现方案  
> **更新日期**：2025-11-23  
> **版本**：v1.0  
> **难度评级**：⭐⭐⭐⭐（核心业务逻辑，需要深入理解 Markdown 语法）

---

## 📋 目录

1. [功能概述](#功能概述)
2. [架构设计](#架构设计)
3. [核心方法实现](#核心方法实现)
4. [技术难点与解决方案](#技术难点与解决方案)
5. [测试策略](#测试策略)
6. [实现路线](#实现路线)

---

## 🎯 功能概述

### 职责定位

**useMarkdown** 是编辑器的核心格式化引擎,负责将用户的格式化意图转换为 Markdown 语法操作。

```
用户意图 → useMarkdown → Markdown 语法 → 更新编辑器内容
   ↓            ↓              ↓              ↓
 点击加粗    识别选中文本    包裹 **text**   触发重新渲染
```

### 核心功能矩阵

| 功能类别     | 操作类型             | 输入          | 输出      | 复杂度  |
| -------- | ---------------- | ----------- | ------- | ---- |
| **行内格式** | applyFormat      | 选中文本 + 格式类型 | 包裹后的文本  | ⭐⭐   |
| **块级元素** | insertBlock      | 光标位置 + 块类型  | 插入的块结构  | ⭐⭐⭐  |
| **文本包裹** | wrapWithMarkdown | 文本 + 前后缀    | 包裹后的文本  | ⭐    |
| **格式转换** | markdownToHtml   | Markdown 文本 | HTML 文本 | ⭐⭐⭐⭐ |
| **状态检测** | getCurrentFormat | 光标位置        | 当前格式状态  | ⭐⭐⭐  |
### Markdown 操作矩阵

| 操作        | Markdown 语法      | 作用范围 | 备注         |
| --------- | ---------------- | ---- | ---------- |
| bold      | `**text**`       | 选中文本 |            |
| italic    | `*text*`         | 选中文本 |            |
| code      | `` `text` ``     | 选中文本 |            |
| highlight | `==text==`       | 选中文本 | marked 不支持 |
| link      | `[text](url)`    | 选中文本 |            |
| heading1  | `# text`         | 整行   |            |
| heading2  | `## text`        | 整行   |            |
| heading3  | `### text`       | 整行   |            |
| quote     | `> text`         | 整段   |            |
| codeBlock | ` ```js``` `     | code |            |
| table     | \| col \| col \| | 新块   |            |
| image     | `![alt](url)`    | 新块   |            |
| video     | 自定义语法            | 新块   |            |
| embedLink | 自定义语法            | 新块   |            |
| divider   | `---`            | 新块   |            |


### Markdown 转 HTML 映射策略

本编辑器采用 **Hybrid View (源码即 UI)** 模式，因此涉及两种不同的 HTML 结构：

1.  **编辑态 (Editing State)**: 用于编辑器内部展示，保持源码可见，使用 CSS 类模拟样式。
2.  **预览/导出态 (Preview/Export State)**: 用于最终展示，转换为标准的语义化 HTML 标签。

#### 1. 编辑态结构 (Hybrid View)

- **基本原则**:
  - **行 (Line)**: 使用 `<div>` 包裹每一行。空行使用 `<div><br></div>`。
  - **样式 (Style)**: 使用 `<span>` 包裹语法标记，通过 CSS 类实现高亮。
  - **源码保留**: 不隐藏 Markdown 标记（如 `**`），而是将其包含在 `span` 中。

- **示例**:

  ```html
  <!-- 标题 -->
  <div><span class="md-h1"># 这是一个标题</span></div>

  <!-- 粗体与斜体 -->
  <div>
    普通文本
    <span class="md-bold">**粗体**</span>
    <span class="md-italic">*斜体*</span>
  </div>

  <!-- 空行 -->
  <div><br /></div>
  ```

#### 2. 预览/导出态结构 (Standard HTML)

遵循 CommonMark/GFM 标准和行业最佳实践：

| Markdown 语法   | 推荐 HTML 标签  | 说明 (最佳实践)                                           |
| :-------------- | :-------------- | :-------------------------------------------------------- |
| **行内样式**    |                 |                                                           |
| `**text**`      | `<strong>`      | 语义化：表示语气强调 (Strong Emphasis)。比 `<b>` 更通用。 |
| `*text*`        | `<em>`          | 语义化：表示强调 (Emphasis)。比 `<i>` 更通用。            |
| `` `text` ``    | `<code>`        | 标准：表示计算机代码片段。                                |
| `==text==`      | `<mark>`        | 语义化：HTML5 新增，表示高亮/标记文本。                   |
| `[text](url)`   | `<a>`           | 标准：超链接。通常配合 `target="_blank"`。                |
| **块级样式**    |                 |                                                           |
| `# text`        | `<h1>` - `<h6>` | 语义化：构建文档大纲，对 SEO 友好。                       |
| `> text`        | `<blockquote>`  | 语义化：引用块。                                          |
| ` ```code ``` ` | `<pre><code>`   | 标准组合：`<pre>` 保留格式，`<code>` 标记代码。           |
| `---`           | `<hr>`          | 语义化：段落级别的主题转换 (Horizontal Rule)。            |
| **媒体**        |                 |                                                           |
| `![alt](url)`   | `<img>`         | 标准：必须包含 `alt` 属性以支持无障碍访问。               |

难度：⭐⭐⭐⭐（需要理解 Markdown 语法和字符串操作）

---

## 🏗️ 架构设计

### 1. 依赖关系图

```
┌─────────────────────────────────────────┐
│  useMarkdown (格式化引擎)               │
├─────────────────────────────────────────┤
│                                         │
│  依赖（输入）:                          │
│  ├─ EditorState           (编辑器状态) │
│  ├─ UseSelectionReturn    (选中操作)   │
│  └─ ReturnType<useHistory> (历史管理)  │
│                                         │
│  提供（输出）:                          │
│  ├─ applyFormat()    (应用格式)        │
│  ├─ insertBlock()    (插入块)          │
│  ├─ wrapWithMarkdown() (包裹文本)      │
│  ├─ markdownToHtml()  (转换HTML)       │
│  └─ getCurrentFormat() (格式检测)      │
│                                         │
└─────────────────────────────────────────┘
         ↓                    ↓
┌────────────────┐    ┌──────────────────┐
│ useSelection   │    │ markdown-parser  │
│ (选中文本操作) │    │ (语法解析工具)   │
└────────────────┘    └──────────────────┘
```

**依赖关系说明**：

```
useMarkdown
  ├─ 依赖 types/editor.ts (EditorState, FloatingActionType, BlockActionType)
  ├─ 依赖 useSelection.ts (UseSelectionReturn - 包含方法)
  └─ 依赖 useHistory.ts (ReturnType<typeof useHistory>)

✅ 单向依赖：useMarkdown → useSelection (不存在反向依赖)
✅ 类型独立：所有类型都在 types/editor.ts 中集中管理
✅ 避免循环依赖：依赖方向清晰，不会产生循环引用
```

### 2. 函数签名设计

```typescript
import type { UseSelectionReturn } from './useSelection'

export function useMarkdown(
  state: EditorState,
  selection: UseSelectionReturn,  // ✅ 传入完整的 composable（包含方法）
  history: ReturnType<typeof useHistory>
) {
  // 核心方法
  const applyFormat = (action: FloatingActionType): void => { ... }
  const insertBlock = (action: BlockActionType, position?: number): void => { ... }
  const wrapWithMarkdown = (before: string, after: string): void => { ... }
  const markdownToHtml = (markdown: string): string => { ... }
  const getCurrentFormat = (): FormatState => { ... }

  // 返回公开 API
  return { 
    applyFormat, 
    insertBlock, 
    wrapWithMarkdown, 
    markdownToHtml, 
    getCurrentFormat 
  }
}

// ✅ 导出类型供其他模块使用
export type UseMarkdownReturn = ReturnType<typeof useMarkdown>
```

**设计说明**：

1. **selection 参数为何是 UseSelectionReturn 而非 SelectionInfo**：
   - `SelectionInfo` 只包含数据（start, end, selectedText）
   - `UseSelectionReturn` 包含所有操作方法（wrapSelection, setCursor 等）
   - useMarkdown 需要调用这些方法来实现格式化，而不是直接操作 DOM

2. **依赖注入模式**：
   - useMarkdown 作为高层业务逻辑，依赖低层工具（useSelection, useHistory）
   - 通过参数注入，而非内部创建，便于测试和复用

3. **ReturnType 工具类型的使用**：
   - `ReturnType<typeof useHistory>` 自动推断 useHistory 的返回类型
   - 避免手写类型定义，保持类型和实现同步

### 3. 类型定义

```typescript
// 浮动工具栏操作类型（行内格式）
type FloatingActionType = 
  | 'bold'       // 加粗 **text**
  | 'italic'     // 斜体 *text*
  | 'code'       // 行内代码 `text`
  | 'highlight'  // 高亮 ==text==
  | 'link'       // 链接 [text](url)

// 块级操作类型
type BlockActionType = 
  | 'heading1'   // 一级标题 # text
  | 'heading2'   // 二级标题 ## text
  | 'heading3'   // 三级标题 ### text
  | 'quote'      // 引用块 > text
  | 'codeBlock'  // 代码块 ```lang\ncode\n```
  | 'table'      // 表格 | col | col |
  | 'image'      // 图片 ![alt](url)
  | 'video'      // 视频（自定义语法）
  | 'embedLink'  // 嵌入链接（自定义语法）
  | 'divider'    // 分割线 ---

// 当前格式状态
interface FormatState {
  isBold: boolean        // 是否加粗
  isItalic: boolean      // 是否斜体
  isCode: boolean        // 是否代码
  isHighlight: boolean   // 是否高亮
  headingLevel: 0 | 1 | 2 | 3  // 标题级别（0 = 非标题）
  isQuote: boolean       // 是否引用
}
```

---

## 🔧 核心方法实现

### 方法 1: applyFormat() - 应用行内格式

**功能**：对选中文本应用格式（加粗、斜体、代码等）

**实现策略**：

```typescript
const applyFormat = (action: FloatingActionType): void => {
  const { selectedText, start, end } = selection.getSelection()
  
  // 1. 无选中文本 → 不执行
  if (!selectedText) {
    console.warn('没有选中文本，无法应用格式')
    return
  }

  // 2. 根据操作类型确定 Markdown 语法
  const formatMap: Record<FloatingActionType, { before: string; after: string }> = {
    bold: { before: '**', after: '**' },
    italic: { before: '*', after: '*' },
    code: { before: '`', after: '`' },
    highlight: { before: '==', after: '==' },
    link: { before: '[', after: '](url)' }  // 需要特殊处理
  }

  const { before, after } = formatMap[action]

  // 3. 检查是否已经应用了该格式（toggle 逻辑）
  const isAlreadyFormatted = 
    selectedText.startsWith(before) && selectedText.endsWith(after)

  let newText: string

  if (isAlreadyFormatted) {
    // 移除格式
    newText = selectedText.slice(before.length, -after.length)
  } else {
    // 应用格式
    newText = `${before}${selectedText}${after}`
  }

  // 4. 替换选中文本
  replaceRange(start, end, newText)

  // 5. 记录到历史栈（支持撤销）
  history.addTransaction({
    id: generateId(),
    label: `应用格式: ${action}`,
    actions: [{ type: 'format', content: newText, start, end }],
    timestamp: Date.now()
  })
}
```

**关键设计点**：

1. **Toggle 逻辑**：已格式化的文本点击同样按钮会取消格式
2. **边界检查**：必须有选中文本才能执行
3. **事务记录**：每次格式化都记录到历史栈，支持撤销

**特殊处理：链接格式**

```typescript
// 链接需要弹出输入框让用户输入 URL
if (action === 'link') {
  const url = prompt('请输入链接地址:', 'https://')
  if (!url) return  // 用户取消

  newText = `[${selectedText}](${url})`
}
```

---

### 方法 2: insertBlock() - 插入块级元素

**功能**：在指定位置插入块级元素（标题、代码块、表格等）

**实现策略**：

```typescript
const insertBlock = (action: BlockActionType, position?: number): void => {
  // 1. 确定插入位置（如果未指定，使用当前光标位置）
  const insertPos = position ?? selection.getSelection().start

  // 2. 根据块类型生成模板
  const blockTemplates: Record<BlockActionType, string> = {
    heading1: '# 标题\n',
    heading2: '## 标题\n',
    heading3: '### 标题\n',
    quote: '> 引用内容\n',
    codeBlock: '```javascript\n// 代码\n```\n',
    table: '| 列1 | 列2 | 列3 |\n| --- | --- | --- |\n| 单元格 | 单元格 | 单元格 |\n',
    image: '![图片描述](图片URL)\n',
    video: '<video src="视频URL"></video>\n',
    embedLink: '<iframe src="嵌入URL"></iframe>\n',
    divider: '---\n'
  }

  const blockContent = blockTemplates[action]

  // 3. 在光标位置插入块内容
  insertAtPosition(insertPos, blockContent)

  // 4. 记录到历史
  history.addTransaction({
    id: generateId(),
    label: `插入块: ${action}`,
    actions: [{ type: 'insert', content: blockContent, start: insertPos }],
    timestamp: Date.now()
  })

  // 5. 移动光标到插入内容的合适位置
  const newCursorPos = insertPos + blockContent.indexOf('标题')  // 定位到可编辑区域
  selection.setCursor(newCursorPos)
}
```

**关键设计点**：

1. **模板化**：每种块都有预定义模板，用户插入后可编辑
2. **光标定位**：插入后自动移动光标到可编辑区域（如"标题"文字位置）
3. **换行处理**：块级元素末尾添加 `\n` 确保后续内容独立

---

### 方法 3: wrapWithMarkdown() - 通用文本包裹

**功能**：用指定的前后缀包裹选中文本（底层工具方法）

**实现策略**：

```typescript
const wrapWithMarkdown = (before: string, after: string): void => {
  const { selectedText, start, end } = selection.getSelection()

  if (!selectedText) {
    console.warn('没有选中文本')
    return
  }

  const wrapped = `${before}${selectedText}${after}`
  replaceRange(start, end, wrapped)
}
```

**用途**：

- 作为 `applyFormat()` 的底层实现
- 可供插件系统使用（自定义格式）

---

### 方法 4: markdownToHtml() - Markdown 转 HTML

**功能**：将 Markdown 文本转换为 HTML（用于预览模式）

**实现策略（使用 marked 库）**：

```typescript
import { marked } from 'marked'
import DOMPurify from 'dompurify'

const markdownToHtml = (markdown: string): string => {
  try {
    // 1. 配置 marked
    marked.setOptions({
      gfm: true,          // GitHub Flavored Markdown
      breaks: true,       // 支持换行符转 <br>
      headerIds: true,    // 自动生成标题 ID
      mangle: false       // 不混淆邮箱地址
    })

    // 2. 解析 Markdown
    const rawHtml = marked.parse(markdown)

    // 3. 使用 DOMPurify 清理 HTML（防 XSS）
    const cleanHtml = DOMPurify.sanitize(rawHtml, {
      ALLOWED_TAGS: [
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6',
        'p', 'br', 'hr',
        'strong', 'em', 'code', 'pre',
        'a', 'img',
        'ul', 'ol', 'li',
        'blockquote',
        'table', 'thead', 'tbody', 'tr', 'th', 'td'
      ],
      ALLOWED_ATTR: ['href', 'src', 'alt', 'title', 'class', 'id']
    })

    return cleanHtml
  } catch (error) {
    console.error('Markdown 解析失败:', error)
    return '<p>解析错误</p>'
  }
}
```

**关键设计点**：

1. **安全性优先**：使用 DOMPurify 防止 XSS 攻击
2. **白名单机制**：只允许特定的 HTML 标签和属性
3. **错误处理**：解析失败时返回友好提示

**依赖库**：

```bash
pnpm add marked dompurify
```

---

### 方法 5: getCurrentFormat() - 检测当前格式状态

**功能**：检测光标所在位置的格式状态（用于工具栏按钮高亮）

**实现策略**：

```typescript
const getCurrentFormat = (): FormatState => {
  const { start, selectedText } = selection.getSelection()
  const currentLine = selection.getCurrentLine()

  // 初始化状态
  const formatState: FormatState = {
    isBold: false,
    isItalic: false,
    isCode: false,
    isHighlight: false,
    headingLevel: 0,
    isQuote: false
  }

  // 检测行内格式（基于选中文本或光标周围文本）
  const checkText = selectedText || getTextAroundCursor(start, 10)
  
  formatState.isBold = /\*\*[^*]+\*\*/.test(checkText)
  formatState.isItalic = /\*[^*]+\*/.test(checkText) && !formatState.isBold
  formatState.isCode = /`[^`]+`/.test(checkText)
  formatState.isHighlight = /==[^=]+==/.test(checkText)

  // 检测标题级别（基于当前行）
  const headingMatch = currentLine.match(/^(#{1,3})\s/)
  if (headingMatch) {
    formatState.headingLevel = headingMatch[1].length as 1 | 2 | 3
  }

  // 检测引用
  formatState.isQuote = currentLine.startsWith('>')

  return formatState
}
```

**用途**：

- 工具栏按钮高亮显示（如加粗文本时，加粗按钮高亮）
- 帮助用户了解当前编辑位置的格式状态

---

## 🎯 技术难点与解决方案

### 难点 1: Toggle 逻辑的复杂性

**问题**：如何准确检测文本是否已格式化？

**场景**：

```
用户选中 "**加粗**" → 应该移除格式 → 结果是 "加粗"
用户选中 "加粗"   → 应该应用格式 → 结果是 "**加粗**"
```

**解决方案**：

```typescript
// 精确检测前后缀
const isAlreadyFormatted = (text: string, before: string, after: string): boolean => {
  return text.startsWith(before) && text.endsWith(after) && text.length > before.length + after.length
}
```

### 难点 2: 嵌套格式的处理

**问题**：如何处理嵌套格式（如"加粗的斜体"）？

**场景**：

```
用户选中 "***加粗斜体***"
点击"取消加粗" → 应该变成 "*斜体*"（而不是清空所有格式）
```

**解决方案**：

```typescript
// 分层检测和移除
const removeFormat = (text: string, format: 'bold' | 'italic'): string => {
  if (format === 'bold') {
    // 移除 **
    return text.replace(/\*\*/g, '')
  } else if (format === 'italic') {
    // 移除单个 * (但保留 **)
    return text.replace(/(?<!\*)\*(?!\*)/g, '')
  }
  return text
}
```

### 难点 3: 光标位置的精确计算

**问题**：格式化后如何保持光标在正确位置？

**场景**：

```
文本: "hello |world"  (光标在 |)
应用加粗 → "hello **|world**"  (光标仍在 world 前)
```

**解决方案**：

```typescript
// 计算偏移量
const newCursorPos = start + before.length
selection.setCursor(newCursorPos)
```

### 难点 4: Markdown 解析的性能优化

**问题**：大文档实时预览会导致性能问题

**解决方案**：

```typescript
import { debounce } from 'lodash-es'

// 使用 debounce 延迟解析（300ms）
const debouncedParse = debounce((markdown: string) => {
  return markdownToHtml(markdown)
}, 300)
```

---

## 🧪 测试策略

### 1. 单元测试覆盖矩阵

| 测试场景 | 测试用例 | 数据象限 |
|---------|---------|---------|
| **applyFormat** | | |
| - 加粗正常文本 | "text" → "**text**" | 正常数据 |
| - 取消已加粗文本 | "**text**" → "text" | 正常数据 |
| - 空选中 | "" → 不执行 | 边界数据 |
| - 嵌套格式 | "***text***" → 正确处理 | 异常数据 |
| **insertBlock** | | |
| - 插入标题 | 光标位置插入 "# 标题\n" | 正常数据 |
| - 插入代码块 | 光标位置插入代码块模板 | 正常数据 |
| - 文档开头插入 | position = 0 | 边界数据 |
| - 文档末尾插入 | position = maxLength | 边界数据 |
| **markdownToHtml** | | |
| - 标准 Markdown | "**bold**" → "<strong>bold</strong>" | 正常数据 |
| - XSS 攻击代码 | "<script>alert()</script>" → 清理后的安全 HTML | 异常数据 |
| - 空字符串 | "" → "" | 边界数据 |
| - 超长文档 | 10000+ 字符 | 极端数据 |
| **getCurrentFormat** | | |
| - 检测加粗 | "**text**" → isBold = true | 正常数据 |
| - 检测标题级别 | "## title" → headingLevel = 2 | 正常数据 |
| - 无格式文本 | "plain text" → 所有状态 = false | 正常数据 |

### 2. 集成测试

```typescript
describe('useMarkdown 集成测试', () => {
  test('完整格式化流程：选中文本 → 加粗 → 撤销 → 重做', () => {
    // 1. 选中文本
    selection.selectRange(0, 4)  // "text"
    
    // 2. 应用加粗
    markdown.applyFormat('bold')
    expect(state.content).toBe('**text**')
    
    // 3. 撤销
    history.undo()
    expect(state.content).toBe('text')
    
    // 4. 重做
    history.redo()
    expect(state.content).toBe('**text**')
  })
})
```

---

## 🚀 实现路线

### Step 1: 基础工具方法（1-2 小时）

- [ ] 实现 `wrapWithMarkdown()` - 通用包裹方法
- [ ] 实现 `replaceRange()` - 文本替换辅助函数
- [ ] 实现 `generateId()` - 事务 ID 生成
- [ ] 编写单元测试

### Step 2: 行内格式化（2-3 小时）

- [ ] 实现 `applyFormat()` - 加粗、斜体、代码、高亮
- [ ] 实现 Toggle 逻辑
- [ ] 处理链接格式的特殊逻辑
- [ ] 编写单元测试（覆盖 4 象限）

### Step 3: 块级元素（2-3 小时）

- [ ] 实现 `insertBlock()` - 标题、代码块、表格等
- [ ] 实现块模板系统
- [ ] 实现光标自动定位
- [ ] 编写单元测试

### Step 4: Markdown 转换（2-3 小时）

- [ ] 配置 marked 库
- [ ] 实现 `markdownToHtml()`
- [ ] 集成 DOMPurify 安全过滤
- [ ] 测试 XSS 防护

### Step 5: 格式检测（1-2 小时）

- [ ] 实现 `getCurrentFormat()`
- [ ] 实现正则检测逻辑
- [ ] 编写测试用例

### Step 6: 集成与优化（2-3 小时）

- [ ] 集成到 `useMarkdownEditor`
- [ ] 性能优化（debounce）
- [ ] 编写集成测试
- [ ] 达到 85%+ 测试覆盖率

**总计预估时间**：10-16 小时（2-3 天开发）

---

## ✅ 验收标准

### 功能完整性

- [ ] 支持所有行内格式（加粗、斜体、代码、高亮、链接）
- [ ] 支持所有块级元素（标题、引用、代码块、表格等）
- [ ] Toggle 逻辑正确（再次点击取消格式）
- [ ] Markdown 转 HTML 正确且安全（防 XSS）
- [ ] 格式检测准确（工具栏按钮高亮正确）

### 代码质量

- [ ] 单元测试覆盖率 ≥ 85%
- [ ] 所有测试用例通过
- [ ] TypeScript 类型检查无错误
- [ ] 代码注释清晰完整

### 性能指标

- [ ] Markdown 转 HTML 耗时 < 300ms（1000 字文档）
- [ ] 格式化操作响应时间 < 50ms
- [ ] 无内存泄漏

---

## 📚 参考资料

- [Markdown 官方语法](https://www.markdownguide.org/basic-syntax/)
- [marked 库文档](https://marked.js.org/)
- [DOMPurify 文档](https://github.com/cure53/DOMPurify)
- [CommonMark 规范](https://commonmark.org/)

---
