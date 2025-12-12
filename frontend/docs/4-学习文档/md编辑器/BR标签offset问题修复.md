
## 问题现象

在空行（`<div><br></div>`）上应用段落格式和内联格式时，光标位置会多移动一位。

## 根本原因

### DOM 结构

```html
<div contenteditable>
  <div>Hello</div>
  <div><br /></div>
  <!-- 空行 -->
  <div>World</div>
</div>
```

### innerText 表现

```
innerText: "Hello\n\n\nWorld"
索引:       01234 567 89012
            Hello \n\n\nWorld
                  ↑  ↑
                  6  7  ← 空行占据2个位置
```

### getCurrentLineInfo 的问题

当光标在空行（索引 6 或 7）时：

1. **向前查找行首**: 遇到索引 5 的`\n`，所以 `lineStart = 6`
2. **向后查找行尾**: 遇到索引 7 或 8 的`\n`，所以 `lineEnd` 可能是 7 或 8
3. **问题**: 空行可能被识别为：
    - `lineText = "\n"` (如果光标在索引 6)
    - `lineText = ""` (如果光标在索引 7)

### 为什么会有 2 个换行符？

innerText 的规则：

- **DIV 边界**: 产生 1 个`\n`
- **BR 标签**: 产生 1 个`\n`
- **空 DIV（只含 BR）**: = DIV 的`\n` + BR 的`\n` = 2 个`\n`
---

### 成熟编辑器的做法

**ProseMirror / Slate.js / Quill / Draft.js** 等框架都采用：

```
独立文档模型（JSON树） → DOM渲染视图
         ↑
    位置计算基于模型，不基于DOM
```

**优点**：彻底避免 DOM 怪异行为  
**缺点**：架构复杂，开发成本高

--- 

# 实现 getTextContent 替代 innerText - 实施计划

## 问题总结

修改 `getCurrentLineInfo` **无法**解决 `applyInlineFormat` 的问题，因为：

- `applyInlineFormat` 使用 `getSelectionInfo()`
- `getSelectionInfo()` 依赖 `innerText`
- `innerText` 对 BR 的处理是固定的（双换行）
- **所有**基于文本内容的逻辑都会受影响

## 根本性解决方案

### 核心思想

> 不再使用 `innerText`，而是自己遍历 DOM 树计算文本内容

### 实现位置

`/Users/limq/00-app/fastapi_blog/frontend/src/components/editor/utils/selection.ts`

添加新函数：

```typescript
/**
 * 从DOM树获取文本内容（替代innerText）
 *
 * 规则：
 * - BR标签不产生字符
 * - 只有DIV边界产生换行符
 * - <div><br></div> 产生单个 \n
 *
 * @param root - contenteditable根元素
 * @returns 文本内容
 */
export function getTextContent(root: HTMLElement): string {
  let text = "";

  function traverse(node: Node) {
    if (node.nodeType === Node.TEXT_NODE) {
      text += node.textContent || "";
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      if (node.nodeName === "BR") {
        // BR不产生字符
      } else {
        // 递归处理子节点
        for (const child of node.childNodes) {
          traverse(child);
        }

        // DIV边界产生换行
        if (node.nodeName === "DIV" && node !== root && node.nextSibling) {
          text += "\n";
        }
      }
    }
  }

  traverse(root);
  return text;
}
```

---

## 修改范围

### 1. useSelection.ts

#### 修改 `getSelectionInfo`

```typescript
const getSelectionInfo = (): SelectionInfo => {
  const ele = editorElement.value;
  if (!ele) {
    return { start: 0, end: 0, selectedText: "", isEmpty: true };
  }

  const sel = window.getSelection();
  if (!sel || sel.rangeCount === 0) {
    return { start: 0, end: 0, selectedText: "", isEmpty: true };
  }

  const anchorNode = sel.anchorNode;
  const focusNode = sel.focusNode;
  const anchorOffset = sel.anchorOffset;
  const focusOffset = sel.focusOffset;

  let start = getAbsoluteOffset(anchorNode as Node, anchorOffset, ele);
  let end = getAbsoluteOffset(focusNode as Node, focusOffset, ele);

  if (start > end) {
    [start, end] = [end, start];
  }

  // ✅ 修改：使用 getTextContent 替代 innerText
  const text = getTextContent(ele);
  const selectedText = text.substring(start, end);

  return { start, end, selectedText, isEmpty: start === end };
};
```

