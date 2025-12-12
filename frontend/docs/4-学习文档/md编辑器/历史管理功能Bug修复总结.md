# 历史管理功能 Bug 修复总结

> 日期：2025-11-30  
> 阶段：撤销/重做功能优化

本文档记录了在实现历史管理功能（撤销/重做）过程中遇到的典型 bug 及其解决方案。

---

## Bug 1: 第一次撤销无效

### 问题现象

用户输入文字后，第一次按 `Ctrl+Z` 时页面内容不变化，需要按第二次才能正常撤销。

### 问题原因

**根本原因**：`inputTimer` 在 setTimeout 回调执行后没有重置为 `null`。

```typescript
// ❌ 错误代码
inputTimer = window.setTimeout(() => {
  historyAPI.pushTransaction(...)
  // 缺少：inputTimer = null
}, 500)

// 撤销时
if (inputTimer) {  // ⚠️ inputTimer 是数字（timer ID），判断为 true
  // 误以为还在防抖期间，强制记录当前内容（重复记录）
  historyAPI.pushTransaction(...)
}
```

**问题流程**：

1. 用户输入 "test" → 500ms 后记录到历史（记录 1）
2. `inputTimer` 还保留着 timer ID（一个数字，如 123）
3. 用户按 Ctrl+Z → 检查 `if (inputTimer)` 为 true
4. 强制记录当前内容（记录 2，与记录 1 相同）
5. 执行 undo，撤销到记录 1（内容相同，页面无变化）❌

### 解决方案

在 setTimeout 回调最后添加 `inputTimer = null`：

```typescript
// ✅ 正确代码
inputTimer = window.setTimeout(() => {
  historyAPI.pushTransaction(...)
  inputTimer = null  // ✅ 重置为 null，标记防抖已完成
}, 500)
```

**修复文件**：`EditorContent.vue`

### 知识点

- `setTimeout` 返回的是 timer ID（数字）
- 数字是 truthy 值，`if (number)` 会判断为 true
- 需要手动重置为 `null` 来标记定时器已完成

---

## Bug 2: 中文输入法拼音被记录到历史

### 问题现象

使用中文输入法输入"你好"后，撤销时先回到拼音状态"nihao"，而不是直接删除。

### 问题原因

**根本原因**：`handleInput` 在组合输入期间也设置了定时器，导致拼音状态被记录。

**中文输入流程**：

```
1. 用户输入 'n' → input 事件 → 设置定时器A
2. 用户输入 'i' → input 事件 → 取消A，设置定时器B
...
6. 完成 "nihao" → 等待500ms → 定时器到期，记录 "nihao" ⚠️
7. 用户选择"你好" → input 事件 → 设置定时器C
8. 定时器C到期 → 记录 "你好" ✅

历史栈：["nihao", "你好"]  ← 拼音不应该被记录
```

### 解决方案

**添加 IME 组合输入状态检测**：

#### 1. 添加状态标志

```typescript
let isComposing = false;
```

#### 2. 监听组合事件

```typescript
// 输入法组合开始（用户开始输入拼音）
const handleCompositionStart = () => {
  isComposing = true
}

// 输入法组合结束（用户确认文字）
const handleCompositionEnd = () => {
  isComposing = false
  // 组合结束后，手动记录最终文字
  if (editorRef.value) {
    const newContent = editorRef.value.innerHTML
    historyAPI.pushTransaction(newContent, '输入文本', ...)
  }
}
```

#### 3. handleInput 中检查状态

```typescript
const handleInput = () => {
  if (editorRef.value) {
    // 立即更新界面
    emit('update:modelValue', newContent)
    editorState.content = newContent

    // ⚡️ 组合输入期间不设置定时器
    if (isComposing) {
      return  // 跳过历史记录
    }

    // 防抖记录（只在非组合状态执行）
    if (inputTimer) clearTimeout(inputTimer)
    inputTimer = setTimeout(() => {
      historyAPI.pushTransaction(...)
    }, 500)
  }
}
```

#### 4. 绑定事件

```vue
<div
  contenteditable="true"
  @input="handleInput"
  @compositionstart="handleCompositionStart"
  @compositionend="handleCompositionEnd"
>
```

**修复文件**：`EditorContent.vue`

### 知识点

**Composition Events（组合事件）**：

| 事件               | 触发时机         | 作用                                     |
| ------------------ | ---------------- | ---------------------------------------- |
| `compositionstart` | 用户开始输入拼音 | 设置 `isComposing = true`                |
| `compositionend`   | 用户选择候选词   | 设置 `isComposing = false`，记录最终文字 |

**核心思想**：拼音是临时状态，只有确认的文字才应该记录到历史。

---

## Bug 3: 撤销到空格时光标跳到最前面

### 问题现象

输入 "你好 hello"（中间有空格），撤销 "hello" 后，光标应该在 "你好 " 末尾，但实际跳到了最前面。

### 问题原因

**根本原因**：`getNodeAndOffset` 在某些情况下找不到正确的节点位置，返回 `null`，导致 `setCursor` 直接 return，光标没有设置。

**可能的原因**：

- 浏览器将空格转换为 `&nbsp;`（不间断空格）
- `getNodeAndOffset` 遍历 DOM 时计算偏移错误
- 找不到目标位置，返回 `null`

```typescript
// setCursor 中
const nodeAndOffset = getNodeAndOffset(position, ele);
if (!nodeAndOffset) {
  console.warn("无法设置光标位置");
  return; // ⚠️ 直接 return，光标停留在原位（可能是开头）
}
```

### 解决方案

