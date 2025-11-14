# 数据库设计参考

## 📊 数据库概览

**数据库名称**：`blogdb`
**数据库类型**：PostgreSQL 17.6
**字符编码**：UTF-8
**时区**：UTC

## 🏗️ 核心设计原则

- **主键策略**：所有表使用 UUID 作为主键，支持分布式系统
- **时间戳**：所有表包含 `created_at` 和 `updated_at` 字段
- **软删除**：重要数据支持软删除机制
- **索引策略**：合理添加索引优化查询性能
- **约束完整性**：严格的数据完整性约束

## 字段分类的核心原则
### 1️⃣ **业务核心字段**

描述实体本质特征的数据

```python
# User 模型
username: str           # 用户身份
email: str             # 联系方式
hashed_password: str   # 认证凭证

# Post 模型
title: str             # 文章标题
content: str           # 文章内容
author_id: int         # 作者关系
```

**判断标准**：没有这个字段，实体就不完整

---

### 2️⃣ **状态字段 (State)**

记录实体**当前所处的状态**，会随时间/操作**频繁变化**

#### 特征识别

- ✅ **动态性**：经常被修改
- ✅ **反映现状**：描述"现在是什么样"
- ✅ **触发业务逻辑**：不同状态对应不同处理规则

#### User 模型状态字段

```python
is_active: bool        # 账户当前是否可用
is_admin: bool     # 当前是否拥有管理员权限
is_verified: bool      # 邮箱当前是否已验证
```

**为什么是状态？**

- `is_active`: 可以被禁用/恢复，影响登录权限
- `is_superuser`: 可以升级/降级角色
- `is_verified`: 完成邮箱验证后从 False → True

#### Post 模型状态字段

```python
status: PostStatus     # 草稿/已发布/已删除
view_count: int        # 浏览次数（持续增长）
```

**为什么是状态？**

- `status`: 编辑流程中频繁切换（草稿→发布→下线）
- `view_count`: 每次访问都会 +1

---

### 3️⃣ **配置字段 (Configuration)**

定义实体的**规则/策略/偏好**，变化频率低，像"开关"

#### 特征识别

- ✅ **静态性**：很少修改
- ✅ **控制行为**：决定"如何运作"
- ✅ **用户主动设置**：通常在创建/设置时确定

#### Post 模型配置字段

```python
is_published: bool        # 是否公开（用户设置）
allow_comments: bool      # 是否允许评论（作者控制）
is_featured: bool         # 是否精选（编辑决策）
```

**为什么是配置？**

- `is_published`: 作者主动选择"要不要公开"
- `allow_comments`: 作者决定文章的交互规则
- `is_featured`: 运营设置的展示策略

---

### 🤔 边界模糊案例分析

#### Case 1: `Post.status` vs `Post.is_published`

```python
# 方案 A：用 status 统一管理（推荐）
status: PostStatus  # draft/published/archived

# 方案 B：拆分为多个布尔字段
is_published: bool
is_archived: bool
```

**分析**：

- `status` 更像**状态机**（互斥状态：草稿/发布/归档）
- `is_published` 更像**配置开关**（作者的发布意图）

**选择依据**：

- 如果状态有明确的**流转规则**（草稿→审核→发布）→ 用枚举
- 如果是**独立的布尔属性**（可以同时为真）→ 用独立字段

---

#### Case 2: `User.is_active` 到底是状态还是配置？

```python
is_active: bool  # 账户是否激活
```

**双重性质**：

- **状态视角**：账户当前可用性（管理员可禁用）
- **配置视角**：账户功能开关（用户可注销）

**判断关键**：看**谁触发修改**

- 由**系统/管理员**修改 → 描述"事实" → 状态
- 由**用户主动**设置 → 描述"策略" → 配置

这里 `is_active` 主要由管理员控制（封号/解封），所以归类为**状态**。

---

#### Case 3: `view_count` 为什么不是配置？

