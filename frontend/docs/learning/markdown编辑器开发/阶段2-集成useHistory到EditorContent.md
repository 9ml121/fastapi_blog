# 阶段2：集成 useHistory 到 EditorContent 实现指南

## 一、任务目标

在 `EditorContent.vue` 中集成 `useHistory`，实现：

1. ✅ 初始化历史管理模块
2. ✅ 暴露 undo/redo API 给父组件
3. ✅ 绑定键盘快捷键（Ctrl+Z / Ctrl+Shift+Z）

---

## 二、当前 EditorContent.vue 结构回顾

```vue
<script setup>
// 1. 导入
import { useSelection } from '../composables/useSelection'
import { useMarkdown } from '../composables/useMarkdown'

// 2. Props & Emits
const props = defineProps<{ modelValue?: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', value: string): void }>()

// 3. 响应式数据
const editorRef = ref<HTMLDivElement | null>(null)
const editorState = reactive<EditorState>({ ... })

// 4. 初始化 Composables
const selectionAPI = useSelection(editorRef, editorState)
const markdownAPI = useMarkdown(editorState, selectionAPI)

// 5. 暴露 API
defineExpose({
  ...selectionAPI,
  ...markdownAPI,
  editorElement: editorRef,
  state: editorState,
})
</script>
```

---

## 三、需要做的修改

### 修改点1: 导入 useHistory ✅

**位置**：在 `<script setup>` 的导入部分

**现有代码**：

```typescript
import { ref, reactive, watch } from 'vue'
import type { EditorState } from '../types/editor'
import { useSelection } from '../composables/useSelection'
import { useMarkdown } from '../composables/useMarkdown'
```

**新增代码**：

```typescript
import { ref, reactive, watch } from 'vue'
import type { EditorState } from '../types/editor'
import { useSelection } from '../composables/useSelection'
import { useMarkdown } from '../composables/useMarkdown'
import { useHistory } from '../composables/useHistory' // ⚡️ 新增
```

---

### 修改点2: 初始化 useHistory ✅

**位置**：在初始化 Composables 部分，`markdownAPI` 之后

**现有代码**：

```typescript
// 初始化 composables
const selectionAPI = useSelection(editorRef, editorState)
const markdownAPI = useMarkdown(editorState, selectionAPI)
```

**新增代码**：

```typescript
// 初始化 composables
const selectionAPI = useSelection(editorRef, editorState)
const markdownAPI = useMarkdown(editorState, selectionAPI)
const historyAPI = useHistory(editorState) // ⚡️ 新增
```

**知识点**：

- `useHistory` 只需要 `editorState` 参数
- 返回的 `historyAPI` 包含：`pushTransaction`, `undo`, `redo`, `canUndo`, `canRedo`

---

### 修改点3: 暴露 History API ✅

**位置**：在 `defineExpose` 部分

**现有代码**：

```typescript
defineExpose({
  ...selectionAPI,
  ...markdownAPI,
  editorElement: editorRef,
  state: editorState,
})
```

**修改后代码**：

```typescript
defineExpose({
  ...selectionAPI,
  ...markdownAPI,
  ...historyAPI, // ⚡️ 新增：暴露 undo, redo, canUndo, canRedo 等
  editorElement: editorRef,
  state: editorState,
})
```

**效果**：
父组件现在可以这样调用：

```typescript
editorContentRef.value.undo()
editorContentRef.value.redo()
editorContentRef.value.canUndo.value
```

---

### 修改点4: 绑定键盘快捷键 ⚡️（核心）

**位置**：在方法部分，`handleInput` 之后新增

**需要新增的代码**：

```typescript
// ============ 快捷键处理 ===========
const handleKeyDown = (event: KeyboardEvent) => {
  // 检测修饰键（支持 Windows/Linux 的 Ctrl 和 macOS 的 Cmd）
  const isMod = event.ctrlKey || event.metaKey

  // 撤销：Ctrl+Z / Cmd+Z
  if (isMod && event.key === 'z' && !event.shiftKey) {
    event.preventDefault() // ⚠️ 阻止浏览器默认撤销

    const previousContent = historyAPI.undo()
    if (previousContent !== null && editorRef.value) {
      // 恢复内容到编辑器
      editorRef.value.innerHTML = previousContent
      editorState.content = previousContent
      emit('update:modelValue', previousContent)
    }
    return
  }

  // 重做：Ctrl+Shift+Z / Cmd+Shift+Z
  if (isMod && event.key === 'z' && event.shiftKey) {
    event.preventDefault() // ⚠️ 阻止默认行为

    const nextContent = historyAPI.redo()
    if (nextContent !== null && editorRef.value) {
      // 恢复内容到编辑器
      editorRef.value.innerHTML = nextContent
      editorState.content = nextContent
      emit('update:modelValue', nextContent)
    }
    return
  }
}
```

