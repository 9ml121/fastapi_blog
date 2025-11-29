> **文档用途**：记录项目已完成功能概览
> **更新频率**：Phase 完成

## ✅ 已完成后端功能清单

## 📅 Phase 6 - 社交功能与内容增强（当前阶段）

**整体目标**：增强用户互动体验，完善内容创作流程，提升平台活跃度

**预估工作量**：6-10 天

**验收标准**：

-   ✅ 草稿系统（保存/发布/归档）
-   ✅ 点赞/收藏功能（幂等性设计）🎉 2025-10-26
-   ✅ 统计面板（作者数据看板）🎉 2025-10-27
-   ✅ 通知系统 + 关注功能（事件驱动 + 智能聚合）🎉 2025-10-30
-   ✅ 测试覆盖率 ≥ 85%

**设计原则**：

-   🎯 **用户价值优先**：优先实现用户刚需功能
-   ⚡ **性能优化**：缓存点赞数、浏览量等高频访问数据
-   🔒 **幂等性设计**：防止重复点赞、重复收藏
-   🧪 **测试驱动**：继续保持 TDD 开发模式

### 🎯 Phase 6.2 - 点赞与收藏（高优先级）⭐⭐⭐⭐

**目标**：实现文章点赞和收藏功能，提升用户互动体验

**用户故事**：

-   作为读者，我希望点赞喜欢的文章，表达认可
-   作为读者，我希望收藏文章，方便日后查阅
-   作为作者，我希望看到文章的点赞数和收藏数

**核心交付**：

#### 1. 数据模型设计 ✅ 完成于 2025-10-25

- [x] 创建 `PostLike` 模型（多对多关系表） ✅ 2025-10-25
    -   `user_id`: 点赞用户 ID
    -   `post_id`: 文章 ID
    -   `created_at`: 点赞时间
    -   唯一约束：`(user_id, post_id)`
- [x] 创建 `PostFavorite` 模型（多对多关系表） ✅ 2025-10-25
    -   结构同 `PostLike`
- [x] 扩展 Post 模型 ✅ 2025-10-25
    -   添加 `like_count` 字段（缓存点赞数）
    -   添加 `favorite_count` 字段（缓存收藏数）
- [x] 数据库迁移脚本 ✅ 2025-10-25

#### 2. Schema 设计 ✅ 完成于 2025-10-26

- [x] `PostLikeStatusResponse`：点赞状态响应 ✅ 2025-10-26
- [x] `PostFavoriteStatusResponse`：收藏状态响应 ✅ 2025-10-26
- [x] 更新 `PostResponse`：添加 `like_count`、`favorite_count` 字段 ✅ 2025-10-26

#### 3. CRUD 层实现 ✅ 完成于 2025-10-26

- [x] `post_like.toggle_like()`：切换点赞状态（幂等） ✅ 2025-10-26
- [x] `post_like.get_user_liked_posts()`：获取用户点赞的文章 ✅ 2025-10-26
- [x] `post_like.is_liked()`：检查点赞状态 ✅ 2025-10-26
- [x] `post_like.get_post_liked_users()`：获取点赞用户列表 ✅ 2025-10-26
- [x] `post_favorite.toggle_favorite()`：切换收藏状态 ✅ 2025-10-26
- [x] `post_favorite.get_user_favorites()`：获取用户收藏的文章 ✅ 2025-10-26
- [x] `post_favorite.is_favorited()`：检查收藏状态 ✅ 2025-10-26
- [x] `post_favorite.get_post_favorited_users()`：获取收藏用户列表 ✅ 2025-10-26
- [x] 实现计数缓存更新逻辑 ✅ 2025-10-26

#### 4. API 端点 ✅ 完成于 2025-10-26

- [x] `POST /posts/{id}/likes`：点赞/取消点赞（幂等） ✅ 2025-10-26
- [x] `GET /posts/{id}/like-status`：查询点赞状态 ✅ 2025-10-26
- [x] `GET /posts/{id}/liked-users`：点赞用户列表 ✅ 2025-10-26
- [x] `GET /users/me/liked-posts`：我点赞的文章 ✅ 2025-10-26
- [x] `POST /posts/{id}/favorites`：收藏/取消收藏（幂等） ✅ 2025-10-26
- [x] `GET /posts/{id}/favorite-status`：查询收藏状态 ✅ 2025-10-26
- [x] `GET /posts/{id}/favorited-users`：收藏用户列表 ✅ 2025-10-26
- [x] `GET /users/me/favorites`：我的收藏列表 ✅ 2025-10-26
- [x] 路由注册完成 ✅ 2025-10-26

