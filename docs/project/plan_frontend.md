> **文档用途**：制定前端开发学习计划
> **更新频率**：前端开发前
# 前端开发学习计划

## 项目概述

**目标**：为现有 FastAPI 博客后端开发完整的前端应用

**技术栈**（已确定）：Vue 3 + Vite + TypeScript + Tailwind CSS + Pinia + Vue Router + Axios + Vditor

**学习周期**：2-3 周（每天 3-4 小时）

**核心原则**：
- ✅ 实战驱动：直接对接真实后端 API
- ✅ 渐进式学习：从基础到进阶，逐步深入
- ✅ 教学互动：理论讲解 + 实操任务 + 答疑复盘

---

## 技术选型决策思路

本前端项目采用**轻量级、高效率**的技术栈设计。以下是关键决策：

### 1️⃣ **框架选择：Vue 3（而非 React）**

| 决策因素 | Vue 3 | React |
|---------|-------|-------|
| 学习曲线 | ⭐ 平缓 | ⭐⭐⭐ 陡峭 |
| 初学者友好度 | ✅ 最优 | ⚠️ 需要 JS 基础 |
| 项目进度 | ✅ 快 | ⚠️ 慢 |
| 与 FastAPI 的适配 | ✅ 完美 | ✅ 完美 |

**决策理由**：
- ✅ 你已学过 Vue 3，再换框架浪费时间
- ✅ Vue 3 的 Composition API 适合博客这类项目
- ✅ 官方文档中文友好，遇到问题易解决
- ⚠️ React 的函数式编程更适合大团队复杂项目，现在不需要

**何时学 React？** 功能完成后（3-6 个月），作为职业拓展。有 Vue 基础，学 React 只需 2-3 周。

---

### 2️⃣ **构建工具：Vite（而非 Webpack）**

| 维度 | Vite | Webpack |
|------|------|---------|
| 冷启动 | 100ms | 5000ms+ |
| HMR 更新 | 毫秒级 | 秒级 |
| 配置复杂度 | ⭐ 简单 | ⭐⭐⭐ 复杂 |
| 官方推荐 | ✅ Vue 官方标配 | ⚠️ 逐步淘汰 |

**决策理由**：
- ✅ `npm create vue@latest` 默认使用 Vite
- ✅ 开发体验最好（秒级热更新）
- ✅ 配置最简洁（基本零配置）
- ✅ 生产环保优化（Rollup）

---

### 3️⃣ **样式方案：Tailwind CSS（而非 Element Plus/Ant Design）**

| 维度 | Tailwind CSS | Element Plus | Ant Design Vue |
|------|-------------|--------------|----------------|
| 学习难度 | ⭐ 平缓 | ⭐⭐ 中等 | ⭐⭐ 中等 |
| 自定义程度 | ✅✅ 极高 | ⚠️ 受限 | ⚠️ 受限 |
| 文件体积 | ✅ 仅需要的部分 | ⚠️ 整个组件库 | ⚠️ 整个组件库 |
| 学习价值 | ✅ 深入理解 CSS | ❌ 黑盒使用组件 | ❌ 黑盒使用组件 |
| 响应式支持 | ✅✅ 一流 | ✅ 好 | ✅ 好 |

**决策理由**：
- ✅ 初学者应该学习 CSS 基础，而非依赖组件库
- ✅ Tailwind 的 utility-first 思想高效且易懂
- ✅ 自定义能力强，博客设计不受束缚
- ✅ 生产包体积小（只打包用到的样式）
- ⚠️ 组件库在大型企业应用中有优势，博客项目用不上

---

### 4️⃣ **状态管理：Pinia（而非 Vuex/Redux）**

| 维度 | Pinia | Vuex | Redux |
|------|-------|------|-------|
| API 易用性 | ✅ 最好 | ⚠️ 冗长 | ❌ 复杂 |
| TypeScript 支持 | ✅ 一流 | ⚠️ 次优 | ✅ 好 |
| 包体积 | ✅ 最小 | ⚠️ 较大 | ⚠️ 较大 |
| Vue 官方推荐 | ✅ 官方新标准 | ⚠️ 已淘汰 | - |