```python
view_count: int  # 浏览计数
```

**反例思考**：如果是配置，应该是这样

```python
max_views: int        # 最大浏览限制（配置）
current_views: int    # 当前浏览数（状态）
```

**本质区别**：

- `view_count` 是**系统自动维护**的统计数据 → 状态
- 如果是**用户设定的阈值** → 配置

---

### 📊 完整对比表

| 维度        | 业务核心字段                 | 状态字段                        | 配置字段                        |
| --------- | ---------------------- | --------------------------- | --------------------------- |
| **修改频率**  | 很少                     | 频繁                          | 偶尔                          |
| **由谁修改**  | 用户输入                   | 系统/业务流程                     | 用户主动设置                      |
| **影响逻辑**  | 定义实体                   | 触发不同行为，影响流程                 | 控制功能开关，不影响流程                |
| **举例**    | Post.title, Uesr.email | Post.status, User.is_active | Post.is_featured, User.role |
| **数据库索引** | 常加索引                   | 常加索引（查询条件）                  | 较少索引                        |

---
### 🎓 实战判断流程

遇到新字段时，依次问自己：

```
1. 没有这个字段，实体还完整吗？
   ├─ 否 → 业务核心字段
   └─ 是 → 继续

2. 这个字段会被频繁修改吗？
   ├─ 是 → 继续 3
   └─ 否 → 配置字段

3. 修改是由系统自动触发的吗？
   ├─ 是 → 状态字段
   └─ 否 → 配置字段
```

---

### 💡 设计建议

#### 1. 优先用枚举而不是多个布尔字段

```python
# ❌ 不推荐：多个布尔字段（可能出现矛盾状态）
is_draft: bool
is_published: bool
is_archived: bool

# ✅ 推荐：枚举状态机
status: PostStatus  # 互斥且清晰
```

#### 2. 状态和配置可以共存

```python
class Post:
    status: PostStatus           # 状态：当前发布状态
    allow_comments: bool         # 配置：是否允许评论
    is_featured: bool            # 配置：是否精选显示
```

#### 3. 命名约定

```python
# 状态字段：描述当前状态
is_active          # 当前是否激活
status             # 当前状态
last_login_at      # 最后登录时间

# 配置字段：描述策略/偏好
allow_*            # 是否允许
enable_*           # 是否启用
max_*              # 最大限制
```

---


## 📋 表结构设计

### 1. 用户表 (users)

**用途**：管理系统用户，包括普通用户和管理员

| 字段名           | 数据类型         | 约束                       | 描述             | 字段类型        | 索引     | 更新          |
| ------------- | ------------ | ------------------------ | -------------- | ----------- | ------ | ----------- |
| id            | UUID         | PK                       | 用户唯一标识         | 主键          | PK     |             |
| username      | VARCHAR(50)  | UNIQUE, NOT NULL         | 用户名（登录用）       | 业务核心字段-登录凭证 | UNIQUE |             |
| email         | VARCHAR(255) | UNIQUE, NOT NULL         | 邮箱地址           | 业务核心字段-登录凭证 | UNIQUE |             |
| password_hash | VARCHAR(255) | NOT NULL                 | 密码哈希值          | 业务核心字段-登录凭证 | -      |             |
| nickname      | VARCHAR(100) | NOT NULL                 | 显示昵称           | 业务核心字段-基本信息 | -      |             |
| avatar        | VARCHAR(255) | NULL                     | 头像 URL         | 业务核心字段-基本信息 | -      |             |
| bio           | VARCHAR(255) | NULL                     | 个人简介           | 业务核心字段-基本信息 |        | 20251028 新增 |
| role          | ENUM         | NOT NULL, DEFAULT 'user' | 用户角色           | 配置字段        | INDEX  |             |
| is_active     | BOOLEAN      | NOT NULL, DEFAULT true   | 账户是否激活（管理员可禁用） | 状态字段        | INDEX  |             |
| is_verified   | BOOLEAN      | NOT NULL, DEFAULT false  | 邮箱验证状态         | 状态字段        | -      |             |
| last_login    | TIMESTAMP    | NULL                     | 最后登录时间         | 时间戳字段       | INDEX  |             |
| created_at    | TIMESTAMP    | NOT NULL, DEFAULT NOW()  | 创建时间           | 时间戳字段       | INDEX  |             |
| updated_at    | TIMESTAMP    | NOT NULL, DEFAULT NOW()  | 更新时间           | 时间戳字段       | -      |             |
| deleted_at    | TIMESTAMP    | NULL                     | 软删除时间（用户删除账号）  | 时间戳字段       |        |             |


