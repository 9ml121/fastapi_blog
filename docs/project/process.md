# 项目开发进展

> **文档用途**：AI 快速了解项目进度和历史已完成内容
> **更新频率**：Phase 开始、子任务完成、Phase 完成

---

## 🎯 当前任务

**Phase 6 - 社交功能与内容增强**（🚀 进行中）

**当前子任务**：Phase 6.1 - 草稿系统（高优先级）

**下一步行动**：

1. 开始 Phase 6.1 草稿系统开发

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
-   ✅ **泛型分页系统**：`app/api/pagination.py`
    -   `PaginatedResponse[ItemType]` 泛型设计
    -   安全排序功能（防 SQL 注入）
    -   支持多种过滤条件
-   ✅ **CORS 跨域配置**：前后端分离支持
-   ✅ **测试体系完善**：
    -   306 个测试，100% 通过率
    -   91% 测试覆盖率（目标 85%）
    -   测试数据四象限全覆盖

---

## 📅 Phase 6 - 社交功能与内容增强（当前阶段）

**整体目标**：增强用户互动体验，完善内容创作流程，提升平台活跃度

**预估工作量**：6-10 天

**验收标准**：

-   ✅ 草稿系统（保存/发布/归档）
-   ✅ 点赞/收藏功能（幂等性设计）
-   ✅ 统计面板（作者数据看板）
-   ✅ 通知系统基础版（评论/点赞通知）
-   ✅ 测试覆盖率 ≥ 85%

**设计原则**：

-   🎯 **用户价值优先**：优先实现用户刚需功能
-   ⚡ **性能优化**：缓存点赞数、浏览量等高频访问数据
-   🔒 **幂等性设计**：防止重复点赞、重复收藏
-   🧪 **测试驱动**：继续保持 TDD 开发模式

---

### 🎯 Phase 6.1 - 草稿系统（高优先级）⭐⭐⭐⭐⭐

**目标**：实现文章草稿保存、发布、归档功能，完善内容创作流程

**用户故事**：

-   作为作者，我希望保存未完成的文章草稿，以便稍后继续编辑
-   作为作者，我希望预览草稿效果，确认无误后再发布
-   作为作者，我希望将过时文章归档，不再公开展示

**核心交付**：

#### 1. 数据模型扩展

-   [x] 扩展 Post 模型的 `status` 字段 ✅ 2025-10-16
    -   `draft`: 草稿（仅作者可见）
    -   `published`: 已发布（公开可见）
    -   `archived`: 已归档（仅作者可见）
-   [x] 添加 `published_at` 字段（发布时间） ✅ 2025-10-16
-   [x] 数据库迁移脚本 ✅ 2025-10-16

#### 2. Schema 设计

-   [x] 更新 `PostCreate`：支持指定初始 status ✅ 2025-10-17
-   [x] 更新 `PostUpdate`：允许更新 status ✅ 2025-10-17

#### 3. CRUD 层实现

-   [x] `post.get_user_drafts()`：获取用户草稿列表 ✅ 2025-10-17
-   [x] `post.publish()`：发布草稿（更新 status 和 published_at） ✅ 2025-10-17
-   [x] `post.archive()`：归档文章 ✅ 2025-10-17
-   [x] `post.revert_to_draft()`: 转换为草稿 ✅ 2025-10-17
-   [x] 更新 `get_paginated()`：支持 status 过滤 ✅ 2025-10-17

#### 4. API 端点

-   [x] `GET /posts/drafts`：查看我的草稿列表 ✅ 2025-10-17
-   [x] `POST /posts/`：创建文章（默认 status=draft） ✅ 2025-10-17
-   [x] `PATCH /posts/{id}/publish`：发布草稿 ✅ 2025-10-17
-   [x] `PATCH /posts/{id}/archive`：归档文章 ✅ 2025-10-17
-   [x] 更新 `GET /posts/`：只返回已发布文章（公开访问） ✅ 2025-10-17
-   [x] 更新权限控制：草稿和归档文章仅作者可见 ✅ 2025-10-17

#### 5. 测试

-   [x] 草稿 CRUD 测试（创建、查询、更新） ✅ 2025-10-18
-   [x] 发布流程测试（draft → published） ✅ 2025-10-18
-   [x] 归档流程测试（published → archived） ✅ 2025-10-18
-   [x] 权限控制测试（其他用户无法查看草稿） ✅ 2025-10-18
-   [x] 边界测试（空草稿、重复发布等） ✅ 2025-10-18

**技术要点**：

-   状态机设计：draft → published → archived
-   权限控制：草稿和归档文章仅作者可访问
-   业务规则：已发布文章可以回退为草稿

**预估工作量**：1-2 天

---

### 🏗️ 架构优化任务 - CRUD 层分页逻辑重构（Phase 6.1 完成后）⭐⭐⭐⭐

**背景**：当前 CRUD 层违反了分层原则，调用了 API 层的分页工具

**问题**：

