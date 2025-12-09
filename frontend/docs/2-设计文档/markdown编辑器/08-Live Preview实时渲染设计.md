# Live Preview 实时渲染设计文档

> **文档目的**:详细设计基于 CSS 驱动的 Live Preview 实时渲染功能  
> **维护人**：项目团队  
> **创建日期**：2025-12-04  
> **版本**：v1.0  
> **设计理念**：Obsidian 风格的所见即所得体验

---

## 📋 目录

1. [设计概述](#设计概述)
2. [技术方案](#技术方案)
3. [架构设计](#架构设计)
4. [核心功能](#核心功能)
5. [API 设计](#api-设计)
6. [实施计划](#实施计划)
7. [验收标准](#验收标准)
8. [扩展规划](#扩展规划)

---

## 🎯 设计概述

### 1. 产品定位

**Live Preview** 是一种所见即所得的 Markdown 编辑体验，让用户在编辑时实时看到渲染效果，无需切换到预览模式。

**设计目标**：

- ✅ **保留符号**：Markdown 语法符号始终可见（便于编辑）
- ✅ **弱化显示**：符号颜色变浅，不干扰阅读
- ✅ **实时渲染**：内容立即应用富文本样式
- ✅ **光标稳定**：频繁渲染不影响光标位置
- ✅ **性能优异**：支持大文档编辑（1000+ 行）
- ✅ **标题层级规范**：H1唯一（文章标题）、目录从H2开始、最多支持到H3

### 2. 使用场景

```
┌─────────────────────────────────────────┐
│        编辑器使用场景（2种模式）         │
├─────────────────────────────────────────┤
│                                         │
│  1️⃣ 编辑模式（Live Preview）            │
│     - 场景：个人中心写文章               │
│     - 特点：实时预览 + 可编辑            │
│     - 符号：弱化显示（灰色）             │
│     - 组件：MarkdownEditor.vue          │
│                                         │
│  2️⃣ 阅读模式（只读浏览）                 │
│     - 场景：文章详情页                   │
│     - 特点：完全渲染 + 只读              │
│     - 符号：完全隐藏                     │
│     - 组件：MarkdownReader.vue          │
│                                         │
└─────────────────────────────────────────┘
```

### 3. 设计原则

| 原则         | 说明                     | 实现方式            |
| ------------ | ------------------------ | ------------------- |
| **性能优先** | 频繁更新不能卡顿         | CSS 驱动 + 防抖优化 |
| **代码复用** | 编辑和阅读共享逻辑       | 统一的 composable   |
| **易于扩展** | 支持目录、高亮等增强功能 | 模块化设计          |
| **学习友好** | 实现逻辑清晰易懂         | 渐进式架构          |

---

## 🏗️ 技术方案

### 1. 方案选择：ContentEditable + CSS 驱动

#### **核心思想**

```
传统方案（DOM 操作）：
  输入 → JS 解析 → 生成 HTML → 替换 DOM → 恢复光标
         ↑ 性能差、光标管理复杂

我们的方案（CSS 驱动）：
  输入 → JS 标记类型 → 更新 data 属性 → CSS 自动渲染
         ↑ 性能好、光标天然稳定
```

#### **技术要点**

| 技术点       | 实现方式                           | 优势                       |
| ------------ | ---------------------------------- | -------------------------- |
| **块级格式** | `data-line-type` 属性 + CSS 选择器 | 零 DOM 操作，性能好        |
| **行内格式** | 轻量 DOM 标记（`<b>`、`<i>` 等）   | 保留 `data-token` 便于管理 |
| **符号弱化** | CSS 伪元素 + `color: #9CA3AF`      | 纯 CSS 实现，高效          |
| **光标管理** | 基于文本偏移量保存/恢复            | 避免光标跳转               |

### 2. 数据流向

```
用户输入
  ↓
handleInput 事件
  ↓
检测 IME 状态（中文输入法）
  ↓ 如果不在输入法激活状态
防抖 200ms
  ↓
updateLineTypes() - 检测行类型
  ├─ 遍历所有行
  ├─ 正则匹配类型（标题、列表、引用等）
  └─ 更新 data-line-type 属性
  ↓
markInlineFormats() - 标记行内格式
  ├─ 匹配粗体 **text**
  ├─ 匹配斜体 *text*
  ├─ 匹配代码 `code`
  └─ 用 <b>、<i>、<code> 包裹
  ↓
CSS 自动渲染
  ├─ 块级样式（字体大小、颜色等）
  └─ 行内样式（粗体、斜体等）
  ↓
显示最终效果
```

---

## 📐 架构设计

### 1. 文件结构

```
src/components/editor/
├── composables/
│   ├── useLivePreview.ts              ← 核心逻辑（新增）
│   ├── useMarkdownEditor.ts           ← 现有，集成 Live Preview
│   └── useTableOfContents.ts          ← 目录导航（可选，后续）
│
├── utils/
│   ├── livePreviewHelpers.ts          ← 辅助函数（新增）
│   └── markdown.ts                    ← 现有
│
├── sub-components/
│   ├── EditorContent.vue              ← 修改，集成 Live Preview
│   ├── MarkdownEditor.vue             ← 现有
│   └── MarkdownReader.vue             ← 阅读模式（新增，可选）
│
└── styles/
    └── livePreview.css                ← Live Preview 样式（新增，可选）
```

### 2. 核心模块

#### **useLivePreview.ts - 核心 Composable**

```typescript
/**
 * Live Preview 核心逻辑
 * - 行类型检测（标题、列表、引用等）
 * - data 属性标记
 * - 行内格式标记
 */
export function useLivePreview(
  containerRef: Ref<HTMLElement | null>,
  options?: LivePreviewOptions,
) {
  return {
    updateLineTypes, // 更新所有行的类型
    markInlineFormats, // 标记行内格式
    detectLineType, // 检测单行类型
    applyLivePreview, // 一键应用 Live Preview
  }
}
```

#### **livePreviewHelpers.ts - 辅助工具**

```typescript
/**
 * 辅助函数：
 * - 正则匹配规则
 * - DOM 操作工具
 * - 光标位置管理
 */
export {
  HEADING_REGEX, // 标题正则
  LIST_REGEX, // 列表正则
  QUOTE_REGEX, // 引用正则
  saveCursorPosition, // 保存光标
  restoreCursorPosition, // 恢复光标
}
```

---

## 🔧 核心功能

### 1. 块级格式渲染

#### **标题层级规范**

遵循现代文档网站设计原则：

- ✅ **H1 标题**：文章标题，整篇文章只能有**一个**（用于定义页面主题）
- ✅ **H2 标题**：主要章节，可以有**多个**（出现在目录导航）
- ✅ **H3 标题**：章节下的小节，可以有**多个**（出现在目录导航，带缩进）
- ❌ **H4-H6**：不支持（引导用户简化内容结构）

**设计理由**：

- SEO 友好（搜索引擎更重视 H1-H3）
- 目录清晰（右侧导航最多双层结构）
- 移动端友好（扁平结构易于浏览）
- 内容质量（强制用户简化和重组内容）

#### **支持的格式**

| 格式     | Markdown 语法  | data-line-type | CSS 选择器                      | 数量限制  |
| -------- | -------------- | -------------- | ------------------------------- | --------- |
| H1 标题  | `# 标题`       | `heading-1`    | `[data-line-type="heading-1"]`  | **仅1个** |
| H2 标题  | `## 标题`      | `heading-2`    | `[data-line-type="heading-2"]`  | 多个      |
| H3 标题  | `### 标题`     | `heading-3`    | `[data-line-type="heading-3"]`  | 多个      |
| 列表     | `- 项目`       | `list-item`    | `[data-line-type="list-item"]`  | 多个      |
| 引用     | `> 引用`       | `quote`        | `[data-line-type="quote"]`      | 多个      |
| 代码块   | ` ```code``` ` | `code-block`   | `[data-line-type="code-block"]` | 多个      |
| 普通段落 | `文本`         | `paragraph`    | `[data-line-type="paragraph"]`  | 多个      |

#### **检测逻辑**

````typescript
function detectLineType(text: string): LineType {
  // 只支持 H1-H3（符合现代文档标准）
  if (/^###\s/.test(text)) return 'heading-3'
  if (/^##\s/.test(text)) return 'heading-2'
  if (/^#\s/.test(text)) return 'heading-1'

  // H4-H6 不支持，当作普通段落处理
  // if (/^####\s/.test(text)) return 'paragraph'  // 自动忽略

  if (/^[-*]\s/.test(text)) return 'list-item'
  if (/^>\s/.test(text)) return 'quote'
  if (/^```/.test(text)) return 'code-block'

  return 'paragraph'
}

/**
 * H1 唯一性检查
 */
function checkH1Uniqueness(containerRef: Ref<HTMLElement | null>): void {
  if (!containerRef.value) return

  const h1Elements = containerRef.value.querySelectorAll('[data-line-type="heading-1"]')

  if (h1Elements.length === 0) {
    // 提示：建议添加一个主标题
    showInfo('建议添加一个一级标题（H1）作为文章标题')
  }

  if (h1Elements.length > 1) {
    // 警告：检测到多个 H1
    showWarning('检测到 ' + h1Elements.length + ' 个一级标题，建议只使用一个作为文章标题')

    // 可选：自动降级多余的 H1 为 H2
    // h1Elements.forEach((el, index) => {
    //   if (index > 0) {
    //     el.dataset.lineType = 'heading-2'
    //   }
    // })
  }
}
````

#### **CSS 样式示例**

```css
/* H2 标题 */
[data-line-type='heading-2'] {
  font-size: 24px;
  font-weight: 600;
  line-height: 1.3;
  margin: 18px 0 14px;
  color: #111827;
}

/* 符号弱化 */
[data-line-type='heading-2']::first-line {
  color: #9ca3af; /* 灰色 */
}

/* 列表 */
[data-line-type='list-item'] {
  padding-left: 24px;
  position: relative;
}

[data-line-type='list-item']::before {
  content: '•';
  position: absolute;
  left: 8px;
  color: #6b7280;
}
```

### 2. 行内格式渲染

#### **支持的格式**

| 格式     | Markdown 语法 | HTML 标记                                | CSS 类名     |
| -------- | ------------- | ---------------------------------------- | ------------ |
| 粗体     | `**text**`    | `<b class="md-bold">text</b>`            | `.md-bold`   |
| 斜体     | `*text*`      | `<i class="md-italic">text</i>`          | `.md-italic` |
| 行内代码 | `` `code` ``  | `<code class="md-code">code</code>`      | `.md-code`   |
| 链接     | `[text](url)` | `<a class="md-link" href="url">text</a>` | `.md-link`   |

#### **标记逻辑**

```typescript
function markInlineFormats(element: HTMLDivElement): void {
  let html = element.innerHTML

  // 1. 粗体（保留 data-token 用于光标管理）
  html = html.replace(/\*\*([^*]+)\*\*/g, '<b class="md-bold" data-token="**">$1</b>')

  // 2. 斜体
  html = html.replace(/\*([^*]+)\*/g, '<i class="md-italic" data-token="*">$1</i>')

  // 3. 行内代码
  html = html.replace(/`([^`]+)`/g, '<code class="md-code" data-token="`">$1</code>')

  // 4. 链接
  html = html.replace(
    /\[([^\]]+)\]\(([^)]+)\)/g,
    '<a class="md-link" href="$2" data-token="[]()">$1</a>',
  )

  // 仅在内容变化时更新
  if (html !== element.innerHTML) {
    element.innerHTML = html
  }
}
```

#### **CSS 样式示例**

```css
/* 粗体 */
.md-bold {
  font-weight: bold;
  color: #111827;
}

/* 用伪元素显示符号 */
.md-bold::before,
.md-bold::after {
  content: '**';
  color: #9ca3af;
  font-weight: normal;
  user-select: none; /* 选中时不包含符号 */
}

/* 行内代码 */
.md-code {
  background-color: #f3f4f6;
  color: #dc2626;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: 'Courier New', monospace;
  font-size: 14px;
}

.md-code::before,
.md-code::after {
  content: '`';
  color: #9ca3af;
  background: transparent;
}

/* 链接 */
.md-link {
  color: #0ea5e9;
  text-decoration: underline;
}
```

### 3. 性能优化

#### **防抖策略**

```typescript
// 输入防抖：200ms（比历史记录的 500ms 更快）
let livePreviewTimer: number | null = null

const handleInput = () => {
  if (isComposing) return // IME 激活时不处理

  // 清除旧的定时器
  if (livePreviewTimer) {
    clearTimeout(livePreviewTimer)
  }

  // 设置新的定时器
  livePreviewTimer = window.setTimeout(() => {
    applyLivePreview()
    livePreviewTimer = null
  }, 200)
}
```

#### **增量更新**

```typescript
// 只更新变化的行，而不是全部重新渲染
function updateChangedLines(changedIndices: number[]): void {
  const lines = containerRef.value?.children

  changedIndices.forEach((index) => {
    const line = lines?.[index] as HTMLDivElement
    if (line) {
      const text = line.textContent || ''
      const type = detectLineType(text)

      // 仅在类型变化时更新
      if (line.dataset.lineType !== type) {
        line.dataset.lineType = type
      }

      markInlineFormats(line)
    }
  })
}
```

#### **避免重复渲染**

```typescript
// 检查内容是否真的变化
function markInlineFormats(element: HTMLDivElement): void {
  const newHtml = processInlineFormats(element.innerHTML)

  // 只在内容变化时更新 DOM
  if (newHtml !== element.innerHTML) {
    element.innerHTML = newHtml
  }
}
```

### 4. 光标管理

#### **核心挑战**

```
问题：更新 innerHTML 后，光标会跳到开头

解决方案：
  1. 渲染前：保存光标位置（基于文本偏移量）
  2. 渲染 DOM
  3. 渲染后：恢复光标位置（跳过 data-token 节点）
```

#### **实现方式**

```typescript
function applyLivePreview(): void {
  if (!containerRef.value) return

  // 1. 保存光标位置
  const cursorPos = saveCursorPosition(containerRef.value)

  // 2. 更新行类型和格式
  updateLineTypes()

  // 3. 恢复光标位置
  if (cursorPos !== null) {
    restoreCursorPosition(containerRef.value, cursorPos)
  }
}

// 保存光标位置（基于文本偏移量）
function saveCursorPosition(element: HTMLElement): number | null {
  const selection = window.getSelection()
  if (!selection || selection.rangeCount === 0) return null

  const range = selection.getRangeAt(0)
  const preCaretRange = range.cloneRange()
  preCaretRange.selectNodeContents(element)
  preCaretRange.setEnd(range.endContainer, range.endOffset)

  return preCaretRange.toString().length
}

// 恢复光标位置（跳过符号节点）
function restoreCursorPosition(element: HTMLElement, offset: number): void {
  // 使用现有的 useSelection 中的 setCursor 方法
  // 需要处理跳过 [data-token] 属性的节点
}
```

### 5. IME 输入法兼容

```typescript
let isComposing = false

const handleCompositionStart = () => {
  isComposing = true

  // 暂停 Live Preview
  if (livePreviewTimer) {
    clearTimeout(livePreviewTimer)
    livePreviewTimer = null
  }
}

const handleCompositionEnd = () => {
  isComposing = false

  // 输入法结束后立即渲染一次
  applyLivePreview()
}
```

---

## 🔌 API 设计

### 1. useLivePreview Composable

```typescript
interface LivePreviewOptions {
  enabled?: boolean           // 是否启用（默认 true）
  autoUpdate?: boolean        // 是否自动更新（默认 true）
  debounceDelay?: number      // 防抖延迟（默认 200ms）
  preserveTokens?: boolean    // 是否保留符号（默认 true）
  readonly?: boolean          // 是否只读模式（默认 false）
}

export function useLivePreview(
  containerRef: Ref<HTMLElement | null>,
  options: LivePreviewOptions = {}
) {
  return {
    // 状态
    isEnabled: Ref<boolean>

    // 方法
    updateLineTypes: () => void
    markInlineFormats: (element: HTMLDivElement) => void
    detectLineType: (text: string) => LineType
    applyLivePreview: () => void

    // 控制
    enable: () => void
    disable: () => void
    toggle: () => void
  }
}
```

### 2. EditorContent 集成

```vue
<script setup lang="ts">
import { useLivePreview } from '../composables/useLivePreview'

const editorRef = ref<HTMLDivElement | null>(null)

// 集成 Live Preview
const livePreview = useLivePreview(editorRef, {
  enabled: true,
  debounceDelay: 200,
})

const handleInput = () => {
  // ... 现有逻辑 ...

  // 应用 Live Preview
  livePreview.applyLivePreview()
}
</script>
```

### 3. MarkdownReader（阅读模式）

```vue
<script setup lang="ts">
const props = defineProps<{
  content: string
  showToc?: boolean // 是否显示目录
}>()

// 阅读模式：禁用自动更新，隐藏符号
const livePreview = useLivePreview(readerRef, {
  autoUpdate: false,
  preserveTokens: false, // 完全隐藏符号
  readonly: true,
})
</script>

<template>
  <div class="markdown-reader" :class="{ 'hide-tokens': !preserveTokens }">
    <div ref="readerRef" v-html="content"></div>
  </div>
</template>

<style>
/* 阅读模式：完全隐藏符号 */
.markdown-reader.hide-tokens [data-token]::before,
.markdown-reader.hide-tokens [data-token]::after {
  display: none;
}
</style>
```

---

## 📅 实施计划

### 阶段1：基础CSS样式层（1天）

**任务清单**：

- [ ] 创建 `composables/useLivePreview.ts` 文件框架
- [ ] 创建 CSS 样式（可在 EditorContent.vue 中或独立文件）
- [ ] 实现标题样式（H1-H3）
  - 字体大小、字重、行高
  - 符号弱化（`::first-line` 或伪元素）
- [ ] 实现列表样式
  - 圆点替代 `-` 符号
  - 左侧缩进
- [ ] 实现引用样式
  - 左边框 + 背景色
  - `>` 符号弱化

**验收标准**：

- ✅ 手动添加 `data-line-type` 后，样式正确显示
- ✅ 符号颜色为 #9CA3AF
- ✅ 不使用 JS，纯 CSS 测试通过

---

### 阶段2：JS行类型检测与标记（1天）

**任务清单**：

- [ ] 实现 `detectLineType(text: string)` 函数
  - 正则匹配标题、列表、引用、代码块
  - 优先级处理（H3 > H2 > H1）
- [ ] 实现 `updateLineTypes()` 函数
  - 遍历所有行元素
  - 检测类型并更新 `data-line-type`
  - 防抖优化（200ms）
- [ ] 集成到 `EditorContent.vue`
  - 在 `handleInput` 中调用
  - 处理 IME 兼容（composing 时不更新）
- [ ] 编写单元测试

**验收标准**：

- ✅ 输入 `## 标题` 后，自动添加 `data-line-type="heading-2"`
- ✅ CSS 样式自动生效
- ✅ IME 输入法不干扰渲染
- ✅ 不影响撤销/重做功能

---

### 阶段3：行内格式标记（1-1.5天）

**任务清单**：

- [ ] 实现 `markInlineFormats(element)` 函数
  - 粗体：`**text**` 转换
  - 斜体：`*text*` 转换
  - 行内代码：`` `code` `` 转换
  - 链接：`[text](url)` 转换
- [ ] 添加行内格式 CSS 样式
  - `.md-bold` 样式 + 伪元素
  - `.md-italic` 样式 + 伪元素
  - `.md-code` 样式 + 伪元素
  - `.md-link` 样式
- [ ] 处理嵌套格式（可选）
  - 简单嵌套：`**粗体*斜体***`
- [ ] 集成到 `updateLineTypes()` 中
- [ ] 编写单元测试

**验收标准**：

- ✅ 输入 `**粗体**` 后，文字加粗，符号变灰
- ✅ 输入 `` `code` `` 后，背景变灰，符号变浅
- ✅ 链接可点击
- ✅ 光标位置稳定（不跳转）

---

### 阶段4：优化与测试（0.5-1天）

**任务清单**：

- [ ] 性能优化
  - 增量更新（只更新变化的行）
  - 防抖优化测试
  - 避免重复渲染检查
- [ ] 光标位置优化
  - 完善 `saveCursorPosition`
  - 完善 `restoreCursorPosition`
  - 测试各种场景（选中、快捷键等）
- [ ] IME 兼容性测试
  - 中文输入法（拼音）
  - 日文输入法
- [ ] 浏览器兼容性测试
  - Chrome/Edge
  - Firefox
  - Safari
- [ ] 功能测试
  - 复杂格式混合
  - 大文档性能（500+ 行）
  - 撤销/重做集成测试
  - 历史记录不受影响

**验收标准**：

- ✅ 输入流畅，无明显卡顿（< 100ms）
- ✅ 光标稳定，不跳转
- ✅ 中文输入法正常
- ✅ 撤销/重做功能正常
- ✅ 主流浏览器兼容

---

## ✅ 验收标准

### 1. 功能完整性

- [ ] 支持所有块级格式（H1-H3、列表、引用、代码块）
- [ ] 支持所有行内格式（粗体、斜体、代码、链接）
- [ ] 符号正确弱化显示（#9CA3AF）
- [ ] 编辑和阅读模式都正常工作

### 2. 性能指标

- [ ] 输入响应时间 < 100ms
- [ ] 渲染延迟 < 200ms（防抖后）
- [ ] 支持大文档（1000+ 行）无卡顿
- [ ] 内存占用稳定，无泄漏

### 3. 用户体验

- [ ] 光标位置稳定，不跳转
- [ ] 中文输入法正常工作
- [ ] 选中文本后格式化正常
- [ ] 撤销/重做功能不受影响

### 4. 代码质量

- [ ] TypeScript 无错误和警告
- [ ] 单元测试覆盖核心逻辑
- [ ] 代码有完整注释
- [ ] ESLint 检查通过

### 5. 兼容性

- [ ] Chrome/Edge（主要）
- [ ] Firefox
- [ ] Safari
- [ ] 移动端浏览器（响应式）

---

## 🚀 扩展规划

### Phase 2 后续功能（可选）

#### 1. 目录导航（1-2天）

```typescript
// 基于 Live Preview 的目录导航
const { tocItems, activeId, scrollToHeading } = useTableOfContents(editorRef, {
  autoUpdate: true, // 编辑模式自动更新
  highlightCurrent: true,
})

// 目录只显示 H2 和 H3（H1 作为页面标题，不在目录中）
function generateTOC() {
  // 只查询 H2 和 H3
  const headings = containerRef.value?.querySelectorAll(
    '[data-line-type="heading-2"], [data-line-type="heading-3"]',
  )

  return Array.from(headings || []).map((el) => ({
    level: el.dataset.lineType === 'heading-2' ? 2 : 3,
    text: el.textContent?.trim() || '',
    id: el.id,
  }))
}
```

**目录结构示例**：

```
目录
├─ 第一章（H2）
│  ├─ 小节1（H3）
│  └─ 小节2（H3）
├─ 第二章（H2）
│  └─ 小节1（H3）
└─ 第三章（H2）
```

**优势**：

- ✅ 直接基于 `data-line-type` 查询
- ✅ 无需重新解析 Markdown
- ✅ 编辑和阅读模式完全复用
- ✅ 双层结构清晰易读（H2 + H3）
- ✅ H1 不在目录中（作为页面标题单独显示）

#### 2. MarkdownReader 组件（1天）

```vue
<!-- 阅读模式组件 -->
<MarkdownReader :content="article.content" :show-toc="true" :enable-code-highlight="true" />
```

**特点**：

- 符号完全隐藏
- 代码语法高亮
- 图片懒加载
- 点击放大

#### 3. 性能优化（可选）

- 虚拟滚动（超大文档）
- Web Worker 解析（复杂格式）
- 缓存渲染结果

---

## 📊 风险评估

### 技术风险

| 风险               | 影响 | 概率 | 应对方案                           |
| ------------------ | ---- | ---- | ---------------------------------- |
| 光标跳转问题       | 高   | 中   | 完善光标保存/恢复逻辑，充分测试    |
| IME 兼容性问题     | 中   | 中   | compositionstart/end 事件处理      |
| 性能问题（大文档） | 中   | 低   | 防抖 + 增量更新 + 性能测试         |
| 浏览器兼容性       | 低   | 低   | 主流浏览器都支持 data 属性和伪元素 |

### 应对策略

1. **光标管理**：使用成熟的方案（基于 useSelection）
2. **渐进式实施**：先完成基础功能，再优化细节
3. **充分测试**：每个阶段都要验收通过再进入下一阶段
4. **降级方案**：如果 CSS 方案有问题，可以回退到纯 DOM 方案

---

## 📝 版本历史

| 版本 | 日期       | 内容         |
| ---- | ---------- | ------------ |
| v1.0 | 2025-12-04 | 初始设计文档 |

---

## 🔗 相关文档

- [Markdown 编辑器概设](01-Markdown%20编辑器概设.md)
- [编辑器类型架构设计](02-编辑器类型架构设计文档.md)
- [Composable 辅助函数架构设计](03-Composable%20辅助函数架构设计.md)
- [项目进度管理](01-PROCESS.md)

---

**下一步**：等待审核批准后，开始阶段1的实施工作。