**枚举定义**：
```sql
CREATE TYPE user_role AS ENUM ('user', 'admin');
```

>[!NOTE]
> 软删除字段说明：
> 
> | 场景 | is_active | deleted_at | 说明 |
> |--------|------------|------------|----------------|
> | 正常用户 | True | None | 可以正常使用 |
> | 管理员禁用 | False | None | 违规、审核等，可恢复 |
> | 用户删除账号 | True/False | 2025-10-05 | 用户主动删除，30天内可恢复 |


### 2. 文章表 (posts)

**用途**：存储博客文章内容和元数据

| 字段名            | 数据类型         | 约束                        | 描述       | 字段类型          | 索引     | 更新        |
| -------------- | ------------ | ------------------------- | -------- | ------------- | ------ | --------- |
| id             | UUID         | PK                        | 文章唯一标识   | 主键            | PK     |           |
| title          | VARCHAR(200) | NOT NULL                  | 文章标题     | 业务核心字段-文章内容   | INDEX  |           |
| content        | TEXT         | NOT NULL                  | 文章正文     | 业务核心字段-文章内容   | -      |           |
| summary        | VARCHAR(500) | NULL                      | 文章摘要     | 业务核心字段-文章内容   | -      |           |
| slug           | VARCHAR(200) | UNIQUE, NOT NULL          | URL 友好标识 | 业务核心字段-文章内容   | UNIQUE |           |
| status         | ENUM         | NOT NULL, DEFAULT 'draft' | 发布状态     | 状态字段          | INDEX  |           |
| is_featured    | BOOLEAN      | NOT NULL, DEFAULT false   | 是否置顶     | 配置字段          | INDEX  |           |
| view_count     | INTEGER      | NOT NULL, DEFAULT 0       | 浏览次数     | 状态字段          | -      |           |
| like_count     | INTEGER      | NOT NULL, DEFAULT 0       | 点赞数      | 状态字段          |        | Phase6 新增 |
| favorite_count | INTEGER      | NOT NULL, DEFAULT 0       | 收藏数      | 状态字段          |        | Phase6 新增 |
| author_id      | UUID         | FK, NOT NULL              | 作者 ID    | 关联外键-users.id | INDEX  |           |
| published_at   | TIMESTAMP    | NULL                      | 发布时间     | 时间戳字段         | INDEX  |           |
| created_at     | TIMESTAMP    | NOT NULL, DEFAULT NOW()   | 创建时间     | 时间戳字段         | INDEX  |           |
| updated_at     | TIMESTAMP    | NOT NULL, DEFAULT NOW()   | 更新时间     | 时间戳字段         | -      |           |

**枚举定义**：
```sql
CREATE TYPE post_status AS ENUM ('draft', 'published', 'archived');
```

**外键约束**：
```sql
ALTER TABLE posts ADD CONSTRAINT fk_posts_author
FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE;
```

### 3. 评论表 (comments)

**用途**：存储文章评论，支持层级结构

