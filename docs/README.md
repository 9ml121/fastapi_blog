# 项目文档导航

欢迎来到 FastAPI 博客系统的文档中心！本项目采用全栈开发，文档按前后端分离组织。

## 📋 快速导航

### 🎯 项目管理（所有人必读）
- **[项目概览](./project/overview.md)** - 已完成功能一览
- **[后端开发计划](./project/plan_backend.md)** - 后端 Product Backlog
- **[前端开发计划](./project/plan_frontend.md)** - 前端 Product Backlog
- **[当前开发进展](./project/process.md)** - Sprint Backlog
- [技术债务清单](./project/todos.md) - 待优化项

### 🔧 开发规范（开发必读）
- **[Python 编码规范](./standards/python.md)** - 后端代码标准
- **[数据库模型规范](./standards/database-models.md)** - SQLAlchemy 开发标准
- **[测试开发规范](./standards/testing.md)** - 测试标准和要求
- [前端编码规范](./standards/frontend.md) - 前端代码标准（待创建）

### 🏗️ 后端设计文档
架构决策、技术选型、为什么这样设计
- [Phase 6 - 通知系统概设](./design_backend/phase6_通知系统概设.md)
- [更多设计文档](./design_backend/) - 后端设计目录

### 📚 后端学习文档
编码教程、实战指南、如何实现
- [Phase 4 - 文章管理 CRUD](./learning_backend/phase4_文章管理/)
- [Phase 5 - API 完善](./learning_backend/phase5_API完善/)
- [Phase 6 - 社交功能](./learning_backend/phase6_社交功能/)
- [更多学习文档](./learning_backend/) - 后端学习目录

### 🏗️ 前端设计文档
架构决策、技术选型、为什么这样设计
- [Phase 1 - 架构设计](./design_frontend/phase1_架构设计.md)（待创建）
- [更多设计文档](./design_frontend/) - 前端设计目录

### 📚 前端学习文档
编码教程、实战指南、如何实现
- **[Phase 1 - Vue 3 基础](./learning_frontend/phase1_vue3_basics.md)** - Vue 3 入门教程
- [更多学习文档](./learning_frontend/) - 前端学习目录

### 🗄️ 数据库相关
- [数据库 Schema](./database/schema.sql) - 表结构定义
- [数据库设计说明](./database/design.md) - ER 图和关系设计（待创建）

---

## 🎯 使用指南

### 📖 场景 1：开始新的开发任务
1. 查看 **project/plan_*.md** 了解任务目标和验收标准
2. 阅读 **design_*/phaseX_概设.md** 理解架构设计
3. 参考 **learning_*/phaseX_*.md** 学习实现方法
4. 遵循 **standards/** 中的开发规范

### 🔍 场景 2：了解项目进展
1. 查看 **project/overview.md** - 已完成功能一览
2. 查看 **project/process.md** - 当前正在做什么

### 🐛 场景 3：查找问题答案
- **开发规范问题** → `standards/`
- **架构设计问题** → `design_*/`
- **编码实现问题** → `learning_*/`
- **项目进展问题** → `project/`
- **数据库问题** → `database/`

---

## 📚 文档分类说明

| 分类 | 职责 | 典型内容 | 更新频率 |
|------|------|---------|---------|
| **project/** | 项目管理 | 任务清单、进度追踪、已完成功能 | 频繁更新 |
| **standards/** | 开发规范 | 编码风格、命名规范、必须遵循的规则 | 项目初期制定 |
| **design_*/** | 架构设计 | 技术选型、架构图、为什么这样设计 | Phase 开始前 |
| **learning_*/** | 编码教程 | 代码示例、实战任务、如何实现 | 编码过程中 |
| **database/** | 数据库专项 | Schema、迁移脚本、ER 图 | 数据库变更时 |

---

## 🔄 文档维护

### 典型开发流程中的文档更新
1. **Phase 开始**：更新 `project/plan_*.md`（制定计划）
2. **设计阶段**：创建 `design_*/phaseX_概设.md`（架构设计）
3. **编码阶段**：创建 `learning_*/phaseX_*.md`（教程）+ 更新 `project/process.md`（进度）
4. **Phase 完成**：更新 `project/overview.md`（总结）

### 文档更新责任
- 📝 **AI**：自动更新 process.md、创建 learning 文档、design 文档
- 👤 **用户**：Review 并确认 plan 文档、overview 文档、记录 todos.md

### 具体案例：开发"通知系统"功能

```
1. 制定计划
   project/plan_backend.md
   → Phase 6.4：通知系统（任务清单、验收标准）

2. 架构设计
   design_backend/phase6_通知系统概设.md
   → 为什么用事件驱动？为什么聚合通知？技术选型对比

3. 编码教程
   learning_backend/phase6_社交功能/phase6_4_通知系统代码讲解.md
   → 如何实现通知 CRUD？代码示例、留白任务

4. 数据库变更
   alembic/versions/xxx_add_notifications.py
   → Alembic 迁移脚本

5. 进度追踪
   project/process.md
   → 标记"通知系统"子任务完成状态

6. 完成总结
   project/overview.md
   → 添加"✅ 通知系统：事件驱动、智能聚合"
```

---

**💡 提示**：建议将此页面加入书签，作为文档查找的起点！