**决策理由**：
- ✅ Pinia 是 Vue 官方推荐的最新方案
- ✅ API 简洁（直观的 getters 和 actions）
- ✅ TypeScript 原生支持
- ✅ 博客项目的全局状态简单（用户、通知），Pinia 完全足够

**用户状态示例**：
```typescript
// stores/auth.ts
export const useAuthStore = defineStore('auth', () => {
  const user = ref(null)
  const isLoggedIn = computed(() => !!user.value)
  
  const login = async (credentials) => {
    const response = await api.post('/login', credentials)
    user.value = response.data
  }
  
  return { user, isLoggedIn, login }
})
```

---

### 5️⃣ **Markdown 编辑器：Vditor（而非 Editor.js）**

| 维度 | Vditor | Editor.js |
|------|--------|-----------|
| 学习难度 | ⭐ 简单 | ⭐⭐⭐ 复杂 |
| Markdown 支持 | ✅ 原生完美 | ⚠️ 需要插件 |
| 初始化代码 | ✅ 3 行 | ⚠️ 20+ 行 + 插件 |
| 与 Vue 3 集成 | ✅ 零成本 | ⚠️ 需要适配 |
| 中文文档 | ✅ 完善 | ⚠️ 英文为主 |
| 博客适配度 | ✅✅ 完美 | ⚠️ 过度设计 |
| 包体积 | ✅ 200KB | ⚠️ 更大（+ 插件） |

**决策理由**：
- ✅ 博客的核心是 Markdown，Vditor 完全适配
- ✅ 编辑 Markdown → 存储 Markdown → 展示 Markdown，流程最简洁
- ✅ Editor.js 是为"富内容编辑"设计（如 Notion），博客用不上
- ✅ 国内用户多，遇到问题容易找到解决方案

**核心集成流程**：
```vue
<!-- 编辑页面 -->
<div id="vditor"></div>

<script>
const markdown = vditor.getValue()  // 获得 Markdown
// 发送给 FastAPI 存储
</script>

<!-- 显示页面 -->
<div v-html="marked(post.content)"></div>

<script>
// FastAPI 返回的是 Markdown，用 marked.js 渲染成 HTML
</script>
```

**简洁高效，无冗余！**

---

### 6️⃣ **后端集成：FastAPI（维持现状，不用 Nuxt 后端）**

| 架构方案 | 适用场景 | 推荐度 |
|---------|---------|--------|
| **前后端分离**（当前） | ✅ 初学者 / 博客项目 / 前后端分工 | ✅✅✅ 最推荐 |
| Nuxt 全栈 | ⚠️ 简单项目 / 想要 SSR | ⚠️ 后阶段可选 |
| 混合（Next.js） | ⚠️ React 项目 / 要求 SSR | ❌ 当前不适用 |

**决策理由**：
- ✅ FastAPI 后端已完成，功能完善（6 个 Phase）
- ✅ 前后端分离是业界标准，解耦最彻底
- ✅ 前端 Vue、后端 Python，各自独立发展
- ✅ API 通信通过 REST，零耦合
- ⏰ **Week 3 可选**：如果需要 SSR/SEO，升级 Nuxt 3（FastAPI 保持不变）

**数据流**：
```
前端（Vue）→ HTTP 请求 → FastAPI 后端 → 数据库
前端（Vue）← HTTP 响应 ← FastAPI 后端 ← 数据库
```

完全清晰，无任何冲突！

---

### 7️⃣ **路由方案：Vue Router（而非 Nuxt 自动路由）**

**决策理由**：
- ✅ Vue Router 是 Vue 官方标准路由
- ✅ 学习价值：深入理解路由机制（不是黑盒）
- ✅ 配置自由度高，适合学习
- ⏰ **Week 3 可选**：升级 Nuxt 3 后，改用约定式路由

**示例路由配置**：
```typescript
// router/index.ts
const routes = [
  { path: '/', component: () => import('../pages/Home.vue') },
  { path: '/posts/:id', component: () => import('../pages/PostDetail.vue') },
  { path: '/posts/create', component: () => import('../pages/PostCreate.vue') },
  { path: '/login', component: () => import('../pages/Login.vue') },
]
```

---

## 完整技术栈总结

