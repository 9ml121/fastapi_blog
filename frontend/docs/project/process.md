
# 项目开发进展

> **文档用途**：详细拆解当前 Phase 阶段任务清单（带状态）  
> **更新频率**：每完成子任务时更新  
> **已完成功能总结**：见 [overview.md](./overview.md)

---

## 当前 Sprint：Phase 2 - Markdown 编辑器模块开发

**开始时间**：2025-11-18  
**计划周期**：4 周（标准版本）  
**目标**：开发生产级可复用的 WYSIWYG Markdown 编辑器  
**最终目标**：可复用到其他项目，并可选择开源到 GitHub + npm

---

---

# 🚀 Phase 2: Markdown 编辑器模块开发（4周计划 - Plan B）

> **开发形式**：独立模块，遵循微服务架构思想  
> **目标**：开发完成后可复用到其他项目，最终开源到 GitHub + npm  
> **设计文档**：[markdown_editor_design.md](../design/markdown_editor_design.md)

## 📅 阶段规划

### **Week 1: Phase 1 - 基础架构 + 自动保存**

**目标**：搭建编辑器核心框架、类型系统、自动保存机制

**位置**：`frontend/src/components/editor/`

- [ ] **Task 1.1**: 创建编辑器类型定义 + 自动保存配置
  - [ ] 创建 `types/editor.ts`
  - [ ] 定义 EditorState, SelectionInfo, ToolbarConfig 等类型
  - [ ] 定义 EditorPlugin 插件接口
  - [ ] 编写类型文档注释
  
- [ ] **Task 1.2**: 实现 useMarkdownEditor Composable + 自动保存逻辑
  - [ ] 创建 `composables/useMarkdownEditor.ts`
  - [ ] 定义编辑器状态管理结构（content、title、isDirty等）
  - [ ] 实现自动保存逻辑（debounce 500ms、localStorage存储）
  - [ ] 实现自动恢复草稿功能
  - [ ] 定义核心编辑方法接口框架
  - [ ] 编写基础框架代码
  
- [ ] **Task 1.3**: 实现 selection 工具函数
  - [ ] 创建 `utils/selection.ts`
  - [ ] 实现 getSelection() - 获取选中文本
  - [ ] 实现 setSelection() - 设置光标位置
  - [ ] 实现 wrapText() - 包裹文本（加粗、斜体等）
  
- [ ] **Task 1.4**: 实现 markdown 工具函数
  - [ ] 创建 `utils/markdown.ts`
  - [ ] 配置 marked 库
  - [ ] 实现 parseMarkdown() 解析函数
  - [ ] 实现代码高亮（highlight.js）
  
- [ ] **Task 1.5**: 编写单元测试框架
  - [ ] 创建 `__tests__/editor.spec.ts`
  - [ ] 创建 `__tests__/useMarkdownEditor.spec.ts`
  - [ ] 创建 `__tests__/selection.spec.ts`
  - [ ] 测试框架配置

**验收标准**：
- ✅ TypeScript 编译无错误
- ✅ 所有类型定义导出正确（含 AutoSaveConfig）
- ✅ useMarkdownEditor 基础框架 + 自动保存逻辑可用
- ✅ 自动保存可正常保存到 localStorage
- ✅ 工具函数单元测试覆盖 ≥ 80%

---

### **Week 2: Phase 2 - 核心 WYSIWYG 功能**

**目标**：实现编辑器的核心编辑功能（所见即所得）

- [ ] **Task 2.1**: 实现 contenteditable 编辑区 + 集成自动保存
  - [ ] 创建 `sub-components/EditorContent.vue`
  - [ ] 实现 contenteditable div
  - [ ] 实现 input/change 事件监听
  - [ ] 集成自动保存：编辑内容触发 debounce 保存
  - [ ] 处理焦点状态
  
