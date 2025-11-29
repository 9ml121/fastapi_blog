## 🎓 深入理解：ReturnType 工具类型

### 什么是 ReturnType？

`ReturnType<T>` 是 TypeScript 内置的工具类型（Utility Type），用于**自动推断函数的返回值类型**。

### 为什么需要 ReturnType？

**问题场景**：手写返回类型容易出错

```typescript
// ❌ 不好的做法：手写类型定义（容易不一致）
interface UseSelectionReturn {
  getSelection: () => SelectionInfo
  setCursor: (position: number) => void
  wrapSelection: (before: string, after: string) => void
  // ... 9 个方法
}

export function useSelection(): UseSelectionReturn {
  // 实现...
  return {
    getSelection,
    setCursor,
    wrapSelection,
    // ... 假设你新增了 getTextAroundCursor 方法
    getTextAroundCursor  // ❌ 忘记在接口中添加，TypeScript 报错
  }
}

// 😰 问题：
// 1. 需要维护两份定义（接口 + 实现）
// 2. 新增方法容易遗漏更新接口
// 3. 修改返回值需要同时修改接口
```

**解决方案**：使用 ReturnType 自动推断

```typescript
// ✅ 好的做法：使用 ReturnType 自动推断
export function useSelection(
  editorElement: Ref<HTMLElement | null>,
  state: EditorState
) {
  // 实现...
  return {
    getSelection,
    setCursor,
    wrapSelection,
    getTextAroundCursor  // ✅ 新增方法，类型自动更新
  }
}

// ✅ 自动从函数推断类型
export type UseSelectionReturn = ReturnType<typeof useSelection>

// 🎉 好处：
// 1. 只需修改函数实现，类型自动同步
// 2. 不会出现类型和实现不一致
// 3. 符合 DRY（Don't Repeat Yourself）原则
```

---

### ReturnType 的原理

**TypeScript 内置定义**：

```typescript
// TypeScript 源码中的定义
type ReturnType<T extends (...args: any) => any> = 
  T extends (...args: any) => infer R ? R : any
```

**工作原理解析**：

```typescript
// 步骤 1: 接受一个函数类型 T
type ReturnType<T extends (...args: any) => any> = ...
//                ^^^^^^^^^^^^^^^^^^^^^^^^^^^
//                约束 T 必须是一个函数类型

// 步骤 2: 使用条件类型 + infer 推断返回值类型
T extends (...args: any) => infer R ? R : any
//                          ^^^^^
//                          infer R 表示"推断并命名返回值类型为 R"

// 步骤 3: 返回推断出的类型 R
```

**实际示例**：

```typescript
// 示例 1: 简单函数
function add(a: number, b: number) {
  return a + b
}

type AddReturn = ReturnType<typeof add>
// 推断过程：
// 1. typeof add → (a: number, b: number) => number
// 2. 提取返回值类型 → number
// 结果：AddReturn = number

// 示例 2: 复杂对象返回
function getUser() {
  return { 
    id: 1, 
    name: 'Alice',
    email: 'alice@example.com'
  }
}

type User = ReturnType<typeof getUser>
// 推断过程：
// 1. typeof getUser → () => { id: number; name: string; email: string }
// 2. 提取返回值类型 → { id: number; name: string; email: string }
// 结果：User = { id: number; name: string; email: string }

// 示例 3: Composable
function useCounter() {
  const count = ref(0)
  const increment = () => count.value++
  const decrement = () => count.value--
  
  return { count, increment, decrement }
}

type UseCounterReturn = ReturnType<typeof useCounter>
// 结果：
// {
//   count: Ref<number>
//   increment: () => void
//   decrement: () => void
// }
```

---

### ReturnType 的三大应用场景

#### 场景 1: 导出 Composable 的返回类型

```typescript
// useMarkdown.ts
export function useMarkdown(
  state: EditorState,
  selection: UseSelectionReturn,
  history: ReturnType<typeof useHistory>
) {
  const applyFormat = (action: FloatingActionType): void => { ... }
  const insertBlock = (action: BlockActionType): void => { ... }
  
  return { applyFormat, insertBlock }
}

// ✅ 导出返回类型供其他模块使用
export type UseMarkdownReturn = ReturnType<typeof useMarkdown>

// useMarkdownEditor.ts
import type { UseMarkdownReturn } from './useMarkdown'

export function useMarkdownEditor(config: EditorConfig) {
  // ✅ 明确声明类型
  const markdown: UseMarkdownReturn = useMarkdown(state, selection, history)
  
  return { markdown }
}
```

