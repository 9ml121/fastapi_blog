# Phase 6 - 文章管理模块架构设计

> **版本**: v1.0
> **最后更新**: 2025-10-16

---

## 📋 目录

1. [模块概述](#模块概述)
2. [架构设计](#架构设计)
3. [Phase 6.1 - 草稿系统设计](#phase-61---草稿系统设计)
4. [数据流与业务逻辑](#数据流与业务逻辑)

---

## 模块概述

### 业务目标
实现完整的文章生命周期管理系统，支持：
- ✅ **内容管理**：创建、编辑、删除文章
- ✅ **状态管理**：草稿、发布、归档三种状态
- ✅ **标签系统**：多对多关系，支持分类
- ✅ **权限控制**：作者/管理员分级权限
- ✅ **分页查询**：支持过滤、排序

### 技术栈
- **ORM**: SQLAlchemy 2.0+ (声明式映射)
- **数据验证**: Pydantic v2
- **API框架**: FastAPI
- **数据库**: PostgreSQL
- **迁移工具**: Alembic

---

## 架构设计

### Level 1: 代码级架构（Code Level）

展示各层的详细类结构和方法签名。

==TODO==  ❌ 错误：PostUpdate 和 PostFilters 继承 BaseModel， 不是继承PostBase！ PostBase也是继承BaseModel，没有画出来

```mermaid
classDiagram
    %% 数据模型层
    class Post {
        +UUID id
        +str title
        +str content
        +str slug
        +str summary
        +PostStatus status
        +datetime published_at
        +UUID author_id
        +bool is_featured
        +int view_count
        ---
        +publish() void
        +archive() void
        +revert_to_draft() void
        +increment_view_count() void
        +set_summary_from_content() void
        ---
        +is_draft: bool
        +is_published: bool
        +is_archived: bool
        +word_count: int
        +reading_time: int
    }

    class PostStatus {
        <<enumeration>>
        DRAFT
        PUBLISHED
        ARCHIVED
    }

    %% Schema 层
    class PostBase {
        +str title
        +str content
        +str summary
    }

    class PostCreate {
        +PostStatus status
        +list~UUID~ tag_ids
    }

    class PostUpdate {
        +str title
        +str content
        +PostStatus status
    }

    class PostResponse {
        +UUID id
        +str title
        +PostStatus status
        +datetime published_at
        +UserResponse author
        +list~TagResponse~ tags
    }

    class PostFilters {
        +str author_id
        +str tag_id
        +PostStatus status
        +str search
    }

    %% CRUD 层
    class CRUDPost {
        +get_by_slug(slug) Post
        +create_post(data, author_id) Post
        +update(post_id, data) Post
        +get_paginated(filters, page, size) PaginatedResponse
        +get_user_drafts(user_id) list~Post~
        +publish(post_id) Post
        +archive(post_id) Post
    }

    %% 关系
    Post --> PostStatus : uses
    PostCreate --|> PostBase : inherits
    PostUpdate --|> PostBase : inherits
    PostResponse --|> PostBase : inherits
    CRUDPost ..> Post : operates on
    CRUDPost ..> PostCreate : uses
    CRUDPost ..> PostUpdate : uses
```

### Level 2: 组件级架构（Component Level）

展示模块之间的依赖关系和数据流。

```mermaid
flowchart TB
    subgraph "API 路由层 (api/v1/endpoints/posts.py)"
        A1["POST /posts - 创建文章"]
        A2["GET /posts - 文章列表"]
        A3["GET /posts/{id} - 文章详情"]
        A4["PATCH /posts/{id} - 更新文章"]
        A5["DELETE /posts/{id} - 删除文章"]
        A6["GET /posts/drafts - 草稿列表"]
        A7["PATCH /posts/{id}/publish - 发布"]
        A8["PATCH /posts/{id}/archive - 归档"]
    end

    subgraph "Schema 验证层 (schemas/post.py)"
        B1["PostCreate - 创建验证"]
        B2["PostUpdate - 更新验证"]
        B3["PostResponse - 响应格式"]
        B4["PostFilters - 查询过滤"]
    end

    subgraph "CRUD 业务层 (crud/post.py)"
        C1["CRUDPost.create_post"]
        C2["CRUDPost.get_paginated"]
        C3["CRUDPost.update"]
        C4["CRUDPost.get_user_drafts"]
        C5["CRUDPost.publish"]
        C6["CRUDPost.archive"]
    end

    subgraph "数据模型层 (models/post.py)"
        D1["Post Model"]
        D2["PostStatus Enum"]
        D3["业务方法: publish/archive/revert_to_draft"]
    end

    subgraph "数据库层"
        E1[("PostgreSQL")]
    end

    %% 数据流
    A1 --> B1 --> C1 --> D1 --> E1
    A2 --> B4 --> C2 --> D1 --> E1
    A3 --> C2 --> D1 --> E1
    A4 --> B2 --> C3 --> D1 --> E1
    A6 --> C4 --> D1 --> E1
    A7 --> C5 --> D3 --> E1
    A8 --> C6 --> D3 --> E1

    %% 返回流
    E1 -.-> D1 -.-> B3 -.-> A1
```

### Level 3: 请求处理流程（Sequence Diagram）

展示一次完整的文章发布流程。

```mermaid
sequenceDiagram
    participant Client as 客户端
    participant API as API 路由
    participant Auth as 权限验证
    participant CRUD as CRUD 层
    participant Model as Post 模型
    participant DB as 数据库

    %% 创建草稿
    Client->>API: POST /posts (创建草稿)
    API->>Auth: 验证 JWT Token
    Auth-->>API: 返回当前用户
    API->>CRUD: create_post(data, user_id)
    CRUD->>Model: 创建 Post 实例 (status=draft)
    Model->>DB: INSERT INTO posts
    DB-->>Model: 返回 Post 对象
    Model-->>CRUD: Post (status=draft)
    CRUD-->>API: PostResponse
    API-->>Client: 201 Created

    %% 发布文章
    Client->>API: PATCH /posts/{id}/publish
    API->>Auth: 验证作者权限
    Auth-->>API: 权限通过
    API->>CRUD: publish(post_id)
    CRUD->>Model: post.publish()
    Model->>Model: status = PUBLISHED<br/>published_at = now()
    Model->>DB: UPDATE posts SET status, published_at
    DB-->>Model: 更新成功
    Model-->>CRUD: Post (status=published)
    CRUD-->>API: PostResponse
    API-->>Client: 200 OK

    %% 查询已发布文章列表
    Client->>API: GET /posts (公开访问)
    API->>CRUD: get_paginated(filters={status: published})
    CRUD->>DB: SELECT * FROM posts WHERE status='published'
    DB-->>CRUD: List[Post]
    CRUD-->>API: PaginatedResponse[PostResponse]
    API-->>Client: 200 OK (仅已发布)
```

---



---

## 参考资源

- [SQLAlchemy 2.0 Documentation](https://docs.sqlalchemy.org/en/20/)
- [FastAPI Best Practices](https://fastapi.tiangolo.com/tutorial/)
- [State Machine Pattern](https://refactoring.guru/design-patterns/state)
