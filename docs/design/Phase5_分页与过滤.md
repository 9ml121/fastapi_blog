# Phase 5 - 分页与过滤

> **文档用途**：分页与过滤功能的理论与实践
> **创建时间**：2025-10-11
> **更新策略**：根据项目实际需求更新分页策略和过滤条件

---

## 📚 目录

1. [业务目标与需求分析](#1-业务目标与需求分析)
2. [分页方案设计](#2-分页方案设计)
3. [技术实现设计](#3-技术实现设计)
4. [API 端点更新](#4-api-端点更新)
5. [前端友好设计](#5-前端友好设计)
6. [性能优化](#6-性能优化)
7. [测试设计](#7-测试设计)
8. [实施计划](#8-实施计划)

---

## 1. 业务目标与需求分析

### 1.1 业务目标

为列表接口添加**生产级**的分页、排序、过滤功能，使前端能够：

-   高效浏览大量数据（文章、评论）
-   按多种条件筛选内容
-   自定义排序规则
-   获得良好的分页体验

### 1.2 为什么需要分页功能？

#### 真实场景

```
❌ 没有分页：
GET /api/v1/posts
返回：10,000 篇文章 😱
问题：
- 响应时间：5-10秒
- 内存占用：500MB+
- 前端渲染：浏览器卡死
- 用户体验：极差

✅ 有分页：
GET /api/v1/posts?page=1&size=20
返回：20 篇文章 + 分页信息 ⚡
优势：
- 响应时间：<100ms
- 内存占用：5MB
- 前端渲染：流畅
- 用户体验：优秀
```

### 1.3 功能需求

#### 核心功能

1. **分页浏览**：支持页码跳转，每页数量可配置
2. **多维度排序**：按时间、热度、标题等字段排序
3. **灵活筛选**：按作者、标签、发布状态等条件筛选
4. **全文搜索**：在标题、内容、摘要中搜索关键词

#### 非功能性需求

1. **性能要求**：分页查询响应时间 < 500ms
2. **安全要求**：防止 SQL 注入，限制查询参数范围
3. **可扩展性**：支持新增筛选条件和排序字段
4. **前端友好**：提供完整的分页信息和状态

---

## 2. 分页方案设计

### 2.1 方案选择：偏移分页

| 方案         | 优点               | 缺点                 | 适用场景                |
| ------------ | ------------------ | -------------------- | ----------------------- |
| **偏移分页** | 实现简单、支持跳页 | 深度分页性能问题     | ✅ 博客系统（≤10 万条） |
| 游标分页     | 性能稳定           | 实现复杂、不支持跳页 | 社交媒体 feed           |
| 搜索分页     | 功能强大           | 依赖外部服务         | 复杂搜索场景            |

**选择理由**：

-   博客文章数量可控（不会无限增长）
-   用户需要页码跳转功能
-   实现简单，团队易于维护

### 2.2 分页参数设计

#### 查询参数格式

```bash
GET /api/v1/posts?page=1&size=20&sort=created_at&order=desc
```

#### 参数说明

| 参数    | 类型   | 默认值     | 说明     | 限制           |
| ------- | ------ | ---------- | -------- | -------------- |
| `page`  | int    | 1          | 页码     | ≥ 1            |
| `size`  | int    | 20         | 每页数量 | 1-100          |
| `sort`  | string | created_at | 排序字段 | 预定义字段列表 |
| `order` | string | desc       | 排序方向 | asc/desc       |

#### 安全考虑

```python
# 限制 size 最大值，防止恶意请求
size: int = Field(default=20, ge=1, le=100, description="每页数量（1-100）")

# 验证 sort 字段，防止 SQL 注入
allowed_sort_fields = ["created_at", "updated_at", "title", "view_count"]
if sort not in allowed_sort_fields:
    sort = "created_at"  # 默认值
```

### 2.3 响应格式设计

#### 分页响应示例

```json
{
    "items": [
        {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "title": "FastAPI 入门教程",
            "slug": "fastapi-tutorial",
            "summary": "本文介绍 FastAPI 的基础知识",
            "content": "...",
            "author": {
                "id": "...",
                "username": "johndoe",
                "nickname": "张三",
                "avatar": "https://..."
            },
            "tags": [{ "id": "...", "name": "Python", "slug": "python" }],
            "view_count": 1250,
            "created_at": "2025-01-10T10:00:00Z",
            "updated_at": "2025-01-10T10:00:00Z"
        }
    ],
    "total": 150,
    "page": 1,
    "size": 20,
    "pages": 8,
    "has_next": true,
    "has_prev": false
}
```

#### 字段说明

| 字段       | 类型    | 说明         | 前端用途       |
| ---------- | ------- | ------------ | -------------- |
| `items`    | Array   | 数据列表     | 渲染内容       |
| `total`    | number  | 总记录数     | 显示"共 X 条"  |
| `page`     | number  | 当前页码     | 高亮当前页     |
| `size`     | number  | 每页数量     | 分页大小选择器 |
| `pages`    | number  | 总页数       | 生成分页器     |
| `has_next` | boolean | 是否有下一页 | 控制下一页按钮 |
| `has_prev` | boolean | 是否有上一页 | 控制上一页按钮 |

---

## 3. 技术实现设计

### 3.1 通用分页工具

#### 文件：`app/api/pagination.py`（新建）

```python
"""
通用分页工具

提供：
1. 分页参数模型（PaginationParams）
2. 分页响应模型（PaginatedResponse）
3. 分页查询函数（paginate）
"""

from typing import Generic, TypeVar, List, Any, Optional
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import select, func, asc, desc, or_
from datetime import datetime

T = TypeVar('T')

class PaginationParams(BaseModel):
    """分页查询参数"""
    page: int = Field(default=1, ge=1, description="页码（从1开始）")
    size: int = Field(default=20, ge=1, le=100, description="每页数量（1-100）")
    sort: str = Field(default="created_at", description="排序字段")
    order: str = Field(default="desc", regex="^(asc|desc)$", description="排序方向")

    @property
    def offset(self) -> int:
        """计算 OFFSET 值"""
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        """获取 LIMIT 值"""
        return self.size


class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应格式"""
    items: List[T] = Field(description="数据列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    size: int = Field(description="每页数量")
    pages: int = Field(description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_prev: bool = Field(description="是否有上一页")

    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        params: PaginationParams
    ) -> "PaginatedResponse[T]":
        """创建分页响应"""
        pages = (total + params.size - 1) // params.size  # 向上取整

        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
            has_next=params.page < pages,
            has_prev=params.page > 1
        )


def paginate_query(
    db: Session,
    query: Any,
    params: PaginationParams,
    *,
    count_query: Optional[Any] = None
) -> tuple[List[Any], int]:
    """
    执行分页查询

    Args:
        db: 数据库会话
        query: 基础查询
        params: 分页参数
        count_query: 可选的自定义计数查询

    Returns:
        tuple: (items, total)
    """
    # 获取总数
    if count_query is None:
        count_query = select(func.count()).select_from(query.subquery())

    total = db.execute(count_query).scalar()

    # 应用排序
    # 注意：这里需要根据具体模型来处理排序字段
    # 在实际使用中，各个 CRUD 方法会处理排序逻辑

    # 应用分页
    paginated_query = query.offset(params.offset).limit(params.limit)
    items = db.execute(paginated_query).scalars().all()

    return items, total
```

#### 设计亮点

1. **类型安全**：使用 Generic[T] 支持任意类型的分页
2. **参数验证**：Pydantic 自动验证参数范围和格式
3. **响应计算**：自动计算 `has_next`、`has_prev` 等前端需要的字段
4. **可扩展性**：支持自定义计数查询和排序逻辑

### 3.2 文章列表分页

#### 更新文件：`app/crud/post.py`

```python
from app.api.pagination import PaginationParams, PaginatedResponse, paginate_query

def get_posts_paginated(
    db: Session,
    *,
    params: PaginationParams,
    author_id: UUID | None = None,
    tag_slug: str | None = None,
    published_only: bool = True,
    search: str | None = None
) -> PaginatedResponse[Post]:
    """
    获取分页文章列表

    Args:
        db: 数据库会话
        params: 分页参数
        author_id: 按作者ID筛选
        tag_slug: 按标签slug筛选
        published_only: 只显示已发布文章
        search: 搜索关键词（标题和内容）
    """

    # 构建基础查询
    query = select(Post).options(
        selectinload(Post.author),
        selectinload(Post.tags)
    )

    # 应用过滤条件
    conditions = []

    if published_only:
        conditions.append(Post.is_published == True)

    if author_id:
        conditions.append(Post.author_id == author_id)

    if tag_slug:
        query = query.join(Post.tags).where(Tag.slug == tag_slug)

    if search:
        search_condition = or_(
            Post.title.ilike(f"%{search}%"),
            Post.content.ilike(f"%{search}%"),
            Post.summary.ilike(f"%{search}%")
        )
        conditions.append(search_condition)

    if conditions:
        query = query.where(*conditions)

    # 应用排序
    sort_column = _get_sort_column(Post, params.sort)
    if params.order == "desc":
        query = query.order_by(desc(sort_column))
    else:
        query = query.order_by(asc(sort_column))

    # 执行分页
    items, total = paginate_query(db, query, params)

    return PaginatedResponse.create(items, total, params)


def _get_sort_column(model, sort_field: str):
    """获取排序列，支持字段映射"""
    sort_mapping = {
        "created_at": model.created_at,
        "updated_at": model.updated_at,
        "title": model.title,
        "view_count": model.view_count,
    }
    return sort_mapping.get(sort_field, model.created_at)
```

#### 扩展功能

1. **多字段筛选**：支持按作者、标签、发布状态筛选
2. **搜索功能**：在标题、内容、摘要中搜索关键词
3. **安全排序**：使用白名单机制防止 SQL 注入
4. **性能优化**：使用 `selectinload` 避免 N+1 查询

### 3.3 评论列表分页

#### 更新文件：`app/crud/comment.py`

```python
from app.api.pagination import PaginationParams, PaginatedResponse, paginate_query

def get_comments_paginated(
    db: Session,
    *,
    params: PaginationParams,
    post_id: UUID | None = None,
    parent_id: UUID | None = None
) -> PaginatedResponse[Comment]:
    """
    获取分页评论列表

    Args:
        db: 数据库会话
        params: 分页参数
        post_id: 按文章ID筛选（获取某文章的所有评论）
        parent_id: 按父评论ID筛选（获取某评论的回复）
    """

    # 构建基础查询
    query = select(Comment).options(
        selectinload(Comment.author),
        selectinload(Comment.post)
    )

    # 应用过滤条件
    conditions = []

    if post_id:
        conditions.append(Comment.post_id == post_id)

    if parent_id:
        conditions.append(Comment.parent_id == parent_id)
    else:
        # 如果没有指定 parent_id，只获取顶级评论
        conditions.append(Comment.parent_id.is_(None))

    if conditions:
        query = query.where(*conditions)

    # 评论按创建时间正序排列（旧评论在前）
    query = query.order_by(Comment.created_at.asc())

    # 执行分页
    items, total = paginate_query(db, query, params)

    return PaginatedResponse.create(items, total, params)
```

#### 评论分页特点

1. **层级支持**：可以获取顶级评论或回复评论
2. **默认排序**：评论按时间正序（对话流程）
3. **灵活查询**：支持获取某文章的所有评论或某评论的回复

---

## 4. API 端点更新

### 4.1 文章列表端点

#### 更新文件：`app/api/v1/endpoints/posts.py`

````python
from app.api.pagination import PaginationParams
from app.schemas.post import PostResponse

@router.get("/", response_model=PaginatedResponse[PostResponse])
def get_posts(
    db: Session = Depends(get_db),
    params: PaginationParams = Depends(),
    author_id: UUID | None = Query(None, description="按作者ID筛选"),
    tag: str | None = Query(None, description="按标签slug筛选"),
    published: bool = Query(True, description="只显示已发布文章"),
    search: str | None = Query(None, description="搜索关键词（标题和内容）"),
    sort: str = Query(
        default="created_at",
        regex="^(created_at|updated_at|title|view_count)$",
        description="排序字段"
    )
) -> Any:
    """
    获取文章列表（分页）

    ### 功能特性
    - ✅ 分页浏览（支持页码跳转）
    - ✅ 多维度排序（时间、标题、热度）
    - ✅ 灵活筛选（作者、标签、发布状态）
    - ✅ 全文搜索（标题、内容、摘要）

    ### 使用示例

    ```bash
    # 获取第2页，每页10条，按热度排序
    GET /api/v1/posts?page=2&size=10&sort=view_count&order=desc

    # 搜索包含"FastAPI"的文章
    GET /api/v1/posts?search=FastAPI

    # 获取某作者的所有文章
    GET /api/v1/posts?author_id=xxx&published=false
    ```
    """
    posts = crud_post.get_posts_paginated(
        db,
        params=params,
        author_id=author_id,
        tag_slug=tag,
        published_only=published,
        search=search
    )
    return posts
````

### 4.2 评论列表端点

#### 更新文件：`app/api/v1/endpoints/comments.py`

```python
from app.api.pagination import PaginationParams
from app.schemas.comment import CommentResponse

@router.get("/posts/{post_id}/comments", response_model=PaginatedResponse[CommentResponse])
def get_post_comments(
    post_id: UUID,
    db: Session = Depends(get_db),
    params: PaginationParams = Depends()
) -> Any:
    """
    获取文章评论列表（分页）

    获取指定文章的所有顶级评论（分页显示）
    """
    # 验证文章存在
    post = crud_post.get_post(db, post_id=post_id)
    if not post:
        raise ResourceNotFoundError("文章")

    comments = crud_comment.get_comments_paginated(
        db,
        params=params,
        post_id=post_id,
        parent_id=None  # 只获取顶级评论
    )
    return comments


@router.get("/comments/{comment_id}/replies", response_model=PaginatedResponse[CommentResponse])
def get_comment_replies(
    comment_id: UUID,
    db: Session = Depends(get_db),
    params: PaginationParams = Depends()
) -> Any:
    """
    获取评论回复列表（分页）

    获取指定评论的所有回复（分页显示）
    """
    # 验证评论存在
    comment = crud_comment.get_comment(db, comment_id=comment_id)
    if not comment:
        raise ResourceNotFoundError("评论")

    replies = crud_comment.get_comments_paginated(
        db,
        params=params,
        post_id=None,  # 不限制文章
        parent_id=comment_id  # 获取回复
    )
    return replies
```

---

## 5. 前端友好设计

### 5.1 TypeScript 类型定义

```typescript
// types/pagination.ts
export interface PaginationParams {
    page?: number; // 页码，默认1
    size?: number; // 每页数量，默认20
    sort?: string; // 排序字段，默认created_at
    order?: "asc" | "desc"; // 排序方向，默认desc
}

export interface PaginatedResponse<T> {
    items: T[];
    total: number;
    page: number;
    size: number;
    pages: number;
    has_next: boolean;
    has_prev: boolean;
}

export interface Post {
    id: string;
    title: string;
    slug: string;
    summary: string;
    content: string;
    author: {
        id: string;
        username: string;
        nickname: string;
        avatar?: string;
    };
    tags: Array<{
        id: string;
        name: string;
        slug: string;
    }>;
    view_count: number;
    created_at: string;
    updated_at: string;
}
```

### 5.2 React 分页组件

```typescript
// components/Pagination.tsx
import React from "react";
import { PaginatedResponse } from "../types/pagination";

interface PaginationProps {
    data: PaginatedResponse<any>;
    onPageChange: (page: number) => void;
    onSizeChange?: (size: number) => void;
}

export const Pagination: React.FC<PaginationProps> = ({
    data,
    onPageChange,
    onSizeChange,
}) => {
    const { page, size, pages, has_next, has_prev, total } = data;

    // 生成页码数组（显示当前页前后2页）
    const getPageNumbers = () => {
        const start = Math.max(1, page - 2);
        const end = Math.min(pages, page + 2);
        return Array.from({ length: end - start + 1 }, (_, i) => start + i);
    };

    return (
        <div className="flex items-center justify-between">
            <div className="text-sm text-gray-700">
                共 {total} 条记录，第 {page} / {pages} 页
            </div>

            <div className="flex items-center space-x-2">
                {/* 上一页 */}
                <button
                    disabled={!has_prev}
                    onClick={() => onPageChange(page - 1)}
                    className="px-3 py-1 border rounded disabled:opacity-50"
                >
                    上一页
                </button>

                {/* 页码 */}
                {getPageNumbers().map((pageNum) => (
                    <button
                        key={pageNum}
                        onClick={() => onPageChange(pageNum)}
                        className={`px-3 py-1 border rounded ${
                            pageNum === page
                                ? "bg-blue-500 text-white"
                                : "hover:bg-gray-100"
                        }`}
                    >
                        {pageNum}
                    </button>
                ))}

                {/* 下一页 */}
                <button
                    disabled={!has_next}
                    onClick={() => onPageChange(page + 1)}
                    className="px-3 py-1 border rounded disabled:opacity-50"
                >
                    下一页
                </button>

                {/* 每页数量选择器 */}
                {onSizeChange && (
                    <select
                        value={size}
                        onChange={(e) => onSizeChange(Number(e.target.value))}
                        className="ml-4 border rounded px-2 py-1"
                    >
                        <option value={10}>10条/页</option>
                        <option value={20}>20条/页</option>
                        <option value={50}>50条/页</option>
                    </select>
                )}
            </div>
        </div>
    );
};
```

### 5.3 文章列表页面

```typescript
// pages/Posts.tsx
import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import { Post, PaginationParams, PaginatedResponse } from "../types";

export const PostsPage: React.FC = () => {
    const [posts, setPosts] = useState<PaginatedResponse<Post> | null>(null);
    const [loading, setLoading] = useState(false);
    const [filters, setFilters] = useState<PaginationParams>({
        page: 1,
        size: 20,
        sort: "created_at",
        order: "desc",
    });

    // 加载文章列表
    const loadPosts = async (params: PaginationParams = filters) => {
        setLoading(true);
        try {
            const response = await api.get("/api/v1/posts", { params });
            setPosts(response.data);
            setFilters(params);
        } catch (error) {
            console.error("Failed to load posts:", error);
        } finally {
            setLoading(false);
        }
    };

    // 页码变化
    const handlePageChange = (page: number) => {
        loadPosts({ ...filters, page });
    };

    // 每页数量变化
    const handleSizeChange = (size: number) => {
        loadPosts({ ...filters, size, page: 1 });
    };

    // 排序变化
    const handleSortChange = (sort: string) => {
        loadPosts({ ...filters, sort, page: 1 });
    };

    useEffect(() => {
        loadPosts();
    }, []);

    if (loading || !posts) return <div>Loading...</div>;

    return (
        <div>
            {/* 搜索和筛选 */}
            <div className="mb-4">
                <input
                    type="text"
                    placeholder="搜索文章..."
                    onChange={(e) =>
                        loadPosts({
                            ...filters,
                            search: e.target.value,
                            page: 1,
                        })
                    }
                    className="mr-4 px-3 py-2 border rounded"
                />

                <select
                    value={filters.sort}
                    onChange={(e) => handleSortChange(e.target.value)}
                    className="px-3 py-2 border rounded"
                >
                    <option value="created_at">最新发布</option>
                    <option value="updated_at">最近更新</option>
                    <option value="view_count">最多浏览</option>
                    <option value="title">标题排序</option>
                </select>
            </div>

            {/* 文章列表 */}
            <div className="grid gap-4 mb-6">
                {posts.items.map((post) => (
                    <div key={post.id} className="border rounded p-4">
                        <h3 className="text-lg font-semibold mb-2">
                            {post.title}
                        </h3>
                        <p className="text-gray-600 mb-2">{post.summary}</p>
                        <div className="flex items-center text-sm text-gray-500">
                            <span>作者：{post.author.nickname}</span>
                            <span className="ml-4">
                                浏览：{post.view_count}
                            </span>
                            <span className="ml-4">{post.created_at}</span>
                        </div>
                    </div>
                ))}
            </div>

            {/* 分页组件 */}
            <Pagination
                data={posts}
                onPageChange={handlePageChange}
                onSizeChange={handleSizeChange}
            />
        </div>
    );
};
```

---

## 6. 性能优化

### 6.1 数据库优化

#### 索引建议

```sql
-- 文章表索引
CREATE INDEX idx_posts_created_at ON posts(created_at DESC);
CREATE INDEX idx_posts_author_id ON posts(author_id);
CREATE INDEX idx_posts_is_published ON posts(is_published);
CREATE INDEX idx_posts_view_count ON posts(view_count DESC);

-- 复合索引用于常见查询组合
CREATE INDEX idx_posts_published_created ON posts(is_published, created_at DESC);
CREATE INDEX idx_posts_author_published ON posts(author_id, is_published);

-- 评论表索引
CREATE INDEX idx_comments_post_id ON comments(post_id);
CREATE INDEX idx_comments_parent_id ON comments(parent_id);
CREATE INDEX idx_comments_created_at ON comments(created_at);

-- 全文搜索索引（PostgreSQL）
CREATE INDEX idx_posts_search ON posts USING gin(
  to_tsvector('english', title || ' ' || content || ' ' || summary)
);
```

#### 查询优化

```python
# 使用 selectinload 避免 N+1 查询
query = select(Post).options(
    selectinload(Post.author),      # 预加载作者
    selectinload(Post.tags)         # 预加载标签
)

# 使用 exists 检查而不是加载完整对象
def post_exists(db: Session, post_id: UUID) -> bool:
    return db.execute(
        select(func.count()).where(Post.id == post_id)
    ).scalar() > 0
```

### 6.2 缓存策略

#### Redis 缓存热门页面

```python
import redis
from app.core.config import settings

redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    decode_responses=True
)

def cache_key(params: PaginationParams, **filters) -> str:
    """生成缓存键"""
    filter_str = "&".join(f"{k}={v}" for k, v in filters.items() if v)
    return f"posts:page={params.page}:size={params.size}:sort={params.sort}:{filter_str}"

def get_cached_posts(key: str) -> Optional[dict]:
    """获取缓存的分页数据"""
    data = redis_client.get(key)
    return json.loads(data) if data else None

def cache_posts(key: str, data: dict, ttl: int = 300) -> None:
    """缓存分页数据（5分钟）"""
    redis_client.setex(key, ttl, json.dumps(data, default=str))
```

---

## 7. 测试设计

### 7.1 测试数据四象限

| 数据类型     | 测试场景                          |
| ------------ | --------------------------------- |
| **正常数据** | 分页浏览、排序筛选、搜索功能      |
| **边界数据** | 第一页/最后一页、空列表、最大页数 |
| **异常数据** | 无效页码、超大 size、非法排序字段 |
| **极端数据** | 深度分页、大量数据、复杂筛选条件  |

### 7.2 核心测试用例

#### 分页功能测试

```python
# tests/test_pagination.py

class TestPaginationParams:
    """测试分页参数验证"""

    def test_valid_params(self):
        """✅ 正常数据：有效参数"""
        params = PaginationParams(page=1, size=20, sort="created_at", order="desc")
        assert params.page == 1
        assert params.size == 20
        assert params.offset == 0

    def test_page_boundary(self):
        """✅ 边界数据：页码边界值"""
        # 最小页码
        params = PaginationParams(page=1)
        assert params.offset == 0

        # 大页码
        params = PaginationParams(page=100, size=10)
        assert params.offset == 990

    def test_size_limits(self):
        """✅ 边界数据：每页数量限制"""
        # 最小值
        params = PaginationParams(size=1)
        assert params.size == 1

        # 最大值
        params = PaginationParams(size=100)
        assert params.size == 100

        # 超出最大值（应该被验证器拒绝）
        with pytest.raises(ValidationError):
            PaginationParams(size=101)

    def test_invalid_page(self):
        """❌ 异常数据：无效页码"""
        with pytest.raises(ValidationError):
            PaginationParams(page=0)  # 页码必须 ≥ 1

    def test_invalid_order(self):
        """❌ 异常数据：无效排序方向"""
        with pytest.raises(ValidationError):
            PaginationParams(order="invalid")  # 只能是 asc/desc


class TestPostPagination:
    """测试文章分页功能"""

    def test_first_page(self, db: Session, sample_posts):
        """✅ 正常数据：第一页"""
        params = PaginationParams(page=1, size=5)
        result = crud_post.get_posts_paginated(db, params=params)

        assert len(result.items) <= 5
        assert result.page == 1
        assert result.size == 5
        assert result.has_prev is False
        assert isinstance(result.total, int)

    def test_last_page(self, db: Session, sample_posts):
        """✅ 边界数据：最后一页"""
        # 假设有23条数据，每页10条，第3页是最后一页（只有3条）
        params = PaginationParams(page=3, size=10)
        result = crud_post.get_posts_paginated(db, params=params)

        assert len(result.items) <= 10
        assert result.page == 3
        assert result.has_next is False
        assert result.has_prev is True

    def test_empty_result(self, db: Session):
        """✅ 边界数据：空结果"""
        params = PaginationParams(search="nonexistent")
        result = crud_post.get_posts_paginated(db, params=params)

        assert len(result.items) == 0
        assert result.total == 0
        assert result.pages == 0
        assert result.has_next is False
        assert result.has_prev is False

    def test_sort_by_title(self, db: Session, sample_posts):
        """✅ 正常数据：按标题排序"""
        params = PaginationParams(sort="title", order="asc")
        result = crud_post.get_posts_paginated(db, params=params)

        titles = [post.title for post in result.items]
        assert titles == sorted(titles)

    def test_filter_by_author(self, db: Session, sample_posts, sample_user):
        """✅ 正常数据：按作者筛选"""
        params = PaginationParams()
        result = crud_post.get_posts_paginated(
            db,
            params=params,
            author_id=sample_user.id
        )

        for post in result.items:
            assert post.author_id == sample_user.id

    def test_search_functionality(self, db: Session, sample_posts):
        """✅ 正常数据：搜索功能"""
        # 创建测试数据
        search_post = Post(
            title="FastAPI Tutorial",
            content="This is about FastAPI framework",
            author_id=sample_user.id
        )
        db.add(search_post)
        db.commit()

        params = PaginationParams(search="FastAPI")
        result = crud_post.get_posts_paginated(db, params=params)

        assert len(result.items) >= 1
        for post in result.items:
            assert "FastAPI" in post.title or "FastAPI" in post.content
```

#### 性能测试

```python
class TestPaginationPerformance:
    """测试分页性能"""

    def test_deep_pagination_performance(self, db: Session, many_posts):
        """✅ 极端数据：深度分页性能"""
        import time

        # 测试第100页的性能
        params = PaginationParams(page=100, size=20)

        start_time = time.time()
        result = crud_post.get_posts_paginated(db, params=params)
        end_time = time.time()

        # 深度分页应该在500ms内完成
        assert end_time - start_time < 0.5
        assert len(result.items) <= 20

    def test_large_size_pagination(self, db: Session, many_posts):
        """✅ 极端数据：大页面分页"""
        params = PaginationParams(page=1, size=100)  # 每页100条

        result = crud_post.get_posts_paginated(db, params=params)

        assert len(result.items) <= 100
        # 即使是大页面，响应时间也应该合理
        # 这个测试会根据具体数据量调整期望时间
```

---

## 8. 实施计划

### 8.1 开发步骤

1. **Step 1: 基础设施**（2 小时）

    - 创建 `app/api/pagination.py`
    - 实现 `PaginationParams` 和 `PaginatedResponse`
    - 编写基础单元测试

2. **Step 2: CRUD 层**（3 小时）

    - 更新 `app/crud/post.py` 添加分页方法
    - 更新 `app/crud/comment.py` 添加分页方法
    - 添加搜索和筛选功能

3. **Step 3: API 层**（2 小时）

    - 更新 `app/api/v1/endpoints/posts.py`
    - 更新 `app/api/v1/endpoints/comments.py`
    - 添加查询参数和文档

4. **Step 4: 测试**（3 小时）
    - 编写分页功能测试
    - 性能测试和优化
    - 集成测试验证

### 8.2 文件修改清单

| 文件                               | 修改内容     | 新增/修改 | 优先级 |
| ---------------------------------- | ------------ | --------- | ------ |
| `app/api/pagination.py`            | 通用分页工具 | 新建      | P0     |
| `app/crud/post.py`                 | 文章分页方法 | 修改      | P0     |
| `app/crud/comment.py`              | 评论分页方法 | 修改      | P0     |
| `app/api/v1/endpoints/posts.py`    | 分页端点     | 修改      | P0     |
| `app/api/v1/endpoints/comments.py` | 分页端点     | 修改      | P0     |
| `tests/test_pagination.py`         | 分页功能测试 | 新建      | P1     |

### 8.3 验收标准

-   [x] 支持分页浏览（page/size）
-   [x] 支持多种排序（时间、热度、标题）
-   [x] 支持灵活筛选（作者、标签、状态）
-   [x] 支持搜索功能（全文搜索）
-   [x] 响应格式前端友好
-   [x] 性能满足要求（<500ms）
-   [x] 测试覆盖率 ≥ 85%

---

## 参考资源

-   [FastAPI 分页最佳实践](https://fastapi.tiangolo.com/tutorial/sql-databases/#pagination)
-   [SQLAlchemy 分页查询](https://docs.sqlalchemy.org/en/20/orm/queryguide/select.html#pagination)
-   [RESTful API 分页设计](https://restfulapi.net/pagination/)
-   [前端分页组件设计](https://ant.design/components/pagination/)