```
┌─────────────────────────────────────────────────────────┐
│              前端技术栈最终确定版                        │
├─────────────────────────────────────────────────────────┤
│                                                         │
│  框架层        Vue 3 Composition API                   │
│  构建工具      Vite（秒级热更新）                       │
│  类型检查      TypeScript（类型安全）                   │
│  样式方案      Tailwind CSS（utility-first）           │
│  状态管理      Pinia（官方标准）                        │
│  路由管理      Vue Router（官方标准）                   │
│  HTTP 客户端   Axios（拦截器、请求封装）              │
│  编辑器        Vditor + marked.js（Markdown 方案）     │
│  表单验证      Vee-Validate（可选）                     │
│  代码质量      ESLint + Prettier（强制风格）           │
│  开发工具      Vue DevTools + Vite 调试                │
│                                                         │
│  后端（不变）  FastAPI + PostgreSQL                    │
│  API 通信      REST HTTP 协议                           │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## 整体架构

```
fastapi_blog/
├── app/              # 后端代码（已完成 FastAPI）
├── frontend/         # 前端代码（新建 Vue 3）
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
│   │   │   ├── styles/     # Tailwind + 全局样式
│   │   │   └── images/
│   │   ├── App.vue         # 根组件
│   │   └── main.ts         # 应用入口
│   ├── public/             # 静态文件
│   ├── package.json
│   ├── vite.config.ts      # Vite 配置
│   ├── tsconfig.json       # TypeScript 配置
│   └── tailwind.config.js  # Tailwind 配置
├── docs/
│   ├── design_frontend/    # 前端设计文档
│   └── learning_frontend/  # 前端学习文档
└── (后端文件省略...)
```

**架构设计原则**：
- ✅ `pages/` = 页面级组件（对应路由）
- ✅ `components/` = 可复用组件（无路由）
- ✅ `composables/` = 逻辑复用（hooks）
- ✅ `stores/` = 全局状态（Pinia）
- ✅ `utils/` = 工具函数（API、认证等）
- ✅ 清晰的职责划分，易于维护和扩展

---

## 学习路径（2周核心 + 1周进阶）

### Week 1：Vue 3 基础 + 核心功能（7天）

**目标**：掌握 Vue 3 核心概念，实现登录和文章管理

#### Phase 1.1：Vue 3 基础（Day 1-2）
- [ ] 搭建开发环境（Vite + TypeScript）
- [ ] Vue 3 核心概念（响应式、组件、生命周期）
- [ ] 实战：创建基础布局组件（Header、Footer、Sidebar）
- [ ] 验收：运行开发服务器，展示基础页面

#### Phase 1.2：API 对接 + 认证（Day 3-4）
- [ ] Axios 封装与拦截器配置
- [ ] JWT Token 管理（登录、刷新、持久化）
- [ ] 实战：登录/注册页面 + Token 自动续期
- [ ] 验收：登录成功后跳转，Token 过期自动刷新

#### Phase 1.3：文章列表 + 路由（Day 5-7）
- [ ] Vue Router 配置（路由守卫、动态路由）
- [ ] 列表渲染 + 分页组件
- [ ] 实战：文章列表页 + 详情页 + Markdown 渲染
- [ ] 验收：分页加载、路由跳转、未登录拦截

---

### Week 2：完整功能 + 状态管理（7天）

**目标**：完成所有核心功能，掌握状态管理和组件通信

#### Phase 2.1：文章发布 + Markdown 编辑器（Day 8-9）
- [ ] 表单处理 + 表单验证（Vee-Validate）
- [ ] **Markdown 编辑器集成（Vditor）** ✅ 已确定
- [ ] 实战：文章发布/编辑页 + 草稿自动保存
- [ ] 验收：实时预览、标签选择、图片上传

**为什么选 Vditor？** 详见"技术选型决策思路"第 5️⃣ 点

#### Phase 2.2：评论系统 + 交互功能（Day 10-11）
- [ ] 组件通信（Props、Emit、Provide/Inject）
- [ ] 嵌套评论组件实现
- [ ] 实战：评论列表 + 发表评论 + 点赞/收藏
- [ ] 验收：实时更新评论数、乐观更新 UI

#### Phase 2.3：状态管理 + 用户中心（Day 12-14）
- [ ] Pinia 状态管理（Store 定义、Getters、Actions）
- [ ] 全局状态：用户信息、通知数量
- [ ] 实战：个人中心（资料编辑、我的文章、草稿箱）
- [ ] 验收：状态同步、权限控制（作者/管理员）

---

### Week 3：Nuxt 3 升级 + 生产部署（可选 / 进阶）

**目标**：（可选）迁移到 Nuxt 3，实现 SSR 和生产环境部署

**何时升级？**
- ✅ 功能完全实现（Week 1-2）
- ✅ 需要 SEO 优化（文章页 SSR 渲染）
- ✅ 想要首屏加载速度优化

**重要**：FastAPI 后端保持不变！Nuxt 只处理前端渲染层。

#### Phase 3.1：Nuxt 3 项目迁移（Day 15-17）
- [ ] Nuxt 3 项目结构与约定
- [ ] 服务端渲染（SSR）与数据获取
- [ ] 实战：迁移现有代码到 Nuxt 架构
- [ ] 验收：SEO 友好的文章页、首屏渲染速度

#### Phase 3.2：生产环境配置（Day 18-19）
- [ ] API 代理配置（Nginx 反向代理）
- [ ] 环境变量管理（.env）
- [ ] 实战：Docker 容器化 + CI/CD 配置
- [ ] 验收：前后端联调成功、生产环境访问

#### Phase 3.3：性能优化 + 进阶特性（Day 20-21）
- [ ] 懒加载、代码分割、图片优化
- [ ] PWA 支持（离线访问、通知推送）
- [ ] 实战：性能监控（Lighthouse）+ 优化报告
- [ ] 验收：Lighthouse 评分 90+

---

## 学习资源

### 官方文档（必读）
- [Vue 3 官方文档](https://cn.vuejs.org/)
- [Nuxt 3 官方文档](https://nuxt.com.cn/)
- [Pinia 官方文档](https://pinia.vuejs.org/zh/)
- [Vue Router 官方文档](https://router.vuejs.org/zh/)

### 推荐教程
- **Vue Mastery**（英文视频，质量高）
- **技术胖 Vue 3 实战**（B站，中文免费）
- **Nuxt 3 从入门到精通**（官方课程）

### 工具推荐

**VS Code 插件**（开发工具）：
- Volar（Vue 官方语言支持）
- ESLint（代码检查）
- Prettier（代码格式化）
- Tailwind CSS IntelliSense（样式自动完成）

**浏览器插件**：
- Vue DevTools（Vue 调试工具）

**npm 包**（核心依赖）：
- `vue` - 框架
- `vite` - 构建工具
- `typescript` - 类型检查
- `pinia` - 状态管理
- `vue-router` - 路由
- `axios` - HTTP 客户端
- `vditor` - Markdown 编辑器 ✅
- `marked` - Markdown 渲染 ✅
- `tailwindcss` - CSS 框架 ✅
- `vee-validate` - 表单验证（可选）
- `@vitejs/plugin-vue` - Vite Vue 插件

**官方文档**（必读）：
- [Vditor 文档](https://ld246.com/article/1549638745630)（中文详细）
- [Tailwind CSS 文档](https://tailwindcss.com/)
- [Marked 文档](https://marked.js.org/)

---

## 当前进度

### ✅ 已完成
- [x] 创建学习计划文档

### 🔄 进行中
- [ ] Phase 1.1：Vue 3 基础（Day 1-2）

### 📋 待开始
- [ ] Phase 1.2：API 对接 + 认证
- [ ] Phase 1.3：文章列表 + 路由
- [ ] Phase 2.1：文章发布 + Markdown 编辑器
- [ ] Phase 2.2：评论系统 + 交互功能
- [ ] Phase 2.3：状态管理 + 用户中心
- [ ] Phase 3.1：Nuxt 3 项目迁移（选修）
- [ ] Phase 3.2：生产环境配置（选修）
- [ ] Phase 3.3：性能优化 + 进阶特性（选修）

---

## 验收标准

### Week 1 验收（核心功能）
- ✅ 用户能登录/注册并保持登录状态
- ✅ 显示文章列表（分页、搜索）
- ✅ 查看文章详情（Markdown 渲染）
- ✅ 路由权限控制（未登录拦截）

### Week 2 验收（完整功能）
- ✅ 发布/编辑文章（Markdown 编辑器）
- ✅ 评论系统（发表、嵌套、点赞）
- ✅ 个人中心（资料管理、文章管理）
- ✅ 全局状态管理（用户、通知）

### Week 3 验收（生产就绪）
- ✅ SEO 友好（SSR）
- ✅ 生产环境部署成功
- ✅ Lighthouse 评分 90+
- ✅ 移动端响应式适配

---

## 学习建议

1. **理论与实践结合**
   - 每天先学理论（1小时），再实战编码（2-3小时）
   - 遇到问题先查文档，再问 AI

2. **代码质量保障**
   - 使用 ESLint + Prettier 保持代码风格
   - 组件拆分合理，单一职责原则
   - 写注释，特别是复杂逻辑

3. **进度追踪**
   - 每天更新 `frontend_process.md` 进度
   - 遇到困难及时记录到 `docs/learning_frontend/` 文档
   - 每周复盘，总结学习心得

4. **不要追求完美**
   - Week 1-2 先实现功能，不纠结样式
   - Week 3 再优化体验和性能
   - 渐进式改进，避免过早优化

---

## 下一步行动（Week 1 Day 1）

### Step 1️⃣：初始化 Vue 3 + Vite + Tailwind 项目

```bash
# 创建 Vue 3 + Vite 项目
npm create vue@latest frontend

