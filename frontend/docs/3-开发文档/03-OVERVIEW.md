> **文档用途**：记录项目已完成功能概览
> **更新频率**：Phase 完成

# 已完成功能 overview

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

## Phase 3: 登录功能开发

**目标**：实现完整的用户登录功能，包括前端 UI 和 API 对接

### 1. 前端 UI 组件

- ✅ 登录页面基础布局（`LoginView.vue`）
- ✅ 品牌 Logo 组件（`BrandLogo.vue`）
- ✅ 输入框组件（`FormInput.vue`）
- ✅ 密码可见性切换
- ✅ 登录按钮加载状态动画
- ✅ 错误提示显示

### 2. 认证模块 (`modules/auth/`)

- ✅ Token 管理工具（`token.ts`）
- ✅ Axios 实例 + 拦截器（`api.ts`）
- ✅ Pinia Auth Store（`auth.store.ts`）

### 3. API 对接

- ✅ 登录 API 调用（OAuth2 表单格式）
- ✅ 登录成功跳转（`router.push`）
- ✅ 401 错误区分处理（登录失败 vs Token 过期）

### 4. 路由守卫

- ✅ 全局前置守卫（`beforeEach`）
- ✅ 路由 meta 权限标记（`requiresAuth`）
- ✅ 未登录重定向到登录页

### 相关文档

- [登录功能 PRD](../1-需求文档/01-登录功能PRD.md)
- [登录功能概设](../2-设计文档/登录功能/登录功能概设.md)
- [登录页面 UI 设计](../2-设计文档/登录功能/登录页面UI设计.md)

---

## Phase 4: 注册功能开发

**目标**：实现完整的用户注册流程，包括邮箱验证码、前端 UI 和后端 API

### 1. 后端 API (`app/api/v1/endpoints/auth.py`)

- ✅ 发送验证码 API（`POST /auth/send-code`）
- ✅ 用户注册 API（`POST /auth/register`）
- ✅ 注册成功自动签发 JWT Token（免二次登录）

### 2. 邮件验证码系统

- ✅ Redis 验证码存储（`app/db/redis_client.py`）
  - `save_verification_code()` - 存储验证码（5分钟过期）
  - `verify_code()` - 校验验证码（验证成功后自动删除）
- ✅ 邮件发送服务（`app/core/email_utils.py`）
  - 使用 `fastapi-mail` + Jinja2 模板
  - 异步后台发送（`BackgroundTasks`）
- ✅ 邮件 HTML 模板（`app/templates/email_template.html`）
  - 品牌 Header + 验证码突出显示 + 有效期红色警示
  - 底部注册链接

### 3. 前端注册页面 (`RegisterView.vue`)

- ✅ 表单布局（邮箱、密码、确认密码、验证码）
- ✅ 发送验证码按钮 + 60秒倒计时
- ✅ 实时表单校验（`@/utils/validators`）
- ✅ 密码可见性切换
- ✅ 加载状态动画
- ✅ 错误信息显示

### 4. 认证状态管理 (`auth.store.ts`)

- ✅ `register()` action - 调用注册 API
- ✅ 注册成功后自动保存 token + user 信息
- ✅ 注册成功跳转首页

### 5. Toast 通知组件

- ✅ `toast.store.ts` - Pinia 状态管理
- ✅ `ToastContainer.vue` - 全局通知容器
  - 四种类型：success/error/warning/info
  - `TransitionGroup` 列表动画
  - 3秒自动消失

### 6. API 封装 (`auth.api.ts`)

- ✅ `registerApi()` - 注册接口
- ✅ `sendCodeApi()` - 发送验证码接口
- ✅ 统一 `AuthResponse` 类型定义

### 相关文件清单

| 层级 | 文件路径 |
|-----|---------|
| 后端 API | `app/api/v1/endpoints/auth.py` |
| 后端 Schema | `app/schemas/user.py` |
| 后端 CRUD | `app/crud/user.py` |
| Redis 工具 | `app/db/redis_client.py` |
| 邮件服务 | `app/core/email_utils.py` |
| 邮件模板 | `app/templates/email_template.html` |
| 前端页面 | `frontend/src/views/RegisterView.vue` |
| 前端 Store | `frontend/src/stores/auth.store.ts` |
| 前端 Store | `frontend/src/stores/toast.store.ts` |
| 前端组件 | `frontend/src/components/ToastContainer.vue` |
| 前端 API | `frontend/src/api/auth.api.ts` |
| 表单验证 | `frontend/src/utils/validators.ts` |

