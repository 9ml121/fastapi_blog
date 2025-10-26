# 项目开发进展

> **文档用途**：AI 快速了解项目进度和历史已完成内容
> **更新频率**：Phase 开始、子任务完成、Phase 完成

---

## 🎯 当前任务

**Phase 6 - 社交功能与内容增强**（🚀 进行中）

**当前子任务**：Phase 6.3 - 统计面板（中优先级）

**下一步行动**：

1. 开始 Phase 6.3 统计面板功能开发
2. 可选：Phase 6.4 通知系统基础版开发

---

## ✅ 已完成功能清单（避免重复开发）

### Phase 1-2：基础设施 ✅

-   ✅ SQLAlchemy 模型：`User`, `Post`, `Comment`, `Tag`, `PostView`
    -   代码位置：`app/models/*.py`
-   ✅ 数据库配置和迁移（Alembic）
-   ✅ 应用配置：`app/core/config.py`

### Phase 3：认证系统 ✅

-   ✅ 用户注册/登录 API
-   ✅ JWT Token 认证：`app/core/security.py`
-   ✅ 权限依赖：`get_current_user`, `get_current_active_user`
-   ✅ User CRUD 完整实现

### Phase 4：内容管理 ✅

-   ✅ **文章 CRUD**：`app/crud/post.py`, `app/api/v1/endpoints/posts.py`
    -   支持标签关联（多对多）
    -   权限控制（作者/管理员）
-   ✅ **标签 CRUD**：`app/crud/tag.py`, `app/api/v1/endpoints/tags.py`
    -   去重逻辑、删除保护
-   ✅ **评论 CRUD**：`app/crud/comment.py`, `app/api/v1/endpoints/comments.py`
    -   递归树形结构
    -   嵌套路由：`/posts/{post_id}/comments`
-   ✅ **技术模式**：
    -   泛型 CRUD 基类
    -   RESTful 最佳实践（PATCH 语义）
    -   selectinload 优化 N+1 查询

### Phase 5：API 完善与前端准备 ✅

-   ✅ **用户资料管理**：`app/api/v1/endpoints/users.py`
    -   个人资料查看/更新（`/users/me`）
    -   密码修改（旧密码验证）
-   ✅ **全局异常处理系统**：`app/core/exceptions.py`
    -   自定义异常基类 + 8 个业务异常类
    -   统一错误格式（支持前端国际化）
    -   4 个全局异常处理器
-   ✅ **泛型分页系统**：`app/core/pagination.py`
    -   `PaginatedResponse[ItemType]` 泛型设计
    -   安全排序功能（防 SQL 注入）
    -   支持多种过滤条件
-   ✅ **CORS 跨域配置**：前后端分离支持
-   ✅ **测试体系完善**：
    -   306 个测试，100% 通过率
    -   91% 测试覆盖率（目标 85%）
    -   测试数据四象限全覆盖

### Phase 6：社交功能与内容增强 ✅

-   ✅ **草稿系统**：完整的文章状态管理（draft/published/archived）
    -   数据模型：Post 模型扩展 status 和 published_at 字段
    -   CRUD 层：get_user_drafts、publish、archive、revert_to_draft 方法
    -   API 端点：GET /posts/drafts、PATCH /posts/{id}/publish 等
    -   权限控制：草稿和归档文章仅作者可见
-   ✅ **架构优化重构**：CRUD 层分页逻辑分离
    -   分页逻辑从 CRUD 层移动到 core 层（符合行业最佳实践）
    -   Post CRUD：get_paginated → build_published_posts_query
    -   Comment CRUD：get_paginated_by_post → build_top_level_comments_query
    -   业务逻辑优化：公开接口默认只返回已发布文章
    -   代码质量：无 linting 错误，测试覆盖率保持
-   ✅ **点赞收藏系统**：完整的用户互动功能（Phase 6.2）🎉 2025-10-26
    -   数据模型：PostLike 和 PostFavorite 模型，支持唯一约束和级联删除
    -   CRUD 层：幂等操作 toggle_like、toggle_favorite，状态查询方法
    -   API 端点：8 个 RESTful 端点，支持点赞/收藏和状态查询
    -   高级功能：文章置顶（featured posts）、查询优化
    -   测试覆盖：27 个测试全部通过，覆盖各种边界情况
    -   技术亮点：幂等性设计、性能优化、权限控制、RESTful 设计

---

## 📅 Phase 6 - 社交功能与内容增强（当前阶段）

**整体目标**：增强用户互动体验，完善内容创作流程，提升平台活跃度

**预估工作量**：6-10 天

**验收标准**：

-   ✅ 草稿系统（保存/发布/归档）
-   ✅ 点赞/收藏功能（幂等性设计）🎉 2025-10-26
-   [ ] 统计面板（作者数据看板）
-   [ ] 通知系统基础版（评论/点赞通知）
-   ✅ 测试覆盖率 ≥ 85%

**设计原则**：

-   🎯 **用户价值优先**：优先实现用户刚需功能
-   ⚡ **性能优化**：缓存点赞数、浏览量等高频访问数据
-   🔒 **幂等性设计**：防止重复点赞、重复收藏
-   🧪 **测试驱动**：继续保持 TDD 开发模式


---

