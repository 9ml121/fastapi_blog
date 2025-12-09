# 阶段3：在 useMarkdown 中记录操作实现指南

## 一、任务目标

让格式化操作（加粗、标题、插入代码块等）能被记录到历史，实现真正可用的撤销/重做功能。

---

## 二、核心思路

### 当前问题

虽然你已经实现了快捷键（Ctrl+Z），但现在按下去**什么都不会发生**，因为：

```typescript
// 当前状态
historyAPI.undo() // 调用成功
historyState.transactions // ← 空数组！没有任何历史记录
```

**原因**：还没有任何地方调用 `pushTransaction()`。

### 解决方案

在每次格式化操作后，记录到历史：

```typescript
// 用户点击加粗按钮
applyInlineFormat('bold')  // 执行格式化
  ↓
replaceRange(start, end, newText)  // 修改内容
  ↓
historyAPI.pushTransaction(state.content, '应用加粗')  // ⚡️ 记录到历史
```

---

## 三、实现步骤

### 步骤1: 修改 useMarkdown 函数签名 ✅

**位置**：`useMarkdown.ts` 的函数定义

**现有代码**：

```typescript
export function useMarkdown(state: EditorState, selectionModule: UseSelectionReturn) {
  // ...
}
```

**修改后**：

```typescript
export function useMarkdown(
  state: EditorState,
  selectionModule: UseSelectionReturn,
  historyModule: UseHistoryReturn, // ⚡️ 新增参数
) {
  // ...
}
```

**知识点**：

- 我们需要传入 `historyModule`，这样才能调用 `pushTransaction()`
- `UseHistoryReturn` 类型已经在 `useHistory.ts` 中导出了

---

### 步骤2: 在 applyInlineFormat 中记录历史 🔥

**位置**：`useMarkdown.ts` 中的 `applyInlineFormat` 函数

**现有代码**：

```typescript
const applyInlineFormat = (action: InlineFormatType): void => {
  // ... 前面的逻辑 ...

  replaceRange(start, end, newText)

  // 重新选中格式化后的文本
  selectRange(start, start + newText.length)
  // todo: 记录到历史栈  ← 这行注释就是提示你要做这个！
}
```

**修改后**：

```typescript
const applyInlineFormat = (action: InlineFormatType): void => {
  // === Link 格式需要特殊处理 ===
  if (action === 'link') {
    handleLinkFormat(start, end, selectedText, isEmpty)
    // ⚡️ Link格式化后也要记录
    historyModule.pushTransaction(state.content, `应用${action}格式`)
    return
  }

  const { before, after } = formatMap[action]

  // === 场景1：空选区 → 插入标记，光标在中间 ===
  if (isEmpty) {
    insertText(before + after)
    setCursor(start + before.length)
    // ⚡️ 记录到历史
    historyModule.pushTransaction(state.content, `应用${action}格式`)
    return
  }

  // === 场景2：有选中 ===
  // ... 计算 newText ...

  replaceRange(start, end, newText)
  selectRange(start, start + newText.length)

  // ⚡️ 记录到历史（统一在这里记录）
  historyModule.pushTransaction(state.content, `应用${action}格式`)
}
```

**重点理解**：

#### 为什么要在多个地方调用？

```typescript
// ❌ 错误想法：只在最后统一记录
const applyInlineFormat = (action: InlineFormatType): void => {
  if (action === 'link') {
    handleLinkFormat(...)
    return  // ← 这里就返回了，后面的 pushTransaction 不会执行！
  }

  // ... 其他逻辑

  historyModule.pushTransaction(...)  // ← link 操作走不到这里
}

// ✅ 正确做法：每个分支都记录
if (action === 'link') {
  handleLinkFormat(...)
  historyModule.pushTransaction(...)  // ← link 的记录
  return
}

if (isEmpty) {
  insertText(...)
  historyModule.pushTransaction(...)  // ← 空选区的记录
  return
}

// 有选中的记录
historyModule.pushTransaction(...)
```

#### label 参数的作用

```typescript
pushTransaction(state.content, `应用${action}格式`)
//                              ^^^^^^^^^^^^^^^^^^^^
//                              这是调试信息，方便查看历史记录
```

**示例**：

- `应用bold格式`
- `应用italic格式`
- `应用heading1格式`

---

### 步骤3: 在 applyParagraphFormat 中记录历史 ✅

**位置**：`useMarkdown.ts` 中的 `applyParagraphFormat` 函数

**现有代码**：