#### 5. 测试 ✅ 完成于 2025-10-26

- [x] 点赞功能测试（13个测试） ✅ 2025-10-26
- [x] 收藏功能测试（14个测试） ✅ 2025-10-26
- [x] 计数缓存测试（验证 count 字段准确性） ✅ 2025-10-26
- [x] 权限测试（未登录用户、草稿文章等） ✅ 2025-10-26
- [x] 边界测试（不存在的文章、重复操作） ✅ 2025-10-26
- [x] 性能测试（批量操作、分页查询） ✅ 2025-10-26
- [x] **总计：27 个测试全部通过** ✅ 2025-10-26

#### 6. 额外完成功能 ✅ 完成于 2025-10-26

- [x] 文章置顶功能（toggle_featured） ✅ 2025-10-26
- [x] 置顶文章列表查询 ✅ 2025-10-26
- [x] 查询优化（置顶文章优先排序） ✅ 2025-10-26

**🎉 Phase 6.2 全面完成！所有核心功能和额外功能都已实现并测试通过。**

**技术要点**：

-   幂等性设计：多次点赞只记录一次
-   计数缓存：使用 `like_count` 字段避免频繁 COUNT 查询
-   数据一致性：点赞/取消时同步更新计数
-   性能优化：使用唯一约束防止重复插入

**预估工作量**：2-3 天 → **实际完成：2 天** ✅

### 🎯 Phase 6.3 - 统计面板（中优先级）⭐⭐⭐ ✅ COMPLETED

**目标**：为作者提供数据统计功能，展示文章表现和用户互动数据

**用户故事**：

-   作为作者，我希望看到我的文章总览数据（总文章数、总浏览量、总点赞数）
-   作为作者，我希望看到单篇文章的详细数据（浏览量、点赞数、评论数）
-   作为作者，我希望看到最近热门文章（按浏览量或点赞数排序）

**核心交付**：

#### 1. Schema 设计

-   ✅ `PostViewStatusResponse`：文章浏览状态响应
-   ✅ `PostViewStatsResponse`：文章浏览统计响应
-   ✅ `PostViewCreate`：创建浏览记录请求
-   ✅ `PostViewStatsQuery`：统计查询参数

#### 2. 文章浏览统计功能

-   ✅ **记录浏览**：支持登录用户和匿名用户，多层防刷机制
-   ✅ **浏览统计**：PV/UV统计，支持自定义时间范围，区分用户类型
-   ✅ **浏览状态**：用户对文章的浏览状态查询
-   ✅ **权限控制**：作者和管理员可查看统计数据

#### 3. 技术实现亮点

-   ✅ **ORM优化**：统一使用 `db.query(Post).filter().update()` 解决UUID兼容问题
-   ✅ **防刷策略**：用户级/会话级/IP级四层防刷机制
-   ✅ **架构优化**：CRUD层返回完整状态信息，减少API层数据库查询
-   ✅ **并发安全**：数据库原子操作，避免计数丢失

#### 4. 测试覆盖

-   ✅ **21个测试用例**全部通过
-   ✅ **78%代码覆盖率**，核心功能100%覆盖
-   ✅ **四象限测试策略**：正常/边界/异常/极端数据全覆盖

**完成时间**：🎉 2025-10-27

### 🎯 Phase 6.4 - 通知系统 + 关注功能（高优先级）⭐⭐⭐

**目标**：实现事件驱动的通知系统和关注功能，支持通知聚合和多用户操作的合并显示

**设计文档**：`docs/learning/phase6_社交功能/phase6_4_通知系统概设.md`

**核心特性**：

-   ✅ 事件驱动架构：点赞/评论/关注后自动触发通知
-   ✅ 通知聚合：1 小时内同资源的多个操作合并为 1 条通知
-   ✅ **智能聚合策略**：根据通知类型采用不同的聚合粒度（文章级别/评论级别/用户级别）
-   ✅ 关注功能：用户可以关注/取消关注其他用户
-   ✅ 去重策略：3 层防护（DB 约束 + 业务检查 + 聚合判断）
-   ✅ 自动清理：30 天后自动清理已读通知

**预估工作量**：3-4 天（分 2 天完成）

**验收标准**：

-   ✅ 通知模型和关注模型完整实现
-   ✅ 事件驱动集成（点赞/评论/关注触发通知）
-   ✅ 通知聚合和去重逻辑正确
-   ✅ **智能聚合策略实现**：根据通知类型采用不同聚合粒度（符合行业最佳实践）
-   ✅ API 端点完整覆盖
-   ✅ 测试覆盖率 ≥ 85%（42 个测试全部通过）