# 选择配置（推荐）：
# ✅ TypeScript? Yes
# ✅ JSX? No
# ✅ Vue Router? Yes
# ✅ Pinia? Yes
# ✅ Vitest? Yes
# ✅ Playwright? No（可选）
# ✅ ESLint? Yes
# ✅ Prettier? Yes

cd frontend
npm install

# 安装 Tailwind CSS
npm install tailwindcss @tailwindcss/vite

# 安装 Vditor（编辑器）
npm install vditor

# 安装 marked（Markdown 渲染）
npm install marked
```

### Step 2️⃣：配置 Tailwind CSS

**vite.config.ts** - 添加 Tailwind 插件：
```typescript
import tailwindcss from '@tailwindcss/vite'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
})
```

**src/style.css** - 导入 Tailwind：
```css
@import "tailwindcss";
```

### Step 3️⃣：验证项目启动

```bash
npm run dev
```

访问 `http://localhost:5173`，看到欢迎页面即成功！

### Step 4️⃣：项目结构检查

```
frontend/
├── src/
│   ├── components/       # ✅ 已有
│   ├── stores/           # ✅ 已有（Pinia）
│   ├── router/           # ✅ 已有
│   ├── assets/           # ✅ 已有
│   ├── App.vue
│   ├── main.ts
│   └── style.css         # ✅ Tailwind 已导入
├── vite.config.ts        # ✅ Tailwind 已配置
└── package.json
```

