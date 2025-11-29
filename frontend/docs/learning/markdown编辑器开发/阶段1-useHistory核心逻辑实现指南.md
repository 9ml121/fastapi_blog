# useHistory 核心逻辑实现指南

## 一、任务目标

在 `useHistory.ts` 中实现一个完整的历史记录管理系统，包含：

1. ✅ 状态定义（transactions, currentIndex）
2. ✅ `pushTransaction()` - 记录新操作
3. ✅ `undo()` - 撤销
4. ✅ `redo()` - 重做
5. ✅ `canUndo` / `canRedo` - 计算属性

---

## 二、文件结构框架

```typescript
import { reactive, computed } from 'vue'
import type { EditorState, EditTransaction } from '../types/editor'

export function useHistory(state: EditorState) {
  // 1️⃣ 内部状态定义
  // 2️⃣ 辅助函数
  // 3️⃣ 核心方法：pushTransaction
  // 4️⃣ 核心方法：undo
  // 5️⃣ 核心方法：redo
  // 6️⃣ 计算属性
  // 7️⃣ 返回 API
}

export type UseHistoryReturn = ReturnType<typeof useHistory>
```

---

## 三、详细实现步骤

### 步骤1: 定义内部状态 ✅

**目标**：创建一个响应式的历史栈。

```typescript
import { reactive, computed } from 'vue'
import type { EditorState, EditTransaction } from '../types/editor'

export function useHistory(state: EditorState) {
  // 1️⃣ 内部状态定义
  const historyState = reactive({
    transactions: [] as EditTransaction[], // 历史快照数组
    currentIndex: -1, // 当前指针位置
  })

  // ... 后续代码
}
```

**知识点讲解**：

- **为什么用 `reactive` 而不是 `ref`？**
  - `reactive` 适合管理对象，可以直接访问属性（`historyState.transactions`）
  - 如果用 `ref`，需要每次都写 `.value`（`historyState.value.transactions`）

- **为什么 `currentIndex = -1`？**
  - `-1` 表示初始状态，还没有任何操作
  - 第一次操作后会变成 `0`

---

### 步骤2: 实现辅助函数 `generateId()` ✅

**目标**：为每个 transaction 生成唯一 ID。

```typescript
// 2️⃣ 辅助函数
const generateId = (): string => {
  return `txn_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
}
```

**知识点讲解**：

- **为什么需要 ID？**
  - 方便调试，可以在控制台追踪每个操作
  - 未来可能用于更复杂的历史管理（比如分支历史）

- **ID 格式**：`txn_1701234567890_abc123`
  - `Date.now()`：时间戳，保证时间上唯一
  - `Math.random()`：随机字符串，保证同一时间的操作唯一

---

### 步骤3: 实现 `pushTransaction()` 🔥 核心

**目标**：记录新操作到历史栈。

```typescript
// 3️⃣ 核心方法：pushTransaction
const pushTransaction = (content: string, label: string = '未命名操作'): void => {
  // 第1步：创建新的 transaction 对象
  const newTransaction: EditTransaction = {
    id: generateId(),
    label,
    content, // ⚠️ 快照式：保存完整内容
    timestamp: Date.now(),
  }

  // 第2步：⚠️ 关键！丢弃 currentIndex 之后的所有历史
  // 原因：用户在历史中间做了新操作，未来的历史就失效了
  historyState.transactions = historyState.transactions.slice(0, historyState.currentIndex + 1)

  // 第3步：添加新 transaction 到栈顶
  historyState.transactions.push(newTransaction)

  // 第4步：指针移动到最新位置
  historyState.currentIndex = historyState.transactions.length - 1

  // 第5步：（可选）限制历史栈大小，避免内存爆炸
  const MAX_HISTORY_SIZE = 50
  if (historyState.transactions.length > MAX_HISTORY_SIZE) {
    // 删除最早的快照（FIFO 队列）
    historyState.transactions.shift()
    historyState.currentIndex--
  }
}
```

**重点理解：为什么要 `slice(0, currentIndex + 1)`？**

看这个例子：

```
初始状态：
transactions = [T0, T1, T2, T3, T4]
currentIndex = 2

用户撤销了2次（回到 T2），然后做了新操作 T_new：

=== 执行前 ===
transactions = [T0, T1, T2, T3, T4]
                        ↑
                   currentIndex = 2

=== slice(0, 3) ===
transactions = [T0, T1, T2]  // T3 和 T4 被丢弃了！

=== push(T_new) ===
transactions = [T0, T1, T2, T_new]
                             ↑
                        currentIndex = 3
