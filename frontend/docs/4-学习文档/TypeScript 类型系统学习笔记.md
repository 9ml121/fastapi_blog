# TypeScript 类型系统学习笔记：以 Editor 为例

> **学习目标**：通过 `types/editor.ts` 的实际代码，理解 TypeScript 在大型前端项目中的核心作用。

---

## 1. 为什么我们需要写这么多类型定义？

初学者可能会觉得写 `interface` 很麻烦，直接写代码不好吗？
但在多人协作或复杂项目中，类型定义就像是**建筑蓝图**。

- **防呆设计**：如果你把 `title` 拼写成了 `titel`，TS 会立刻报错，不用等到运行时才崩溃。
- **智能提示**：当你输入 `state.` 时，编辑器会自动列出 `content`, `history` 等属性，不用去翻文档。
- **重构信心**：如果你想改名一个属性，TS 会帮你找出所有引用它的地方。

---

## 2. 核心概念解析

### 2.1 Interface (接口) —— 定义数据的“形状”

在 `types/editor.ts` 中，我们大量使用了 `interface`。它就像一个模具，规定了对象必须长什么样。

```typescript
// 规定了 EditorContent 必须有 title 和 content 两个字符串属性
export interface EditorContent {
  title: string
  content: string
}
```

**初学者技巧**：

- 把 `interface` 看作是**契约**。
- `?` 表示可选属性（比如 `lastSaved?: Date`），意味着这个属性可能有，也可能没有（undefined）。

### 2.2 Discriminated Union (辨识联合) —— TS 的黑魔法

这是 `types/editor.ts` 中最高级的用法，出现在 `ToolbarConfig` 中：

```typescript
export type ToolbarConfig =
  | {
      position: 'floating' // 辨识字段
      items: FloatingToolbarItem[] // 对应浮动菜单项
    }
  | {
      position: 'blockMenu' // 辨识字段
      items: BlockToolbarItem[] // 对应块菜单项
    }
```

**它的妙处**：
当你判断 `config.position === 'floating'` 时，TS 会自动推断出 `config.items` 一定是 `FloatingToolbarItem[]` 类型！
这避免了你把“浮动菜单”的配置错传给“块菜单”。

### 2.3 状态分层设计 (State Layering)

我们没有把所有状态混在一起，而是分成了 4 层：

1.  **Content (内容层)**：`title`, `content` —— **最重要，要存数据库**。
2.  **History (历史层)**：`transactions` —— **用于撤销重做**。
3.  **UI (界面层)**：`isSaving`, `selection` —— **用户看着爽，但不存库**。
4.  **Error (错误层)**：`error` —— **出事了才用**。

```typescript
// 通过 extends 关键字，把这 4 层组合成一个完整的 EditorState
export interface EditorState extends EditorContent, EditorHistory, EditorUIState, EditorErrorState {
  // ...
}
```

**初学者心得**：
不要把所有变量都堆在一个大对象里。按“生命周期”（存不存库、变不变）来分类，代码会清晰很多。

---

## 3. 常见 TypeScript 符号速查

| 符号        | 例子                          | 含义                                    |
| :-------- | :-------------------------- | :------------------------------------ |
| `?`       | `name?: string`             | **可选属性**。可以是 string，也可以是 undefined。   |
| `\|`      | `string \| number`          | **联合类型**。或者是 string，或者是 number。       |
| `[]`      | `Action[]`                  | **数组**。一堆 Action 组成的列表。               |
| `extends` | `interface A extends B`     | **继承**。A 包含了 B 的所有属性，还可以加自己的。         |
| `??`      | `title: config.title ?? ''` | **空值合并操作符**。如果左边是undefined, 把结果变成`''` |

---

## 4. 下一步建议

当你开始写 `useMarkdownEditor.ts` 时，你会发现这些类型的威力：

- 当你写 `state.selection.` 时，会自动提示 `start`, `end`。
- 当你写 `history.addTransaction(...)` 时，它会强制你传入正确的 `EditTransaction` 结构。

**动手试试**：
在 VS Code 中按住 `Ctrl` (或 `Cmd`) 点击代码中的 `EditorState`，跳转到定义处，看看它们是如何被组装起来的。