### 🎯 Phase 6.3 - 统计面板（中优先级）⭐⭐⭐

**目标**：为作者提供数据统计功能，展示文章表现和用户互动数据

**用户故事**：

-   作为作者，我希望看到我的文章总览数据（总文章数、总浏览量、总点赞数）
-   作为作者，我希望看到单篇文章的详细数据（浏览量、点赞数、评论数）
-   作为作者，我希望看到最近热门文章（按浏览量或点赞数排序）

**核心交付**：

#### 1. Schema 设计

-   [ ] `AuthorStats`：作者统计数据响应
    -   `total_posts`: 总文章数
    -   `total_views`: 总浏览量
    -   `total_likes`: 总点赞数
    -   `total_comments`: 总评论数
    -   `trending_posts`: 热门文章列表
-   [ ] `PostDetailStats`：单篇文章统计
    -   `view_count`: 浏览量
    -   `like_count`: 点赞数
    -   `comment_count`: 评论数
    -   `favorite_count`: 收藏数

#### 2. CRUD 层实现

-   [ ] `user.get_author_stats()`：聚合查询作者统计数据
-   [ ] `post.get_post_stats()`：获取单篇文章统计
-   [ ] `post.get_trending_posts()`：获取热门文章（7 天内）

#### 3. API 端点

-   [ ] `GET /users/me/stats`：获取我的统计数据
-   [ ] `GET /posts/{id}/stats`：获取文章统计数据
-   [ ] `GET /posts/trending`：获取热门文章列表

#### 4. 测试

-   [ ] 统计聚合测试（验证计算准确性）
-   [ ] 热门文章排序测试
-   [ ] 空数据测试（新用户无文章）
-   [ ] 性能测试（聚合查询性能）

**技术要点**：

-   聚合查询：使用 SQLAlchemy 的 `func.count()`、`func.sum()`
-   性能优化：考虑缓存统计数据（Redis）
-   时间范围：热门文章限定最近 7 天

**预估工作量**：1-2 天

---

### 🎯 Phase 6.4 - 通知系统基础版（中优先级）⭐⭐⭐

**目标**：实现基础通知功能，及时告知作者文章互动情况

**用户故事**：

-   作为作者，当有人评论我的文章时，我希望收到通知
-   作为作者，当有人点赞我的文章时，我希望收到通知
-   作为用户，我希望查看未读通知，标记已读

**核心交付**：

#### 1. 数据模型设计

-   [ ] 创建 `Notification` 模型
    -   `user_id`: 接收通知的用户 ID
    -   `type`: 通知类型（comment/like/reply）
    -   `content`: 通知内容
    -   `related_post_id`: 关联文章 ID（可选）
    -   `related_comment_id`: 关联评论 ID（可选）
    -   `is_read`: 是否已读
    -   `created_at`: 创建时间
-   [ ] 数据库迁移脚本

#### 2. Schema 设计

-   [ ] `NotificationResponse`：通知响应
-   [ ] `NotificationType`：通知类型枚举

#### 3. CRUD 层实现

-   [ ] `notification.create_notification()`：创建通知
-   [ ] `notification.get_user_notifications()`：获取用户通知（分页）
-   [ ] `notification.mark_as_read()`：标记已读
-   [ ] `notification.get_unread_count()`：获取未读数量

#### 4. 业务逻辑集成

-   [ ] 评论创建时：通知文章作者（评论通知）
-   [ ] 评论回复时：通知被回复者（回复通知）
-   [ ] 点赞时：通知文章作者（点赞通知）
-   [ ] 通知去重：同一文章的点赞通知合并

#### 5. API 端点

-   [ ] `GET /notifications`：获取通知列表（分页）
-   [ ] `GET /notifications/unread-count`：获取未读数量
-   [ ] `PATCH /notifications/{id}/read`：标记单个通知已读
-   [ ] `PATCH /notifications/mark-all-read`：标记所有通知已读
-   [ ] `DELETE /notifications/{id}`：删除通知

#### 6. 测试

-   [ ] 通知创建测试（评论、点赞触发通知）
-   [ ] 通知查询测试（分页、过滤）
-   [ ] 已读状态测试
-   [ ] 通知去重测试
-   [ ] 权限测试（只能查看自己的通知）

**技术要点**：

-   事件驱动：在评论、点赞等操作后触发通知创建
-   通知去重：相同类型的通知合并（如多人点赞同一文章）
-   性能优化：使用 `unread_count` 字段缓存未读数量
-   扩展性：预留 WebSocket/SSE 实时推送接口

**预估工作量**：2-3 天

**注意事项**：

-   当前版本为轮询方式，前端定时请求通知列表
-   Phase 7 可升级为 WebSocket 实时推送

---

## 📝 Phase 6 开发顺序

**推荐顺序**：6.2 → 6.3 → 6.4

**理由**：

1. **点赞/收藏**优先：为统计面板和通知系统提供数据基础
2. **统计面板**其次：依赖点赞/收藏数据，展示数据价值
3. **通知系统**最后：依赖前面所有功能，构建完整闭环

**灵活调整**：

-   如果时间紧张，可先完成 6.2，其余放到 Phase 7
-   如果想快速看到效果，可 6.2 → 6.4（跳过统计面板）

---