- [ ] **Task 2.2**: 完善 useMarkdownEditor 核心逻辑
  - [ ] 实现 bold() - 加粗
  - [ ] 实现 italic() - 斜体
  - [ ] 实现 insertLink() - 插入链接
  - [ ] 实现 insertHeading() - 插入标题
  - [ ] 实现 insertCodeBlock() - 插入代码块
  
- [ ] **Task 2.3**: 实现编辑历史（撤销/重做）
  - [ ] 实现 undo() 和 redo() 方法
  - [ ] 维护操作历史栈
  - [ ] 实现 canUndo() 和 canRedo() 状态检查
  
- [ ] **Task 2.4**: 实现浮动工具栏逻辑
  - [ ] 创建 `composables/useToolbar.ts`
  - [ ] 实现工具栏显示/隐藏逻辑
  - [ ] 实现按钮激活状态检测
  - [ ] 处理工具栏位置计算

**验收标准**：
- ✅ 编辑区可以实时输入 Markdown
- ✅ 工具栏方法能正确修改文本
- ✅ 撤销/重做功能正常
- ✅ 自动保存在编辑时每 500ms 触发一次
- ✅ 集成测试通过

---

### **Week 3: Phase 3 - UI 组件层**

**目标**：实现完整的编辑器 UI 组件

- [ ] **Task 3.1**: 实现标题输入组件
  - [ ] 创建 `sub-components/EditorTitle.vue`
  - [ ] contenteditable 标题框
  - [ ] 回车键聚焦正文
  
- [ ] **Task 3.2**: 实现头部组件 + 自动保存状态展示
  - [ ] 创建 `sub-components/EditorHeader.vue`
  - [ ] 显示自动保存状态（"自动保存中..."、"已保存"、保存时间）
  - [ ] 显示发布/草稿状态
  - [ ] 工具选项按钮
  
- [ ] **Task 3.3**: 完善编辑内容组件
  - [ ] 优化 EditorContent.vue
  - [ ] 处理占位符显示
  - [ ] 样式调整
  
- [ ] **Task 3.4**: 实现浮动工具栏组件
  - [ ] 创建 `sub-components/EditorToolbar.vue`
  - [ ] 工具栏按钮 (B/I/Link/Code/...)
  - [ ] 工具栏位置定位
  - [ ] 动画效果
  
- [ ] **Task 3.5**: 实现页脚组件
  - [ ] 创建 `sub-components/EditorFooter.vue`
  - [ ] 显示字数统计
  - [ ] 显示阅读时间
  - [ ] 显示保存时间
  
- [ ] **Task 3.6**: 实现主组件
  - [ ] 创建 `MarkdownEditor.vue`
  - [ ] 整合所有子组件
  - [ ] 实现 v-model 双向绑定
  - [ ] Props 和 Events 实现

- [ ] **Task 3.7**: 编写编辑器样式
  - [ ] 创建 `styles/editor.css`
  - [ ] 应用设计系统色彩和排版
  - [ ] 响应式设计（lg/md/sm）
  - [ ] 动画过渡

**验收标准**：
- ✅ 所有组件正确显示
- ✅ 响应式设计测试通过
- ✅ 组件集成测试覆盖 ≥ 85%

---

### **Week 4: Phase 4 - 测试、文档与优化**

**目标**：完善测试、优化性能、编写文档、实现增强功能

- [ ] **Task 4.1**: 完善单元测试
  - [ ] 补充 selection 工具函数测试
  - [ ] 补充 markdown 工具函数测试
  - [ ] 补充 useMarkdownEditor 测试
  - [ ] 达到 ≥ 85% 覆盖率
  
- [ ] **Task 4.2**: 编写集成测试
  - [ ] 测试编辑器完整流程
  - [ ] 测试撤销/重做
  - [ ] 测试快捷键
  - [ ] 集成测试覆盖 ≥ 85%
  
- [ ] **Task 4.3**: 性能优化与完善
  - [ ] 优化 Markdown 渲染性能
  - [ ] 优化光标位置检测
  - [ ] 优化内存占用
  - [ ] 代码风格检查（ESLint/Prettier）
  
