# Phase 6.2 点赞与收藏功能 - 概要设计

> **设计目标**：实现文章点赞和收藏功能，提升用户互动体验
> **预估工作量**：2-3 天
> **技术重点**：幂等性设计、计数缓存、性能优化

---

## 1. 业务逻辑与用户故事

### 1.1 核心场景

**读者视角**：
- 浏览文章时，看到点赞数和收藏数
- 点击喜欢按钮，表达对文章的认可
- 收藏优质文章，方便日后查阅
- 查看自己的点赞历史和收藏列表

**作者视角**：
- 实时看到文章的互动数据
- 通过数据分析文章受欢迎程度
- 了解哪些内容更能引起共鸣

### 1.2 业务规则

**前提条件**：
- ⭐ **重要**：只能对已发布（status='published'）的文章进行点赞/收藏
- ❌ 草稿（draft）和归档（archived）文章不允许互动操作

**点赞规则**：
- ✅ 用户可以对已发布文章点赞/取消点赞
- ✅ 同一用户对同一文章只能点赞一次
- ✅ 点赞状态可以切换（幂等操作）
- ✅ 点赞后实时更新计数

**收藏规则**：
- ✅ 用户可以收藏/取消收藏已发布文章
- ✅ 收藏状态可以切换
- ✅ 收藏列表支持分页查询
- ✅ 收藏数实时更新

---

## 2. 技术选型与架构设计

### 2.1 数据模型设计

#### 方案对比

**方案A：纯关联表模式**
```python
# 优点：数据一致性最好
# 缺点：每次查询需要 COUNT 操作，性能较差
class PostLike(Base):
    user_id: int
    post_id: int
    created_at: datetime
```

**方案B：关联表 + 缓存字段** ⭐ **推荐方案**
```python
# 优点：查询性能好，数据一致性可控
# 缺点：需要维护缓存字段同步
class Post(Base):
    like_count: int = 0      # 缓存点赞数
    favorite_count: int = 0  # 缓存收藏数

class PostLike(Base):
    user_id: int
    post_id: int
    created_at: datetime
```

**技术决策理由**：
1. **性能优先**：文章列表页频繁显示点赞数，避免 COUNT 查询
2. **一致性可控**：通过数据库约束和事务保证一致性
3. **扩展性好**：为后续统计功能提供数据基础

### 2.2 API 设计模式

#### RESTful 设计原则

```
POST   /posts/{id}/like     # 切换点赞状态（幂等）
GET    /posts/{id}/likes    # 获取点赞列表（分页）
GET    /users/me/liked-posts # 我的点赞历史

POST   /posts/{id}/favorite # 切换收藏状态（幂等）
GET    /users/me/favorites  # 我的收藏列表
```

**设计亮点**：
- **幂等性**：重复调用同一接口，结果一致
- **语义化**：POST 表示状态切换，GET 表示查询
- **权限控制**：只有登录用户才能操作

### 2.3 并发控制策略

#### 重复点赞问题

**问题场景**：用户快速双击点赞按钮

**解决方案**：
1. **数据库唯一约束**：`(user_id, post_id)` 唯一索引
2. **应用层幂等检查**：先查询再决定操作
3. **事务隔离**：使用 SERIALIZABLE 隔离级别

---

## 3. 数据库设计详解

### 3.1 表结构设计

```sql
-- 文章点赞表
CREATE TABLE post_likes (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    post_id INTEGER NOT NULL REFERENCES posts(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, post_id)  -- 防止重复点赞
);

-- 文章收藏表
CREATE TABLE post_favorites (
    id SERIAL PRIMARY KEY,
    user_id INTEGER NOT NULL REFERENCES users(id),
    post_id INTEGER NOT NULL REFERENCES posts(id),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(user_id, post_id)  -- 防止重复收藏
);

-- 扩展文章表
ALTER TABLE posts
ADD COLUMN like_count INTEGER DEFAULT 0,
ADD COLUMN favorite_count INTEGER DEFAULT 0;
```

### 3.2 索引优化策略