#### 修改 `getCurrentLineInfo`

```typescript
const getCurrentLineInfo = (): {
  lineStart: number;
  lineEnd: number;
  lineText: string;
} => {
  const ele = editorElement.value;
  if (!ele) return { lineStart: 0, lineEnd: 0, lineText: "" };

  // ✅ 使用 getTextContent 替代 innerText
  const text = getTextContent(ele);
  const selection = getSelectionInfo();

  let lineStart = selection.start;
  while (lineStart > 0 && text[lineStart - 1] !== "\n") {
    lineStart--;
  }

  let lineEnd = selection.start;
  while (lineEnd < text.length && text[lineEnd] !== "\n") {
    lineEnd++;
  }

  return {
    lineStart,
    lineEnd,
    lineText: text.substring(lineStart, lineEnd),
  };
};
```

### 2. useMarkdownEditor.ts

#### 修改 `onInput`

```typescript
const onInput = (e: InputEvent) => {
  const target = e.target as HTMLElement;

  // ✅ 使用 getTextContent 替代 innerText
  const currentText = getTextContent(target);

  if (currentText !== state.content) {
    state.content = currentText;
    state.isDirty = true;

    if (callbacks?.onContentChange) {
      callbacks.onContentChange(currentText);
    }
  }
};
```

#### 修改初始化

```typescript
onMounted(() => {
  if (editorRef.value) {
    selectionAPI.setupSelectionListener();
    // ✅ 使用 getTextContent
    selectionAPI.state.content = getTextContent(editorRef.value);
    // ...
  }
});
```

---

## 验证计划

### 测试用例

#### 1. 空行文本内容

```typescript
// DOM
<div>Hello</div>
<div><br></div>
<div>World</div>

// innerText (旧): "Hello\n\n\nWorld" (3个\n)
// getTextContent (新): "Hello\n\nWorld" (2个\n) ✅
```

#### 2. 空行选中

```typescript
// 选中空行 <div><br></div>
// 旧: selectedText = "\n\n"
// 新: selectedText = "\n" ✅
```

#### 3. applyInlineFormat on 空行

```typescript
// 在空行上应用加粗
// 旧: selectedText = "\n\n" → newText = "**\n\n**" ❌
// 新: selectedText = "\n" → 应该直接忽略或提示 ✅
```

#### 4. applyParagraphFormat on 空行

```typescript
// 在空行上添加标题
// 旧: lineText = "\n", 光标位置错误
// 新: lineText = "", 光标位置正确 ✅
```

### 边界情况

1. **连续空行**
    
    ```html
    <div><br /></div>
    <div><br /></div>
    ```
    
    getTextContent 应返回: `"\n\n"`
    
2. **行内 BR（如果存在）**
    
    ```html
    <div>Hello<br />World</div>
    ```
    
    按当前规则，BR 不产生字符，所以是: `"HelloWorld\n"` **注意**：如果需要支持行内 BR，需要额外判断
    
3. **空编辑器**
    
    ```html
    <div><br /></div>
    ```
    
    getTextContent 应返回: `""` (空字符串，没有 DIV 边界)
    

---

## 风险评估与解决方案

### ⚠️ 高风险 1：坐标系统一致性（必须同步修改）

**问题**：`getAbsoluteOffset` 和 `getNodeAndOffset` 目前把 BR 当作 1 个字符处理

**必须修改**：

#### getAbsoluteOffset

```typescript
if (currentNode.nodeName === "BR") {
  // ✅ 修改：BR不产生任何偏移量
  // 什么都不做
}
```

#### getNodeAndOffset