```typescript
const applyParagraphFormat = (action: ParagraphFormatType): void => {
  // ... 前面的逻辑 ...

  // 6. 替换当前行
  replaceRange(lineStart, lineEnd, newLine)

  // 7. 设置新光标位置
  setCursor(newCursorPos)
}
```

**修改后**：

```typescript
const applyParagraphFormat = (action: ParagraphFormatType): void => {
  // ... 前面的逻辑 ...

  // 6. 替换当前行
  replaceRange(lineStart, lineEnd, newLine)

  // 7. 设置新光标位置
  setCursor(newCursorPos)

  // ⚡️ 8. 记录到历史
  historyModule.pushTransaction(state.content, `应用${action}格式`)
}
```

**简单吧？** 因为段落格式化没有分支，只需要在最后加一行。

---

### 步骤4: 在 insertBlock 中记录历史 ✅

**位置**：`useMarkdown.ts` 中的 `insertBlock` 函数

**现有代码**：

```typescript
const insertBlock = (action: BlockInsertType): void => {
  // ... 前面的逻辑 ...

  // 5. 替换空行
  replaceRange(lineStart, lineEnd, template)

  // 6. 设置光标或选区
  if (selectionStart !== null && selectionEnd !== null) {
    selectRange(selectionStart, selectionEnd)
  } else if (cursorPosition !== null) {
    setCursor(cursorPosition)
  }
}
```

**修改后**：

```typescript
const insertBlock = (action: BlockInsertType): void => {
  // ... 前面的逻辑 ...

  // 5. 替换空行
  replaceRange(lineStart, lineEnd, template)

  // 6. 设置光标或选区
  if (selectionStart !== null && selectionEnd !== null) {
    selectRange(selectionStart, selectionEnd)
  } else if (cursorPosition !== null) {
    setCursor(cursorPosition)
  }

  // ⚡️ 7. 记录到历史
  historyModule.pushTransaction(state.content, `插入${action}`)
}
```

---

### 步骤5: 修改 EditorContent.vue 中的调用 ✅

**位置**：`EditorContent.vue` 中的 composables 初始化

**现有代码**：

```typescript
// ======== 初始化 composables =========
const selectionAPI = useSelection(editorRef, editorState)
const markdownAPI = useMarkdown(editorState, selectionAPI)
const historyAPI = useHistory(editorState)
```

**修改后**：

```typescript
// ======== 初始化 composables =========
const selectionAPI = useSelection(editorRef, editorState)
const historyAPI = useHistory(editorState) // ⚡️ 移到上面，因为 useMarkdown 需要它
const markdownAPI = useMarkdown(editorState, selectionAPI, historyAPI) // ⚡️ 传入 historyAPI
```

**重点**：

- `historyAPI` 必须在 `markdownAPI` 之前初始化
- 因为 `useMarkdown` 需要 `historyAPI` 作为参数

---

## 四、完整的修改示例

### useMarkdown.ts 的修改

```typescript
import type { UseHistoryReturn } from './useHistory' // ⚡️ 1. 导入类型

export function useMarkdown(
  state: EditorState,
  selectionModule: UseSelectionReturn,
  historyModule: UseHistoryReturn, // ⚡️ 2. 新增参数
) {
  const { getSelectionInfo, replaceRange, insertText, setCursor, selectRange, getCurrentLineInfo } =
    selectionModule

  const applyInlineFormat = (action: InlineFormatType): void => {
    const formatMap: Record<InlineFormatType, { before: string; after: string }> = {
      bold: { before: '**', after: '**' },
      italic: { before: '*', after: '*' },
      code: { before: '`', after: '`' },
      highlight: { before: '==', after: '==' },
      link: { before: '[', after: '](url)' },
    }

    const { start, end, selectedText, isEmpty } = getSelectionInfo()

    // === Link 格式需要特殊处理 ===
    if (action === 'link') {
      handleLinkFormat(start, end, selectedText, isEmpty)
      historyModule.pushTransaction(state.content, `应用${action}格式`) // ⚡️ 记录
      return
    }

    const { before, after } = formatMap[action]

    // === 场景1：空选区 ===
    if (isEmpty) {
      insertText(before + after)
      setCursor(start + before.length)
      historyModule.pushTransaction(state.content, `应用${action}格式`) // ⚡️ 记录
      return
    }

    // === 场景2：有选中 ===
    const isFullyFormatted =
      selectedText.startsWith(before) &&
      selectedText.endsWith(after) &&
      selectedText.length > before.length + after.length

    let newText: string

    if (isFullyFormatted) {
      newText = selectedText.slice(before.length, -after.length)
    } else if (selectedText.includes(before)) {
      const cleanText = removeAllFormatMarkers(selectedText, before, after)
      newText = before + cleanText + after
    } else {
      newText = before + selectedText + after
    }

    replaceRange(start, end, newText)
    selectRange(start, start + newText.length)

    historyModule.pushTransaction(state.content, `应用${action}格式`) // ⚡️ 记录
  }

  const applyParagraphFormat = (action: ParagraphFormatType): void => {
    // ... 前面的逻辑不变 ...

    replaceRange(lineStart, lineEnd, newLine)
    setCursor(newCursorPos)

    historyModule.pushTransaction(state.content, `应用${action}格式`) // ⚡️ 记录
  }

  const insertBlock = (action: BlockInsertType): void => {
    // ... 前面的逻辑不变 ...

    replaceRange(lineStart, lineEnd, template)

    if (selectionStart !== null && selectionEnd !== null) {
      selectRange(selectionStart, selectionEnd)
    } else if (cursorPosition !== null) {
      setCursor(cursorPosition)
    }

    historyModule.pushTransaction(state.content, `插入${action}`) // ⚡️ 记录
  }

  return {
    applyInlineFormat,
    applyParagraphFormat,
    insertBlock,
  }
}
```

