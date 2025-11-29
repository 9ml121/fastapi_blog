> **文档用途**：当前 Phase 阶段目标和实现步骤（正在做什么）
>
> **更新时机**：
>
> 1.  phase阶段开始前, 覆盖更新「当前phase阶段目标」和「待实现功能」
> 2.  开始子任务前，更新「下一步实施计划」
> 3.  完成子任务后，更新「已完成功能」，标记「待实现功能」
>
> **归档时机**：phase阶段全部完成后，将已完成功能归档到`04-OVERVIEW.md`

---

# 🎯 当前 Sprint：Phase 2 - Markdown 编辑器模块开发

> **开发形式**：独立模块，遵循微服务架构思想
> **目标**：开发生产级可复用的 WYSIWYG Markdown 编辑器  
> **最终目标**：可复用到其他项目，并可选择开源到 GitHub + npm
> **设计文档**：[Markdown 编辑器概设.md](01-Markdown%20编辑器概设.md)

---

## ✅ 已完成功能

### 1. **基础架构**（部分完成）

- ✅ 类型系统 (`types/editor.ts`)
- ✅ Selection工具函数 (`utils/selection.ts`)
  - getTextContent() - BR标签修复
  - getAbsoluteOffset()
  - getNodeAndOffset()
- ✅ `useSelection` Composable
  - 文本选择、光标控制、范围替换
  - 包裹文本、插入文本
  - 当前行信息

### 2. **Markdown格式化**（核心完成）

- ✅ `useMarkdown` Composable
  - applyInlineFormat() - 粗体、斜体、代码、高亮、链接
  - applyParagraphFormat() - 标题(H1-H3)、引用
  - insertBlock() - 代码块、图片、表格、视频、嵌入链接、分割线
  - ✅ 光标位置bug修复（4个关键bug）
  - ✅ 自动换行逻辑优化
- ✅ `utils/markdown.ts` - Markdown转HTML + 外部链接新窗口

### 3. **UI组件层**（✅ 已完成 - 2025-11-28）

- ✅ `EditorContent.vue`
  - contenteditable 编辑区
  - 集成 useMarkdown 和 useSelection
  - v-model 双向绑定
  - defineExpose 暴露 API
  - 完整的样式和注释

- ✅ `EditorToolbar.vue`
  - 固定工具栏（完整版）
  - 行内格式：Bold, Italic, Code, Highlight, Link
  - 段落格式：H1, H2, H3, Quote
  - 块级插入：CodeBlock, Image, Table, Divider
  - 使用 Lucide Icons
  - 分类事件系统

- ✅ `MarkdownEditor.vue`
  - 整合 EditorContent + EditorToolbar + 标题输入
  - v-model 双向绑定（content + title）
  - Props/Events 配置
  - defineExpose 暴露统一 API
  - 响应式样式

### 4. **测试基础设施**

- ✅ 基础HTML测试页面（selection、offset、roundtrip）
- ✅ Markdown转换测试页面
- ✅ EditorDemo.vue（手动测试工具）
- ✅ 浏览器自动化测试（Browser Subagent）

---

## ❌ 待实现功能

| 优先级        | 功能模块                     | 预计时间  | 依赖                                  | 状态          |
| ------------- | ---------------------------- | --------- | ------------------------------------- | ------------- |
| ~~**P0** 🔴~~ | ~~**UI组件层**~~             | ~~5-7天~~ | ~~useMarkdown, useSelection~~         | ✅ **已完成** |
| **P0** 🔴     | **useHistory** (撤销/重做)   | 2-3天     | 独立                                  | ⏳ 待开始     |
| **P1** 🟡     | **useMarkdownEditor** (整合) | 1-2天     | useMarkdown, useSelection, useHistory | ⏳ 待开始     |
| **P2** 🟢     | **useAutoSave**              | 1-2天     | useMarkdownEditor                     | ⏳ 待开始     |
| **P2** 🟢     | **useShortcuts** (快捷键)    | 1天       | useMarkdown                           | ⏳ 待开始     |

**✅ UI组件层已完成！为什么下一步是 useHistory？**

- ✅ 撤销/重做是编辑器的核心功能
- ✅ 独立模块，不依赖其他功能
- ✅ 完成后可以立即集成到 UI 中测试

---

## 🚀 下一步实施计划

### ✅ 第一阶段：UI组件层（已完成 - 2025-11-28）⭐⭐⭐⭐⭐

**目标**：实现可用的编辑器界面 ✅

#### ✅ Day 1-2: 核心编辑组件

- [x] **创建 EditorContent.vue**
  - [x] contenteditable 编辑区
  - [x] 集成 useMarkdown
  - [x] 集成 useSelection
  - [x] 基础样式
  - [x] v-model 双向绑定
  - [x] defineExpose API

