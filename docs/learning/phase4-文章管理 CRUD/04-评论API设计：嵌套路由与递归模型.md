# 评论 API 设计：嵌套路由与递归模型

> **Phase 4.4.3 学习文档** - 评论管理 API 的设计思路与最佳实践

## 📋 目录

- [一、评论系统的业务特性](#一评论系统的业务特性)
- [二、嵌套路由设计](#二嵌套路由设计)
- [三、评论层级结构实现](#三评论层级结构实现)
- [四、递归模型应用](#四递归模型应用)
- [五、权限控制设计](#五权限控制设计)
- [六、性能优化](#六性能优化)

---

## 一、评论系统的业务特性

### 1.1 评论与文章/标签的区别

| 资源类型 | 业务特性 | 访问场景 |
|---------|---------|---------|
| **文章** | 独立资源 | 可单独查询、展示列表 |
| **标签** | 独立资源 | 可单独查询、展示列表 |
| **评论** | 依附资源 | 总是围绕特定文章存在 |

### 1.2 常见业务场景

✅ **高频场景**：
- "查看某篇文章的所有评论"
- "为某篇文章添加评论"
- "回复某条评论"

❌ **低频场景**：
- "查看所有评论"（除管理后台外很少使用）
- "单独获取某条评论"（通常通过文章评论列表获取）

**设计原则**：API 设计应该反映资源的业务关系 → **使用嵌套路由**

---

## 二、嵌套路由设计

### 2.1 方案对比

#### 方案 A：平铺路由（不推荐）

```http
POST   /comments?post_id=xxx        # 创建评论
GET    /comments?post_id=xxx        # 查询评论
GET    /comments/{comment_id}       # 获取单条评论
PATCH  /comments/{comment_id}       # 更新评论
DELETE /comments/{comment_id}       # 删除评论
```

**问题**：
- 😕 需要通过查询参数表达资源关系
- 😕 URL 不直观，不符合 RESTful 规范
- 😕 需要额外验证 `post_id` 的有效性

#### 方案 B：嵌套路由（推荐）✅

```http
POST   /posts/{post_id}/comments           # 为文章创建评论
GET    /posts/{post_id}/comments           # 获取文章的所有评论
GET    /posts/{post_id}/comments/{comment_id}  # 获取单条评论
PATCH  /posts/{post_id}/comments/{comment_id}  # 更新评论
DELETE /posts/{post_id}/comments/{comment_id}  # 删除评论
```

**优势**：
- ✅ URL 直接体现层级关系
- ✅ 符合 RESTful 资源嵌套设计
- ✅ 路径参数自动验证
- ✅ 语义清晰，可读性强

### 2.2 嵌套路由的实现

#### FastAPI 路由定义

```python
from fastapi import APIRouter

router = APIRouter()

# 嵌套路由：/posts/{post_id}/comments
@router.post("/{post_id}/comments", response_model=CommentResponse)
async def create_comment(
    post_id: UUID,                              # 路径参数：文章ID
    comment_in: CommentCreate,                  # 请求体
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    """为指定文章创建评论"""
    # post_id 已经通过路径参数传入，无需查询参数
    pass

@router.get("/{post_id}/comments", response_model=list[CommentResponse])
async def get_comments(
    post_id: UUID,                              # 路径参数：文章ID
    db: Session = Depends(get_db),
):
    """获取文章的所有评论（树形结构）"""
    pass
```

#### 路由注册

```python
# app/api/v1/api.py
from app.api.v1.endpoints import posts, comments

# 将评论路由嵌套到 posts 下
api_router.include_router(
    comments.router,
    prefix="/posts",          # 前缀：/posts
    tags=["评论管理"],
)
```

**最终 URL**：
- `/api/v1/posts/{post_id}/comments` ✅

### 2.3 嵌套路由的优势

#### 优势 1：URL 即文档

```http
# 一眼看出：这是"文章的评论"
GET /posts/abc-123/comments

# 而不是需要阅读文档才知道
GET /comments?post_id=abc-123
```

#### 优势 2：路径参数自动校验

```python
@router.post("/{post_id}/comments")
async def create_comment(
    post_id: UUID,  # FastAPI 自动验证 UUID 格式
    ...
):
    # 如果 post_id 不是有效 UUID，FastAPI 自动返回 422
    pass
```

#### 优势 3：业务逻辑内聚

```python
# 在函数开头就能验证文章存在性
post = crud.post.get(db, id=post_id)
if not post:
    raise HTTPException(404, "文章不存在")

# 后续逻辑可以确保 post 存在
comment = crud.comment.create_with_post(
    db, obj_in=comment_in, post_id=post.id
)
```

---

## 三、评论层级结构实现

### 3.1 数据库设计回顾

#### Comment 模型的自引用关系

```python
class Comment(Base):
    __tablename__ = "comments"

    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    content: Mapped[str] = mapped_column(Text, nullable=False)

    # 外键：父评论ID（None 表示顶级评论）
    parent_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("comments.id", ondelete="CASCADE"),
        nullable=True,
    )

    # 关系映射：自引用
    parent: Mapped["Comment | None"] = relationship(
        "Comment",
        remote_side=[id],              # 🔥 关键：指定远端是 id 字段
        back_populates="replies",
    )

    replies: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="parent",
        cascade="all, delete-orphan",  # 删除评论时级联删除子评论
    )
```

**关键点**：
- `remote_side=[id]`：解决自引用的歧义性
- `cascade="all, delete-orphan"`：删除父评论时自动删除所有子评论

### 3.2 评论结构示意

```
文章：《FastAPI 入门教程》
│
├─ 评论1: "写得很好！"                    (parent_id=None, 顶级评论)
│  ├─ 评论2: "同意楼上"                   (parent_id=评论1)
│  └─ 评论3: "@用户2 感谢支持"             (parent_id=评论1)
│
└─ 评论4: "请问如何部署？"                 (parent_id=None, 顶级评论)
   └─ 评论5: "可以用 Docker"              (parent_id=评论4)
```

### 3.3 前端展示需求

前端通常需要**树形结构**，而不是扁平列表：

#### 树形结构（推荐）✅

```json
[
  {
    "id": "comment-1",
    "content": "写得很好！",
    "author": {...},
    "replies": [
      {
        "id": "comment-2",
        "content": "同意楼上",
        "replies": []
      },
      {
        "id": "comment-3",
        "content": "@用户2 感谢支持",
        "replies": []
      }
    ]
  },
  {
    "id": "comment-4",
    "content": "请问如何部署？",
    "replies": [
      {
        "id": "comment-5",
        "content": "可以用 Docker",
        "replies": []
      }
    ]
  }
]
```

**优势**：
- ✅ 前端直接渲染，无需额外处理
- ✅ 层级关系清晰
- ✅ 支持无限层级嵌套

#### 扁平列表（不推荐）❌

```json
[
  {"id": "comment-1", "content": "写得很好！", "parent_id": null},
  {"id": "comment-2", "content": "同意楼上", "parent_id": "comment-1"},
  {"id": "comment-3", "content": "@用户2 感谢支持", "parent_id": "comment-1"},
  {"id": "comment-4", "content": "请问如何部署？", "parent_id": null},
  {"id": "comment-5", "content": "可以用 Docker", "parent_id": "comment-4"}
]
```

**问题**：
- ❌ 前端需要自己组装树结构（增加复杂度）
- ❌ 层级关系不直观

---

## 四、递归模型应用

### 4.1 Pydantic 递归模型

#### CommentResponse 定义

```python
from pydantic import BaseModel, ConfigDict
from uuid import UUID
from datetime import datetime

class CommentResponse(BaseModel):
    """评论响应模型（递归结构）"""

    id: UUID
    content: str
    author: UserResponse           # 嵌套：作者信息
    created_at: datetime
    replies: list["CommentResponse"] = []  # 🔥 递归：回复列表

    model_config = ConfigDict(
        from_attributes=True,      # 允许从 ORM 对象创建
    )
```

**关键点**：
- `list["CommentResponse"]`：用字符串引用自身类型
- `from_attributes=True`：支持从 ORM 模型转换

### 4.2 递归模型的工作原理

#### Pydantic 如何处理递归？

```python
# ORM 查询结果
comment_orm = Comment(
    id=UUID("..."),
    content="写得很好！",
    author=User(...),
    replies=[
        Comment(id=UUID("..."), content="同意楼上", replies=[]),
        Comment(id=UUID("..."), content="感谢支持", replies=[]),
    ]
)

# Pydantic 自动递归序列化
comment_response = CommentResponse.model_validate(comment_orm)

# 结果
{
  "id": "...",
  "content": "写得很好！",
  "author": {...},
  "replies": [
    {"id": "...", "content": "同意楼上", "replies": []},
    {"id": "...", "content": "感谢支持", "replies": []}
  ]
}
```

**工作流程**：
1. Pydantic 验证顶层 `CommentResponse` 字段
2. 遇到 `replies: list["CommentResponse"]` 时
3. 递归调用 `CommentResponse` 验证每个子评论
4. 直到 `replies=[]`（递归终止条件）

### 4.3 递归模型的应用场景

| 场景 | 模型设计 |
|------|---------|
| **评论系统** | `Comment → replies: list["Comment"]` |
| **组织架构** | `Department → children: list["Department"]` |
| **分类目录** | `Category → subcategories: list["Category"]` |
| **文件系统** | `Folder → subfolders: list["Folder"]` |

---

## 五、权限控制设计

### 5.1 评论操作权限矩阵

| 操作 | 权限要求 | HTTP 状态码 |
|------|---------|------------|
| **创建评论** | 登录用户 | 401（未登录）|
| **查看评论** | 公开访问 | - |
| **删除评论** | 评论作者本人 | 403（无权限）|

### 5.2 创建评论权限

```python
@router.post("/{post_id}/comments", response_model=CommentResponse)
async def create_comment(
    post_id: UUID,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),  # 🔥 需要登录
):
    """创建评论（需要登录）"""
    # 1. 验证文章存在
    post = crud.post.get(db, id=post_id)
    if not post:
        raise HTTPException(404, "文章不存在")

    # 2. 如果是回复，验证父评论存在
    if comment_in.parent_id:
        parent = crud.comment.get(db, id=comment_in.parent_id)
        if not parent or parent.post_id != post_id:
            raise HTTPException(404, "父评论不存在或不属于该文章")

    # 3. 创建评论
    comment = crud.comment.create_post(
        db=db,
        obj_in=comment_in,
        author_id=current_user.id,
        post_id=post_id,
    )
    return comment
```

### 5.3 删除评论权限

```python
@router.delete(
    "/{post_id}/comments/{comment_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_comment(
    post_id: UUID,
    comment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),  # 🔥 需要登录
):
    """删除评论（仅作者本人）"""
    # 1. 查询评论
    comment = crud.comment.get(db, id=comment_id)
    if not comment:
        raise HTTPException(404, "评论不存在")

    # 2. 验证评论属于该文章
    if comment.post_id != post_id:
        raise HTTPException(404, "评论不属于该文章")

    # 3. 权限检查：只能删除自己的评论
    if comment.user_id != current_user.id:
        raise HTTPException(403, "无权删除他人评论")

    # 4. 执行删除（会级联删除所有子评论）
    crud.comment.remove(db, id=comment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

### 5.4 扩展：文章作者权限

如果需要实现"文章作者可以删除文章下的任何评论"：

```python
@router.delete("/{post_id}/comments/{comment_id}")
async def delete_comment(
    post_id: UUID,
    comment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
):
    comment = crud.comment.get(db, id=comment_id)
    if not comment:
        raise HTTPException(404, "评论不存在")

    # 查询文章
    post = crud.post.get(db, id=post_id)
    if not post:
        raise HTTPException(404, "文章不存在")

    # 权限检查：评论作者 OR 文章作者
    is_comment_author = comment.user_id == current_user.id
    is_post_author = post.author_id == current_user.id

    if not (is_comment_author or is_post_author):
        raise HTTPException(403, "无权删除此评论")

    crud.comment.remove(db, id=comment_id)
    return Response(status_code=status.HTTP_204_NO_CONTENT)
```

---

## 六、性能优化

### 6.1 N+1 查询问题

#### 问题场景

```python
# 查询所有顶级评论 - 1 次查询
top_comments = db.query(Comment).filter(Comment.parent_id == None).all()

# 遍历每个评论，访问 replies - N 次查询
for comment in top_comments:
    print(comment.replies)  # 每次访问触发一次查询 ❌
```

**查询次数**：1 + N（N = 顶级评论数）

#### 解决方案：lazy="selectin"

```python
# app/models/comment.py
class Comment(Base):
    replies: Mapped[list["Comment"]] = relationship(
        "Comment",
        back_populates="parent",
        lazy="selectin",  # 🔥 关键配置
        cascade="all, delete-orphan",
    )
```

**效果**：
- 第 1 次查询：获取所有顶级评论
- 第 2 次查询：批量获取所有子评论（一次性）

**查询次数**：2 次（无论有多少顶级评论）

### 6.2 lazy 策略对比

| 策略 | 加载时机 | 查询次数 | 适用场景 |
|------|---------|---------|---------|
| `select`（默认） | 首次访问时 | 1 + N | 很少访问关联数据 |
| `joined` | 立即加载（JOIN） | 1 | 总是需要关联数据 |
| `selectin` | 立即加载（IN） | 2 | 一对多关系优化 |
| `subquery` | 立即加载（子查询） | 2 | 复杂场景 |

### 6.3 评论查询优化实践

```python
# app/crud/comment.py
class CRUDComment(CRUDBase[Comment, CommentCreate, CommentUpdate]):
    def get_by_post(
        self,
        db: Session,
        *,
        post_id: UUID,
    ) -> list[Comment]:
        """获取文章的所有顶级评论（递归加载回复）

        性能优化：
        1. 只查询顶级评论（parent_id=None）
        2. replies 使用 lazy="selectin" 批量加载
        3. 总查询次数：2 次（无论评论层级多深）
        """
        return (
            db.query(Comment)
            .filter(
                Comment.post_id == post_id,
                Comment.parent_id == None,  # 只返回顶级评论
            )
            .order_by(Comment.created_at.desc())  # 最新评论在前
            .all()
        )
```

---

## 七、最佳实践总结

### 7.1 设计原则

1. **资源关系体现在 URL**
   - ✅ `/posts/{post_id}/comments` - 嵌套路由
   - ❌ `/comments?post_id=xxx` - 查询参数

2. **返回树形结构而非扁平列表**
   - ✅ 顶级评论 + 递归 replies
   - ❌ 所有评论的扁平列表

3. **权限检查三步走**
   - 第一步：验证资源存在（404）
   - 第二步：验证用户登录（401）
   - 第三步：验证操作权限（403）

### 7.2 性能优化要点

1. **使用 `lazy="selectin"` 避免 N+1 查询**
   ```python
   replies: Mapped[list["Comment"]] = relationship(
       lazy="selectin",  # 关键配置
   )
   ```

2. **只返回顶级评论，递归包含回复**
   ```python
   db.query(Comment).filter(Comment.parent_id == None).all()
   ```

3. **级联删除减少手动操作**
   ```python
   cascade="all, delete-orphan"  # 删除父评论自动删除子评论
   ```

### 7.3 常见陷阱

| 陷阱 | 正确做法 |
|------|---------|
| ❌ 返回所有评论（扁平） | ✅ 只返回顶级评论（树形） |
| ❌ 忘记验证 post_id | ✅ 先查询 post 是否存在 |
| ❌ 忘记验证 parent_id 属于同一文章 | ✅ 检查 `parent.post_id == post_id` |
| ❌ 直接删除评论不检查权限 | ✅ 验证 `comment.user_id == current_user.id` |

---

## 八、思考题

### 问题 1：路由设计
**为什么 `POST /posts/{post_id}/comments` 比 `POST /comments?post_id=xxx` 更好？**

<details>
<summary>点击查看答案</summary>

**答案**：
1. **语义清晰**：URL 直接表达"为某篇文章创建评论"，无需阅读文档
2. **RESTful 规范**：资源层级关系通过 URL 体现（评论属于文章）
3. **参数验证**：路径参数 `post_id` 由 FastAPI 自动验证（如 UUID 格式）
4. **业务内聚**：可以在函数开头统一验证文章存在性
5. **开发体验**：前端更容易理解和使用

</details>

### 问题 2：权限验证
**如果要实现"文章作者可以删除文章下的任何评论"，应该如何修改删除端点的权限检查逻辑？**

<details>
<summary>点击查看答案</summary>

**答案**：
```python
# 原逻辑：只检查评论作者
if comment.user_id != current_user.id:
    raise HTTPException(403, "无权删除他人评论")

# 扩展逻辑：评论作者 OR 文章作者
post = crud.post.get(db, id=post_id)
is_comment_author = comment.user_id == current_user.id
is_post_author = post.author_id == current_user.id

if not (is_comment_author or is_post_author):
    raise HTTPException(403, "无权删除此评论")
```

**关键点**：
- 需要额外查询 `post` 获取 `author_id`
- 使用逻辑或：`is_comment_author or is_post_author`
- 保持 403 状态码的语义一致性

</details>

### 问题 3：数据返回
**为什么 `GET /posts/{post_id}/comments` 只返回顶级评论（parent_id=None），而不是返回所有评论？**

<details>
<summary>点击查看答案</summary>

**答案**：
1. **前端体验**：树形结构直接渲染，无需前端组装
   ```json
   [
     {"id": 1, "content": "...", "replies": [
       {"id": 2, "content": "...", "replies": []}
     ]}
   ]
   ```

2. **性能优化**：结合 `lazy="selectin"`，只需 2 次查询完成所有数据加载
   - 第 1 次：顶级评论
   - 第 2 次：所有子评论（批量）

3. **业务语义**：用户期望看到的是"评论 + 回复"的层级结构，而非无序列表

4. **扩展性**：支持无限层级嵌套（递归模型自动处理）

**对比扁平列表**：
```json
// ❌ 扁平列表：前端需要自己组装树
[
  {"id": 1, "parent_id": null},
  {"id": 2, "parent_id": 1},
  {"id": 3, "parent_id": 1}
]
```

</details>

---

## 九、延伸阅读

- [RESTful API 设计指南](https://restfulapi.net/)
- [FastAPI 嵌套路由文档](https://fastapi.tiangolo.com/tutorial/bigger-applications/)
- [Pydantic 递归模型](https://docs.pydantic.dev/latest/concepts/models/#recursive-models)
- [SQLAlchemy relationship lazy 策略](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html#lazy-loading)

---

**文档版本**：v1.0
**创建时间**：2025-10-09
**适用版本**：FastAPI 0.115+, SQLAlchemy 2.0+, Pydantic 2.0+
