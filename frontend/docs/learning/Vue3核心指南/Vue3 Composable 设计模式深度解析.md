# Vue3 Composable 设计模式深度解析

> **文档目的**：深入理解 Vue3 Composable 的核心设计模式
> **创建日期**：2025-11-24
> **适用人群**：Vue3 中级开发者
> **前置知识**：JavaScript 闭包、TypeScript 基础、Vue3 响应式系统

---

## 📋 目录

1. [什么是 Composable](#什么是-composable)
2. [核心设计模式](#核心设计模式)
   - [闭包机制](#1-闭包机制)
   - [依赖注入](#2-依赖注入)
   - [分层架构](#3-分层架构)
3. [实战案例分析](#实战案例分析)
4. [Composable vs Pinia](#composable-vs-pinia)
5. [使用场景建议](#使用场景建议)
6. [最佳实践](#最佳实践)

---

## 🎯 什么是 Composable

### 定义

**Composable** 是 Vue3 中用于封装和复用**有状态逻辑**的函数。它通过组合函数的方式替代了 Vue2 中的 Mixins，解决了 Mixins 的诸多问题。

### 基本形式

```typescript
// 最简单的 Composable
export function useCounter() {
  const count = ref(0)

  const increment = () => count.value++
  const decrement = () => count.value--

  return { count, increment, decrement }
}

// 使用
const { count, increment } = useCounter()
```

### 与 Mixins 的对比

| 特性 | Mixins | Composable |
|------|--------|------------|
| **来源明确性** | ❌ 不知道属性从哪来 | ✅ 导入明确 |
| **命名冲突** | ❌ 容易冲突 | ✅ 解构时可重命名 |
| **参数配置** | ❌ 难以传参 | ✅ 函数参数灵活 |
| **TypeScript** | ❌ 类型推断困难 | ✅ 完美类型推断 |
| **逻辑复用** | ⚠️ 只能按组件复用 | ✅ 可跨组件、跨项目 |

---

## 🏗️ 核心设计模式

### 1. 闭包机制

#### 什么是闭包？

**闭包** = 函数 + 函数能访问的外部变量

```typescript
function createCounter() {
  let count = 0  // ← 这个变量会被"捕获"

  return {
    increment: () => count++,  // 这些函数"记住"了 count
    decrement: () => count--,
    getValue: () => count
  }
}

const counter = createCounter()
counter.increment()  // count = 1
console.log(counter.getValue())  // 1

// ⚡ count 变量被"封装"在闭包中，外部无法直接访问
```

#### Composable 中的闭包

Composable 通过闭包实现**参数绑定**和**上下文封装**：

```typescript
// 📁 useSelection.ts
export function useSelection(
  editorElement: Ref<HTMLElement | null>,  // ① 外部参数
  state: EditorState
) {
  // ② 内部方法通过闭包"记住"了外部参数
  const getSelection = (): SelectionInfo => {
    const ele = editorElement.value  // ← 使用闭包中的 editorElement
    // ...
    state.selection = sel  // ← 使用闭包中的 state
    return sel
  }

  const replaceRange = (start: number, end: number, newText: string): void => {
    const element = editorElement.value  // ← 同样使用闭包中的 editorElement
    // ...
  }

  // ③ 返回"携带闭包"的方法
  return { getSelection, replaceRange }
}
```

**闭包的三大优势**：

| 优势 | 说明 | 示例 |
|------|------|------|
| **简化调用** | 不需要每次传递相同参数 | `getSelection()` vs `getSelection(editorRef, state)` |
| **封装上下文** | 隐藏实现细节，只暴露接口 | 外部不需要知道内部用了什么变量 |
| **状态隔离** | 每次调用创建独立闭包 | 多个编辑器实例互不影响 |

#### 闭包的"背包"可视化

```
┌────────────────────────────────────────────┐
│  selectionModule (对象)                     │
├────────────────────────────────────────────┤
│  ├─ getSelection [Function]                │
│  │   └─ 背包 🎒                            │
│  │       ├─ editorElement: Ref<HTMLDiv>   │
│  │       └─ state: EditorState            │
│  │                                         │
│  ├─ replaceRange [Function]                │
│  │   └─ 背包 🎒                            │
│  │       ├─ editorElement: Ref<HTMLDiv>   │
│  │       └─ state: EditorState            │
│  │                                         │
│  └─ wrapSelection [Function]               │
│      └─ 背包 🎒                            │
│          ├─ editorElement: Ref<HTMLDiv>   │
│          └─ state: EditorState            │
└────────────────────────────────────────────┘

调用 replaceRange(0, 5, "text") 时：
1. JavaScript 打开 replaceRange 的"背包" 🎒
2. 取出 editorElement 和 state
3. 使用它们执行函数
4. 用户无需手动传入这些参数
```

---

### 2. 依赖注入

#### 什么是依赖注入？

**依赖注入（Dependency Injection）**：将依赖项从外部传入，而不是在内部创建。

```typescript
// ❌ 不好的做法：内部创建依赖（硬编码）
function useMarkdown() {
  const editorElement = document.querySelector('#editor')  // 硬编码
  const state = reactive({ ... })

  const applyFormat = () => {
    // 使用 editorElement 和 state
  }
}

// ✅ 好的做法：依赖注入（灵活配置）
function useMarkdown(
  state: EditorState,          // 注入依赖
  selectionModule: UseSelectionReturn  // 注入依赖
) {
  const applyFormat = () => {
    // 使用注入的依赖
    selectionModule.getSelection()
  }
}
```

#### 依赖注入的优势

| 优势 | 说明 |
|------|------|
| **可测试性** | 可以注入 Mock 对象进行单元测试 |
| **灵活性** | 可以注入不同的实现（多编辑器实例） |
| **解耦** | 模块之间通过接口依赖，不依赖具体实现 |
| **控制反转** | 由调用方控制依赖的创建和生命周期 |

#### 实战示例：测试中的依赖注入

```typescript
// useMarkdown.spec.ts - 单元测试

describe('useMarkdown', () => {
  test('应用加粗格式', () => {
    // ✅ 创建 Mock 依赖
    const mockSelection: UseSelectionReturn = {
      getSelection: vi.fn(() => ({
        start: 0,
        end: 5,
        selectedText: 'hello',
        isEmpty: false
      })),
      wrapSelection: vi.fn(),
      replaceRange: vi.fn(),
      // ...
    }

    const mockState = reactive<EditorState>({ ... })
    const mockHistory = { addTransaction: vi.fn() }

    // ✅ 注入 Mock 依赖
    const markdown = useMarkdown(mockState, mockSelection, mockHistory)

    // 执行测试
    markdown.applyFormat('bold')

    // ✅ 验证调用
    expect(mockSelection.wrapSelection).toHaveBeenCalledWith('**', '**')
  })
})
```

---

### 3. 分层架构

#### 三层架构模式

Composable 通常采用**三层架构**：

```
┌─────────────────────────────────────────────────┐
│  协调层 (Coordinator)                            │
│  - useMarkdownEditor                            │
│  - 职责：创建和组装所有 Composables              │
│  - 示例：创建 state、editorRef，调用子模块       │
└─────────────────────────────────────────────────┘
                      ↓ 依赖
┌─────────────────────────────────────────────────┐
│  业务逻辑层 (Business Logic)                     │
│  - useMarkdown, useHistory                      │
│  - 职责：实现具体的业务逻辑                       │
│  - 示例：格式化文本、撤销重做                     │
└─────────────────────────────────────────────────┘
                      ↓ 依赖
┌─────────────────────────────────────────────────┐
│  工具层 (Utility)                                │
│  - useSelection, useDebounce, useThrottle       │
│  - 职责：提供通用的底层能力                       │
│  - 示例：文本选择、防抖、节流                     │
└─────────────────────────────────────────────────┘
                      ↓ 使用
┌─────────────────────────────────────────────────┐
│  Browser API / Vue API                          │
│  - window.getSelection(), reactive(), ref()     │
└─────────────────────────────────────────────────┘
```

#### 层级职责划分

| 层级 | 职责 | 特点 | 示例 |
|------|------|------|------|
| **协调层** | 组装模块、管理生命周期 | 知道所有模块，负责连接 | useMarkdownEditor |
| **业务逻辑层** | 实现业务规则 | 依赖工具层，不关心底层实现 | useMarkdown |
| **工具层** | 提供通用能力 | 无业务逻辑，可跨项目复用 | useSelection |

#### 实战示例：完整的参数传递链路

```typescript
// ============================================================================
// 📁 useMarkdownEditor.ts - 协调层
// ============================================================================

export function useMarkdownEditor(config: EditorConfig) {
  // ① 创建共享状态
  const state = reactive<EditorState>({ ... })
  const editorRef = ref<HTMLDivElement | null>(null)

  // ② 创建工具层实例（传入依赖）
  const selectionModule = useSelection(editorRef, state)
  const historyModule = useHistory(state, config)

  // ③ 创建业务逻辑层实例（注入依赖）
  const markdown = useMarkdown(state, selectionModule, historyModule)

  // ④ 对外暴露统一 API
  return {
    state,
    editorRef,
    markdown,
    selection: selectionModule,
    history: historyModule
  }
}
```

```typescript
// ============================================================================
// 📁 useSelection.ts - 工具层
// ============================================================================

export function useSelection(
  editorElement: Ref<HTMLElement | null>,  // 接收依赖
  state: EditorState
) {
  // 通过闭包封装实现细节
  const getSelection = (): SelectionInfo => {
    const ele = editorElement.value
    // ... 底层 DOM 操作
    state.selection = result
    return result
  }

  const replaceRange = (start, end, newText) => {
    // ... 底层文本替换
  }

  // 只暴露必要的接口
  return { getSelection, replaceRange, wrapSelection }
}
```

```typescript
// ============================================================================
// 📁 useMarkdown.ts - 业务逻辑层
// ============================================================================

export function useMarkdown(
  state: EditorState,
  selectionModule: UseSelectionReturn,  // 接收已配置的依赖
  historyModule: UseHistoryReturn
) {
  // 解构依赖
  const { getSelection, wrapSelection } = selectionModule

  // 实现业务逻辑
  const applyInlineFormat = (action: InlineFormatType): void => {
    const { selectedText, isEmpty } = getSelection()  // 调用工具层

    if (isEmpty) return

    // 业务逻辑：格式化文本
    const formatMap = {
      bold: { before: '**', after: '**' },
      italic: { before: '*', after: '*' },
      // ...
    }

    const { before, after } = formatMap[action]
    wrapSelection(before, after)  // 调用工具层

    // 记录历史
    historyModule.addTransaction({ ... })
  }

  return { applyInlineFormat }
}
```

---

## 📚 实战案例分析

### 案例：编辑器的 Composable 架构

基于我们的 Markdown 编辑器项目，让我们深入分析完整的 Composable 架构。

#### 调用流程图

```
用户操作
  ↓
Vue Component
  ↓
const { markdown } = useMarkdownEditor(config)
  │
  ├─ 创建 state = reactive({ ... })
  ├─ 创建 editorRef = ref(null)
  │
  ├─ const selectionModule = useSelection(editorRef, state)
  │   │
  │   └─ 返回 { getSelection, replaceRange, wrapSelection }
  │       └─ 这些方法通过闭包"记住"了 editorRef 和 state
  │
  ├─ const historyModule = useHistory(state, config)
  │   │
  │   └─ 返回 { addTransaction, undo, redo }
  │       └─ 这些方法通过闭包"记住"了 state
  │
  └─ const markdown = useMarkdown(state, selectionModule, historyModule)
      │
      └─ 返回 { applyFormat, insertBlock, ... }
          └─ 这些方法使用注入的依赖

用户调用 markdown.applyFormat('bold')
  ↓
applyFormat 内部调用 selectionModule.getSelection()
  ↓
getSelection 通过闭包访问 editorRef.value (DOM 元素)
  ↓
读取 DOM，计算选区
  ↓
更新 state.selection（响应式）
  ↓
返回 { start, end, selectedText }
  ↓
applyFormat 继续执行，调用 wrapSelection('**', '**')
  ↓
wrapSelection 通过闭包访问 editorRef.value，修改 DOM
  ↓
调用 historyModule.addTransaction() 记录历史
  ↓
完成
```

#### 闭包捕获示例

```typescript
// 时间线演示

// T1: useMarkdownEditor 执行
const state = reactive({ content: 'Hello World' })
const editorRef = ref<HTMLDivElement>(/* DOM 元素 */)

// T2: 调用 useSelection
const selectionModule = useSelection(editorRef, state)
//                                   ↓          ↓
//                    这两个引用被捕获到闭包中
//
//  selectionModule = {
//    getSelection: [Function with closure {
//      editorElement: editorRef,  ← 引用
//      state: state                ← 引用
//    }],
//    replaceRange: [Function with closure { ... }]
//  }

// T3: 调用 useMarkdown
const markdown = useMarkdown(state, selectionModule, historyModule)
//                                   ↑
//                      传递的是"已绑定参数"的对象

// T4: 用户操作
markdown.applyFormat('bold')

// T5: applyFormat 内部
const applyFormat = (action) => {
  // 调用 getSelection()
  const { selectedText } = selectionModule.getSelection()
  //                                      ↑
  //  JavaScript 执行流程：
  //  1. 找到 getSelection 函数
  //  2. 发现它的闭包"背包"里有 editorElement 和 state
  //  3. 打开"背包"，取出 editorElement 和 state
  //  4. 执行函数：const ele = editorElement.value
  //  5. 使用 ele 进行 DOM 操作
  //  6. 更新 state.selection = ...
}
```

#### 依赖注入测试示例

```typescript
// 完整的测试代码

import { describe, test, expect, vi } from 'vitest'
import { reactive } from 'vue'
import { useMarkdown } from './useMarkdown'
import type { UseSelectionReturn, UseHistoryReturn } from './types'

describe('useMarkdown - 依赖注入测试', () => {
  test('应用加粗格式时应该调用正确的依赖方法', () => {
    // 1. 准备 Mock 依赖
    const mockSelection: UseSelectionReturn = {
      getSelection: vi.fn(() => ({
        start: 0,
        end: 5,
        selectedText: 'hello',
        isEmpty: false
      })),
      wrapSelection: vi.fn(),
      replaceRange: vi.fn(),
      setCursor: vi.fn(),
      // ... 其他方法
    }

    const mockHistory: UseHistoryReturn = {
      addTransaction: vi.fn(),
      undo: vi.fn(),
      redo: vi.fn(),
      // ...
    }

    const mockState = reactive({
      content: 'hello world',
      selection: { start: 0, end: 0, selectedText: '', isEmpty: true }
    })

    // 2. 注入 Mock 依赖
    const markdown = useMarkdown(mockState, mockSelection, mockHistory)

    // 3. 执行操作
    markdown.applyFormat('bold')

    // 4. 验证调用
    expect(mockSelection.getSelection).toHaveBeenCalled()
    expect(mockSelection.wrapSelection).toHaveBeenCalledWith('**', '**')
    expect(mockHistory.addTransaction).toHaveBeenCalled()
  })

  test('选中文本为空时不应该执行格式化', () => {
    const mockSelection: UseSelectionReturn = {
      getSelection: vi.fn(() => ({
        start: 0,
        end: 0,
        selectedText: '',
        isEmpty: true  // 空选区
      })),
      wrapSelection: vi.fn(),
      // ...
    }

    const markdown = useMarkdown(mockState, mockSelection, mockHistory)
    markdown.applyFormat('bold')

    // 验证 wrapSelection 没有被调用
    expect(mockSelection.wrapSelection).not.toHaveBeenCalled()
  })
})
```

---

## ⚖️ Composable vs Pinia

### 核心区别

| 维度             | Composable | Pinia             |
| -------------- | ---------- | ----------------- |
| **定位**         | 逻辑复用       | 全局状态管理            |
| **作用域**        | 组件级/模块级    | 应用级               |
| **状态共享**       | 显式传递或依赖注入  | 全局单例              |
| **生命周期**       | 随组件/调用创建销毁 | 应用生命周期            |
| **DevTools**   | ❌ 无专用工具    | ✅ Vue DevTools 支持 |
| **持久化**        | 需要自己实现     | ✅ 插件支持            |
| **SSR**        | 需要手动处理     | ✅ 原生支持            |
| **TypeScript** | ✅ 完美       | ✅ 完美              |

### 使用场景对比

#### Composable 适用场景

```typescript
// ✅ 场景 1: 封装可复用的 UI 逻辑
export function useModal() {
  const isOpen = ref(false)
  const open = () => isOpen.value = true
  const close = () => isOpen.value = false

  return { isOpen, open, close }
}

// 每个组件都有独立的 modal 状态
const modal1 = useModal()
const modal2 = useModal()

// ✅ 场景 2: 封装业务逻辑
export function useMarkdown(state, selection, history) {
  // 编辑器相关的业务逻辑
  const applyFormat = (action) => { ... }
  return { applyFormat }
}

// ✅ 场景 3: 封装底层能力
export function useDebounce(fn, delay) {
  let timer = null
  return (...args) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }
}
```

#### Pinia 适用场景

```typescript
// ✅ 场景 1: 全局用户状态
export const useUserStore = defineStore('user', () => {
  const userInfo = ref<User | null>(null)
  const isLoggedIn = computed(() => !!userInfo.value)

  const login = async (credentials) => {
    const user = await api.login(credentials)
    userInfo.value = user
  }

  const logout = () => {
    userInfo.value = null
  }

  return { userInfo, isLoggedIn, login, logout }
})

// 全应用共享同一个用户状态

// ✅ 场景 2: 购物车状态
export const useCartStore = defineStore('cart', () => {
  const items = ref<CartItem[]>([])
  const total = computed(() => items.value.reduce((sum, item) => sum + item.price, 0))

  const addItem = (item) => items.value.push(item)
  const removeItem = (id) => items.value = items.value.filter(i => i.id !== id)

  return { items, total, addItem, removeItem }
})
```

### 组合使用示例

Composable 和 Pinia 可以**协同工作**：

```typescript
// 📁 stores/editor.ts - Pinia Store（全局状态）
export const useEditorStore = defineStore('editor', () => {
  const documents = ref<Document[]>([])
  const currentDocId = ref<string | null>(null)

  const currentDoc = computed(() =>
    documents.value.find(d => d.id === currentDocId.value)
  )

  const saveDocument = async (doc: Document) => {
    await api.saveDocument(doc)
    // ...
  }

  return { documents, currentDoc, saveDocument }
})

// 📁 composables/useMarkdownEditor.ts - Composable（组件逻辑）
export function useMarkdownEditor(config: EditorConfig) {
  const editorStore = useEditorStore()  // ✅ 使用 Pinia Store

  const state = reactive<EditorState>({ ... })
  const editorRef = ref<HTMLDivElement | null>(null)

  const selectionModule = useSelection(editorRef, state)
  const markdown = useMarkdown(state, selectionModule, history)

  // 保存到全局 Store
  const save = async () => {
    await editorStore.saveDocument({
      id: config.id,
      content: state.content,
      title: state.title
    })
  }

  return { state, editorRef, markdown, save }
}

// 📁 EditorComponent.vue - 组件中使用
<script setup>
const editorStore = useEditorStore()  // 全局状态
const { state, markdown, save } = useMarkdownEditor({
  id: editorStore.currentDoc.id,
  content: editorStore.currentDoc.content
})  // 组件逻辑
</script>
```

---

## 🎯 使用场景建议

### 决策树

```
需要状态管理吗？
  ├─ 否 → 使用普通函数工具（utils）
  └─ 是 ↓

状态需要跨组件共享吗？
  ├─ 否 → 使用 Composable
  │        └─ 例：useModal, useForm, useDebounce
  └─ 是 ↓

状态需要全局共享吗？（多个页面都要用）
  ├─ 是 → 使用 Pinia
  │        └─ 例：useUserStore, useCartStore, useSettingsStore
  └─ 否 ↓

状态需要在父子组件间共享吗？
  ├─ 是 → 使用 provide/inject 或 props/emit
  └─ 否 → 使用 Composable（组件内部逻辑）
```

### 实际场景举例

| 场景 | 推荐方案 | 理由 |
|------|---------|------|
| **用户登录状态** | Pinia | 全应用共享，需要持久化 |
| **模态框开关** | Composable | 组件级状态，不需要共享 |
| **表单验证** | Composable | 可复用逻辑，每个表单独立 |
| **购物车** | Pinia | 跨页面共享，需要持久化 |
| **防抖/节流** | Composable | 通用工具，无状态共享需求 |
| **主题切换** | Pinia | 全局配置，需要持久化 |
| **编辑器逻辑** | Composable | 复杂业务逻辑，多实例 |
| **路由状态** | Vue Router | 专用路由管理 |

---

## 💡 最佳实践

### 1. 命名规范

```typescript
// ✅ 好的命名
export function useMousePosition() { ... }  // use + 功能描述
export function useDebounce() { ... }
export function useMarkdown() { ... }

// ❌ 不好的命名
export function mousePosition() { ... }  // 缺少 use 前缀
export function markdown() { ... }
export function helper() { ... }  // 命名不明确
```

### 2. 返回值规范

```typescript
// ✅ 返回对象（可解构）
export function useCounter() {
  const count = ref(0)
  const increment = () => count.value++

  return { count, increment }  // 可按需解构
}

// 使用
const { count } = useCounter()  // 只取需要的

// ❌ 返回数组（顺序固定）
export function useCounter() {
  const count = ref(0)
  const increment = () => count.value++

  return [count, increment]  // 必须按顺序
}

// 使用
const [count, increment] = useCounter()  // 顺序不能错
```

### 3. 参数设计

```typescript
// ✅ 使用对象参数（可扩展）
export function useMarkdownEditor(config: {
  content?: string
  autoSave?: boolean
  onSave?: (content: string) => void
}) {
  // ...
}

// ❌ 多个位置参数（难以扩展）
export function useMarkdownEditor(
  content: string,
  autoSave: boolean,
  onSave: (content: string) => void
) {
  // 新增参数会破坏兼容性
}
```

### 4. 副作用管理

```typescript
// ✅ 清理副作用
export function useEventListener(target, event, handler) {
  onMounted(() => {
    target.addEventListener(event, handler)
  })

  onUnmounted(() => {
    target.removeEventListener(event, handler)  // 清理
  })
}

// ❌ 忘记清理
export function useEventListener(target, event, handler) {
  onMounted(() => {
    target.addEventListener(event, handler)
  })
  // 内存泄漏！
}
```

### 5. TypeScript 类型定义

```typescript
// ✅ 导出返回类型
export function useSelection(
  editorElement: Ref<HTMLElement | null>,
  state: EditorState
) {
  // ...
  return { getSelection, replaceRange, wrapSelection }
}

// ✅ 导出类型供其他模块使用
export type UseSelectionReturn = ReturnType<typeof useSelection>

// 使用
function useMarkdown(
  state: EditorState,
  selection: UseSelectionReturn  // 类型清晰
) {
  // ...
}
```

### 6. 避免过度抽象

```typescript
// ❌ 过度抽象（没必要）
export function useNumber() {
  const value = ref(0)
  const setValue = (v) => value.value = v
  return { value, setValue }
}

// ✅ 直接使用 ref（更简单）
const value = ref(0)

// ✅ 有意义的抽象（封装了业务逻辑）
export function useCounter() {
  const count = ref(0)
  const increment = () => count.value++
  const decrement = () => count.value--
  const reset = () => count.value = 0

  return { count, increment, decrement, reset }
}
```

---

## 📚 参考资料

### 官方文档

- [Vue3 Composition API 官方文档](https://vuejs.org/guide/reusability/composables.html)
- [Pinia 官方文档](https://pinia.vuejs.org/)
- [VueUse - Composable 库](https://vueuse.org/)

### 推荐阅读

- 《Vue.js 设计与实现》- 霍春阳
- [Anthony Fu 的 Composable 设计分享](https://antfu.me/posts/composable-vue-vueday-2021)
- [Composable vs Pinia 对比文章](https://vueschool.io/articles/vuejs-tutorials/state-management-with-composition-api/)

### 进阶主题

- **Composable 的异步处理**：如何在 Composable 中处理 Promise 和错误
- **Composable 的性能优化**：避免不必要的响应式开销
- **Composable 的测试策略**：如何编写可测试的 Composable

---

## 🎓 总结

### 核心要点回顾

1. **闭包**：Composable 的核心机制，实现参数绑定和上下文封装
2. **依赖注入**：提高可测试性和灵活性
3. **分层架构**：协调层 → 业务逻辑层 → 工具层，职责清晰
4. **Composable vs Pinia**：前者用于逻辑复用，后者用于全局状态管理
5. **最佳实践**：命名规范、类型定义、副作用管理、避免过度抽象

### 学习建议

1. **理解闭包**：这是掌握 Composable 的关键
2. **实践依赖注入**：尝试编写可测试的 Composable
3. **分层思考**：设计 Composable 时考虑职责划分
4. **合理选择**：根据场景选择 Composable 还是 Pinia
5. **参考 VueUse**：学习优秀的 Composable 实现

---

**下一步学习**：
- 📖 阅读 VueUse 源码，学习高质量 Composable 的实现
- 🔧 尝试重构现有代码，提取可复用的 Composable
- 🧪 编写单元测试，验证依赖注入的价值