```

**为什么要丢弃 T3 和 T4？**

- 因为历史已经被改变了！
- 如果保留 T3 和 T4，用户重做时会回到"另一个平行宇宙"的状态，这是不合理的。

---

### 步骤4: 实现 `undo()` ⬅️ 撤销

**目标**：回到上一个历史状态。

```typescript
// 4️⃣ 核心方法：undo
const undo = (): string | null => {
  // 第1步：检查是否可以撤销
  if (historyState.currentIndex < 0) {
    console.warn('[useHistory] 无法撤销：已经在初始状态')
    return null
  }

  // 第2步：指针后退
  historyState.currentIndex--

  // 第3步：返回新的内容
  if (historyState.currentIndex === -1) {
    // 回到初始空白状态
    console.log('[useHistory] 撤销到初始状态')
    return ''
  } else {
    // 返回指针位置的快照内容
    const targetTransaction = historyState.transactions[historyState.currentIndex]
    console.log(`[useHistory] 撤销到: ${targetTransaction.label}`)
    return targetTransaction.content
  }
}
```

**状态变化示意**：

```
=== 撤销前 ===
transactions = [T0, T1, T2, T3]
currentIndex = 3  (当前在 T3)

=== 执行 undo() ===
currentIndex--  →  currentIndex = 2

=== 返回 ===
return transactions[2].content  (返回 T2 的内容)
```

**边界情况**：

- `currentIndex = 0` 时调用 `undo()` → 回到初始空白（`currentIndex = -1`，返回 `''`）
- `currentIndex = -1` 时调用 `undo()` → 返回 `null`（无法撤销）

---

### 步骤5: 实现 `redo()` ➡️ 重做

**目标**：前进到下一个历史状态。

```typescript
// 5️⃣ 核心方法：redo
const redo = (): string | null => {
  // 第1步：检查是否可以重做
  if (historyState.currentIndex >= historyState.transactions.length - 1) {
    console.warn('[useHistory] 无法重做：已经在最新状态')
    return null
  }

  // 第2步：指针前进
  historyState.currentIndex++

  // 第3步：返回新的内容
  const targetTransaction = historyState.transactions[historyState.currentIndex]
  console.log(`[useHistory] 重做到: ${targetTransaction.label}`)
  return targetTransaction.content
}
```

**状态变化示意**：

```
=== 重做前 ===
transactions = [T0, T1, T2, T3]
currentIndex = 1  (当前在 T1)

=== 执行 redo() ===
currentIndex++  →  currentIndex = 2

=== 返回 ===
return transactions[2].content  (返回 T2 的内容)
```

**边界情况**：

- `currentIndex = 2`，`transactions.length = 3` 时调用 `redo()` → 返回 `null`（无法重做）

---

### 步骤6: 实现计算属性 `canUndo` / `canRedo` ✅

**目标**：实时判断当前是否可以撤销/重做。

```typescript
// 6️⃣ 计算属性
const canUndo = computed(() => {
  return historyState.currentIndex >= 0
})

const canRedo = computed(() => {
  return historyState.currentIndex < historyState.transactions.length - 1
})
```

**知识点讲解**：

- **为什么用 `computed` 而不是普通函数？**
  - `computed` 会自动缓存结果，只有依赖变化时才重新计算
  - 提高性能，避免重复计算

- **使用场景**：
  ```vue
  <!-- 工具栏中的撤销按钮 -->
  <button :disabled="!canUndo">撤销</button>
  <button :disabled="!canRedo">重做</button>
  ```

---

### 步骤7: 返回 API ✅

**目标**：暴露所有方法和状态给外部使用。

```typescript
// 7️⃣ 返回 API
return {
  // 方法
  pushTransaction,
  undo,
  redo,

  // 计算属性
  canUndo,
  canRedo,

  // 调试用（可选）
  getHistory: () => ({
    transactions: historyState.transactions,
    currentIndex: historyState.currentIndex,
  }),
}
```

**最终导出类型**：

```typescript
export type UseHistoryReturn = ReturnType<typeof useHistory>
```

---

## 四、完整代码示例

```typescript
import { reactive, computed } from 'vue'
import type { EditorState, EditTransaction } from '../types/editor'