| 字段名         | 数据类型      | 约束                      | 描述         | 字段类型             | 索引    |
| ----------- | --------- | ----------------------- | ---------- | ---------------- | ----- |
| id          | UUID      | PK                      | 评论唯一标识     | 主键               | PK    |
| content     | TEXT      | NOT NULL                | 评论内容       | 业务核心内容           | -     |
| post_id     | UUID      | FK, NOT NULL            | 所属文章 ID    | 关联外键-posts.id    | INDEX |
| author_id   | UUID      | FK, NOT NULL            | 评论者 ID     | 关键外键-users.id    | INDEX |
| parent_id   | UUID      | FK, NULL                | 父评论 ID（层级） | 关键外键-comments.id | INDEX |
| is_approved | BOOLEAN   | NOT NULL, DEFAULT true  | 是否审核通过     | 状态字段             | INDEX |
| is_deleted  | BOOLEAN   | NOT NULL, DEFAULT false | 软删除标记      | 状态字段             | INDEX |
| created_at  | TIMESTAMP | NOT NULL, DEFAULT NOW() | 创建时间       | 时间戳字段            | INDEX |
| updated_at  | TIMESTAMP | NOT NULL, DEFAULT NOW() | 更新时间       | 时间戳字段            | -     |
>[!NOTE] 
>为什么需要审核？
  >- 防止垃圾评论、广告、恶意内容
  >- 管理员可以先审核后再公开显示 

**外键约束**：
```sql
ALTER TABLE comments ADD CONSTRAINT fk_comments_post
FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE;

ALTER TABLE comments ADD CONSTRAINT fk_comments_author
FOREIGN KEY (author_id) REFERENCES users(id) ON DELETE CASCADE;

ALTER TABLE comments ADD CONSTRAINT fk_comments_parent
FOREIGN KEY (parent_id) REFERENCES comments(id) ON DELETE CASCADE;
```
---
#### 评论层级结构设计 🌳

  这是 Comment 模型的核心难点！我们需要支持"评论回复评论"的功能。

##### 设计方案对比

  **方案 1：邻接列表（Adjacency List）**✅ 我们采用这个

  原理：每个评论记录一个 parent_id 字段，指向父评论

  Comment:
    - id: UUID
    - parent_id: UUID | None  # 指向父评论，顶级评论为 None
    - post_id: UUID           # 所属文章
    - user_id: UUID           # 评论作者
    - content: str            # 评论内容

  优点：
  - ✅ 简单直观，易于理解和实现
  - ✅ 插入新评论非常快（只需要一条 INSERT）
  - ✅ 支持无限层级
  - ✅ SQLAlchemy 原生支持（relationship + remote_side）

  缺点：
  - ❌ 查询整棵树需要递归或多次查询
  - ❌ 显示评论树时需要应用层处理

  示例数据：
  文章1的评论：
  ┌─ Comment 1 (parent_id=None)
  │  └─ Comment 2 (parent_id=1)  # 回复 Comment 1
  │     └─ Comment 3 (parent_id=2)  # 回复 Comment 2
  └─ Comment 4 (parent_id=None)

  **方案 2：路径枚举（Path Enumeration）**

  原理：每个评论存储完整路径

  Comment:
    - path: str  # 例如 "1/2/3" 表示 评论3 -> 评论2 -> 评论1

  优点：
  - ✅ 查询子树非常快（LIKE 'path%'）
  - ✅ 可以直接获取层级深度

  缺点：
  - ❌ 更新路径复杂（移动节点时需要更新所有子节点）
  - ❌ 路径长度有限制

##### 2.2 SQLAlchemy 自引用关系（Self-Referential Relationship）

  关键技术：使用 remote_side 参数
```python
class Comment(Base):
      id: Mapped[UUID] = mapped_column(primary_key=True)
      parent_id: Mapped[UUID | None] = mapped_column(ForeignKey("comments.id"))

      # 定义父子关系
      parent: Mapped["Comment | None"] = relationship(
          "Comment",
          remote_side=[id],  # ⭐ 关键：指定"远端"是 id 字段
          back_populates="replies"
      )

      replies: Mapped[list["Comment"]] = relationship(
          "Comment",
          back_populates="parent",
          cascade="all, delete-orphan"  # 删除评论时级联删除子评论
      )
```
  