```typescript
if (node.nodeName === "BR") {
  // ✅ 修改：BR不累加offset
  // 但光标可能在BR位置，需要返回父节点
  if (currentOffset === absoluteOffset) {
    const parent = node.parentNode!;
    const index = Array.from(parent.childNodes).indexOf(node as ChildNode);
    return { node: parent, offset: index };
  }
  // 不累加 currentOffset
}
```

**关键**：三个函数必须保持一致的规则

- `getTextContent`: BR → 0 个字符
- `getAbsoluteOffset`: BR → 0 个偏移量
- `getNodeAndOffset`: BR → 0 个偏移量

---

### ⚠️ 高风险 2：Enter vs Shift+Enter 处理策略

#### 主流编辑器对比

|编辑器|Enter|Shift+Enter|理由|
|---|---|---|---|
|**Typora**|新段落|软换行(BR)|所见即所得，区分段落和换行|
|**Obsidian**|新行|新行（相同）|Markdown 语义，单换行即换行|
|**VSCode**|新行|新行（相同）|代码编辑器，不需要区分|
|**Notion**|新块|块内换行|基于块的编辑模型|

#### 推荐方案：参考 Obsidian（简化）

**理由**：

- ✅ 符合 Markdown 语义（单换行就是换行）
- ✅ 实现简单，不引入 BR 复杂性
- ✅ 符合博客写作习惯
- ✅ 避免 bug（不处理行内 BR）

**实现**：

```typescript
// 所有BR都视为"空行占位符"
// 不产生字符，不区分Enter和Shift+Enter
```

**可选监听**（阻止浏览器默认的 Shift+Enter 行为）：

```typescript
editorRef.value?.addEventListener("keydown", (e) => {
  if (e.key === "Enter" && e.shiftKey) {
    e.preventDefault();
    // 与普通Enter相同：插入新DIV
    document.execCommand("insertParagraph");
  }
});
```

#### 未来扩展（如需软换行）

如果将来需要支持"段落内换行"，可以区分：

```typescript
// getTextContent 中
if (node.nodeName === "BR") {
  const parent = node.parentElement;
  const isInlineBreak =
    parent && parent.nodeName === "DIV" && parent.childNodes.length > 1;

  if (isInlineBreak) {
    text += "\n"; // 行内BR产生换行
  }
  // 孤立BR（空行）不产生字符
}
```

**当前阶段建议**：使用简化方案，避免复杂性

---

### 中风险点

1. **性能**
    
    - `getTextContent` 需要遍历 DOM 树
    - 通常编辑器内容不大，影响可控
    - 可考虑缓存优化（如内容未变时复用）
2. **测试覆盖**
    
    - 需要全面测试所有依赖文本内容的功能
    - 包括选区、格式化、光标定位等
    - 特别关注空行、连续空行等边界情况

---

## 实施步骤

### Phase 1: 实现核心函数（1 小时）

- [ ] 在 `utils/selection.ts` 中实现 `getTextContent`
- [ ] 编写单元测试验证规则正确

### Phase 2: 替换 innerText（2 小时）

- [ ] 修改 `useSelection.ts` 中的 `getSelectionInfo`
- [ ] 修改 `useSelection.ts` 中的 `getCurrentLineInfo`
- [ ] 修改 `useMarkdownEditor.ts` 中的 `onInput`

### Phase 3: 验证和测试（2 小时）

- [ ] 在 EditorDemo 中测试空行场景
- [ ] 测试 `applyInlineFormat` 在空行上的表现
- [ ] 测试 `applyParagraphFormat` 在空行上的表现
- [ ] 测试连续空行、多种格式组合

### Phase 4: 处理边界情况（1 小时）

- [ ] 确定行内 BR 的处理策略
- [ ] 添加相应的边界情况测试
- [ ] 更新文档

---

## 总结

这是**唯一能从根本上解决 BR 双换行问题的方案**：

✅ 一次修改，所有功能受益  
✅ 不需要在每个函数中特殊处理 BR  
✅ 文本内容与坐标系统完全一致  
✅ 符合业界最佳实践的思路

您觉得这个方案如何？我可以开始实施代码。