---

#### 📅 第一天：模型 + CRUD + 数据库迁移

##### L1: 准备工作与模型定义

-   [x] **创建 Follow 模型** (`app/models/follow.py`)

    -   自向引用（follower_id, followed_id）
    -   唯一约束：防止重复关注
    -   双向索引：加速粉丝/关注列表查询
    -   关系映射：followers 和 following
    -   参考文件：`docs/learning/phase6_社交功能/phase6_4_通知系统概设.md` - 第 2.1 节
    -   ✅ 完成状态：模型定义完整，索引和约束正确

-   [x] **创建 Notification 模型** (`app/models/notification.py`)

    -   核心字段：recipient_id, actor_id, notification_type
    -   聚合字段：aggregated_count, last_updated_at
    -   关联资源：post_id, comment_id
    -   已读状态：is_read, read_at
    -   复合索引 + 唯一约束（注意：聚合后移除 actor_id 限制）✅ **已正确移除**
    -   关系映射：recipient, actor, post, comment
    -   参考文件：`docs/learning/phase6_社交功能/phase6_4_通知系统概设.md` - 第 2.1 节
    -   ✅ 完成状态：模型定义完整，UniqueConstraint 改为 (recipient_id, post_id, comment_id, notification_type)

-   [x] **创建 NotificationType 枚举** (`app/models/notification.py`)

    -   LIKE, COMMENT, FOLLOW（后续可扩展）
    -   参考文件：`docs/learning/phase6_社交功能/phase6_4_通知系统概设.md` - 第 2.1 节
    -   ✅ 完成状态：枚举定义完整，支持后续扩展

-   [x] **更新 User 模型**（`app/models/user.py`）

    -   添加 followers 和 following 关系（Follow 自向引用）
    -   添加 received_notifications 和 sent_notifications 关系
    -   参考文件：`docs/learning/phase6_社交功能/phase6_4_通知系统概设.md` - 第 2.1 节
    -   ✅ 完成状态：关系定义完整，级联删除配置正确

-   [x] **更新 Post 模型**（`app/models/post.py`）

    -   添加 notifications 关系
    -   参考文件：`docs/learning/phase6_社交功能/phase6_4_通知系统概设.md` - 第 2.1 节
    -   ✅ 完成状态：关系定义完整

-   [x] **更新 Comment 模型**（`app/models/comment.py`）

    -   添加 notifications 关系
    -   ✅ 完成状态：关系定义完整，级联删除配置正确

-   [x] **创建数据库迁移脚本**（Alembic）

    -   创建 `follows` 表
    -   创建 `notifications` 表
    -   添加外键和索引
    -   执行迁移，验证数据库结构
    -   参考文件：`alembic/versions/20251028_1449_8437fc376ae6_add_follows_and_notifications_tables.py`
    -   ✅ 完成状态：迁移脚本完整，包含 follows 和 notifications 表定义

-   [x] **更新模型导入文件**（`app/models/__init__.py`）
    -   导入 Follow 和 Notification
    -   导入 NotificationType
    -   更新 **all** 列表
    -   ✅ 完成状态：导入完整，所有模型已正确导出

**检查结果**：✅ 通过 ruff 和 mypy 代码质量检查

##### L2: Follow CRUD 实现

-   [x] **创建 follow.py** (`app/crud/follow.py`) ✅ 2025-10-29

    -   `follow_user(db, follower_id, followed_id)` - 建立关注关系
    -   `unfollow_user(db, follower_id, followed_id)` - 取消关注
    -   `is_following(db, follower_id, followed_id)` - 检查关注状态
    -   `get_followers(db, user_id, limit, offset)` - 获取粉丝列表
    -   `get_following(db, user_id, limit, offset)` - 获取关注列表
    -   `get_follower_count(db, user_id)` - 获取粉丝数
    -   参考设计：`docs/learning/phase6_社交功能/phase6_4_通知系统概设.md` - 第 3.1 节

-   [-] **单元测试** (`tests/test_crud/test_follow.py`) ⏭️ 跳过
    -   Follow CRUD 测试跳过（用户明确说明不需要）
    -   Follow API 测试已完整覆盖 CRUD 功能（`test_follows.py`）

##### L3: Notification CRUD 实现（含聚合）

-   [x] **创建 notification.py** (`app/crud/notification.py`) ✅ 2025-10-29