#### 场景 2: 函数参数类型声明（依赖注入）

```typescript
// useToolbar.ts
import type { UseMarkdownReturn } from './useMarkdown'

export function useToolbar(
  markdown: UseMarkdownReturn  // ✅ 清晰的参数类型
) {
  const handleBoldClick = () => {
    markdown.applyFormat('bold')  // ✅ 自动补全和类型检查
  }
  
  return { handleBoldClick }
}
```

#### 场景 3: 测试文件中的 Mock 对象

```typescript
// useMarkdown.spec.ts
import { describe, test, expect, vi } from 'vitest'
import type { UseMarkdownReturn } from './useMarkdown'

describe('useToolbar', () => {
  test('点击加粗按钮应该调用 applyFormat', () => {
    // ✅ 创建类型安全的 Mock 对象
    const mockMarkdown: UseMarkdownReturn = {
      applyFormat: vi.fn(),
      insertBlock: vi.fn(),
      wrapWithMarkdown: vi.fn(),
      markdownToHtml: vi.fn(),
      getCurrentFormat: vi.fn()
    }
    
    const toolbar = useToolbar(mockMarkdown)
    toolbar.handleBoldClick()
    
    // ✅ 验证调用
    expect(mockMarkdown.applyFormat).toHaveBeenCalledWith('bold')
  })
})
```

---

### ReturnType 的高级用法

#### 1. 结合其他工具类型使用

```typescript
// 获取函数参数类型
type Parameters<T> = T extends (...args: infer P) => any ? P : never

function greet(name: string, age: number) {
  return `Hello, ${name}! You are ${age} years old.`
}

type GreetParams = Parameters<typeof greet>
// 结果：[name: string, age: number]

type GreetReturn = ReturnType<typeof greet>
// 结果：string
```

#### 2. 提取 Promise 返回值类型

```typescript
async function fetchUser() {
  return { id: 1, name: 'Alice' }
}

type FetchUserReturn = ReturnType<typeof fetchUser>
// 结果：Promise<{ id: number; name: string }>

// 进一步提取 Promise 内部类型
type Awaited<T> = T extends Promise<infer U> ? U : T

type User = Awaited<FetchUserReturn>
// 结果：{ id: number; name: string }
```

#### 3. 条件类型组合

```typescript
// 自定义工具类型：如果函数返回 Promise，提取内部类型
type UnwrapPromise<T> = 
  ReturnType<T> extends Promise<infer U> ? U : ReturnType<T>

async function getNumber() {
  return 42
}

function getString() {
  return "hello"
}

type NumberType = UnwrapPromise<typeof getNumber>  // number
type StringType = UnwrapPromise<typeof getString>  // string
```

---

### ReturnType vs 手写类型对比表

| 维度 | 手写类型 | ReturnType |
|------|---------|-----------|
| **维护成本** | ❌ 高（需同步两处） | ✅ 低（自动推断） |
| **出错风险** | ❌ 容易不一致 | ✅ 始终一致 |
| **代码复用** | ❌ 类型和实现分离 | ✅ 单一真相源 |
| **IDE 支持** | ⚠️ 需手动更新 | ✅ 自动同步 |
| **重构安全** | ❌ 修改易遗漏 | ✅ 修改自动传播 |

---

### 最佳实践建议

1. **总是导出 Composable 的返回类型**
   ```typescript
   export type UseFooReturn = ReturnType<typeof useFoo>
   ```

2. **参数类型使用导出的类型**
   ```typescript
   function useBar(foo: UseFooReturn) { ... }
   ```

3. **测试中使用类型创建 Mock**
   ```typescript
   const mockFoo: UseFooReturn = { ... }
   ```

4. **避免手写重复类型定义**
   ```typescript
   // ❌ 不要这样
   interface UseFooReturn { ... }
   function useFoo(): UseFooReturn { ... }
   
   // ✅ 应该这样
   function useFoo() { ... }
   export type UseFooReturn = ReturnType<typeof useFoo>
   ```

---