-   ❌ CRUD 层耦合了 API 层的 `paginate_query()` 方法
-   ❌ 破坏了分层独立性和单测能力
-   ❌ 使得其他服务（CLI、定时任务）难以复用 CRUD 层
-   ❌ 公开接口支持 `statuses` 多选，不符合业务逻辑

**改进方案**：

-   重构 CRUD 层：分离 `build_query()` 方法（仅构建查询对象，不分页）
-   重命名 `get_paginated` → `get_published_posts`（语义明确）
-   API 层直接调用 `pagination.paginate_query()`
-   移除 `PostFilters` 的 `statuses` 字段（公开接口只返回已发布）
-   统一应用到 Post、Comment、Tag 等所有模型

**预期效果**：

-   ✅ 分层独立，职责清晰
-   ✅ 提升可测试性
-   ✅ 便于跨服务复用
-   ✅ 业务逻辑更清晰

**预估工作量**：2-3 天

---

#### 📋 重构步骤详解

**阶段 1：Schema 层修改**

-   [ ] **Step 1：修改 PostFilters 模型**
    -   移除 `statuses` 字段（不再支持状态多选）
    -   更新类文档注释
    -   更新示例数据
    -   文件：`app/schemas/post.py`
-   [ ] **Step 2：添加 AdminPostFilters 模型**
    -   新增用于管理员接口的过滤器
    -   支持 `statuses` 字段（多选）
    -   文件：`app/schemas/post.py`

**阶段 2：CRUD 层重构（Post）**

-   [ ] **Step 3：创建 `build_query()` 方法**
    -   提取查询构建逻辑
    -   返回 SQLAlchemy `Select` 对象
    -   包含状态过滤逻辑：默认只返回已发布
    -   支持其他过滤条件（作者、标签、标题等）
    -   文件：`app/crud/post.py`
-   [ ] **Step 4：重构 `get_published_posts()` 方法**
    -   重命名：`get_paginated` → `get_published_posts`
    -   调用 `build_query()` 获取查询对象
    -   应用分页逻辑（调用 `paginate_query()`）
    -   返回 `tuple[list[Post], int]`
    -   文件：`app/crud/post.py`
-   [ ] **Step 5：添加 `get_all_posts()` 方法**
    -   用于管理员查询（包含所有状态）
    -   调用 `build_query()`（无状态限制）
    -   应用分页逻辑
    -   需要权限检查（由 API 层负责）
    -   文件：`app/crud/post.py`

**阶段 3：API 层修改（Posts）**

-   [ ] **Step 6：更新 `GET /posts/` 端点**
    -   更新调用：`post_crud.get_published_posts(...)`
    -   更新文档注释
    -   更新示例 URL
    -   移除 `is_published` 相关说明
    -   文件：`app/api/v1/endpoints/posts.py`
-   [ ] **Step 7：添加 `GET /posts/admin` 端点**
    -   管理员专用端点
    -   调用：`post_crud.get_all_posts(...)`
    -   需要权限检查
    -   支持状态多选过滤
    -   文件：`app/api/v1/endpoints/posts.py`

**阶段 4：其他 CRUD 模型重构（可选）**

-   [ ] **Step 8：检查并修改 Comment CRUD**
    -   如果有类似的 `get_paginated` 方法，进行相同重构
    -   文件：`app/crud/comment.py`、`app/api/v1/endpoints/comments.py`
-   [ ] **Step 9：检查并修改 Tag CRUD**
    -   如果有类似的 `get_paginated` 方法，进行相同重构
    -   文件：`app/crud/tag.py`、`app/api/v1/endpoints/tags.py`

**阶段 5：测试更新**

-   [ ] **Step 10：更新 CRUD 层测试**
    -   修改 `test_crud/test_post.py`
    -   测试 `build_query()` 的查询构建
    -   测试 `get_published_posts()` 的分页逻辑
    -   测试 `get_all_posts()` 的管理员查询
    -   验证默认只返回已发布
    -   移除 `statuses` 参数相关测试
    -   文件：`tests/test_crud/test_post.py`
-   [ ] **Step 11：更新 API 层测试**
    -   修改 `test_api/test_posts.py`
    -   更新 `TestGetPosts` 相关测试
    -   添加 `TestGetPostsAdmin` 测试类
    -   移除 `statuses` 参数相关测试
    -   验证权限控制
    -   文件：`tests/test_api/test_posts.py`

**阶段 6：最终检查**

-   [ ] **Step 12：代码质量检查**
    -   执行 `uv run ruff check app/crud/post.py --fix`
    -   执行 `uv run mypy app/crud/post.py`
    -   执行 `uv run pytest tests/ -v`
    -   执行 `uv run pytest --cov=app` 验证覆盖率 ≥ 85%
    -   移除所有 TODO 注释
-   [ ] **Step 13：文档更新**
    -   更新方法文档字符串
    -   更新使用示例
    -   更新 API 文档
    -   更新 process.md 标记完成

---

#### ✅ 验收标准