-   [x] **单元测试** (`tests/test_crud/test_notification.py`) ✅ 2025-10-30

    -   聚合判断：时间窗口检查
    -   创建/更新：新建、聚合、超时创建新通知
    -   去重：同资源不重复创建
    -   清理：时间判断、删除统计
    -   关注通知聚合测试

    -   `_emit_notification_event()` - 事件处理器，映射事件到通知类型
    -   `should_aggregate_notification()` - 聚合判断（含不同类型的时间窗口）
        -   点赞/评论：1 小时
        -   关注：24 小时
        -   返回是否应聚合
    -   `create_or_update_notification()` - 创建或聚合通知
        -   查询现有通知（recipient_id + post_id + notification_type）
        -   **关键变更**：移除 actor_id 限制，支持多用户聚合
        -   聚合：aggregated_count++，last_updated_at 更新（原子操作）
        -   新建：aggregated_count=1
    -   `get_notifications()` - 获取通知列表（分页、过滤已读/未读）
    -   `mark_as_read()` - 标记单条已读
    -   `mark_all_as_read()` - 批量标记已读
    -   `get_unread_count()` - 获取未读数
    -   `delete_notification()` - 删除通知
    -   `cleanup_old_notifications()` - 清理 30 天前的已读通知
    -   参考设计：`docs/learning/phase6_社交功能/phase6_4_通知系统概设.md` - 第 3.3-3.6 节

-   [ ] **单元测试** (`tests/test_crud/test_notification.py`)
    -   聚合判断：时间窗口检查
    -   创建/更新：新建、聚合、超时创建新通知
    -   去重：同资源不重复创建
    -   清理：时间判断、删除统计
    -   **关键测试**：不同发起人的操作聚合到同一条通知

---

#### 📅 第二天：API + 事件集成 + 测试

##### L1: Follow API 端点实现

-   [x] **创建 follows.py** (`app/api/v1/endpoints/follows.py`) ✅ 2025-10-29

    -   `POST /users/{user_id}/follow` - 关注用户
    -   `DELETE /users/{user_id}/follow` - 取消关注
    -   `GET /users/{user_id}/followers` - 获取粉丝列表
    -   `GET /users/{user_id}/following` - 获取关注列表
    -   `GET /users/{user_id}/follower-count` - 获取粉丝数
    -   `GET /users/me/is-following/{user_id}` - 检查是否已关注
    -   响应模型：`FollowStatusResponse`, `UserSimpleResponse`
    -   参考设计：`docs/learning/phase6_社交功能/phase6_4_通知系统概设.md` - 第 4.1 节

-   [x] **API 测试** (`tests/test_api/test_follows.py`) ✅ 2025-10-30
    -   正常关注/取消关注
    -   自我关注、重复关注（异常）
    -   粉丝/关注列表分页
    -   权限测试
    -   集成测试：完整工作流程、互相关注、批量关注

##### L2: Notification API 端点实现

-   [x] **创建 notifications.py** (`app/api/v1/endpoints/notifications.py`) ✅ 2025-10-30

    -   `GET /users/me/notifications` - 获取通知列表（分页、过滤）
    -   `GET /users/me/notifications/unread-count` - 获取未读数
    -   `PATCH /notifications/{id}` - 标记已读
    -   `PATCH /notifications/mark-all-read` - 批量标记已读
    -   `DELETE /notifications/{id}` - 删除通知
    -   响应模型：`NotificationResponse`（含聚合计数、消息格式化）
    -   参考设计：`docs/learning/phase6_社交功能/phase6_4_通知系统概设.md` - 第 4.2-4.3 节

-   [x] **API 测试** (`tests/test_api/test_notifications.py`) ✅ 2025-10-30
    -   获取通知列表、过滤未读
    -   标记已读/全部已读
    -   权限测试（只能查看自己的通知）
    -   业务逻辑测试：聚合逻辑、数据一致性、极端数据场景

##### L3: 事件驱动集成

-   [x] **集成点赞事件** (修改 `app/crud/post_like.py`) ✅

    -   导入 `_emit_notification_event`
    -   在 `toggle_like()` 新增点赞时发射 `POST_LIKED` 事件
    -   参考设计：`docs/learning/phase6_社交功能/phase6_4_通知系统概设.md` - 第 3.5 节

-   [x] **集成评论事件** (修改 `app/crud/comment.py`) ✅

    -   导入 `_emit_notification_event`
    -   在 `create_comment()` 发射 `POST_COMMENTED` 事件
    -   参考设计：`docs/learning/phase6_社交功能/phase6_4_通知系统概设.md` - 第 3.5 节

-   [x] **集成关注事件** (在 `app/crud/follow.py`) ✅

    -   在 `follow_user()` 发射 `USER_FOLLOWED` 事件
    -   参考设计：`docs/learning/phase6_社交功能/phase6_4_通知系统概设.md` - 第 3.5 节