理解 remote_side：
  - SQLAlchemy 需要知道哪一端是"父"，哪一端是"子"
  - remote_side=[id] 表示：id 字段是关系的"远端"（父节点）
  - 这样 SQLAlchemy 就知道 parent_id 引用的是 id


### 4. 标签表 (tags)

**用途**：文章分类标签管理

| 字段名 | 类型 | 约束 | 描述 | 索引 |
|--------|------|------|------|------|
| id | UUID | PK | 标签唯一标识 | PK |
| name | VARCHAR(50) | UNIQUE, NOT NULL | 标签名称 | UNIQUE |
| slug | VARCHAR(50) | UNIQUE, NOT NULL | URL 友好标识 | UNIQUE |
| description | VARCHAR(255) | NULL | 标签描述 | - |
| color | VARCHAR(7) | NULL | 标签颜色（HEX） | - |
| post_count | INTEGER | NOT NULL, DEFAULT 0 | 文章数量 | - |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 创建时间 | - |
| updated_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 更新时间 | - |

### 5. 文章标签关联表 (post_tags)

**用途**：文章与标签的多对多关联

| 字段名 | 类型 | 约束 | 描述 | 索引 |
|--------|------|------|------|------|
| post_id | UUID | FK, PK | 文章 ID | PK |
| tag_id | UUID | FK, PK | 标签 ID | PK |
| created_at | TIMESTAMP | NOT NULL, DEFAULT NOW() | 关联时间 | - |

**外键约束**：
```sql
ALTER TABLE post_tags ADD CONSTRAINT fk_post_tags_post
FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE;

ALTER TABLE post_tags ADD CONSTRAINT fk_post_tags_tag
FOREIGN KEY (tag_id) REFERENCES tags(id) ON DELETE CASCADE;
```

### 6. 文章浏览记录表 (post_views)

**用途**：记录文章浏览历史和统计

| 字段名        | 类型           | 约束                      | 描述         | 索引    |
| ---------- | ------------ | ----------------------- | ---------- | ----- |
| id         | UUID         | PK                      | 记录唯一标识     | PK    |
| post_id    | UUID         | FK, NOT NULL            | 文章 ID      | INDEX |
| user_id    | UUID         | FK, NULL                | 用户 ID（可为空） | INDEX |
| ip_address | INET         | NULL                    | 访问者 IP     | INDEX |
| user_agent | VARCHAR(500) | NULL                    | 浏览器信息      | -     |
| referer    | VARCHAR(500) | NULL                    | 来源页面       | -     |
| view_time  | INTEGER      | NULL                    | 阅读时长（秒）    | -     |
| viewd_at   | TIMESTAMP    | NOT NULL, DEFAULT NOW() | 浏览时间       | INDEX |
>[!NOTE]
>1. user_id 可控的意义：
> 	- 支持匿名用户浏览（核心需求）
>	- 用户注销后记录仍有效（数据完整性）
>	- 查询需注意：WHERE user_id IS NULL vs WHERE user_id = ?
  >
  >1. 要不要建立 post_id和 user_id的联合唯一索引？
  >	- 不去重：可以统计浏览次数，记录每次浏览实践
  >	- 去重：只记录首次/最后浏览，节省存储空间
  >	- 推荐：不去重，业务层控制重复逻辑
  >	
>1. IP 地址和 User-Agent（防刷和分析）
> 	  - 防刷浏览量：限制同一 IP 短时间内的重复浏览
> 	- 数据分析：统计浏览器、设备、地理位置分布
  >	- 安全审计：记录异常访问行为
  >	  
  >1.  与 Post.view_count 的关系：