### EditorContent.vue 的修改

```typescript
// ======== 初始化 composables =========
const selectionAPI = useSelection(editorRef, editorState)
const historyAPI = useHistory(editorState) // ⚡️ 移到上面
const markdownAPI = useMarkdown(editorState, selectionAPI, historyAPI) // ⚡️ 传入 historyAPI
```

---

## 五、测试方法

完成后，在编辑器中测试：

### 测试1: 加粗操作

```
1. 输入 "测试文字"
2. 选中"文字"
3. 点击加粗按钮 → 变成 "测试**文字**"
4. 按 Ctrl+Z → 应该恢复到 "测试文字" ✅
5. 按 Ctrl+Shift+Z → 应该回到 "测试**文字**" ✅
```

### 测试2: 标题操作

```
1. 输入 "标题"
2. 点击 H1 按钮 → 变成 "# 标题"
3. 按 Ctrl+Z → 应该恢复到 "标题" ✅
```

### 测试3: 插入代码块

````
1. 光标在空行
2. 点击代码块按钮 → 插入 ```python\n\n```
3. 按 Ctrl+Z → 应该删除代码块 ✅
````

### 测试4: 连续操作

```
1. 输入 "测试"
2. 加粗 → "**测试**"
3. 再加斜体 → "***测试***"
4. 按 Ctrl+Z → "**测试**" ✅
5. 再按 Ctrl+Z → "测试" ✅
6. 按 Ctrl+Shift+Z → "**测试**" ✅
```

---

## 六、常见问题

### Q1: 为什么不在 replaceRange 里统一记录？

**不行的原因**：

- `replaceRange` 是底层方法，会被其他地方调用（如光标操作）
- 如果在 `replaceRange` 里记录，会产生很多无用的历史记录

### Q2: 如果忘记在某个分支记录会怎样？

**结果**：

- 那个操作不会被记录到历史
- 撤销时会跳过这个操作
- 用户体验很差

**解决方法**：

- 仔细检查每个 return 前是否记录了
- 运行测试，确保所有操作都能撤销

### Q3: label 参数可以随便写吗？

**可以**，但建议遵循规范：

- ✅ `应用bold格式`
- ✅ `应用heading1格式`
- ✅ `插入codeBlock`
- ❌ `用户点击了按钮`（太抽象）
- ❌ `操作`（没有信息量）

**作用**：调试时在控制台查看历史记录更清晰。

---

## 七、编码清单 ✅

- [ ] 导入 `UseHistoryReturn` 类型
- [ ] 修改 `useMarkdown` 函数签名，添加 `historyModule` 参数
- [ ] 在 `applyInlineFormat` 中记录历史
  - [ ] link 格式的记录
  - [ ] 空选区的记录
  - [ ] 有选中的记录
- [ ] 在 `applyParagraphFormat` 中记录历史
- [ ] 在 `insertBlock` 中记录历史
- [ ] 修改 `EditorContent.vue` 中的初始化顺序
- [ ] 测试所有格式化操作的撤销/重做

---

## 八、下一步

完成阶段3后：

- ✅ 格式化操作可以撤销/重做
- ❌ 用户输入的文字还不能撤销（因为没有处理 handleInput）

这个问题会在**阶段4：处理用户输入**中解决。

---

准备好了吗？打开 `useMarkdown.ts` 开始编码吧！💪
