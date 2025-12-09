> **文档用途**：记录项目已完成功能概览
> **更新频率**：Phase 完成

# ✅ 已完成功能 overview

## Phase 1: 搭建前端基础架构和设计系统

**目标**：掌握 Vue 3 核心概念，初步了解前端常用框架和技术

### 1. 开发环境搭建

- ✅ 初始化 Vite + Vue 3 + TypeScript 项目
- ✅ 配置 ESLint 和 Prettier
- ✅ 启动开发服务器（Port 5174）

### 2. 学习前端项目结构

```
fastapi_blog/
├── app/              # 后端代码（已完成 FastAPI）
├── frontend/         # 前端代码（新建 Vue 3）
│   ├── docs/
│   │   ├── design/   # 前端设计文档
│   │   ├── learning/ # 前端学习文档
│   │   ├── project/  # 前端项目管理文档
│   ├── src/
│   │   ├── pages/          # 页面组件
│   │   │   ├── Home.vue
│   │   │   ├── PostDetail.vue
│   │   │   ├── PostCreate.vue
│   │   │   ├── Login.vue
│   │   │   ├── Register.vue
│   │   │   └── Profile.vue
│   │   ├── components/     # 可复用组件
│   │   │   ├── Header.vue
│   │   │   ├── Footer.vue
│   │   │   ├── CommentList.vue
│   │   │   └── MarkdownEditor.vue
│   │   ├── composables/    # 组合式函数（逻辑复用）
│   │   │   ├── useAuth.ts
│   │   │   ├── usePosts.ts
│   │   │   └── useComments.ts
│   │   ├── stores/         # Pinia 全局状态
│   │   │   ├── auth.ts
│   │   │   ├── posts.ts
│   │   │   └── notifications.ts
│   │   ├── utils/          # 工具函数
│   │   │   ├── api.ts      # Axios 实例 + 拦截器
│   │   │   ├── token.ts    # JWT Token 管理
│   │   │   └── format.ts   # 日期、文本格式化
│   │   ├── router/         # Vue Router 配置
│   │   │   └── index.ts
│   │   ├── assets/         # 静态资源
│   │   │   ├── mian.css    # 全局样式
│   │   │   └── images/
│   │   ├── App.vue         # 根组件
│   │   └── main.ts         # 应用入口
│   ├── index.html          # 应用的 HTML 入口点
│   ├── public/             # 静态文件
│   ├── package.json        # 前端项目包管理
│   ├── vite.config.ts      # Vite 配置
│   ├── tsconfig.json       # TypeScript 配置
└── (后端文件省略...)
```

### 3. 前端技术栈确认

| 分类              | 技术栈                | 说明                       |
| ----------------- | --------------------- | -------------------------- |
| **框架层**        | Vue 3 Composition API | 现代、易学、官方标准       |
| **构建工具**      | Vite                  | 秒级热更新、配置简洁       |
| **类型检查**      | TypeScript            | 类型安全、开发体验好       |
| **包管理器**      | pnpm                  | 快速、精益、严格的依赖管理 |
| **样式方案**      | 原生 CSS              | 参考 Tailwind 设计系统     |
| **Icon 库**       | Lucide Icons          | 精致、定制、500+ 图标库    |
| **状态管理**      | Pinia                 | 官方推荐、API 简洁         |
| **路由管理**      | Vue Router            | 官方标准、灵活配置         |
| **HTTP 客户端**   | Axios                 | 拦截器、请求封装           |
| **Markdown 编辑** | marked.js             | 尽可能原生实现             |
| **表单验证**      | Vee-Validate          | 可选（初期不使用）         |
| **代码质量**      | ESLint + Prettier     | 强制代码风格、自动格式化   |
| **开发工具**      | Vue DevTools + Vite   | 调试、性能分析             |

> 详见：`design/技术选型和设计理念.md`

---

## Phase 2: Markdown 编辑器模块开发

**目标**：开发生产级可复用的 WYSIWYG Markdown 编辑器

### 1. 基础架构

- ✅ 类型系统（InlineFormatType、ParagraphFormatType、BlockInsertType）
- ✅ Selection 工具函数、useSelection Composable
- ✅ useMarkdownEditor 统一 API 接口

### 2. Markdown 格式化

- ✅ useMarkdown Composable（行内格式、段落格式、块级插入）
- ✅ 光标位置 bug 修复、自动换行优化

### 3. UI 组件层

- ✅ EditorContent.vue（contenteditable 编辑区）
- ✅ EditorToolbar.vue（格式化工具栏）
- ✅ MarkdownEditor.vue（整合组件）

### 4. 历史管理

- ✅ useHistory Composable（撤销/重做、快捷键支持）
- ✅ IME 输入优化（防止中间态记录）

### 5. Live Preview 实时渲染

- ✅ useLivePreview Composable（行类型检测）
- ✅ CSS 驱动的样式渲染（标题、列表、引用、代码块）
- ✅ Enter 键自动延续格式
- ✅ Typora 风格符号交互（活动行显示、非活动行隐藏）
- ✅ H1 唯一性检查警告

### 6. 目录导航

- ✅ useTableOfContents Composable
- ✅ TableOfContents.vue 组件
- ✅ TOC 点击跳转（scroll-margin-top）
- ✅ 滚动高亮（Intersection Observer）
- ✅ 空目录自动隐藏

### 7. 粘贴处理

- ✅ 纯文本粘贴（清除富文本格式）
- ⏸️ HTML → Markdown 转换（暂未实现）

### 8. 待完成功能（已暂停）

| 功能                             | 状态    |
| -------------------------------- | ------- |
| 行内格式标记（粗体、斜体、代码） | ⏸️ 暂停 |
| 自动保存                         | ⏸️ 暂停 |
| 快捷键扩展                       | ⏸️ 暂停 |
| 性能优化                         | ⏸️ 暂停 |

---

# 📍 Next: 待定（后端/其他前端功能）