- [x] **EditorTitle**（已集成到 MarkdownEditor）
  - [x] 标题输入框
  - [x] 回车键聚焦正文（可优化） ✅ 2025-11-28

#### ✅ Day 3-4: 工具栏

- [x] **创建 EditorToolbar.vue**
  - [x] 实现固定工具栏（完整版）
  - [x] 行内格式：Bold, Italic, Code, Highlight, Link
  - [x] 段落格式：H1, H2, H3, Quote
  - [x] 块级插入：CodeBlock, Image, Table, Divider
  - [x] 使用 Lucide Icons
  - [x] 分类事件系统

#### ✅ Day 5: 主组件整合

- [x] **创建 MarkdownEditor.vue**
  - [x] 整合 EditorContent + EditorToolbar + 标题输入
  - [x] 实现 v-model 双向绑定（content + title）
  - [x] Props/Events 配置
  - [x] 基础样式调整
  - [x] defineExpose 暴露统一 API

#### ✅ 额外完成：Bug修复与优化

- [x] 段落格式光标位置bug
- [x] 非空行自动换行
- [x] 空编辑器插入失败
- [x] 块级元素光标位置
- [x] CSS详细注释
- [x] 完整的学习文档

**🎯 里程碑达成**：可用的编辑器界面！✅

---

### 第二阶段：核心功能增强（2-4天）

#### Day 6-7: 撤销/重做（历史记录管理）

##### ✅ 阶段1: 实现 useHistory 核心逻辑（已完成 - 2025-11-29）

- [x] **定义内部状态**
  - [x] transactions 历史快照数组
  - [x] currentIndex 当前指针位置
- [x] **实现辅助函数**
  - [x] generateId() - 生成唯一事务ID
- [x] **实现核心方法**
  - [x] pushTransaction() - 记录新操作
  - [x] undo() - 撤销到上一个状态
  - [x] redo() - 重做到下一个状态
- [x] **实现计算属性**
  - [x] canUndo - 是否可撤销
  - [x] canRedo - 是否可重做
- [x] **功能验证**
  - [x] 创建测试组件 HistoryTest.vue
  - [x] 验证7个核心场景（初始状态、历史分支、边界情况等）
  - [x] 所有测试通过 ✅

##### ⏳ 阶段2: 集成到 EditorContent（待实施）

- [ ] **初始化 useHistory**
  - [ ] 在 EditorContent.vue 中初始化 useHistory
  - [ ] 传递 editorState 参数
- [ ] **暴露 API**
  - [ ] 通过 defineExpose 暴露 undo/redo 方法
  - [ ] 暴露 canUndo/canRedo 状态
- [ ] **绑定快捷键**
  - [ ] 监听 Ctrl+Z（撤销）
  - [ ] 监听 Ctrl+Shift+Z（重做）
  - [ ] 处理 macOS 的 Cmd 键

##### ⏳ 阶段3: 在 useMarkdown 中记录操作（待实施）

- [ ] **修改 useMarkdown 签名**
  - [ ] 接收 historyModule 参数
- [ ] **集成 pushTransaction**
  - [ ] applyInlineFormat 操作后记录
  - [ ] applyParagraphFormat 操作后记录
  - [ ] insertBlock 操作后记录

##### ⏳ 阶段4: 处理用户输入（待实施）

- [ ] **实现防抖逻辑**
  - [ ] 在 handleInput 中添加防抖（500ms）
  - [ ] 合并连续输入为单个 transaction
- [ ] **处理边界情况**
  - [ ] 防抖期间撤销的处理
  - [ ] Delete/Backspace 操作的捕获

##### ⏳ 阶段5: UI 集成（待实施）

- [ ] **工具栏按钮**
  - [ ] 添加撤销按钮（Undo）
  - [ ] 添加重做按钮（Redo）
  - [ ] 根据 canUndo/canRedo 禁用按钮
- [ ] **完整测试**
  - [ ] 手动测试所有场景
  - [ ] 验证快捷键功能
  - [ ] 验证防抖合并

#### Day 8-9: 整合层

- [ ] **完善 useMarkdownEditor**
  - [ ] 整合 useMarkdown, useSelection, useHistory
  - [ ] 统一API
  - [ ] getContent / setContent / focus 等方法

**🎯 里程碑**：功能完整的编辑器！

---

### 第三阶段：体验优化（可选，2-3天）

#### 自动保存

- [ ] **实现 useAutoSave**
  - [ ] Debounce 输入事件
  - [ ] localStorage 保存
  - [ ] 草稿恢复
  - [ ] 保存状态显示

#### 快捷键

- [ ] **实现 useShortcuts**
  - [ ] Ctrl+B → 加粗
  - [ ] Ctrl+I → 斜体
  - [ ] Ctrl+K → 链接
  - [ ] 其他常用快捷键

---
