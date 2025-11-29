## 🔧 Composable 辅助函数架构设计

### 整体设计思路

Phase 1.2 的核心是**实现 5 个关键的 Composable**，将编辑器的复杂逻辑分层管理。这遵循了**单一职责原则**和**依赖注入模式**，使代码高度可测试和可维护。

```
编辑器系统依赖关系（分层）：

      ┌─────────────────────────────────┐
      │  useMarkdownEditor()            │  ← 第5层（协调层）
      │  主 Composable（对外接口）      │
      └────────┬────────────────────────┘
               │
      ┌────────┴─────────┬──────────────┬──────────────┐
      │                  │              │              │
      ▼                  ▼              ▼              ▼
  ┌─────────┐    ┌──────────┐    ┌──────────┐    ┌───────────┐
  │useHistory    │useSelection   │useMarkdown    │useAutoSave│ ← 第4层（功能层）
  │撤销重做  │     选中文本    │    格式化           │自动保存    │
  │事务管理  │     光标操作    │    Markdown        │混合方案    │
  └─────────┘    └──────────┘    └──────────┘    └───────────┘
      │              │              │              │
      └──────────────┴──────────────┴──────────────┘
             │
             ▼
      ┌────────────────────────────────┐
      │  EditorState (核心状态)         │  ← 第3层（状态层）
      │  4层状态架构                    │
      └────────────────────────────────┘
             │
             ▼
      ┌────────────────────────────────┐
      │  辅助工具函数                   │  ← 第2层（工具层）
      │  - historyUtils.ts            │
      │  - markdownUtils.ts           │
      │  - selectionUtils.ts          │
      └────────────────────────────────┘
             │
             ▼
      ┌────────────────────────────────┐
      │  TypeScript 类型系统            │  ← 第1层（基础层）
      │  - EditorState                │
      │  - EditTransaction            │
      │  - SelectionInfo              │
      └────────────────────────────────┘
```

### 5 个 Composable 的详细职责

#### 1️⃣ **useSelection** - 文本选中处理（基础层）

**目的**：管理编辑器中的光标位置和文本选中状态

**核心职责**：

```typescript
export function useSelection(
  editorRef: Ref<HTMLDivElement | null>,
  state: EditorState
) {
  // 获取当前选中的文本范围（start, end, selectedText）
  const getSelection = (): SelectionInfo => { ... }

  // 设置光标位置到指定位置
  const setCursor = (position: number): void => { ... }

  // 选中指定范围的文本
  const selectRange = (start: number, end: number): void => { ... }

  // 包裹选中文本（加粗、斜体等）
  const wrapSelection = (before: string, after: string): void => { ... }

  // 判断当前是否有文本被选中
  const hasSelection = (): boolean => { ... }

  // 获取光标所在行的内容
  const getCurrentLine = (): string => { ... }

  return { getSelection, setCursor, selectRange, wrapSelection, hasSelection, getCurrentLine }
}
```

**关键实现细节**：

- 使用浏览器 Selection API（getSelection()、getRangeAt()）
- 处理光标位置的字符偏移计算
- 支持跨越 DOM 节点的选中
- 更新 UI 层的 SelectionInfo 状态

**难度**：⭐⭐（基础，但需要理解 DOM Selection API）

---

#### 2️⃣ **useHistory** - 撤销重做（核心复杂）

**目的**：管理 EditTransaction 栈，支持撤销和重做操作

**核心职责**：

```typescript
export function useHistory(
  state: EditorState,
  config: EditorConfig
) {
  // 添加一个事务到历史栈
  const addTransaction = (tx: EditTransaction): void => { ... }

  // 执行撤销操作（回到上一个事务）
  const undo = (): void => { ... }

  // 执行重做操作（前进到下一个事务）
  const redo = (): void => { ... }

  // 检查是否可以撤销
  const canUndo = (): boolean => { ... }

  // 检查是否可以重做
  const canRedo = (): boolean => { ... }

  // 清空所有历史记录
  const clearHistory = (): void => { ... }

  // 获取历史栈信息（调试用）
  const getHistoryInfo = () => ({
    totalTransactions: number,
    currentIndex: number,
    canUndo: boolean,
    canRedo: boolean,
  })

  return { addTransaction, undo, redo, canUndo, canRedo, clearHistory, getHistoryInfo }
}
```