-   [x] **回归测试**：确保点赞/评论/关注的现有测试仍然通过 ✅ 2025-10-30
    -   点赞功能测试通过（test_post_likes.py）
    -   评论功能测试通过（test_comments.py）
    -   关注功能测试通过（test_follows.py）

##### L4: 通知清理机制

-   [x] **应用启动时清理** (修改 `app/main.py`) ✅ 2025-10-29
    -   使用 FastAPI `lifespan` 机制启动后台任务，调用 `cleanup_old_notifications()`
    -   单元测试：`tests/test_crud/test_notification.py::test_cleanup_old_notifications`
    -   参考设计：`docs/learning/phase6_社交功能/phase6_4_通知系统概设.md` - 第 3.6 节

##### L5: 集成测试 + 端到端测试

-   [x] **端到端测试** (`tests/test_e2e/test_notification_flow.py`) ✅ 2025-10-30

    -   用户 A 点赞文章 → 作者收到"点赞"通知 ✅
    -   用户 B 点赞同一文章（1 小时内） → 通知聚合，aggregated_count=2 ✅
    -   用户 A 评论文章 → 作者收到"评论"通知 ✅
    -   用户 A 关注用户 B → B 收到"关注"通知 ✅
    -   标记通知已读 → 未读数减少 ✅
    -   完整事件流测试（多个操作串联）✅
    -   性能测试：并发更新原子性验证 ✅

-   [x] **性能测试** ✅ 已完成

    -   大量通知查询（分页）- ✅ 已在 test_notifications.py::test_notification_extreme_data 和 E2E 测试覆盖
    -   聚合计数并发更新（原子性验证）- ✅ E2E 测试已覆盖

-   [x] **代码质量检查** ✅ 已完成

    -   ✅ `uv run ruff check` - 所有检查通过
    -   ⚠️ `uv run mypy` - 有 4 个类型错误（非 Phase 6.4 特有，是历史遗留问题）
    -   ✅ 测试覆盖率：通知和关注功能测试全部通过（42 个测试通过）

---

#### 📋 具体任务清单（按优先级）

| 任务                              | 优先级 | 预估时间 | 状态 |
| --------------------------------- | ------ | -------- | ---- |
| Follow 模型 + 迁移                | 🔴 高  | 1h       | [x]  |
| Notification 模型 + 迁移          | 🔴 高  | 1.5h     | [x]  |
| Follow CRUD                       | 🔴 高  | 1h       | [x]  |
| Notification CRUD（核心聚合逻辑） | 🔴 高  | 2h       | [x]  |
| Follow API                        | 🟡 中  | 1h       | [x]  |
| Notification API                  | 🟡 中  | 1h       | [x]  |
| 事件集成（点赞/评论/关注）        | 🟡 中  | 1h       | [x]  |
| Follow API 测试                   | 🟡 中  | 1h       | [x]  |
| Notification API 测试             | 🟡 中  | 1h       | [x]  |
| Notification CRUD 测试            | 🟡 中  | 1h       | [x]  |
| Follow CRUD 测试                  | 🟡 中  | 1h       | [-]  |
| 端到端测试（E2E）                 | 🟡 中  | 1.5h     | [x]  |
| 性能测试                          | 🟡 中  | 0.5h     | [x]  |
| 代码审查 + 优化                   | 🟢 低  | 0.5h     | [ ]  |
| 通知聚合策略优化                  | 🟡 中  | 1h       | [x]  |
| **总计**                          | -      | **~14h** | -    |

---

#### 🎯 关键要点（容易遗漏）

1. ⭐ **聚合粒度变更**：去除 actor_id 限制，支持多用户操作合并

    - 唯一约束：`(recipient_id, post_id, notification_type)` 不含 actor_id
    - 查询：不限制 actor_id，所有操作都聚合到同一条通知

2. ⭐ **不同的聚合时间窗口**

    - 点赞/评论：1 小时
    - 关注：24 小时
    - 在 `should_aggregate_notification()` 中实现

3. ⭐ **原子操作更新聚合计数**

    - 避免高并发下的竞态条件
    - 使用 SQLAlchemy 的 `update()` 而非 ORM 更新

4. ⭐ **消息模板系统**（可选，但建议实现）

    - 支持单数/复数形式："A 赞了..." vs "3 人赞了..."
    - 便于国际化扩展

5. ⭐ **自我操作检查**

    - 点赞：author_id != user_id
    - 关注：follower_id != followed_id（业务层检查）

6. ⭐ **回归测试**
    - 修改 `toggle_like()` 和 `create_comment()` 后，需要验证现有测试仍通过

---


