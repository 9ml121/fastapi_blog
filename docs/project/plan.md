> **文档用途**：制定项目后端开发计划
> **更新频率**：后端开发前

# 后端开发学习计划

## 项目概览

```
项目结构：
  fastapi_blog/
  ├── app/                    # 主应用目录
  │   ├── api/               # API路由 (空)
  │   ├── core/              # 核心配置 (空)
  │   ├── crud/              # CRUD操作 (空)
  │   ├── db/                # 数据库配置 (空)
  │   ├── models/            # SQLAlchemy模型 (空)
  │   └── schemas/           # Pydantic模式 (空)
  ├── main.py                # 入口文件 (仅包含hello函数)
  ├── pyproject.toml         # 项目配置和依赖
  ├── uv.lock               # 依赖锁定文件
  ├── .gitignore            # Git忽略文件
  ├── .python-version       # Python版本
  └── README.md             # 项目说明 (空)

```

---

## 学习路径
 
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
-   ✅ **通知系统 + 关注功能**：事件驱动的通知系统和用户关注功能（Phase 6.4）🎉 2025-10-30
    -   数据模型：Notification 和 Follow 模型，支持通知聚合和关注关系
    -   事件驱动架构：点赞/评论/关注后自动触发通知
    -   智能聚合策略：根据通知类型采用不同聚合粒度（文章级别/评论级别/用户级别）
    -   CRUD 层：完整的通知和关注 CRUD 操作，支持聚合、去重、清理
    -   API 端点：通知列表、已读管理、关注/取消关注、粉丝/关注列表
    -   测试覆盖：42 个测试全部通过（CRUD + API + E2E），覆盖率 96%
    -   技术亮点：事件驱动、聚合策略、原子操作、自动清理、行业最佳实践

---