**核心算法**（重点！）：

```
撤销逻辑：
  currentIndex = 2 (处于 transaction[2] 之后)
  undo() → currentIndex = 1
  → 恢复到 transaction[1] 之后的状态

重做逻辑：
  currentIndex = 1
  redo() → currentIndex = 2
  → 重新应用 transaction[2]

执行新操作时：
  currentIndex = 1
  addTransaction(txNew)
  → 删除 transactions[2...] (之后的所有事务)
  → 添加新事务到末尾
  → currentIndex = 2
```

**关键设计点**：

- 事务必须是**原子的且可逆的**
- 需要存储操作前后的状态（for undo/redo）
- 历史栈大小有限制（防止内存泄漏）
- 新操作会**清空之后的重做历史**

**难度**：⭐⭐⭐（复杂的状态管理逻辑）

---

#### 3️⃣ **useMarkdown** - Markdown 格式化（中等）

**目的**：处理 Markdown 格式的应用，实现格式化操作

**核心职责**：

```typescript
export function useMarkdown(
  state: EditorState,
  selection: SelectionInfo,
  history: ReturnType<typeof useHistory>
) {
  // 应用浮动工具栏操作（加粗、斜体、链接等）
  const applyFormat = (action: FloatingActionType): void => { ... }

  // 插入块级元素（代码块、表格、标题等）
  const insertBlock = (action: BlockActionType, position?: number): void => { ... }

  // 将选中文本转换为 Markdown 语法
  const wrapWithMarkdown = (before: string, after: string): void => { ... }

  // 将 Markdown 内容转换为 HTML（用于预览）
  const markdownToHtml = (markdown: string): string => { ... }

  // 获取当前光标所在行的语法类型（用于判断是否已应用格式）
  const getCurrentFormat = (): { isBold: boolean; isItalic: boolean; ... } => { ... }

  return { applyFormat, insertBlock, wrapWithMarkdown, markdownToHtml, getCurrentFormat }
}
```

**核心实现示例**：

```typescript
// 应用加粗
applyFormat('bold') {
  const { selectedText, start, end } = selection.getSelection();
  if (!selectedText) return;

  // 检查是否已加粗（如果已加粗则取消）
  if (selectedText.startsWith('**') && selectedText.endsWith('**')) {
    // 移除加粗标记
    const unwrapped = selectedText.slice(2, -2);
    editor.replaceRange(start, end, unwrapped);
  } else {
    // 添加加粗标记
    const wrapped = `**${selectedText}**`;
    editor.replaceRange(start, end, wrapped);
  }

  // 记录事务到历史
  history.addTransaction({
    id: generateId(),
    label: `应用加粗`,
    actions: [{ type: 'format', content: wrapped, start, end }],
    timestamp: Date.now(),
  });
}
```


---

#### 4️⃣ **useAutoSave** - 自动保存（异步处理）

**目的**：实现混合方案的本地+服务器自动保存

**核心职责**：

```typescript
export function useAutoSave(
  state: EditorState,
  config: EditorConfig
) {
  // 保存到 localStorage（同步、快速）
  const saveLocal = (): void => { ... }

  // 保存到服务器（异步、带重试）
  const saveToServer = (): Promise<void> => { ... }

  // 启动自动保存定时器
  const startAutoSave = (): void => { ... }

  // 停止自动保存定时器
  const stopAutoSave = (): void => { ... }

  // 从 localStorage 恢复草稿
  const loadDraft = (): EditorState | null => { ... }

  // 清除本地草稿
  const clearDraft = (): void => { ... }

  // 手动保存（用户点击保存按钮时）
  const save = (): Promise<void> => { ... }

  return { saveLocal, saveToServer, startAutoSave, stopAutoSave, loadDraft, clearDraft, save }
}
```