- [ ] **Task 4.4**: 编写完整文档
  - [ ] 编写 `MarkdownEditor/README.md`
  - [ ] API 文档（Props/Events/Methods）
  - [ ] 使用示例（3种用法）
  - [ ] 开发者指南

- [ ] **Task 4.5**: 完善快捷键和辅助编辑函数
  - [ ] 实现快捷键系统（Ctrl+B、Ctrl+I、Ctrl+K 等）
  - [ ] 实现 insertTable() - 插入表格
  - [ ] 实现 insertImage() - 插入图片
  - [ ] 实现 insertQuote() - 插入引用
  - [ ] 优化自动保存触发机制（新增细粒度的debounce配置）

**验收标准**：
- ✅ 测试覆盖率 ≥ 85%，所有测试通过
- ✅ 编辑响应时间 < 100ms
- ✅ 文档完整清晰
- ✅ 所有快捷键正常工作

---

## 📅 未来可选阶段（Week 5+）

如果时间充足或后续项目需要，可选择进行以下工作：

### **Week 5: Phase 5 - Workspace 迁移**

**目标**：将编辑器迁移到 pnpm Workspace

- [ ] 创建 `packages/markdown-editor/` 目录
- [ ] 迁移源代码和测试
- [ ] 配置 Workspace 构建
- [ ] 更新前端依赖

---

### **Optional: Phase 5+ - 测试与优化**

**目标**：完善测试、优化性能、编写文档

- [ ] **Task 5.1**: 完善单元测试
  - [ ] 补充 selection 工具函数测试
  - [ ] 补充 markdown 工具函数测试
  - [ ] 补充 useMarkdownEditor 测试
  - [ ] 达到 ≥ 85% 覆盖率
  
- [ ] **Task 5.2**: 编写集成测试
  - [ ] 测试编辑器完整流程
  - [ ] 测试撤销/重做
  - [ ] 测试自动保存
  - [ ] 测试快捷键
  
- [ ] **Task 5.3**: 性能优化
  - [ ] 优化 Markdown 渲染性能
  - [ ] 优化光标位置检测
  - [ ] 优化内存占用
  
- [ ] **Task 5.4**: 编写完整文档
  - [ ] 编写 `MarkdownEditor/README.md`
  - [ ] API 文档（Props/Events/Methods）
  - [ ] 使用示例（3种用法）
  - [ ] 贡献者指南

- [ ] **Task 5.5**: 代码审查和优化
  - [ ] 代码风格检查（ESLint）
  - [ ] 类型安全检查（TypeScript）
  - [ ] 重复代码优化
  - [ ] 注释完善

**验收标准**：
- ✅ 测试覆盖率 ≥ 85%
- ✅ 所有测试通过
- ✅ 编辑响应时间 < 100ms
- ✅ 文档完整清晰

---

### **Optional: Phase 6 - Workspace 迁移深化**

**目标**：将编辑器迁移到 Workspace 并准备开源

- [ ] **Task 6.1**: 创建 Workspace 结构
  - [ ] 创建 `packages/markdown-editor/` 目录
  - [ ] 创建 `pnpm-workspace.yaml`
  - [ ] 更新根 `package.json`
  
- [ ] **Task 6.2**: 迁移编辑器代码
  - [ ] 复制源代码到 `packages/markdown-editor/src/`
  - [ ] 复制测试到 `packages/markdown-editor/tests/`
  - [ ] 创建 `packages/markdown-editor/package.json`
  - [ ] 创建 `packages/markdown-editor/tsconfig.json`
  
- [ ] **Task 6.3**: 配置 Workspace 构建
  - [ ] 配置编辑器构建脚本
  - [ ] 创建编辑器导出入口 (`index.ts`)
  - [ ] 更新前端依赖（改用 @blog/markdown-editor）
  - [ ] 测试 workspace 集成
  