```sql
-- 查询用户点赞记录
CREATE INDEX idx_post_likes_user_id ON post_likes(user_id);

-- 查询文章点赞记录（用于统计和验证）
CREATE INDEX idx_post_likes_post_id ON post_likes(post_id);

-- 复合索引（支持用户收藏列表分页查询）
CREATE INDEX idx_post_favorites_user_created ON post_favorites(user_id, created_at DESC);
```

### 3.3 数据一致性保障

**事务设计**：
```python
@db.transaction
def toggle_like(user_id: int, post_id: int):
    # 1. 查询当前状态
    exists = session.query(PostLike).filter_by(
        user_id=user_id, post_id=post_id
    ).first()

    if exists:
        # 2. 取消点赞
        session.delete(exists)
        # 3. 更新计数
        post.like_count -= 1
    else:
        # 2. 添加点赞
        like = PostLike(user_id=user_id, post_id=post_id)
        session.add(like)
        # 3. 更新计数
        post.like_count += 1
```

---

## 4. API 接口设计

### 4.1 端点规划

#### 点赞相关接口

```python
# 切换点赞状态
POST /api/v1/posts/{post_id}/like
Response: {
    "is_liked": boolean,
    "like_count": int
}

# 我的点赞历史
GET /api/v1/users/me/liked-posts?page=1&size=20
Response: PaginatedResponse[PostSummary]
```

#### 收藏相关接口

```python
# 切换收藏状态
POST /api/v1/posts/{post_id}/favorite
Response: {
    "is_favorited": boolean,
    "favorite_count": int
}

# 我的收藏列表
GET /api/v1/users/me/favorites?page=1&size=20
Response: PaginatedResponse[PostSummary]
```

### 4.2 Schema 设计

```python
class PostLikeResponse(BaseModel):
    is_liked: bool
    like_count: int

class PostFavoriteResponse(BaseModel):
    is_favorited: bool
    favorite_count: int

class PostWithInteraction(BaseModel):
    # 继承 PostResponse 所有字段
    id: int
    title: str
    # ...
    # 新增互动字段
    is_liked: bool = False
    is_favorited: bool = False
    like_count: int = 0
    favorite_count: int = 0
```

---

## 5. 性能优化策略

### 5.1 查询优化

#### N+1 查询问题

**问题**：获取文章列表时，每篇文章都要查询点赞状态

**解决方案**：
```python
# 方案A：LEFT JOIN 一次性查询
SELECT p.*,
       CASE WHEN pl.user_id IS NOT NULL THEN true ELSE false END as is_liked
FROM posts p
LEFT JOIN post_likes pl ON p.id = pl.post_id AND pl.user_id = :user_id

# 方案B：批量查询 + 字典映射 ⭐ 推荐
post_ids = [post.id for post in posts]
liked_posts = session.query(PostLike.post_id).filter(
    PostLike.user_id == user_id,
    PostLike.post_id.in_(post_ids)
).all()
liked_dict = {post_id for post_id, in liked_posts}
```

### 5.2 缓存策略

#### 计数字段缓存

**更新策略**：
- 实时更新：每次点赞/取消时立即更新计数
- 批量同步：定期校验计数准确性
- 异常修复：提供计数修复工具

```python
def fix_like_counts():
    """修复点赞计数（数据修复工具）"""
    for post in session.query(Post).all():
        actual_count = session.query(func.count(PostLike.id)).filter(
            PostLike.post_id == post.id
        ).scalar()
        if post.like_count != actual_count:
            post.like_count = actual_count
```

---

## 6. 安全性设计

### 6.1 权限控制

**操作权限**：
- ✅ 登录用户可以对已发布文章点赞/收藏
- ❌ 未登录用户无法操作
- ❌ 不能对草稿或归档文章进行互动操作
- ✅ 用户只能查看自己的点赞/收藏历史

**数据权限**：
- ✅ 任何人都可以查看已发布文章的点赞数/收藏数
- ❌ 草稿和归档文章不显示互动数据
- ❌ 不能操作他人的点赞/收藏