export function useHistory(state: EditorState) {
  // 1️⃣ 内部状态定义
  const historyState = reactive({
    transactions: [] as EditTransaction[],
    currentIndex: -1,
  })

  // 2️⃣ 辅助函数
  const generateId = (): string => {
    return `txn_${Date.now()}_${Math.random().toString(36).substring(2, 9)}`
  }

  // 3️⃣ 核心方法：pushTransaction
  const pushTransaction = (content: string, label: string = '未命名操作'): void => {
    const newTransaction: EditTransaction = {
      id: generateId(),
      label,
      content,
      timestamp: Date.now(),
    }

    historyState.transactions = historyState.transactions.slice(0, historyState.currentIndex + 1)
    historyState.transactions.push(newTransaction)
    historyState.currentIndex = historyState.transactions.length - 1

    const MAX_HISTORY_SIZE = 50
    if (historyState.transactions.length > MAX_HISTORY_SIZE) {
      historyState.transactions.shift()
      historyState.currentIndex--
    }
  }

  // 4️⃣ 核心方法：undo
  const undo = (): string | null => {
    if (historyState.currentIndex < 0) {
      console.warn('[useHistory] 无法撤销：已经在初始状态')
      return null
    }

    historyState.currentIndex--

    if (historyState.currentIndex === -1) {
      console.log('[useHistory] 撤销到初始状态')
      return ''
    } else {
      const targetTransaction = historyState.transactions[historyState.currentIndex]
      console.log(`[useHistory] 撤销到: ${targetTransaction.label}`)
      return targetTransaction.content
    }
  }

  // 5️⃣ 核心方法：redo
  const redo = (): string | null => {
    if (historyState.currentIndex >= historyState.transactions.length - 1) {
      console.warn('[useHistory] 无法重做：已经在最新状态')
      return null
    }

    historyState.currentIndex++
    const targetTransaction = historyState.transactions[historyState.currentIndex]
    console.log(`[useHistory] 重做到: ${targetTransaction.label}`)
    return targetTransaction.content
  }

  // 6️⃣ 计算属性
  const canUndo = computed(() => {
    return historyState.currentIndex >= 0
  })

  const canRedo = computed(() => {
    return historyState.currentIndex < historyState.transactions.length - 1
  })

  // 7️⃣ 返回 API
  return {
    pushTransaction,
    undo,
    redo,
    canUndo,
    canRedo,
    getHistory: () => ({
      transactions: historyState.transactions,
      currentIndex: historyState.currentIndex,
    }),
  }
}

export type UseHistoryReturn = ReturnType<typeof useHistory>
```

---

## 五、测试建议

在实现后，你可以在浏览器控制台手动测试：

```javascript
// 假设你在 EditorContent 中暴露了 history
const history = editorContentRef.value

// 测试1: 记录3个操作
history.pushTransaction('内容1', '操作1')
history.pushTransaction('内容2', '操作2')
history.pushTransaction('内容3', '操作3')

console.log(history.getHistory())
// 应该看到 transactions 有3个元素，currentIndex = 2

// 测试2: 撤销
console.log(history.undo()) // 应该返回 '内容2'
console.log(history.undo()) // 应该返回 '内容1'
console.log(history.canRedo.value) // 应该是 true

// 测试3: 重做
console.log(history.redo()) // 应该返回 '内容2'

// 测试4: 在中间状态做新操作（丢弃未来）
history.pushTransaction('新内容', '新操作')
console.log(history.canRedo.value) // 应该是 false（未来被丢弃了）
```

---

## 六、编码清单 ✅

- [ ] 导入必要的类型和函数（`reactive`, `computed`, `EditTransaction`）
- [ ] 定义 `historyState` 响应式状态
- [ ] 实现 `generateId()` 辅助函数
- [ ] 实现 `pushTransaction()` 方法
- [ ] 实现 `undo()` 方法
- [ ] 实现 `redo()` 方法
- [ ] 实现 `canUndo` 计算属性
- [ ] 实现 `canRedo` 计算属性
- [ ] 返回完整 API 对象
- [ ] 导出 `UseHistoryReturn` 类型

---

## 七、常见问题

### Q1: `EditTransaction` 类型在哪定义？

**A**: 在 `types/editor.ts` 中已经定义，直接导入即可：

```typescript
import type { EditTransaction } from '../types/editor'
```

### Q2: 为什么要传入 `state: EditorState` 参数？

**A**: 虽然当前版本的快照式方案不需要直接修改 `state`，但为了未来扩展（比如自动同步 `state.canUndo`），保留这个参数是好的设计。

### Q3: 控制台的 `console.log` 需要保留吗？

**A**: 建议保留，方便调试。如果担心性能，可以用条件编译：

```typescript
if (import.meta.env.DEV) {
  console.log('[useHistory] 撤销到:', targetTransaction.label)
}
```

---

## 八、下一步

完成编码后，**不要急着集成！** 先在这个文件内部做单元测试，确保逻辑正确。

准备好后告诉我，我会指导你进行**阶段2：集成到 EditorContent**。

加油！💪