**在 `setCursor` 中添加 fallback**，当找不到精确位置时，将光标设置到末尾：

```typescript
const setCursor = (position: number): void => {
  const ele = editorElement.value;
  if (!ele) return;

  const nodeAndOffset = getNodeAndOffset(position, ele);

  if (!nodeAndOffset) {
    console.warn(`无法找到位置 ${position}，设置光标到末尾`);
    // ⚡️ Fallback: 设置光标到末尾
    const range = document.createRange();
    ele.focus();
    range.selectNodeContents(ele);
    range.collapse(false); // 折叠到末尾

    const sel = window.getSelection();
    if (sel) {
      sel.removeAllRanges();
      sel.addRange(range);
    }
    return;
  }

  // 正常设置光标...
};
```

**修复文件**：`useSelection.ts`

### 知识点

**DOM Range API**：

- `range.selectNodeContents(node)`：选中节点的所有内容
- `range.collapse(false)`：折叠到末尾（true 为开头）
- Fallback 策略：精确定位失败时，提供合理的默认行为

**HTML 空格处理**：

- 浏览器会自动将某些空格转换为 `&nbsp;`（不间断空格）
- `textContent` 会自动将 `&nbsp;` 转回普通空格
- 我们的 offset 计算基于 `textContent`，所以大部分情况不受影响

---

## Bug 4: 第一行可能没有 div 包裹

### 问题现象

初始化或删除所有内容后重新输入时，第一行可能是裸露的文本节点，导致：

- offset 计算不准确
- 格式化操作异常

```html
<!-- ❌ 错误状态 -->
<div contenteditable>
  hello world
  <!-- 裸露文本节点 -->
</div>

<!-- ✅ 正确状态 -->
<div contenteditable>
  <div>hello world</div>
</div>
```

### 问题原因

contenteditable 的行为不可预测，某些情况下浏览器不会自动创建 `<div>` 包裹。

### 解决方案

**创建 DOM 规范化工具**，确保第一层子节点都被 `<div>` 包裹。

#### 1. 创建工具函数（`utils/dom.ts`）

```typescript
/**
 * 规范化 contenteditable 的 DOM 结构
 * 确保所有文本内容都被 <div> 包裹
 */
export function normalizeDOM(root: HTMLElement): boolean {
  const children = Array.from(root.childNodes); // ✅ 创建静态数组
  let modified = false;

  for (const child of children) {
    // 跳过已有的 DIV
    if (child.nodeName === "DIV") continue;

    // 处理文本节点或 BR
    if (child.nodeType === Node.TEXT_NODE || child.nodeName === "BR") {
      const text = child.textContent?.trim();

      // 跳过纯空白文本
      if (child.nodeType === Node.TEXT_NODE && !text) {
        root.removeChild(child);
        modified = true;
        continue;
      }

      // 创建 div 包裹
      const div = document.createElement("div");
      root.insertBefore(div, child);
      div.appendChild(child); // appendChild 会移动节点
      modified = true;
    }
  }

  return modified;
}
```

#### 2. 在 handleInput 中调用

```typescript
const handleInput = () => {
  if (editorRef.value) {
    // 更新数据...

    if (isComposing) return;

    // ⚡️ 规范化 DOM 结构
    normalizeDOM(editorRef.value);

    // 防抖记录历史...
  }
};
```

**修复文件**：

- 新建 `utils/dom.ts`
- 修改 `EditorContent.vue`

### 知识点

**为什么要用 `Array.from`**：

```typescript
// ❌ 错误：直接遍历 NodeList
for (const child of root.childNodes) {
  root.insertBefore(div, child); // 修改 DOM
  div.appendChild(child); // NodeList 实时更新，可能跳过节点
}

// ✅ 正确：创建静态数组
const children = Array.from(root.childNodes);
for (const child of children) {
  // 即使修改 DOM，children 数组不变
}
```

**性能优化**：

- 只规范化第一层子节点，不递归
- 大部分情况下都是 `continue`，开销很小
- 只在真正需要时才修改 DOM

---

## 总结

### 修复的 Bug 列表

| Bug            | 影响         | 优先级 | 状态      |
| -------------- | ------------ | ------ | --------- |
| 第一次撤销无效 | 用户体验差   | 高     | ✅ 已修复 |
| 中文拼音被记录 | 撤销混乱     | 高     | ✅ 已修复 |
| 光标跳到开头   | 光标位置错误 | 中     | ✅ 已修复 |
| 第一行没有 div | 格式化异常   | 中     | ✅ 已修复 |

### 涉及的文件

- `EditorContent.vue` - 主要修复文件
- `useSelection.ts` - 光标 fallback
- `utils/dom.ts` - 新建工具文件

### 关键技术点

1. **JavaScript 定时器管理**：及时重置 timer ID
2. **IME 组合事件**：处理中文输入法
3. **DOM Range API**：光标位置 fallback
4. **DOM 规范化**：确保一致的 DOM 结构
5. **NodeList vs Array**：Live 集合的陷阱

### 最佳实践

- ✅ 定时器回调后立即重置为 `null`
- ✅ 监听 `compositionstart/end` 处理输入法
- ✅ 关键操作添加 fallback 策略
- ✅ 修改 DOM 时使用 `Array.from` 创建快照
- ✅ 工具函数独立到 `utils` 目录

---

## 参考资料

- [MDN - Composition Events](https://developer.mozilla.org/en-US/docs/Web/API/CompositionEvent)
- [MDN - Range API](https://developer.mozilla.org/en-US/docs/Web/API/Range)
- [MDN - NodeList](https://developer.mozilla.org/en-US/docs/Web/API/NodeList)