1. **代码标准**

    - ✅ ruff 检查通过（0 错误）
    - ✅ mypy 检查通过（0 错误）
    - ✅ 所有测试通过（100% 通过率）
    - ✅ 测试覆盖率 ≥ 85%

2. **功能要求**

    - ✅ 公开接口只返回已发布文章
    - ✅ 管理员接口可以查看所有状态
    - ✅ CRUD 层完全独立，不调用 API 层方法
    - ✅ 分页逻辑完全在 API 层

3. **架构要求**
    - ✅ 分层清晰：CRUD 层职责专一
    - ✅ 可测试性提升：CRUD 层方法易于单测
    - ✅ 可复用性提升：其他服务可直接使用 CRUD 层
    - ✅ 业务逻辑清晰：API 层负责分页、权限；CRUD 层负责数据访问

---

### 📌 注意事项

1. **方法命名变化**

    - `get_paginated` → `get_published_posts`（公开接口）
    - 新增：`get_all_posts`（管理员接口）

2. **Schema 变化**

    - `PostFilters` 移除 `statuses` 字段
    - 新增：`AdminPostFilters`（包含 `statuses`）

3. **API 变化**

    - 新增：`GET /posts/admin` 管理员端点
    - 公开接口默认只返回已发布

4. **向后兼容性**
    - ⚠️ API 行为改变：公开接口不再支持 `statuses` 参数
    - ✅ 新增管理员端点支持完整过滤

---

### 🎯 Phase 6.2 - 点赞与收藏（高优先级）⭐⭐⭐⭐

**目标**：实现文章点赞和收藏功能，提升用户互动体验

**用户故事**：

-   作为读者，我希望点赞喜欢的文章，表达认可
-   作为读者，我希望收藏文章，方便日后查阅
-   作为作者，我希望看到文章的点赞数和收藏数

**核心交付**：

#### 1. 数据模型设计

-   [ ] 创建 `PostLike` 模型（多对多关系表）
    -   `user_id`: 点赞用户 ID
    -   `post_id`: 文章 ID
    -   `created_at`: 点赞时间
    -   唯一约束：`(user_id, post_id)`
-   [ ] 创建 `PostFavorite` 模型（多对多关系表）
    -   结构同 `PostLike`
-   [ ] 扩展 Post 模型
    -   添加 `like_count` 字段（缓存点赞数）
    -   添加 `favorite_count` 字段（缓存收藏数）
-   [ ] 数据库迁移脚本

#### 2. Schema 设计

-   [ ] `PostLikeResponse`：点赞记录响应
-   [ ] `PostWithLikeStatus`：文章响应（包含当前用户是否已点赞）
-   [ ] 更新 `PostResponse`：添加 `like_count`、`favorite_count` 字段

#### 3. CRUD 层实现

-   [ ] `post_like.toggle_like()`：切换点赞状态（幂等）
-   [ ] `post_like.get_user_liked_posts()`：获取用户点赞的文章
-   [ ] `post_like.get_post_likes()`：获取文章的点赞列表
-   [ ] `post_favorite.toggle_favorite()`：切换收藏状态
-   [ ] `post_favorite.get_user_favorites()`：获取用户收藏的文章
-   [ ] 实现计数缓存更新逻辑

#### 4. API 端点

-   [ ] `POST /posts/{id}/like`：点赞/取消点赞（幂等）
-   [ ] `GET /posts/{id}/likes`：获取点赞列表（分页）
-   [ ] `GET /users/me/liked-posts`：我点赞的文章
-   [ ] `POST /posts/{id}/favorite`：收藏/取消收藏（幂等）
-   [ ] `GET /users/me/favorites`：我的收藏列表
-   [ ] 更新 `GET /posts/{id}`：返回当前用户的点赞/收藏状态

#### 5. 测试

-   [ ] 点赞功能测试（点赞、取消、重复点赞）
-   [ ] 收藏功能测试（收藏、取消、重复收藏）
-   [ ] 计数缓存测试（验证 count 字段准确性）
-   [ ] 权限测试（未登录用户无法点赞）
-   [ ] 边界测试（不存在的文章、已删除的文章）
-   [ ] 性能测试（批量点赞操作）

**技术要点**：

-   幂等性设计：多次点赞只记录一次
-   计数缓存：使用 `like_count` 字段避免频繁 COUNT 查询
-   数据一致性：点赞/取消时同步更新计数
-   性能优化：使用唯一约束防止重复插入

**预估工作量**：2-3 天

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

**推荐顺序**：6.1 → 6.2 → 6.3 → 6.4

**理由**：

1. **草稿系统**优先：独立功能，无依赖，提升创作体验
2. **点赞/收藏**其次：为统计面板和通知系统提供数据基础
3. **统计面板**第三：依赖点赞/收藏数据，展示数据价值
4. **通知系统**最后：依赖前面所有功能，构建完整闭环

**灵活调整**：

-   如果时间紧张，可先完成 6.1 + 6.2，其余放到 Phase 7
-   如果想快速看到效果，可 6.1 → 6.2 → 6.4（跳过统计面板）

---
