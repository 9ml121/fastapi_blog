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

基于 **Vue 3 官方文档**和 **VueUse 最佳实践**，我们遵循以下设计原则：

#### 🎯 原则 1：单一职责原则（Single Responsibility Principle）

**定义**：每个 Composable 只负责一个明确的功能域

**实践**：
- ✅ `useSelection`：只管理光标位置和文本选中，不涉及格式化逻辑
- ✅ `useHistory`：只管理撤销重做历史栈，不处理具体格式化
- ✅ `useMarkdown`：只处理 Markdown 格式化转换，不管理状态

**反模式**：
- ❌ 在 `useSelection` 中混入格式化逻辑
- ❌ 在 `useHistory` 中处理自动保存

**参考**：
- [Vue Composition API 最佳实践](https://vuejs.org/guide/reusability/composables.html#conventions-and-best-practices) - 官方推荐每个 composable 功能单一

---

#### 🎯 原则 2：状态所有权分层（State Ownership Hierarchy）

**定义**：根据 Composable 的职责类型，决定状态管理方式

| Composable 类型 | 状态管理 | 本项目实例 | 理由 |
|----------------|---------|-----------|------|
| **工具函数层** | 无状态 / 接收依赖 | `useSelection`、`useMarkdown` | 状态存在于浏览器 API 或外部，不需要重复维护 |
| **功能模块层** | 自己创建状态 | `useHistory`、`useAutoSave` | 状态高度独立，生命周期与模块一致 |
| **业务协调层** | 自己创建 + 聚合子状态 | `useMarkdownEditor` | 负责整合各子模块状态 |

**实践**：

```typescript
// ✅ 正确：useSelection 无状态（工具函数）
export function useSelection(editorElement: Ref<HTMLElement | null>) {
  // 不创建状态，直接读取浏览器 Selection API
  const getSelectionInfo = () => {
    const sel = window.getSelection()  // 状态存在于浏览器
    return { start, end, selectedText }
  }
  return { getSelectionInfo, setCursor, ... }
}

// ✅ 正确：useHistory 自己创建状态（功能模块）
export function useHistory() {
  // 内部创建状态，因为历史栈是模块私有的
  const historyState = reactive<EditorHistory>({
    transactions: [],
    currentIndex: -1,
  })

  // 对外暴露只读状态
  return {
    state: readonly(historyState),  // ⚠️ 关键：只读暴露
    pushTransaction,
    undo,
    redo,
  }
}

// ❌ 错误：强制所有 composable 接收外部状态
export function useHistory(state: EditorState) {
  // 这样做会导致状态耦合，降低可复用性
}
```

**关键要点**：
- **无状态优先**：能不创建状态就不创建（如 `useSelection`）
- **状态必要时内部创建**：功能模块的状态应该内部管理（如 `useHistory`）
- **对外只读暴露**：使用 `readonly()` 防止外部直接修改
- **配置通过参数注入**：行为配置通过参数传递，而非硬编码

**参考**：
- [Vue Composables - State Management](https://vuejs.org/guide/reusability/composables.html#state-management) - 官方说明何时创建内部状态
- [VueUse Design Philosophy](https://vueuse.org/guide/#design-philosophy) - 知名库的设计哲学

---

#### 🎯 原则 3：依赖注入与可测试性（Dependency Injection）

**定义**：Composable 之间通过参数传递依赖，而非硬编码耦合

**实践**：

```typescript
// ✅ 正确：useMarkdown 接收依赖（依赖注入）
export function useMarkdown(selectionAPI: UseSelectionReturn) {
  const toggleInlineFormat = (action: InlineFormatType) => {
    // 使用注入的依赖，而非直接调用 window.getSelection()
    const { start, end } = selectionAPI.getSelectionInfo()
    selectionAPI.replaceRange(start, end, newText)
  }
  return { toggleInlineFormat, ... }
}

// ❌ 错误：硬编码依赖（难以测试）
export function useMarkdown() {
  const toggleInlineFormat = (action: InlineFormatType) => {
    // 直接依赖全局状态，无法在测试中 mock
    const sel = window.getSelection()
  }
}
```

**测试友好性**：

```typescript
// 测试时可以轻松 mock 依赖
const mockSelection = {
  getSelectionInfo: () => ({ start: 0, end: 5, selectedText: 'hello' }),
  replaceRange: vi.fn(),
}

const { toggleInlineFormat } = useMarkdown(mockSelection)
toggleInlineFormat('bold')

expect(mockSelection.replaceRange).toHaveBeenCalledWith(0, 5, '**hello**')
```

**参考**：
- [Testing Composables](https://vuejs.org/guide/scaling-up/testing.html#testing-composables) - Vue 官方测试指南
- [Vitest Best Practices](https://vitest.dev/guide/best-practices.html) - 依赖注入测试模式

---

#### 🎯 原则 4：封装性与最小权限（Encapsulation & Least Privilege）

**定义**：对外只暴露必要的接口，内部状态使用 `readonly()` 保护

**实践**：

```typescript
export function useHistory() {
  // 内部状态（私有）
  const historyState = reactive<EditorHistory>({
    transactions: [],
    currentIndex: -1,
  })

  return {
    // ✅ 对外只读（防止外部直接修改）
    state: readonly(historyState),

    // ✅ 提供方法接口（受控修改）
    pushTransaction: (content: string) => {
      // 内部逻辑保证数据一致性
      historyState.transactions.push(...)
      historyState.currentIndex++
    },

    // ✅ 调试接口（可选）
    getHistoryInfo: () => ({
      transactions: historyState.transactions,  // 返回引用（响应式）
      currentIndex: historyState.currentIndex,
    }),
  }
}
```

**安全性对比**：

| 暴露方式 | 响应式 | 可修改 | 类型安全 | 推荐 |
|---------|-------|--------|---------|-----|
| `historyState` 原始对象 | ✅ | ❌ 可以（危险） | ❌ | 🚫 |
| `readonly(historyState)` | ✅ | ✅ 不可以 | ✅ | ⭐⭐⭐ |
| `getHistoryInfo()` 方法 | ❌ | ✅ 不可以 | ✅ | ⭐⭐ |

**参考**：
- [Vue Reactivity API - readonly()](https://vuejs.org/api/reactivity-core.html#readonly) - 官方 API 文档
- [TypeScript Handbook - readonly](https://www.typescriptlang.org/docs/handbook/2/objects.html#readonly-properties) - 类型层保护

---

#### 🎯 原则 5：渐进式功能与可组合性（Progressive Enhancement）

**定义**：Composable 可以独立使用，也可以组合使用

**实践**：

```typescript
// 场景1：独立使用 useSelection
const editorRef = ref<HTMLDivElement>(null)
const { getSelectionInfo, setCursor } = useSelection(editorRef)

// 场景2：组合使用
const selectionAPI = useSelection(editorRef)
const markdownAPI = useMarkdown(selectionAPI)  // 依赖 useSelection

// 场景3：完整集成
const editorAPI = useMarkdownEditor(editorRef)  // 内部整合所有子模块
```

**设计检查清单**：
- ✅ 每个 composable 可以脱离其他模块单独测试
- ✅ 依赖关系清晰（通过参数声明）
- ✅ 不依赖全局状态或单例

**参考**：
- [Composable Composition Patterns](https://vuejs.org/guide/reusability/composables.html#composition) - 组合模式指南

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

### 📚 参考资料与延伸阅读

本设计文档基于以下行业最佳实践和官方文档：

#### **Vue 3 官方文档**

1. **[Composables Guide](https://vuejs.org/guide/reusability/composables.html)**
   - Vue 3 组合式函数官方指南
   - 涵盖命名规范、状态管理、副作用处理等核心原则
   - **关键章节**：
     - [What is a Composable?](https://vuejs.org/guide/reusability/composables.html#what-is-a-composable)
     - [State Management in Composables](https://vuejs.org/guide/reusability/composables.html#state-management)
     - [Conventions and Best Practices](https://vuejs.org/guide/reusability/composables.html#conventions-and-best-practices)

2. **[Reactivity API - readonly()](https://vuejs.org/api/reactivity-core.html#readonly)**
   - `readonly()` API 详细说明
   - 用于实现状态的只读暴露（原则 4）

3. **[Composition API FAQ](https://vuejs.org/guide/extras/composition-api-faq.html)**
   - 组合式 API 常见问题
   - 为什么选择 Composition API 而非 Options API

4. **[Testing Composables](https://vuejs.org/guide/scaling-up/testing.html#testing-composables)**
   - 官方测试指南
   - 如何使用依赖注入模式提高可测试性（原则 3）

---

#### **VueUse - 行业标杆 Composable 库**

5. **[VueUse 设计哲学](https://vueuse.org/guide/#design-philosophy)**
   - 1000+ star 的 Vue 组合式函数库
   - 展示了生产级 composable 的设计模式
   - **核心理念**：无状态优先、SSR 友好、Tree-shakable

6. **VueUse 实际案例学习**：
   - [`useClipboard`](https://vueuse.org/core/useClipboard/) - 无状态工具函数示例
   - [`useLocalStorage`](https://vueuse.org/core/useLocalStorage/) - 带状态的功能模块示例
   - [`useDebounceFn`](https://vueuse.org/shared/useDebounceFn/) - 依赖注入模式示例

---

#### **TypeScript 最佳实践**

7. **[TypeScript Handbook - readonly](https://www.typescriptlang.org/docs/handbook/2/objects.html#readonly-properties)**
   - TypeScript 只读属性
   - 类型层的封装保护（配合 Vue 的 `readonly()` 使用）

8. **[Effective TypeScript](https://effectivetypescript.com/)**（书籍）
   - Item 7: Think of Types as Sets of Values
   - Item 14: Use Type Operations and Generics to Avoid Repeating Yourself

---

#### **测试最佳实践**

9. **[Vitest Best Practices](https://vitest.dev/guide/best-practices.html)**
   - Vue 生态推荐的测试框架
   - 依赖注入测试模式

10. **[Testing Library Philosophy](https://testing-library.com/docs/guiding-principles/)**
    - "测试应该尽可能接近实际用户使用方式"
    - 适用于 Composable 的集成测试

---

#### **软件工程原则**

11. **[SOLID 原则](https://en.wikipedia.org/wiki/SOLID)**
    - **S**ingle Responsibility Principle（单一职责）→ 原则 1
    - **D**ependency Inversion Principle（依赖倒置）→ 原则 3

12. **[Principle of Least Privilege](https://en.wikipedia.org/wiki/Principle_of_least_privilege)**
    - 最小权限原则 → 原则 4（只读暴露）

---

#### **编辑器架构参考**

13. **[ProseMirror Architecture](https://prosemirror.net/docs/guide/)**
    - 现代富文本编辑器的架构参考
    - Transaction-based editing（事务化编辑）
    - 本项目的 `EditTransaction` 设计受其启发

14. **[Slate.js Design Principles](https://docs.slatejs.org/concepts/02-nodes)**
    - 另一个知名编辑器框架
    - Immutable data structures（不可变数据结构）

---

#### **行业案例学习**

15. **[Notion 编辑器技术博客](https://www.notion.so/blog/topic/tech)**
    - Block-based editing 架构
    - Real-time collaboration 实现

16. **[CodeMirror 6 Architecture](https://codemirror.net/docs/guide/)**
    - 代码编辑器的状态管理
    - Extension system 设计

---

### 📝 设计决策记录（ADR）

**为什么 `useHistory` 自己创建状态？**
- ✅ 历史栈是模块私有的，外部不需要直接访问
- ✅ 生命周期与 composable 一致，不需要外部管理
- ✅ 降低耦合，提高可复用性
- 📚 参考：Vue 官方 [State Management in Composables](https://vuejs.org/guide/reusability/composables.html#state-management)

**为什么 `useSelection` 不创建状态？**
- ✅ Selection 状态已存在于浏览器 API（`window.getSelection()`）
- ✅ 无需在 Vue 中重复维护，避免状态同步问题
- ✅ 符合"无状态优先"原则
- 📚 参考：VueUse [`useClipboard`](https://vueuse.org/core/useClipboard/) 类似设计

**为什么使用 `readonly()` 暴露状态？**
- ✅ 防止外部直接修改内部状态，保证数据一致性
- ✅ 保持响应式（可以 `watch`），但不可修改
- ✅ 编译时（TypeScript）+ 运行时（Vue Proxy）双重保护
- 📚 参考：Vue 官方 [readonly() API](https://vuejs.org/api/reactivity-core.html#readonly)

---

### 🔄 文档更新记录

| 版本 | 日期 | 修改内容 | 理由 |
|------|------|---------|------|
| 1.0 | 2024-01-XX | 初始版本 | - |
| 2.0 | 2025-12-02 | 重写"关键设计原则"章节 | 基于 Vue 3 官方最佳实践和 VueUse 设计哲学，修正状态管理方式 |
| 2.0 | 2025-12-02 | 新增"参考资料与延伸阅读"章节 | 提供权威来源，便于深入学习 |

---