**重点理解**：

#### 1. 为什么要 `event.preventDefault()`？

- 浏览器默认的 `Ctrl+Z` 会触发 contenteditable 的内置撤销
- 我们要用自己的历史管理，所以要阻止浏览器的默认行为

#### 2. 为什么要检查 `ctrlKey || metaKey`？

- Windows/Linux 使用 `Ctrl` 键（`event.ctrlKey`）
- macOS 使用 `Cmd` 键（`event.metaKey`）
- 这样代码可以跨平台工作

#### 3. 为什么要更新 `innerHTML` 和触发 `emit`？

```typescript
editorRef.value.innerHTML = previousContent // 更新 DOM
editorState.content = previousContent // 更新状态
emit('update:modelValue', previousContent) // 通知父组件
```

- 三个地方都要同步更新，保证数据一致性

#### 4. 为什么要检查 `!event.shiftKey`？

```typescript
// 撤销：Ctrl+Z（不能有 Shift）
if (isMod && event.key === 'z' && !event.shiftKey) { ... }

// 重做：Ctrl+Shift+Z（必须有 Shift）
if (isMod && event.key === 'z' && event.shiftKey) { ... }
```

- 两个快捷键都是 `Ctrl+Z`，通过 `shiftKey` 区分

---

### 修改点5: 在模板中绑定事件 ✅

**位置**：`<template>` 部分

**现有代码**：

```vue
<div ref="editorRef" class="editor-editable" contenteditable="true" @input="handleInput"></div>
```

**修改后代码**：

```vue
<div
  ref="editorRef"
  class="editor-editable"
  contenteditable="true"
  @input="handleInput"
  @keydown="handleKeyDown"
></div>
```

---

## 四、完整的修改示例

### 修改后的 `<script setup>` 部分

```typescript
<script lang="ts" setup>
import { ref, reactive, watch } from 'vue'
import type { EditorState } from '../types/editor'
import { useSelection } from '../composables/useSelection'
import { useMarkdown } from '../composables/useMarkdown'
import { useHistory } from '../composables/useHistory'  // ⚡️ 1. 导入

// ========= Props & Emits ============
const props = defineProps<{ modelValue?: string }>()
const emit = defineEmits<{ (e: 'update:modelValue', value: string): void }>()

// =========== 响应式数据 ================
const editorRef = ref<HTMLDivElement | null>(null)
const editorState = reactive<EditorState>({ ... })

// ============ 监听 Props ===========
watch(
  () => props.modelValue,
  (newValue) => {
    if (newValue !== undefined && editorRef.value && newValue !== editorState.content) {
      editorRef.value.innerHTML = newValue
      editorState.content = newValue
    }
  },
  { immediate: true },
)

// ============ 监听 editorState.content ===========
watch(
  () => editorState.content,
  (newContent) => {
    if (newContent && newContent !== props.modelValue) {
      emit('update:modelValue', newContent)
    }
  },
)

// ============ 方法 ===========
const handleInput = () => {
  if (editorRef.value) {
    const newContent = editorRef.value.innerHTML
    emit('update:modelValue', newContent)
    editorState.content = newContent
    editorState.isDirty = true
  }
}

// ⚡️ 新增：快捷键处理
const handleKeyDown = (event: KeyboardEvent) => {
  const isMod = event.ctrlKey || event.metaKey

  // 撤销：Ctrl+Z / Cmd+Z
  if (isMod && event.key === 'z' && !event.shiftKey) {
    event.preventDefault()

    const previousContent = historyAPI.undo()
    if (previousContent !== null && editorRef.value) {
      editorRef.value.innerHTML = previousContent
      editorState.content = previousContent
      emit('update:modelValue', previousContent)
    }
    return
  }

  // 重做：Ctrl+Shift+Z / Cmd+Shift+Z
  if (isMod && event.key === 'z' && event.shiftKey) {
    event.preventDefault()

    const nextContent = historyAPI.redo()
    if (nextContent !== null && editorRef.value) {
      editorRef.value.innerHTML = nextContent
      editorState.content = nextContent
      emit('update:modelValue', nextContent)
    }
    return
  }
}

// ============ 初始化 Composables ===========
const selectionAPI = useSelection(editorRef, editorState)
const markdownAPI = useMarkdown(editorState, selectionAPI)
const historyAPI = useHistory(editorState)  // ⚡️ 2. 初始化

// ======= 暴露 API 给父组件 =========
defineExpose({
  ...selectionAPI,
  ...markdownAPI,
  ...historyAPI,  // ⚡️ 3. 暴露
  editorElement: editorRef,
  state: editorState,
})
</script>
```