---

## Phase 5: 忘记密码功能开发

**目标**：实现完整的密码重置流程，包括邮箱验证码、前端 UI 和后端 API

### 1. 后端 API (`app/api/v1/endpoints/auth.py`)

- ✅ 忘记密码 API（`POST /auth/forgot-password`）
  - 校验邮箱必须已注册（区别于注册场景）
  - 生成 6 位随机验证码
  - 存储到 Redis（5分钟过期）
  - 异步发送验证码邮件
- ✅ 重置密码 API（`POST /auth/reset-password`）
  - 校验验证码有效性
  - 更新用户密码（复用 `update_password` CRUD）
  - 验证成功后自动删除验证码

### 2. 后端 Schema (`app/schemas/user.py`)

- ✅ `PasswordReset` Schema
  - `email`: 邮箱地址（EmailStr 校验）
  - `new_password`: 新密码（强密码校验）
  - `verification_code`: 6位数字验证码（正则校验）

### 3. 后端 CRUD (`app/crud/user.py`)

- ✅ `update_password()` 函数
  - 职责单一：只负责更新密码哈希值
  - 权限校验交由 API 层处理
  - 同时支持"修改密码"和"重置密码"两种场景

### 4. 前端重置密码页面 (`ForgotPasswordView.vue`)

- ✅ 表单布局（邮箱、新密码、确认密码、验证码）
- ✅ 发送验证码按钮 + 60秒倒计时（复用 `useCountdown`）
- ✅ 实时表单校验
  - 邮箱格式校验
  - 密码强度校验（8位+大小写+数字）
  - 确认密码一致性校验
  - 验证码 6 位数字校验
- ✅ 密码可见性切换（Eye/EyeOff 图标）
- ✅ 加载状态动画（Loader2 旋转）
- ✅ 错误提示处理
  - 邮箱未注册提示
  - 验证码错误提示
- ✅ 重置成功后跳转登录页

### 5. 前端 API 封装 (`auth.api.ts`)

- ✅ `forgotPasswordApi()` - 发送验证码接口
- ✅ `resetPasswordApi()` - 重置密码接口
- ✅ `ResetPasswordParams` 类型定义

### 6. 前端路由配置 (`router/index.ts`)

- ✅ 添加 `/forgot-password` 路由
- ✅ 无需登录即可访问（公开路由）

### 7. Composable 工具函数

- ✅ `useCountdown` Composable（`composables/useCountdown.ts`）
  - 倒计时逻辑复用（注册页、重置密码页共用）
  - 防止重复启动
  - 自动清理定时器（onUnmounted）

### 8. 业务逻辑亮点

| 功能点 | 实现细节 |
|--------|---------|
| **邮箱校验差异** | 注册时拒绝已存在的邮箱；忘记密码时要求邮箱必须已注册 |
| **错误提示优化** | 根据后端错误码（`RESOURCE_NOT_FOUND`/`INVALID_VERIFICATION_CODE`）精准提示 |
| **验证码安全** | 验证成功后自动删除（防止重复使用） |
| **UI 一致性** | 复用 `FormInput`/`BrandLogo` 等组件，保持设计统一 |
| **用户体验** | 重置成功后 Toast 提示 + 1秒延迟跳转登录页 |

### 相关文件清单

| 层级 | 文件路径 |
|-----|---------|
| 后端 API | `app/api/v1/endpoints/auth.py` |
| 后端 Schema | `app/schemas/user.py` (`PasswordReset`) |
| 后端 CRUD | `app/crud/user.py` (`update_password`) |
| 前端页面 | `frontend/src/views/ForgotPasswordView.vue` |
| 前端 API | `frontend/src/api/auth.api.ts` |
| 前端路由 | `frontend/src/router/index.ts` |
| 前端工具 | `frontend/src/composables/useCountdown.ts` |
| 表单验证 | `frontend/src/utils/validators.ts` |

---

# 📍 Next: 待定（文章管理 / 个人主页 / 其他）
