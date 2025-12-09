# Markdown 编辑器设计文档

> **文档目的**：定义可复用的 Markdown 编辑器模块的设计方案、样式规范和技术实现  
> **维护人**：项目团队  
> **更新日期**：2025-11-18  
> **版本**：v1.0  
> **设计理念**：生产级高复用模块 - 一次设计，多项目使用

---

## 📋 目录

1. [产品定位](#产品定位)
2. [样式设计](#样式设计)
3. [技术架构](#技术架构)
4. [模块结构](#模块结构)
5. [API 设计](#api-设计)
6. [类型系统](#类型系统)
7. [使用示例](#使用示例)
8. [实现路线](#实现路线)

---

## 🎯 产品定位

### 为什么是这个编辑器？

一个**生产级别、高度可复用**的Markdown编辑器模块，设计原则：

- ✅ **开箱即用** - 零配置启动，满足80%的使用场景
- ✅ **灵活可定制** - 配置驱动，支持深度定制而不修改核心代码
- ✅ **跨框架支持** - 核心逻辑与UI框架解耦，可移植到 React / Angular / Vanilla JS
- ✅ **高度可复用** - 用于博客编辑、评论、笔记、文档等多种场景

### 设计目标

```
┌─────────────────────────────────────────────────┐
│ 目标用户和使用场景                              │
├─────────────────────────────────────────────────┤
│                                                 │
│ 📝 场景1：文章编辑（本项目主场景）              │
│    - 用户需要发布完整的Markdown文章            │
│    - 需要实时预览和格式化工具                  │
│    - 自动保存草稿                              │
│                                                 │
│                                                 │
│ 📓 场景3：笔记编辑（内部项目）                 │
│    - 快速记笔记，支持嵌入代码块和图片         │
│    - 折叠功能，适合长文档                     │
│                                                 │
│ 🔧 场景4：自定义扩展（开发者）                 │
│    - 插件系统支持自定义语法（@mention、emoji）│
│    - 完整的 Hooks 机制                         │
│                                                 │
└─────────────────────────────────────────────────┘
```

### 核心价值

| 维度         | 价值                             |
| ------------ | -------------------------------- |
| **开发效率** | 减少50%的编辑器编码时间          |
| **代码复用** | 一次开发，多项目无缝集成         |
| **可维护性** | 集中维护编辑器逻辑，项目聚焦业务 |
| **用户体验** | Medium级别的编辑体验             |
| **性能**     | 优化的渲染，支持大型文档         |

---

## 🎨 样式设计

### 1\. 编辑器整体布局（Obsidian Live Preview 风格）

````
┌──────────────────────────────────────────────────────┐
│  Header                                              │
│  (自动保存状态 | 发布 | 更多选项)                     │
├──────────────────────────────────────────────────────┤
│                                                      │
│  标题输入框                                           │
│  ┌────────────────────────────────────────────────┐ │
│  │ 我的文章标题 (placeholder)                      │ │
│  │ (contenteditable + font-size: 32px bold)      │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  正文编辑区（Live Preview）                          │
│  ┌────────────────────────────────────────────────┐ │
│  │ <span class="token"># </span>这是二级标题       │ │
│  │                                                │ │
│  │ 这是一段正文。<span class="token">**</span>     │ │
│  │ 粗体文本<span class="token">**</span>、*斜体文本*          │ │
│  │ 和 [链接](url)                                │ │
│  │                                                │ │
│  │ <span class="token">- </span>列表项 1           │ │
│  │ <span class="token">- </span>列表项 2           │ │
│  │                                                │ │
│  │ ```javascript                                 │ │
│  │ const code = 'hello world';                   │ │
│  │ ```                                           │ │
│  │ (contenteditable div)                         │ │
│  │                                                │ │
│  │  ┌─ 浮动工具栏 ──────────────┐               │ │
│  │  │ [B] [I] [Link] [Code] ... │ (选中时出现) │ │
│  │  └───────────────────────────┘              │ │
│  └────────────────────────────────────────────────┘ │
│                                                      │
│  Footer                                              │
│  (字数统计 | 保存状态 | 预计阅读时间)                │
│                                                      │
└──────────────────────────────────────────────────────┘
````

**关键特征（Obsidian Live Preview 风格）**：

- ✅ **保留语法符号**：Markdown 符号（如 `**`, `#`）始终可见，但颜色变浅（弱化）。
- ✅ **实时渲染样式**：内容文本实时应用富文本样式（如粗体、大号标题）。
- ✅ **所见即所得**：无需切换预览模式，编辑体验流畅。
- ✅ **适合学习**：实现逻辑比完全隐藏符号简单，更适合初学者掌握 DOM 操作。

### 2. 色彩规范

基于项目设计系统的编辑器色彩（`phase1_design_system.md`）

#### 编辑区域色彩

```
背景：#FFFFFF (纯白)
文本：#1F2937 (灰-900)
语法符号（Token）：#9CA3AF (灰-400)  <-- 关键：弱化显示的符号
边框：#E5E7EB (灰-200)
焦点环：#0EA5E9 (Primary 蓝)
```

#### 工具栏色彩

```
背景：#FFFFFF (纯白) + shadow-md
按钮默认：#9CA3AF (灰-400) text
按钮激活：#0EA5E9 (Primary 蓝)
按钮悬停：#F3F4F6 (灰-100) bg
```

#### Markdown 格式化色彩（在编辑区内显示）

```
代码块背景：#1F2937 (灰-900)
代码块文本：#FFFFFF (纯白)
代码块边框：#374151 (灰-700)
行号/语法高亮：#10B981 (绿色)

引用块：
  - 左边框：#0EA5E9 (Primary 蓝)
  - 背景：#EFF6FF (蓝-50)
  - 文本：#1e40af (蓝-900)

列表标记：#9CA3AF (灰-400)
链接文本：#0EA5E9 (Primary 蓝)
```

### 3. 排版规范

基于项目设计系统的编辑器排版（`phase1_design_system.md`）

```
┌──────────────────────────────────────────────────┐
│ 编辑区排版                                       │
├──────────────────────────────────────────────────┤
│ 标题输入                                          │
│   - 字体大小：32px (text-4xl)                    │
│   - 字重：bold (font-bold)                       │
│   - 行高：1.2 (leading-tight)                    │
│   - 下边距：16px (mb-4)                         │
│   - 占位符：灰-400 text                         │
│                                                 │
│ 正文输入                                          │
│   - 字体大小：16px (text-base)                  │
│   - 字重：normal                                │
│   - 行高：1.75 (leading-relaxed)               │
│   - 最小高度：600px (min-h-[600px])             │
│   - 占位符：灰-400 text                         │
│                                                 │
│ Markdown 格式显示（在编辑区内）                  │
│   - H1：32px bold / 1.2行高                     │
│   - H2：24px semibold / 1.3行高                │
│   - H3：18px semibold / 1.3行高                │
│   - 正文：16px normal / 1.75行高               │
│   - 代码行内：14px font-mono, bg-gray-100      │
│   - 代码块：14px font-mono, bg-gray-900        │
│                                                 │
└──────────────────────────────────────────────────┘
```

### 4\. 间距规范

```
编辑器容器：max-width: 800px / margin: 0 auto
（Medium的最优阅读宽度）

标题编辑区：
  - padding: 24px (lg)
  - border-bottom: 1px #E5E7EB
  - margin-bottom: 16px (md)

正文编辑区：
  - padding: 24px (lg)
  - min-height: 600px
  - line-height: 1.75 (舒适的行间距)

浮动工具栏：
  - 出现在选中文本上方 8px (xs)
  - padding: 8px (xs)
  - gap: 4px (icon之间)

响应式断点：
  - lg (≥1024px): 编辑器宽度 800px + 侧边栏
  - md (≥768px): 编辑器宽度 100% - 1rem padding
  - sm (<768px): 编辑器宽度 100% - 0.5rem padding，工具栏可滚动
```

### 5. 交互状态

#### 编辑区交互

```
默认：
  - 背景：白色
  - 边框：灰-200
  - 文本：灰-900

聚焦：
  - 背景：白色
  - 边框：Primary 蓝 + 环
  - 文本：灰-900
  - 阴影：ring-2 ring-blue-100

禁用：
  - 背景：灰-50
  - 文本：灰-400
  - 光标：not-allowed
```

#### 工具栏按钮

```
默认：
  - 背景：透明
  - 文本：灰-500
  - 光标：pointer

悬停：
  - 背景：灰-100
  - 文本：灰-700
  - 过渡：transition-colors duration-200

激活（已应用）：
  - 背景：blue-100
  - 文本：Primary 蓝
  - 边框：Primary 蓝

禁用：
  - 文本：灰-300
  - 光标：not-allowed
  - 不透明度：opacity-50
```

### 6. 动画过渡

```
工具栏出现/消失：
  - duration: 150ms (fade-in/out)
  - easing: ease-out

按钮反馈：
  - duration: 200ms
  - easing: ease-out

预览刷新：
  - duration: 300ms (debounce)

标签页切换：
  - duration: 200ms
  - easing: ease-out
```

---

## 🏗️ 技术架构

### 1. 架构设计原理

```
┌──────────────────────────────────────────────────────┐
│               Markdown 编辑器模块架构                 │
├──────────────────────────────────────────────────────┤
│                                                      │
│  ┌─ Vue 3 组件层 ─────────────────────────────────┐ │
│  │                                                 │ │
│  │  MarkdownEditor.vue (主组件)
  ├─ EditorHeader.vue (保存状态、工具选项)
  ├─ EditorTitle.vue (标题输入)
  ├─ EditorContent.vue (正文编辑+WYSIWYG)
  ├─ EditorToolbar.vue (浮动工具栏)
  └─ EditorFooter.vue (字数统计、时间).vue                           │ │
│  │                                                 │ │
│  └─────────────────────────────────────────────────┘ │
│                       ↓                              │
│  ┌─ Composable 层 ────────────────────────────────┐ │
│  │                                                 │ │
│  │  useMarkdownEditor()   ← 核心编辑逻辑          │ │
│  │  useToolbar()          ← 工具栏状态管理        │ │
│  │  useAutoSave()         ← 自动保存              │ │
│  │  useShortcuts()        ← 快捷键处理            │ │
│  │                                                 │ │
│  └─────────────────────────────────────────────────┘ │
│                       ↓                              │
│  ┌─ 工具函数层 ────────────────────────────────────┐ │
│  │                                                 │ │
│  │  markdown-utils.ts                             │ │
│  │  ├─ parseMarkdown()                            │ │
│  │  ├─ renderHtml()                               │ │
│  │  └─ sanitizeHtml()                             │ │
│  │                                                 │ │
│  │  selection-utils.ts                            │ │
│  │  ├─ getSelection()                             │ │
│  │  ├─ setSelection()                             │ │
│  │  └─ wrapText()                                 │ │
│  │                                                 │ │
│  │  editor-helpers.ts                             │ │
│  │  ├─ insertHeading()                            │ │
│  │  ├─ insertLink()                               │ │
│  │  └─ insertCodeBlock()                          │ │
│  │                                                 │ │
│  └─────────────────────────────────────────────────┘ │
│                       ↓                              │
│  ┌─ 类型和配置层 ──────────────────────────────────┐ │
│  │                                                 │ │
│  │  editor.types.ts  (TypeScript 类型定义)       │ │
│  │  editor.config.ts (默认配置)                  │ │
│  │                                                 │ │
│  └─────────────────────────────────────────────────┘ │
│                       ↓                              │
│  ┌─ 外部依赖层 ────────────────────────────────────┐ │
│  │                                                 │ │
│  │  marked           - Markdown 解析             │ │
│  │  highlight.js     - 代码高亮 (可选)           │ │
│  │                                                 │ │
│  └─────────────────────────────────────────────────┘ │
│                                                      │
└──────────────────────────────────────────────────────┘
```

备用：
```
┌─────────────────────────────────────────────┐
│  Component Layer (组件层)                    │
│  ├─ EditorToolbar.vue                       │
│  ├─ FloatingToolbar.vue                     │
│  └─ BlockMenu.vue                           │
└─────────────────────────────────────────────┘
                ↓ 可能直接调用
┌─────────────────────────────────────────────┐
│  Business Logic Layer (业务逻辑层)           │
│  ├─ useMarkdownEditor (协调器)              │
│  ├─ useMarkdown (格式化逻辑)    ← 主要使用者 │
│  ├─ useHistory (历史管理)                   │
│  └─ useAutoSave (自动保存)                  │
└─────────────────────────────────────────────┘
                ↓ 依赖
┌─────────────────────────────────────────────┐
│  Utility Layer (工具层)                      │
│  ├─ useSelection (文本选择)     ← 通用工具   │
│  └─ markdown-parser (解析器)                │
└─────────────────────────────────────────────┘
                ↓ 使用
┌─────────────────────────────────────────────┐
│  Browser API Layer (浏览器 API)              │
│  ├─ window.getSelection()                   │
│  ├─ document.createRange()                  │
│  └─ contenteditable DOM                     │
└─────────────────────────────────────────────┘
```
### 2. 分层优势

| 层级             | 优势                       |
| ---------------- | -------------------------- |
| **组件层**       | Vue 3 特定，UI 实现        |
| **Composable层** | 可复用逻辑，与 UI 框架无关 |
| **工具函数层**   | 纯函数，可在任何环境运行   |
| **类型和配置**   | 支持配置驱动的行为         |

**结果**：核心逻辑可以移植到任何框架！

### 3. 数据流向

```
用户输入 (contenteditable div)
    ↓
实时渲染 Markdown 格式 (所见即所得)
    ↓
获取选中文本 (getSelection - 用于工具栏)
    ↓
工具栏操作：应用格式 (wrapText / insertText)
    ↓
更新 contenteditable 内容
    ↓
触发 input 事件
    ↓
debounce 500ms (防止频繁保存)
    ↓
获取内容 (textContent + innerHTML)
    ↓
自动保存 (localStorage / API)
    ↓
更新编辑状态 (字数、保存时间)
    ↓
发出 change 事件
```

---


## 📁 模块结构

### 完整的文件结构

```
frontend/src/components/editor/
│
├── 📄 MarkdownEditor.vue          ← 主编辑器组件
│
├── 📁 sub-components/
│   ├── EditorHeader.vue           ← 头部（保存状态、工具选项）
│   ├── EditorTitle.vue            ← 标题输入框 (contenteditable)
│   ├── EditorContent.vue          ← 正文编辑区 (contenteditable + WYSIWYG)
│   ├── EditorToolbar.vue          ← 浮动工具栏（选中时出现）
│   └── EditorFooter.vue           ← 页脚（字数、阅读时间）
│
├── 📁 composables/
│   ├── useMarkdownEditor.ts       ← 核心编辑逻辑
│   ├── useToolbar.ts              ← 工具栏状态管理
│   ├── useAutoSave.ts             ← 自动保存逻辑
│   └── useShortcuts.ts            ← 快捷键处理
│
├── 📁 utils/
│   ├── markdown.ts                ← Markdown解析和渲染
│   ├── selection.ts               ← 选中文本和光标操作
│   ├── editor-helpers.ts          ← 编辑器辅助函数
│   └── sanitize.ts                ← HTML安全处理（防XSS）
│
├── 📁 types/
│   └── editor.ts                  ← 类型定义
│
├── 📁 styles/
│   └── editor.css                 ← 编辑器样式
│
├── 📁 __tests__/
│   ├── MarkdownEditor.spec.ts     ← 主组件测试
│   ├── useMarkdownEditor.spec.ts  ← Composable测试
│   └── editor-utils.spec.ts       ← 工具函数测试
│
└── 📄 README.md                   ← 使用文档
```

### 各文件详细说明

#### **MarkdownEditor.vue** (主组件)

```
负责：
- 管理编辑器总体状态
- 协调子组件通信
- 处理 v-model 双向绑定
- 提供配置和插件系统支持
```

#### **composables/** (编辑逻辑)

```
useMarkdownEditor:
  - 编辑内容的增删改查
  - 光标位置管理
  - 选中文本处理
  - 撤销重做历史

useToolbar:
  - 工具栏显示/隐藏逻辑
  - 按钮激活状态
  - 点击处理

useAutoSave:
  - 定时保存逻辑
  - localStorage 存储
  - API 同步

useShortcuts:
  - 快捷键绑定
  - 快捷键执行
```

#### **utils/** (纯函数)

```
markdown.ts:
  - marked.parse() 包装
  - 代码高亮处理
  - GFM 扩展支持

selection.ts:
  - 获取选中文本范围
  - 设置光标位置
  - 包裹文本（加粗、斜体等）

editor-helpers.ts:
  - 插入标题
  - 插入链接
  - 插入代码块
  - 插入表格
```

---

## 🔌 API 设计

### 1. Props 配置（完整的组件API）

```typescript
interface EditorProps {
  // 内容绑定
  modelValue?: string // v-model 内容
  title?: string // 文章标题

  // 编辑器显示模式
  displayMode?: 'compact' | 'normal' | 'fullscreen' // 紧凑 / 正常 / 全屏

  // 尺寸配置
  minHeight?: string // 最小高度
  maxHeight?: string // 最大高度

  // 功能开关
  features?: {
    toolbar?: boolean // 是否显示工具栏
    autoSave?: boolean // 是否自动保存
    footer?: boolean // 是否显示页脚（字数统计）
    markdown?: boolean // 是否支持Markdown语法
    shortcuts?: boolean // 是否启用快捷键
  }

  // 工具栏配置
  toolbarConfig?: ToolbarConfig

  // 自动保存配置
  autoSaveConfig?: AutoSaveConfig

  // 只读模式
  readOnly?: boolean

  // 占位符
  placeholder?: {
    title?: string
    content?: string
  }

  // 插件系统
  plugins?: EditorPlugin[]
}
```

### 2. Events（完整的事件系统）

```typescript
interface EditorEmits {
  // 内容变化
  'update:modelValue': [content: string]
  'update:title': [title: string]
  change: [{ title: string; content: string }]

  // 编辑事件
  input: [content: string]
  focus: []
  blur: []

  // 保存事件
  save: [{ title: string; content: string }]
  saved: [timestamp: number]
  'save-error': [error: Error]

  // 工具栏事件
  'toolbar-action': [action: string]

  // 自定义事件
  'plugin-event': [{ plugin: string; data: any }]
}
```

### 3. Methods（组件方法）

```typescript
interface EditorMethods {
  // 内容操作
  getContent(): string;
  setContent(content: string): void;
  insertText(text: string): void;
  replaceSelection(text: string): void;

  // 格式化
  bold(): void;                           // 加粗选中文本
  italic(): void;                         // 斜体
  insertLink(): void;                     // 插入链接
  insertImage(): void;                    // 插入图片
  insertCodeBlock(): void;                // 插入代码块
  insertTable(): void;                    // 插入表格
  insertHeading(level: 1-6): void;       // 插入标题

  // 编辑历史
  undo(): void;                           // 撤销
  redo(): void;                           // 重做

  // 状态查询
  getState(): EditorState;
  canUndo(): boolean;
  canRedo(): boolean;

  // 其他
  focus(): void;                          // 聚焦编辑区
  save(): Promise<void>;                  // 保存
  export(format: 'html' | 'markdown'): string;  // 导出
}
```

---

## 📐 类型系统

### 核心类型定义

```typescript
// editor.ts

// 编辑器状态
interface EditorState {
  title: string
  content: string
  isDirty: boolean // 是否有未保存的改动
  isSaving: boolean // 是否正在保存
  canUndo: boolean
  canRedo: boolean
  lastSaved?: Date
  selectedText?: string
}

// 选中文本信息
interface SelectionInfo {
  start: number // 选中开始位置
  end: number // 选中结束位置
  selectedText: string // 选中的文本
  isEmpty: boolean // 是否为空
}

// 工具栏配置
interface ToolbarConfig {
  position?: 'floating' | 'fixed' | 'inline' // 工具栏位置
  items?: ToolbarItem[] // 工具栏按钮
  groups?: ToolbarGroup[] // 按钮组
}

interface ToolbarItem {
  id: string // 按钮ID
  label: string // 按钮标签
  icon?: string // 图标
  title?: string // 提示文本
  action?: string // 触发的操作
  hotkey?: string // 快捷键
  disabled?: boolean // 是否禁用
}

// 自动保存配置
interface AutoSaveConfig {
  enabled: boolean
  interval: number // 保存间隔（ms）
  storage: 'localStorage' | 'api' | 'both'
  apiUrl?: string // API 端点
  draftKey?: string // localStorage 键
}

// 插件接口
interface EditorPlugin {
  name: string // 插件名称
  version?: string

  hooks?: {
    beforeParse?: (markdown: string) => string
    afterParse?: (html: string) => string
    beforeInsert?: (text: string) => string
    onToolbarAction?: (action: string) => void
    onSelectionChange?: (selection: SelectionInfo) => void
  }

  commands?: Record<string, (args: any) => void>
}

// 编辑操作历史
interface EditAction {
  type: 'insert' | 'delete' | 'replace' | 'format'
  timestamp: number
  content: {
    before: string
    after: string
    position?: number
  }
}
```

---

## 💡 使用示例

### 方式1：最简单使用（开箱即用）

```vue
<template>
  <div class="container">
    <MarkdownEditor v-model="content" v-model:title="title" mode="split" @save="handleSave" />
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import MarkdownEditor from '@/components/editor/MarkdownEditor.vue'

const title = ref('我的文章')
const content = ref('')

const handleSave = async (data: { title: string; content: string }) => {
  try {
    // 调用 API 保存文章
    await api.posts.create(data)
    console.log('保存成功！')
  } catch (error) {
    console.error('保存失败：', error)
  }
}
</script>
```

### 方式2：完全定制使用

```vue
<template>
  <MarkdownEditor
    v-model="content"
    :config="editorConfig"
    :plugins="customPlugins"
    mode="split"
    read-only="false"
    @save="handleSave"
    @toolbar-action="handleToolbarAction"
  />
</template>

<script setup lang="ts">
import { ref } from 'vue'
import MarkdownEditor from '@/components/editor/MarkdownEditor.vue'
import type { EditorConfig, EditorPlugin } from '@/components/editor/types'

const content = ref('')

// 完整的编辑器配置
const editorConfig: EditorConfig = {
  mode: 'split',
  toolbarConfig: {
    position: 'floating',
    items: [
      { id: 'bold', label: '加粗', hotkey: 'Ctrl+B' },
      { id: 'italic', label: '斜体', hotkey: 'Ctrl+I' },
      { id: 'link', label: '链接', hotkey: 'Ctrl+K' },
      { id: 'code', label: '代码', hotkey: 'Ctrl+`' },
      { id: 'codeblock', label: '代码块', hotkey: 'Ctrl+Shift+C' },
    ],
  },
  autoSaveConfig: {
    enabled: true,
    interval: 10000, // 10s 保存一次
    storage: 'both',
    apiUrl: '/api/drafts/save',
    draftKey: 'article-draft',
  },
  features: {
    toolbar: true,
    autoSave: true,
    preview: true,
    markdown: true,
  },
}

// 自定义插件
const customPlugins: EditorPlugin[] = [
  {
    name: 'mention-plugin',
    hooks: {
      beforeParse: (markdown) => {
        // 将 @username 转换为链接
        return markdown.replace(/@(\w+)/g, '[@$1](user/$1)')
      },
    },
  },
  {
    name: 'emoji-plugin',
    commands: {
      insertEmoji: (emoji) => {
        // 插入emoji
        editor.value?.insertText(emoji)
      },
    },
  },
]

const handleSave = async (data: any) => {
  console.log('保存:', data)
}

const handleToolbarAction = (action: string) => {
  console.log('工具栏点击:', action)
}
</script>
```

### 方式3：Headless 使用（仅用逻辑）

```typescript
// 在其他项目中使用核心逻辑，不使用UI组件
import { useMarkdownEditor } from '@/components/editor/composables/useMarkdownEditor'

const editor = useMarkdownEditor({
  initialContent: '# Hello',
  onChange: (content) => {
    console.log('内容变化:', content)
  },
})

// 直接调用方法
editor.bold() // 加粗
editor.italic() // 斜体
editor.insertLink() // 插入链接
editor.insertCodeBlock() // 插入代码块

// 查询状态
console.log(editor.canUndo())
console.log(editor.getState())

// 导出内容
const html = marked.parse(editor.content.value)
```

---

## 🚀 实现路线

### Phase 1: 基础架构（Week 1）

**目标**：搭建编辑器核心框架和类型系统

- [ ] 创建目录结构和文件框架
- [ ] 编写完整的 TypeScript 类型定义 (`types/editor.ts`)
- [ ] 实现 `useMarkdownEditor` composable 的框架
- [ ] 编写单元测试框架

**输出物**：

- 类型定义文件
- Composable 基础实现
- 测试套件框架

### Phase 2: 核心WYSIWYG功能（Week 2）

**目标**：实现编辑器的核心编辑功能

- [ ] 实现 contenteditable 编辑区
- [ ] 实现文本选中和光标操作（`selection.ts`）
- [ ] 实现 Markdown 解析和渲染（`markdown.ts`）
- [ ] 实现基础格式化操作（加粗、斜体、链接等）
- [ ] 实现编辑历史（撤销/重做）

**输出物**：

- `EditorContent.vue` 组件
- `selection.ts` 工具函数
- `markdown.ts` 工具函数
- 对应单元测试

### Phase 3: UI 组件（Week 3）

**目标**：实现完整的编辑器UI组件

- [ ] 实现 `EditorHeader.vue` (标题输入、保存状态)
- [ ] 实现 `EditorToolbar.vue` (浮动工具栏)
- [ ] 实现 `PreviewPanel.vue` (Markdown 预览)
- [ ] 实现 `MarkdownEditor.vue` (主容器)
- [ ] 应用设计系统样式

**输出物**：

- 所有 Vue 组件
- 编辑器样式文件
- 组件集成测试

### Phase 4: 增强功能（Week 4）

**目标**：实现自动保存、快捷键、插件系统

- [ ] 实现 `useAutoSave` composable
- [ ] 实现 `useShortcuts` composable
- [ ] 实现插件系统框架
- [ ] 实现辅助编辑函数 (`editor-helpers.ts`)
- [ ] 编写集成测试

**输出物**：

- 自动保存逻辑
- 快捷键系统
- 插件接口实现
- 集成测试

### Phase 5: 文档和优化（Week 5）

**目标**：完善文档、性能优化、发布

- [ ] 编写 `README.md` (使用文档)
- [ ] 编写示例项目
- [ ] 性能优化（防抖、虚拟化等）
- [ ] 代码审查和优化
- [ ] 发布 npm 包（可选）

**输出物**：

- 完整使用文档
- 示例代码
- npm 发布配置（可选）

---

## 📊 文件清单

| 文件                               | 优先级 | 周次 | 说明                     |
| ---------------------------------- | ------ | ---- | ------------------------ |
| `types/editor.ts`                  | P0     | 1    | 类型定义，所有文件的基础 |
| `composables/useMarkdownEditor.ts` | P0     | 1-2  | 核心编辑逻辑             |
| `utils/selection.ts`               | P0     | 2    | 光标和选中操作           |
| `utils/markdown.ts`                | P0     | 2    | Markdown 解析渲染        |
| `sub-components/EditorContent.vue` | P0     | 2    | 编辑区核心组件           |
| `EditorTitle.vue`                  | P1     | 2    | 标题输入框               |
| `EditorHeader.vue`                 | P1     | 3    | 头部（保存状态等）       |
| `EditorToolbar.vue`                | P1     | 3    | 浮动工具栏               |
| `EditorFooter.vue`                 | P2     | 4    | 页脚（字数、时间）       |
| `MarkdownEditor.vue`               | P0     | 3    | 主组件                   |
| `composables/useAutoSave.ts`       | P2     | 4    | 自动保存                 |
| `composables/useShortcuts.ts`      | P2     | 4    | 快捷键                   |
| `utils/editor-helpers.ts`          | P2     | 4    | 辅助函数                 |
| `styles/editor.css`                | P1     | 3    | 样式文件                 |
| `__tests__/*`                      | P1     | 1-5  | 测试文件                 |
| `README.md`                        | P1     | 5    | 使用文档                 |

---

## ✅ 验收标准

### 功能完整性

- [ ] 支持基础 Markdown 格式（标题、加粗、斜体、列表、链接）
- [ ] 实时预览功能正常
- [ ] 工具栏所有按钮可用
- [ ] 快捷键响应正确
- [ ] 自动保存功能正常

### 代码质量

- [ ] 测试覆盖率 ≥ 85%
- [ ] TypeScript 无错误和警告
- [ ] ESLint 检查通过
- [ ] 所有公共 API 有文档注释

### 性能指标

- [ ] 编辑响应时间 < 100ms
- [ ] 预览渲染时间 < 300ms
- [ ] 大文档（10000+ 字）可正常编辑
- [ ] 内存占用稳定，无泄漏

### 用户体验

- [ ] Medium 风格的编辑体验
- [ ] 流畅的动画过渡
- [ ] 清晰的视觉反馈
- [ ] 易懂的错误提示

---

## 🔗 相关文档

- [phase1_design_system.md](phase1_design_system.md) - 项目设计系统
- [frontend-styles.md](frontend-styles.md) - Tailwind CSS 规范
- [process.md](01-PROCESS.md) - 项目进度

---

## 📝 版本历史

| 版本 | 日期       | 内容         |
| ---- | ---------- | ------------ |
| v1.0 | 2025-11-18 | 初始设计文档 |

---

**下一步**：等待确认后开始实现 Phase 1 的类型定义和核心 Composable。