---

## 学习资源总结

| 资源 | 链接 | 用途 |
|------|------|------|
| Vue 3 官方文档 | https://cn.vuejs.org/ | 官方标准 |
| Pinia 官方文档 | https://pinia.vuejs.org/zh/ | 状态管理 |
| Vue Router 官方文档 | https://router.vuejs.org/zh/ | 路由 |
| Vditor 文档 | https://ld246.com/article/1549638745630 | Markdown 编辑器 |
| Tailwind CSS 文档 | https://tailwindcss.com/ | 样式框架 |
| Marked 文档 | https://marked.js.org/ | Markdown 渲染 |
| Axios 文档 | https://axios-http.com/zh/ | HTTP 客户端 |

---

## 技术栈决策对标文档

本项目的技术选择已在"技术选型决策思路"部分详细论证。如有疑问，请参考：

- ✅ **为什么选 Vue 3？** → 第 1️⃣ 点
- ✅ **为什么选 Vite？** → 第 2️⃣ 点  
- ✅ **为什么选 Tailwind CSS？** → 第 3️⃣ 点
- ✅ **为什么选 Pinia？** → 第 4️⃣ 点
- ✅ **为什么选 Vditor？** → 第 5️⃣ 点
- ✅ **为什么不用 Nuxt 后端？** → 第 6️⃣ 点
- ✅ **为什么选 Vue Router？** → 第 7️⃣ 点

---

**准备好了吗？Week 1 Day 1 让我们开始代码！** 🚀
