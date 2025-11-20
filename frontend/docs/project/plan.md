> **文档用途**：制定前端开发学习计划
> **更新频率**：前端开发前
# 前端开发学习计划

## 项目概述

**目标**：为现有 FastAPI 博客后端开发完整的前端应用

**应用定位**：**个人博客 + 文章社交**二合一平台
- **个人博客模式**：创作者发布和管理文章，展示个人品牌
- **文章社交模式**：读者发现优质内容，进行社交互动

**设计理念**：**极简专业 + 创新个性**
- 参考 Claude.ai、Medium.com 的专业设计
- 融入紫色品牌色（#8B5CF6）彰显个性
- 内容优先，界面衬托而非主宰
- 支持两种模式的无缝切换

**技术栈**（已确定）：Vue 3 + Vite + TypeScript + Tailwind CSS + Pinia + Vue Router + Axios + Vditor + Lucide Icons

**学习周期**：2-3 周（每天 3-4 小时）

**核心原则**：
- ✅ 实战驱动：直接对接真实后端 API
- ✅ 渐进式学习：从基础到进阶，逐步深入
- ✅ 教学互动：理论讲解 + 实操任务 + 答疑复盘


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

**核心依赖包**（通过 pnpm 管理）：
- `vue` - Vue 3 框架
- `vite` - 构建工具
- `typescript` - 类型检查
- `pinia` - 状态管理
- `vue-router` - 路由
- `axios` - HTTP 客户端
- `vditor` - Markdown 编辑器
- `marked` - Markdown 渲染
- `tailwindcss` - CSS 框架
- `lucide-vue-next` - Icon 库 ⭐ 新增
- `vee-validate` - 表单验证（可选）
- `@vitejs/plugin-vue` - Vite Vue 插件

**安装所有依赖**：
```bash
pnpm install
```

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

# 使用 pnpm 安装依赖（注意：不再使用 npm install）
pnpm install

# 安装 Tailwind CSS
pnpm add -D tailwindcss @tailwindcss/vite

# 安装 Vditor（编辑器）
pnpm add vditor

# 安装 marked（Markdown 渲染）
pnpm add marked

# 安装 Lucide Icons
pnpm add lucide-vue-next
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
pnpm dev
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
| Lucide Icons 官方 | https://lucide.dev/ | Icon 库 ⭐ 新增 |
| Lucide Vue Next | https://lucide.dev/guide/packages/lucide-vue-next | Vue 3 集成 ⭐ 新增 |
| pnpm 官方文档 | https://pnpm.io/zh/ | 包管理器 ⭐ 新增 |

---