**混合方案实现细节**：

```typescript
// 启动自动保存
startAutoSave() {
  // 方案A：仅本地保存
  if (config.autoSave?.storage === 'localStorage') {
    localInterval = setInterval(() => {
      saveLocal();  // 每 2秒保存一次（快速）
    }, 2000);
  }

  // 方案B：仅服务器保存
  if (config.autoSave?.storage === 'api') {
    apiInterval = setInterval(() => {
      saveToServer().catch(err => {
        // 失败记录错误，但不中断用户操作
        console.warn('服务器保存失败:', err);
      });
    }, 10000);  // 每 10秒保存一次（低频）
  }

  // 方案C：混合保存（推荐）
  if (config.autoSave?.storage === 'both') {
    // 本地：高频、同步
    localInterval = setInterval(() => {
      saveLocal();  // 2秒
    }, 2000);

    // 服务器：低频、异步
    apiInterval = setInterval(() => {
      saveToServer().catch(err => {
        // 服务器失败不影响用户，本地有备份
      });
    }, 10000);  // 10秒
  }

  // 页面卸载前强制保存
  window.addEventListener('beforeunload', () => {
    if (config.autoSave?.saveOnBeforeUnload !== false) {
      save();  // 同步保存，不能是异步
    }
  });
}
```

**错误处理和重试**：

```typescript
async saveToServer() {
  let retries = 0;
  const maxRetries = config.autoSave?.maxRetries ?? 3;
  const retryDelay = config.autoSave?.retryDelay ?? 1000;

  while (retries < maxRetries) {
    try {
      const response = await fetch(config.autoSave?.apiUrl, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          title: state.title,
          content: state.content,
          timestamp: Date.now(),
        }),
      });

      if (response.ok) {
        state.lastSaved = new Date();
        return;  // 成功
      }

      // 服务器错误，重试
      retries++;
      await sleep(retryDelay * retries);  // 指数退避
    } catch (error) {
      retries++;
      await sleep(retryDelay * retries);
    }
  }

  // 所有重试都失败，记录错误但不抛出
  console.error('自动保存失败，本地有备份');
}
```

**难度**：⭐⭐⭐（异步处理、重试逻辑、混合方案）

---

#### 5️⃣ **useMarkdownEditor** - 主 Composable（协调层）

**目的**：协调其他 4 个 Composable，暴露统一的编辑器 API

**核心职责**：

```typescript
export function useMarkdownEditor(config: EditorConfig) {
  // 1. 初始化状态
  const state = reactive<EditorState>({
    title: config.title ?? '',
    content: config.content ?? '',
    transactions: [],
    currentIndex: -1,
    selection: { start: 0, end: 0, selectedText: '', isEmpty: true },
    isSaving: false,
    isDirty: false,
    isFocused: false,
    hasError: false,
    canUndo: false,
    canRedo: false,
  })

  // 2. 初始化子 Composable
  const editorRef = ref<HTMLDivElement>(null)
  const history = useHistory(state, config)
  const selection = useSelection(editorRef, state)
  const markdown = useMarkdown(state, state.selection, history)
  const autoSave = useAutoSave(state, config)

  // 3. 暴露的公开 API（对外接口）

  // 内容操作
  const insertTransaction = (tx: EditTransaction) => {
    history.addTransaction(tx)
    state.isDirty = true
  }

  const undo = () => {
    history.undo()
    state.isDirty = true
  }

  const redo = () => {
    history.redo()
    state.isDirty = true
  }

  // 格式化操作
  const formatSelection = (action: FloatingActionType) => {
    markdown.applyFormat(action)
    state.isDirty = true
  }

  const insertContent = (action: BlockActionType, position?: number) => {
    markdown.insertBlock(action, position)
    state.isDirty = true
  }

  // 保存操作
  const save = async () => {
    try {
      state.isSaving = true
      await autoSave.save()
      state.isDirty = false
      state.lastSaved = new Date()
    } catch (error) {
      state.hasError = true
      state.error = {
        code: 'SAVE_ERROR',
        message: '保存失败',
        originalError: error as Error,
        timestamp: Date.now(),
        recoverable: true,
      }
    } finally {
      state.isSaving = false
    }
  }

  // 4. 生命周期
  onMounted(() => {
    // 从 localStorage 恢复草稿
    const draft = autoSave.loadDraft()
    if (draft) {
      state.content = draft.content
      state.title = draft.title
    }

    // 启动自动保存
    autoSave.startAutoSave()

    // 监听内容变化（debounce 500ms）
    watch(
      () => [state.content, state.title],
      debounce(() => {
        autoSave.saveLocal() // 保存草稿
      }, 500),
    )
  })

  onBeforeUnmount(() => {
    autoSave.stopAutoSave()
  })

  // 5. 返回暴露的 API
  return {
    // 状态（只读）
    state: readonly(state),

    // 操作方法
    insertTransaction,
    undo,
    redo,
    formatSelection,
    insertContent,
    save,

    // 工具方法
    getSelection: () => selection.getSelection(),
    setCursor: (pos: number) => selection.setCursor(pos),
    clearDraft: () => autoSave.clearDraft(),

    // 查询方法
    canUndo: () => history.canUndo(),
    canRedo: () => history.canRedo(),
  }
}
```