### 修改后的 `<template>` 部分

```vue
<template>
  <div class="editor-content">
    <div
      ref="editorRef"
      class="editor-editable"
      contenteditable="true"
      @input="handleInput"
      @keydown="handleKeyDown"
    ></div>
  </div>
</template>
```

---

## 五、如何测试？

### 测试1: 快捷键是否生效

1. 在编辑器中输入一些文字："测试内容"
2. 按 `Ctrl+B`（加粗），变成 `**测试内容**`
3. 按 `Ctrl+Z`（撤销），应该回到 `测试内容`
4. 按 `Ctrl+Shift+Z`（重做），应该回到 `**测试内容**`

### 测试2: API 是否正确暴露

在父组件（如 `MarkdownEditor.vue`）的浏览器控制台测试：

```javascript
// 获取 editorContent 引用
const editor = editorContentRef.value

// 测试是否暴露了 historyAPI
console.log('canUndo:', editor.canUndo.value)
console.log('canRedo:', editor.canRedo.value)

// 手动调用 undo
editor.undo()
```

---

## 六、常见问题

### Q1: 为什么快捷键没反应？

**可能原因**：

1. 忘记在 `<template>` 绑定 `@keydown`
2. `handleKeyDown` 函数写错位置（应该在 `return` 之前）
3. 浏览器焦点不在编辑器上

**调试方法**：

```typescript
const handleKeyDown = (event: KeyboardEvent) => {
  console.log('按键:', event.key, 'Ctrl:', event.ctrlKey, 'Shift:', event.shiftKey)
  // ... 其他代码
}
```

### Q2: 撤销后内容乱了？

**可能原因**：

- 没有同时更新 `innerHTML`、`state.content` 和 `emit`

**解决方法**：
确保三个地方都更新：

```typescript
editorRef.value.innerHTML = previousContent // DOM
editorState.content = previousContent // State
emit('update:modelValue', previousContent) // 父组件
```

### Q3: macOS 上快捷键不工作？

**原因**：

- macOS 使用 `Cmd` 键（`metaKey`），不是 `Ctrl`

**解决方法**：
已经在代码中处理了：

```typescript
const isMod = event.ctrlKey || event.metaKey // ✅ 支持两种
```

---

## 七、编码清单 ✅

- [ ] 导入 `useHistory`
- [ ] 初始化 `historyAPI`
- [ ] 在 `defineExpose` 中暴露 `...historyAPI`
- [ ] 实现 `handleKeyDown` 函数
  - [ ] 检测修饰键（支持 Ctrl/Cmd）
  - [ ] 处理撤销快捷键（Ctrl+Z）
  - [ ] 处理重做快捷键（Ctrl+Shift+Z）
  - [ ] 阻止浏览器默认行为
  - [ ] 更新 DOM、State 和触发 emit
- [ ] 在模板中绑定 `@keydown="handleKeyDown"`
- [ ] 测试快捷键功能
- [ ] 测试 API 暴露

---

## 八、下一步

完成阶段2后，你就可以：

- ✅ 在编辑器中使用 `Ctrl+Z` / `Ctrl+Shift+Z` 撤销重做
- ✅ 父组件可以调用 `undo()` / `redo()` 方法

**但是**，现在还有一个问题：

- ❌ 格式化操作（加粗、插入标题等）**不会被记录到历史**
- ❌ 用户输入的文字**不会被记录到历史**

这些问题会在**阶段3（集成到 useMarkdown）**和**阶段4（处理用户输入）**解决。

---

准备好了吗？打开 `EditorContent.vue` 开始编码吧！💪