**业务规则验证**：
- ✅ API 层验证文章状态必须是 'published'
- ✅ 返回明确的错误信息（如"只能对已发布文章进行互动操作"）

### 6.2 防刷机制

**频率限制**：
```python
# 短时间内大量点赞操作
@limiter.limit("30/minute")  # 每分钟最多30次
async def toggle_like():
    pass
```

**异常检测**：
- 监控异常点赞模式
- 记录操作日志
- 必要时进行封禁

---

## 7. 测试策略

### 7.1 测试设计原则

**测试数据四象限**：
1. **正常数据**：标准用户对已发布文章点赞/收藏操作
2. **边界数据**：新用户、空列表、单页边界
3. **异常数据**：不存在的文章、已删除文章、草稿文章、归档文章
4. **极端数据**：大量点赞、快速连续操作

### 7.2 关键测试场景

```python
# 幂等性测试
async def test_like_toggle_idempotent():
    # 第一次点赞
    response1 = await client.post("/posts/1/like")
    assert response1.json()["is_liked"] == True

    # 第二次点赞（应该取消）
    response2 = await client.post("/posts/1/like")
    assert response2.json()["is_liked"] == False

# 并发测试
async def test_concurrent_likes():
    # 模拟多个用户同时点赞
    tasks = [client.post(f"/posts/1/like") for _ in range(10)]
    responses = await asyncio.gather(*tasks)
    # 验证数据一致性

# 文章状态限制测试
async def test_like_draft_post():
    # 尝试对草稿文章点赞（应该失败）
    draft_post = create_post(status="draft")
    response = await client.post(f"/posts/{draft_post.id}/like")
    assert response.status_code == 400
    assert "只能对已发布文章" in response.json()["detail"]

async def test_like_archived_post():
    # 尝试对归档文章点赞（应该失败）
    archived_post = create_post(status="archived")
    response = await client.post(f"/posts/{archived_post.id}/like")
    assert response.status_code == 400
    assert "只能对已发布文章" in response.json()["detail"]
```

---

## 8. 扩展性考虑

### 8.1 未来功能扩展

**通知系统集成**：
- 点赞时通知文章作者
- 收藏时可以不通知（避免打扰）

**统计分析功能**：
- 日均点赞数统计
- 热门文章排行
- 用户行为分析

**社交功能增强**：
- 关注用户的点赞动态
- 基于点赞的内容推荐

### 8.2 架构扩展点

**缓存层**：Redis 缓存热点数据
**消息队列**：异步处理通知
**数据仓库**：离线分析用户行为

---

## 9. 开发计划

### 9.1 实施步骤

**Step 1**: 数据模型设计（1天）
- 创建 PostLike、PostFavorite 模型
- 数据库迁移脚本
- 基础 CRUD 操作

**Step 2**: API 接口实现（1天）
- 点赞/收藏接口
- 查询接口
- 权限控制

**Step 3**: 集成测试（0.5天）
- 功能测试
- 性能测试
- 边界测试

### 9.2 质量保障

- **代码质量**：ruff + mypy 检查
- **测试覆盖率**：目标 90%+
- **性能基准**：单次操作 < 100ms
- **数据一致性**：事务保障 + 约束校验

---

## 10. 思考题

为了检验你对设计的理解，请思考以下问题：

1. **幂等性设计**：为什么点赞接口设计为 POST /posts/{id}/like 而不是 PUT？这种设计如何保证幂等性？

2. **性能权衡**：为什么不直接每次 COUNT 查询点赞数，而要维护 like_count 字段？这种设计的优缺点是什么？

3. **并发安全**：如果用户快速双击点赞按钮，可能会出现什么问题？数据库唯一约束是如何解决这个问题的？

4. **扩展性**：如果未来要支持"踩"（dislike）功能，你会如何扩展现有设计？需要修改哪些表和接口？

5. **数据一致性**：在什么情况下 like_count 字段可能与实际点赞数不一致？如何检测和修复这种不一致？