- [ ] **Task 6.4**: 开源准备（文件）
  - [ ] 创建 `LICENSE` (MIT)
  - [ ] 创建 `CHANGELOG.md` (v0.1.0)
  - [ ] 创建 `CONTRIBUTING.md` (贡献指南)
  - [ ] 创建 `.github/workflows/` (CI/CD)

**验收标准**：
- ✅ Workspace 构建成功
- ✅ 前端项目能正常使用编辑器
- ✅ 所有测试通过

---

### **Optional: Phase 7 - 开源发布**

**目标**：开源到 GitHub 并发布 npm 包

- [ ] **Task 7.1**: GitHub 仓库设置
  - [ ] 上传代码到 GitHub
  - [ ] 配置 GitHub Actions (CI/CD)
  - [ ] 配置 Branch Protection Rules
  
- [ ] **Task 7.2**: 发布前准备
  - [ ] 完善 README.md
  - [ ] 编写快速开始指南
  - [ ] 完善 API 文档
  - [ ] 准备发布版本号 (v0.1.0)
  
- [ ] **Task 7.3**: 发布 npm 包
  - [ ] 配置 npm 账户和权限
  - [ ] 运行 `npm publish`
  - [ ] 验证 npm registry
  - [ ] 更新 CHANGELOG.md
  
- [ ] **Task 7.4**: 发布后维护
  - [ ] 收集社区反馈
  - [ ] 处理 GitHub Issues
  - [ ] 修复 Bug
  - [ ] 规划 v0.2.0 功能

**验收标准**：
- ✅ GitHub 仓库公开
- ✅ npm 包发布成功
- ✅ README 文档清晰
- ✅ CI/CD 正常工作

---

## 📊 完整任务清单

| Phase | 任务 | 周次 | 优先级 | 状态 |
|-------|------|------|--------|------|
| 1 | 创建类型定义 + AutoSaveConfig | 1 | P0 | ⬜ |
| 1 | Composable 框架 + 自动保存 | 1-2 | P0 | ⬜ |
| 1 | Selection 工具函数 | 2 | P0 | ⬜ |
| 1 | Markdown 工具函数 | 2 | P0 | ⬜ |
| 1 | 单元测试框架 | 2 | P1 | ⬜ |
| 2 | EditorContent + 自动保存集成 | 2 | P0 | ⬜ |
| 2 | 格式化方法实现 | 3 | P0 | ⬜ |
| 2 | 撤销/重做 | 3 | P1 | ⬜ |
| 2 | 工具栏逻辑 | 3 | P1 | ⬜ |
| 3 | UI 组件实现 | 4 | P1 | ⬜ |
| 3 | 编辑器样式 | 3 | P1 | ⬜ |
| 3 | 主组件整合 | 3 | P0 | ⬜ |
| 4 | 单元测试完善 | 4 | P1 | ⬜ |
| 4 | 集成测试 | 4 | P1 | ⬜ |
| 4 | 性能优化 | 4 | P1 | ⬜ |
| 4 | 文档编写 | 4 | P1 | ⬜ |
| 4 | 快捷键和辅助函数 | 4 | P2 | ⬜ |

---

## 🎯 关键里程碑

- **Week 1 末**：Phase 1 完成，有完整的类型系统 + 自动保存机制 + 工具函数
- **Week 2 末**：Phase 2 完成，有可用的编辑器核心功能 + 自动保存集成
- **Week 3 末**：Phase 3 完成，有完整的 UI 组件（包含自动保存状态显示）
- **Week 4 末**：Phase 4 完成，编辑器功能完整 + 85%+ 测试覆盖 + 完整文档

---

## 📅 下一步计划

立即开始 **Phase 1: 基础架构**（Week 1）

**本周任务**：
1. 创建编辑器类型定义 + AutoSaveConfig (Task 1.1)
2. 实现 useMarkdownEditor + 自动保存逻辑 (Task 1.2)
3. 实现 selection 工具函数 (Task 1.3)
4. 实现 markdown 工具函数 (Task 1.4)
5. 编写单元测试框架 (Task 1.5)