> 	- view_count：冗余字段，快速查询
 > 	- PostView 记录：详细数据，支持分析
  > 	 - 定期同步：post.view_count = len(post.post_views)
  > 1. 性能优化考虑：
> 	- 高频写入：浏览记录每次都插入
  > 	 - 建议：异步写入、批量插入、定期归档
   > 	- 索引：(post_id, viewed_at)、(user_id, viewed_at)

  
**外键约束**：
```sql
ALTER TABLE post_views ADD CONSTRAINT fk_post_views_post
FOREIGN KEY (post_id) REFERENCES posts(id) ON DELETE CASCADE;

ALTER TABLE post_views ADD CONSTRAINT fk_post_views_user
FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE SET NULL;
```

## 🔗 关系设计

### 实体关系图

```
Users (1) ----< (N) Posts
  |                  |
  |                  |
  v                  v
Comments (N) >---- (1) Posts
  |
  v
Comments (自关联 - 层级结构)

Posts (N) ----< >---- (N) Tags
           post_tags

Posts (1) ----< (N) PostViews
Users (1) ----< (N) PostViews (可选)
```

### 关系说明

1. **User → Post**：一对多，一个用户可以发布多篇文章
2. **Post → Comment**：一对多，一篇文章可以有多个评论
3. **User → Comment**：一对多，一个用户可以发表多个评论
4. **Comment → Comment**：自关联，支持评论回复层级
5. **Post ↔ Tag**：多对多，文章可以有多个标签，标签可以关联多篇文章
6. **Post → PostView**：一对多，一篇文章可以有多次浏览记录
7. **User → PostView**：一对多，一个用户可以有多次浏览记录（可选关联）

## 📈 索引策略

### 主要索引

```sql
-- 用户表索引
CREATE INDEX idx_users_role ON users(role);
CREATE INDEX idx_users_is_active ON users(is_active);
CREATE INDEX idx_users_created_at ON users(created_at);
CREATE INDEX idx_users_last_login ON users(last_login);

-- 文章表索引
CREATE INDEX idx_posts_author_id ON posts(author_id);
CREATE INDEX idx_posts_status ON posts(status);
CREATE INDEX idx_posts_is_featured ON posts(is_featured);
CREATE INDEX idx_posts_published_at ON posts(published_at);
CREATE INDEX idx_posts_created_at ON posts(created_at);
CREATE INDEX idx_posts_title ON posts(title);

-- 评论表索引
CREATE INDEX idx_comments_post_id ON comments(post_id);
CREATE INDEX idx_comments_author_id ON comments(author_id);
CREATE INDEX idx_comments_parent_id ON comments(parent_id);
CREATE INDEX idx_comments_is_approved ON comments(is_approved);
CREATE INDEX idx_comments_created_at ON comments(created_at);

-- 浏览记录表索引
CREATE INDEX idx_post_views_post_id ON post_views(post_id);
CREATE INDEX idx_post_views_user_id ON post_views(user_id);
CREATE INDEX idx_post_views_ip_address ON post_views(ip_address);
CREATE INDEX idx_post_views_created_at ON post_views(created_at);
```

### 复合索引

```sql
-- 查询用户的已发布文章
CREATE INDEX idx_posts_author_status ON posts(author_id, status);

-- 查询文章的已审核评论
CREATE INDEX idx_comments_post_approved ON comments(post_id, is_approved);

-- 查询特定时间范围的浏览记录
CREATE INDEX idx_post_views_time_post ON post_views(created_at, post_id);
```

## 🚀 性能优化

### 查询优化
- 使用索引覆盖常见查询模式
- 避免全表扫描
- 合理使用 LIMIT 和分页

### 数据完整性
- 外键约束确保引用完整性
- 检查约束验证数据有效性
- 唯一约束防止重复数据

### 扩展性考虑
- UUID 主键支持分布式
- 预留扩展字段
- 支持软删除机制

---

**最后更新**：2025-01-28
**下次更新**：Post 模型创建后