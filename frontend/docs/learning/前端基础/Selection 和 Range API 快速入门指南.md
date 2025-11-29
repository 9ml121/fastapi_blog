# Selection 和 Range API 快速入门指南

> **学习目标**：理解浏览器文本选中的工作原理，为 useSelection.ts 的开发做准备
>
> **预计时间**：45 分钟（包括练习）
>
> **前置知识**：基础 JavaScript、基础 DOM 概念

---

## 📚 目录

1. [第一层：DOM 树结构](#第一层dom-树结构)
2. [第二层：Selection API](#第二层selection-api)
3. [第三层：Range API](#第三层range-api)
4. [第四层：DOM 遍历](#第四层dom-遍历)
5. [综合练习](#综合练习)
6. [回到 useSelection.ts](#回到-useselectionts)

---

## 第一层：DOM 树结构

### 概念

HTML 被浏览器解析成一棵树，树上的每个节点有不同的**类型**。

### 常见节点类型

```javascript
// 节点类型常量
Node.ELEMENT_NODE    = 1    // <div>, <span>, <b>, 等 HTML 标签
Node.TEXT_NODE       = 3    // 文本内容
Node.COMMENT_NODE    = 8    // <!-- 注释 -->

// 还有其他，但我们只关心这三个
```

### 例子：可视化 DOM 树

```html
<div id="editor">
  Hello <b>World</b>
</div>
```

这个 HTML 的 DOM 树是这样的：

```
div#editor (ELEMENT_NODE)
├── TextNode: "Hello "        (TEXT_NODE)
└── b (ELEMENT_NODE)
    └── TextNode: "World"     (TEXT_NODE)
```

**关键点**：
- 文本不是在标签里，而是作为 TextNode 子节点存在
- `"Hello "` 和 `"World"` 是分开的节点
- 空格也算字符！

### 练习 1：识别 DOM 节点

在浏览器控制台运行这个代码：

```javascript
// 创建一个 HTML 结构
const editor = document.createElement('div');
editor.innerHTML = 'Hello <b>World</b>';
document.body.appendChild(editor);

// 查看它的节点结构
for (const child of editor.childNodes) {
  console.log('节点类型:', child.nodeType);
  console.log('节点内容:', child.textContent || child.nodeValue);
  console.log('---');
}
```

**预期输出**：
```
节点类型: 3 (TEXT_NODE)
节点内容: Hello 
---
节点类型: 1 (ELEMENT_NODE)
节点内容: World
---
```

---

## 第二层：Selection API

### 概念

**Selection** 是浏览器提供的 API，让你**获取和操作用户选中的文本**。

```javascript
const sel = window.getSelection();
```

### Selection 的主要属性

当用户选中文本时：

```javascript
const sel = window.getSelection();

// 选中从哪里开始
sel.anchorNode     // 起点所在的节点（可能是 TextNode 或 Element）
sel.anchorOffset   // 起点在节点内的偏移（从 0 开始）

// 选中到哪里结束
sel.focusNode      // 终点所在的节点
sel.focusOffset    // 终点在节点内的偏移

// 其他有用的属性
sel.rangeCount     // 选中范围的个数（通常是 1）
sel.toString()     // 返回选中的文本字符串
```

### 例子：检查用户的选中

```javascript
// 在编辑器中选中一些文本，然后运行这个代码
const sel = window.getSelection();

if (sel.rangeCount > 0) {
  console.log('你选中了:', sel.toString());
  console.log('起点节点类型:', sel.anchorNode.nodeType);
  console.log('起点偏移:', sel.anchorOffset);
  console.log('终点节点类型:', sel.focusNode.nodeType);
  console.log('终点偏移:', sel.focusOffset);
} else {
  console.log('没有选中任何文本');
}
```

### 关键概念：anchorOffset 是什么？

```
假设有个 TextNode: "Hello World"
       索引:      0123456789...

用户选中从位置 0 到位置 5（"Hello"）：
sel.anchorNode = TextNode("Hello World")
sel.anchorOffset = 0       // 从第 0 个字符开始

sel.focusNode = TextNode("Hello World")
sel.focusOffset = 5        // 到第 5 个字符结束
```

### ⚠️ 重要：正向 vs 反向选中

```javascript
// 如果用户从左往右选中 "Hello"
sel.anchorOffset = 0
sel.focusOffset = 5
// start < end ✅

// 如果用户从右往左反向拖动选中 "Hello"
sel.anchorOffset = 5
sel.focusOffset = 0
// start > end ❌ 需要交换！
```

### 练习 2：获取选中信息

在这个 HTML 中：

```html
<div id="editor" contenteditable>Hello World, this is a test</div>
```

在编辑器中**选中一些文本**，然后运行：

```javascript
const editor = document.getElementById('editor');
const sel = window.getSelection();

if (sel.rangeCount === 0) {
  console.log('请先选中一些文本');
} else {
  const range = sel.getRangeAt(0);
  console.log('你选中了:', sel.toString());
  console.log('选中的长度:', sel.toString().length);
  
  // 判断是否反向选中
  if (sel.anchorOffset > sel.focusOffset) {
    console.log('你是从右往左反向选中的');
  } else {
    console.log('你是从左往右正向选中的');
  }
}
```

---

## 第三层：Range API

### 概念

**Range** 代表一个文本范围。你可以用它来：
- 选中文本
- 修改文本
- 获取范围内的内容

### 创建和使用 Range

```javascript
// 创建一个新的 Range
const range = document.createRange();

// 设置范围的起点和终点
range.setStart(node, offset);   // 从某个节点的某个偏移开始
range.setEnd(node, offset);     // 到某个节点的某个偏移结束

// 应用到浏览器的 Selection
const sel = window.getSelection();
sel.removeAllRanges();  // 清空旧的选中
sel.addRange(range);    // 添加新的范围
```

### 例子：设置光标位置

```javascript
const editor = document.getElementById('editor');

// 创建 Range
const range = document.createRange();

// 设置光标到第一个 TextNode 的位置 5
const firstTextNode = editor.firstChild;  // 这是一个 TextNode
range.setStart(firstTextNode, 5);
range.collapse(true);  // collapse 使光标不是选中范围，而是单点

// 应用到页面
const sel = window.getSelection();
sel.removeAllRanges();
sel.addRange(range);

// 现在浏览器中光标应该在 "Hello|" 的位置
```

### 常用的 Range 操作

```javascript
const range = document.createRange();

// 基本操作
range.setStart(node, offset);     // 设置起点
range.setEnd(node, offset);       // 设置终点
range.collapse(true);             // 折叠成光标（true=起点，false=终点）

// 内容操作
range.extractContents();          // 取出范围内的内容并删除
range.deleteContents();           // 删除范围内的内容
range.cloneContents();            // 复制范围内的内容（不删除）

// 插入内容
const textNode = document.createTextNode('inserted text');
range.insertNode(textNode);       // 在范围开始处插入节点
```

### 练习 3：用 Range 选中文本

```html
<div id="editor" contenteditable>Hello World</div>
```

运行这个代码来选中 "World"：

```javascript
const editor = document.getElementById('editor');

// 获取编辑器内的第一个 TextNode：
// DOM 结构是：
//   <div>
//     TextNode("Hello World")
//   </div>
const textNode = editor.firstChild;

// 创建 Range
const range = document.createRange();
range.setStart(textNode, 6);   // "Hello " 有 6 个字符
range.setEnd(textNode, 11);    // "World" 有 5 个字符，6+5=11

// 应用到 Selection
const sel = window.getSelection();
sel.removeAllRanges();
sel.addRange(range);

// 现在 "World" 应该被选中了
console.log('选中:', sel.toString());
```

---

## 第四层：DOM 遍历

### 问题

前面的例子都假设文本在一个 TextNode 里：
```html
<div>Hello World</div>  <!-- ✅ 简单 -->
```

但实际情况通常是这样：
```html
<div>Hello <b>World</b></div>  <!-- ❌ 复杂 -->
```

在第二种情况，`"Hello "` 和 `"World"` 在**不同的节点**里！

### 核心问题

Selection API 给你的位置是**节点相对的**：
```
sel.anchorNode = TextNode("Hello ")
sel.anchorOffset = 0
```

但你需要的是**全局位置**（相对于整个编辑器）：
```
全局位置 = 0（从编辑器开始）
```

### 解决方案：遍历 DOM 树

需要一个函数把"节点相对位置"转换为"全局位置"：

```javascript
/**
 * 计算从编辑器根节点到目标节点的字符累计
 * 
 * 例子：
 * <div>Hello <b>World</b></div>
 * 
 * 如果目标是 TextNode("World") 内的位置 2：
 * - 首先累计 "Hello " = 6 个字符
 * - 然后累计 <b> 内的位置 2 = 2 个字符
 * - 总计：6 + 2 = 8
 */
function getAbsoluteOffset(targetNode, offsetInNode, root) {
  let absoluteOffset = 0;
  let found = false;
  
  // 深度优先遍历 DOM 树
  function traverse(node) {
    // 如果已找到目标节点，停止
    if (found) return;
    
    // 检查是否到达了目标节点
    if (node === targetNode) {
      absoluteOffset += offsetInNode;
      found = true;
      return;
    }
    
    // 如果是 TextNode，累计字符数
    if (node.nodeType === Node.TEXT_NODE) {
      absoluteOffset += node.textContent.length;
    } 
    // 如果是 Element，递归遍历子节点
    else if (node.nodeType === Node.ELEMENT_NODE) {
      for (const child of node.childNodes) {
        traverse(child);
        if (found) return;  // 找到后立即返回
      }
    }
  }
  
  // 从根节点开始遍历
  traverse(root);
  return absoluteOffset;
}
```

### 为什么需要递归？

```
DOM 树可能很深：
<div>
  Hello
  <b>
    <i>World</i>
  </b>
</div>

如果要获取 <i> 内的位置，需要：
1. 遍历 "Hello" (6个字符)
2. 进入 <b>
3. 进入 <i>
4. 找到位置

这就是为什么需要递归！
```

### 练习 4：手动计算全局位置

假设有这个 HTML：

```html
<div id="editor">Hello <b>World</b></div>
```

问题：如果 Selection API 告诉你：
```
anchorNode = TextNode("World")  (在 <b> 内)
anchorOffset = 2
```

全局位置应该是多少？

**思路**：
1. 首先数 `"Hello "` = 6 个字符
2. 然后加上 TextNode("World") 内的偏移 2
3. 总计 = 6 + 2 = 8

---

## 综合练习

### 练习 5：完整的 getAbsoluteOffset 实现

在浏览器控制台运行这个代码：

```javascript
// 创建测试 HTML
const editor = document.createElement('div');
editor.id = 'editor';
editor.innerHTML = 'Hello <b>World</b>';
document.body.appendChild(editor);

// 实现 getAbsoluteOffset
function getAbsoluteOffset(targetNode, offsetInNode, root) {
  let absoluteOffset = 0;
  let found = false;
  
  function traverse(node) {
    if (found) return;
    
    if (node === targetNode) {
      absoluteOffset += offsetInNode;
      found = true;
      return;
    }
    
    if (node.nodeType === Node.TEXT_NODE) {
      absoluteOffset += node.textContent.length;
    } else if (node.nodeType === Node.ELEMENT_NODE) {
      for (const child of node.childNodes) {
        traverse(child);
        if (found) return;
      }
    }
  }
  
  traverse(root);
  return absoluteOffset;
}

// 测试：获取 <b> 内 "World" 的全局位置
const bElement = editor.querySelector('b');
const worldNode = bElement.firstChild;  // TextNode("World")

const globalPos = getAbsoluteOffset(worldNode, 0, editor);
console.log('全局位置:', globalPos);  // 应该是 6
```

### 练习 6：获取选中的全局位置

```javascript
// 在编辑器中选中 "World"，然后运行：

const editor = document.getElementById('editor');
const sel = window.getSelection();

if (sel.rangeCount > 0) {
  const start = getAbsoluteOffset(sel.anchorNode, sel.anchorOffset, editor);
  const end = getAbsoluteOffset(sel.focusNode, sel.focusOffset, editor);
  
  console.log('选中的全局范围:', Math.min(start, end), '-', Math.max(start, end));
  console.log('选中的文本:', sel.toString());
}
```

---

## 回到 useSelection.ts

现在你理解了这些概念后，再看 useSelection.ts 就简单了：

### getSelection() 函数的逻辑

```typescript
const getSelection = (): SelectionInfo => {
  // 第二层：获取 Selection
  const browserSelection = window.getSelection();
  
  // 检查是否有选中（第二层概念）
  if (!browserSelection || browserSelection.rangeCount === 0) {
    return { start: 0, end: 0, selectedText: '', isEmpty: true }
  }
  
  // 获取 Selection 的起点和终点信息（第二层概念）
  const anchorNode = browserSelection.anchorNode;
  const focusNode = browserSelection.focusNode;
  const anchorOffset = browserSelection.anchorOffset;
  const focusOffset = browserSelection.focusOffset;
  
  // 转换为全局位置（第四层概念）
  let start = getAbsoluteOffset(anchorNode as Node, anchorOffset, editorElement as HTMLElement);
  let end = getAbsoluteOffset(focusNode as Node, focusOffset, editorElement as HTMLElement);
  
  // 处理反向选中（重要！）
  if (start > end) {
    [start, end] = [end, start];
  }
  
  // 提取选中的文本（第三层概念）
  const selectedText = editorElement?.textContent?.substring(start, end) ?? '';
  
  // 返回标准化的 SelectionInfo
  return { start, end, selectedText, isEmpty: start === end };
};
```

### 其他函数的理解

- `setCursor()` - 使用 Range API 设置光标位置
- `selectRange()` - 使用 Range API 选中一个范围
- `wrapSelection()` - 使用 Range API 删除和插入文本
- 都依赖第三层的 Range API 概念

---

## 📝 学习检查清单

学完后，你应该能理解：

- [ ] DOM 树中 TextNode 和 Element 的区别
- [ ] anchorNode、anchorOffset、focusNode、focusOffset 是什么
- [ ] 为什么需要 getAbsoluteOffset() 这样的转换函数
- [ ] Range API 如何用于设置和修改选中
- [ ] 为什么需要处理反向选中
- [ ] getSelection() 函数的完整逻辑

---

## 🎯 下一步

完成这个指南和所有练习后，你就有足够的知识来：

1. ✅ 修正 useSelection.ts 中的代码结构
2. ✅ 理解所有 DOM 操作
3. ✅ 写出高质量的单元测试

**预计完成时间**：45 分钟（包括在浏览器中运行和测试代码）

祝学习愉快！ 🚀