**难度**：⭐⭐（相对简单，主要是协调和暴露 API）

---

### 实现顺序和依赖关系

```
实现顺序（从下往上，底层优先）：

1️⃣ useSelection
   ├─ 依赖：EditorState, 浏览器 Selection API
   ├─ 被依赖：useMarkdown, useMarkdownEditor
   └─ 预期实现时间：2-3 小时

2️⃣ useHistory
   ├─ 依赖：EditorState, EditorConfig
   ├─ 被依赖：useMarkdown, useMarkdownEditor
   └─ 预期实现时间：4-5 小时（核心复杂）

3️⃣ useMarkdown
   ├─ 依赖：EditorState, SelectionInfo, useHistory
   ├─ 被依赖：useMarkdownEditor
   └─ 预期实现时间：3-4 小时

4️⃣ useAutoSave
   ├─ 依赖：EditorState, EditorConfig, HTTP client
   ├─ 被依赖：useMarkdownEditor
   └─ 预期实现时间：3-4 小时

5️⃣ useMarkdownEditor
   ├─ 依赖：所有以上 4 个 Composable
   ├─ 被依赖：UI 组件
   └─ 预期实现时间：2-3 小时（组装）

总计：约 14-19 小时（2-3 天开发）
```

---

### 关键设计原则

#### 🎯 原则 1：单一职责

- 每个 Composable 只负责**一个明确的功能域**
- 例如：useSelection 只管理选中状态，不涉及格式化逻辑

#### 🎯 原则 2：依赖注入

- 子 Composable 不创建自己的状态，接收外部的 state 和 config
- 这样便于测试和复用

#### 🎯 原则 3：可测试性

- 所有逻辑都是纯函数（除了副作用如 DOM 操作）
- 不依赖全局状态，易于单元测试

#### 🎯 原则 4：渐进式功能

- 可以独立使用任何一个 Composable
- 也可以通过 useMarkdownEditor 整合使用

---

### 测试策略

每个 Composable 都需要完整的单元测试：

```typescript
// __tests__/useSelection.spec.ts
describe('useSelection', () => {
  test('应该返回当前选中的文本范围', () => { ... });
  test('应该支持设置光标位置', () => { ... });
  test('应该支持包裹选中文本', () => { ... });
  // ...总计 8-10 个测试用例
});

// __tests__/useHistory.spec.ts
describe('useHistory', () => {
  test('应该添加事务到历史', () => { ... });
  test('撤销应该回到上一个状态', () => { ... });
  test('重做应该前进到下一个状态', () => { ... });
  test('新操作应该清空之后的重做历史', () => { ... });
  // ...总计 12-15 个测试用例（最复杂）
});

// ...其他 Composable 类似
```

**测试覆盖目标**：≥ 85%（重点是核心逻辑）

---
