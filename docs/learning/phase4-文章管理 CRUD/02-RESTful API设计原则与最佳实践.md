# RESTful API 设计原则与最佳实践

> **Phase 4.4 核心知识点**：掌握 RESTful API 的设计原则，构建标准、易用、可维护的 Web API。

## 📚 目录

1. [REST 是什么？](#1-rest-是什么)
2. [HTTP 方法的语义](#2-http-方法的语义)
3. [URL 设计原则](#3-url-设计原则)
4. [状态码的正确使用](#4-状态码的正确使用)
5. [请求与响应格式](#5-请求与响应格式)
6. [错误处理设计](#6-错误处理设计)
7. [分页与过滤](#7-分页与过滤)
8. [版本控制策略](#8-版本控制策略)
9. [常见误区与陷阱](#9-常见误区与陷阱)
10. [国内 vs 国际实践对比](#10-国内-vs-国际实践对比)

---

## 1. REST 是什么？

### 1.1 核心概念

**REST** (Representational State Transfer - 表现层状态转移) 是一种**架构风格**，不是协议或标准。

**三个核心概念**：

```
┌─────────────────────────────────────────┐
│  资源 (Resource)                         │
│  - 一切皆资源：文章、用户、评论...        │
│  - 每个资源有唯一的 URI 标识             │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│  表现层 (Representation)                 │
│  - 资源的表现形式：JSON、XML、HTML...     │
│  - 同一资源可以有多种表现形式            │
└─────────────────────────────────────────┘
           ↓
┌─────────────────────────────────────────┐
│  状态转移 (State Transfer)               │
│  - 通过 HTTP 方法改变资源状态            │
│  - GET/POST/PUT/PATCH/DELETE           │
└─────────────────────────────────────────┘
```

### 1.2 REST 的六大约束

1. **客户端-服务器（Client-Server）**：分离关注点
2. **无状态（Stateless）**：每个请求包含所有必要信息
3. **可缓存（Cacheable）**：响应可以被缓存
4. **统一接口（Uniform Interface）**：标准的 HTTP 方法
5. **分层系统（Layered System）**：客户端不知道直接连接的是哪一层
6. **按需代码（Code on Demand）**：可选，服务器可以返回可执行代码

### 1.3 RESTful vs REST

```python
# REST：架构风格（一套设计理念）
# RESTful：符合 REST 风格的 API 设计

# ✅ RESTful API
GET /api/posts/123

# ❌ 非 RESTful API（RPC 风格）
GET /api/getPostById?id=123
```

---

## 2. HTTP 方法的语义

### 2.1 标准方法定义

| HTTP 方法 | CRUD 对应 | 语义 | 幂等性 | 安全性 |
|-----------|----------|------|--------|--------|
| **GET** | Read | 读取资源 | ✅ 是 | ✅ 是 |
| **POST** | Create | 创建资源 | ❌ 否 | ❌ 否 |
| **PUT** | Update | 完全替换资源 | ✅ 是 | ❌ 否 |
| **PATCH** | Update | 部分更新资源 | ❌ 否* | ❌ 否 |
| **DELETE** | Delete | 删除资源 | ✅ 是 | ❌ 否 |

**注**：PATCH 通常不是幂等的，但如果设计得当可以做到幂等。

### 2.2 幂等性详解

**幂等（Idempotent）**：多次执行相同操作，结果相同。

```python
# ✅ 幂等操作
GET    /posts/123    # 读 10 次，结果一样
PUT    /posts/123    # Body: {"title": "新标题", "content": "..."} 
                     # 更新 10 次，最终状态一样（完全替换）

DELETE /posts/123    # 删除 10 次，结果都是"已删除"（404）

# ❌ 非幂等操作
POST   /posts        # 创建 10 次，产生 10 篇不同的文章

PATCH  /posts/123    # Body: {"view_count": "+1"}
                     # 执行 10 次，浏览量 +10（每次都不同）
```

**为什么重要？**

```python
# 场景：网络不稳定，客户端超时重试

# 幂等操作（安全）
DELETE /posts/123
# 第 1 次：删除成功 → 200 OK
# 第 2 次（重试）：已删除 → 404 Not Found
# 结果：✅ 数据一致

# 非幂等操作（危险）
POST /posts
# 第 1 次：创建成功 → 201 Created (文章 A)
# 第 2 次（重试）：又创建 → 201 Created (文章 B)
# 结果：❌ 重复数据！

# 解决方案：幂等令牌
POST /posts
Headers: X-Idempotency-Key: unique-token-123
# 服务器检查令牌，防止重复创建
```

### 2.3 安全性详解

**安全（Safe）**：不改变服务器状态。

```python
# ✅ 安全方法（只读，不修改数据）
GET    /posts/123
HEAD   /posts/123  # 只返回头部，不返回 body
OPTIONS /posts     # 查询支持的方法

# ❌ 不安全方法（会修改数据）
POST   /posts
PUT    /posts/123
PATCH  /posts/123
DELETE /posts/123
```

### 2.4 PUT vs PATCH 的区别

这是一个经典的混淆点，让我们详细对比：

```python
# 原始资源
{
  "id": 123,
  "title": "旧标题",
  "content": "旧内容",
  "status": "draft",
  "tags": ["Python"]
}

# ====================================
# PUT：完全替换资源
# ====================================
PUT /posts/123
{
  "title": "新标题",
  "content": "新内容"
  # 注意：没有提供 status 和 tags
}

# 结果：❌ status 和 tags 会被清空（或设为默认值）
{
  "id": 123,
  "title": "新标题",
  "content": "新内容",
  "status": null,      # ❌ 被清空了
  "tags": []           # ❌ 被清空了
}

# ====================================
# PATCH：部分更新资源
# ====================================
PATCH /posts/123
{
  "title": "新标题"
  # 只提供要修改的字段
}

# 结果：✅ 其他字段保持不变
{
  "id": 123,
  "title": "新标题",      # ✅ 已更新
  "content": "旧内容",     # ✅ 保持不变
  "status": "draft",      # ✅ 保持不变
  "tags": ["Python"]      # ✅ 保持不变
}
```

**实践建议**：
- 🎯 **大多数情况用 PATCH**：部分更新更符合实际需求
- ⚠️ **PUT 用于完全替换**：如"重置为初始状态"这类场景
- 📖 **我们的项目使用 PATCH**：配合 `exclude_unset=True` 实现

---

## 3. URL 设计原则

### 3.1 核心原则

#### ✅ 原则 1：使用名词，不使用动词

```python
# ✅ 好的设计
GET    /posts              # 名词：文章列表
POST   /posts              # 名词：创建文章
GET    /posts/123          # 名词：特定文章
DELETE /posts/123          # 名词：删除文章

# ❌ 不好的设计
GET    /getPosts           # 动词：获取文章
POST   /createPost         # 动词：创建文章
GET    /posts/get/123      # 混用动词
DELETE /posts/delete/123   # 混用动词
```

**理由**：HTTP 方法已经表达了动作（GET=获取，POST=创建），URL 只需要指定资源。

#### ✅ 原则 2：使用复数形式

```python
# ✅ 推荐：统一使用复数
GET /posts       # 获取文章列表
GET /posts/123   # 获取单篇文章
GET /users       # 获取用户列表
GET /users/456   # 获取单个用户

# ❌ 不推荐：混用单复数
GET /post        # 单数
GET /post/123    # 单数
GET /users       # 复数
GET /user/456    # 又变单数了？
```

**理由**：统一使用复数，规则简单，不需要记忆哪个用单数哪个用复数。

#### ✅ 原则 3：表达层级关系

```python
# ✅ 好的设计：URL 体现资源的层级关系
GET    /posts/123/comments           # 获取文章 123 的评论列表
POST   /posts/123/comments           # 为文章 123 添加评论
GET    /posts/123/comments/456       # 获取文章 123 的评论 456
DELETE /posts/123/comments/456       # 删除文章 123 的评论 456

GET    /users/789/posts              # 获取用户 789 的文章列表
GET    /tags/python/posts            # 获取标签为 python 的文章

# ❌ 不好的设计：扁平结构，关系不清晰
GET    /comments?post_id=123         # 关系不明显
POST   /comments                     # 看不出是哪篇文章的评论
DELETE /comments/456                 # 可以接受，但不如嵌套清晰
```

**权衡**：
- **浅层嵌套（1-2 层）**：推荐，语义清晰
- **深层嵌套（3+ 层）**：不推荐，URL 太长

```python
# ⚠️ 嵌套太深，不推荐
GET /users/123/posts/456/comments/789/replies/101

# ✅ 替代方案：顶层资源 + 查询参数
GET /replies/101
GET /comments?post_id=456
```

#### ✅ 原则 4：使用小写字母和连字符

```python
# ✅ 推荐
GET /blog-posts
GET /user-profiles
GET /api/v1/article-categories

# ❌ 不推荐
GET /BlogPosts        # 大小写敏感，容易出错
GET /blog_posts       # 下划线在 URL 中不够明显
GET /blogposts        # 单词连在一起，难读
```

### 3.2 特殊操作的处理

有时候需要执行"动作"而不是操作"资源"，有以下几种方案：

#### 方案 1：把动作当作资源的属性（推荐）

```python
# 场景：发布文章（从草稿变为发布状态）

# ✅ 推荐：把状态当作资源的属性
PATCH /posts/123
{
  "status": "published"
}

# 优点：
# - 符合 REST 原则（操作资源）
# - 通用性强（同一端点可以改其他状态）
# - 实现简单（复用已有的 update 方法）
```

#### 方案 2：把动作当作子资源（可接受）

```python
# 场景：文章点赞

# ✅ 可接受：把点赞当作子资源
POST   /posts/123/likes     # 点赞（创建点赞记录）
DELETE /posts/123/likes     # 取消点赞（删除点赞记录）

# 优点：
# - 语义清晰（点赞是一个独立的资源）
# - 符合 REST 原则
```

#### 方案 3：使用动词端点（最后选择）

```python
# 场景：复杂的业务操作（如合并两篇文章）

# ⚠️ 可接受，但尽量避免
POST /posts/123/merge
{
  "target_post_id": 456
}

# 使用场景：
# - 操作不是 CRUD
# - 无法用资源属性表达
# - 业务逻辑复杂
```

### 3.3 实战示例：博客系统 API 设计

```python
# ================================
# 文章 API
# ================================
GET    /api/posts                    # 获取文章列表（支持分页、过滤）
POST   /api/posts                    # 创建新文章（草稿状态）
GET    /api/posts/{id}               # 获取指定文章
PATCH  /api/posts/{id}               # 更新文章（支持部分更新）
DELETE /api/posts/{id}               # 删除文章（软删除）

# 特殊操作：发布文章
PATCH  /api/posts/{id}               # Body: {"status": "published"}

# 特殊操作：恢复已删除的文章
PATCH  /api/posts/{id}               # Body: {"is_deleted": false}

# ================================
# 标签 API
# ================================
GET    /api/tags                     # 获取标签列表
GET    /api/tags/{id}                # 获取指定标签
GET    /api/tags/{id}/posts          # 获取该标签下的文章

# ================================
# 评论 API（嵌套资源）
# ================================
GET    /api/posts/{id}/comments      # 获取文章的评论列表
POST   /api/posts/{id}/comments      # 为文章添加评论
GET    /api/comments/{id}            # 获取指定评论（顶层资源）
PATCH  /api/comments/{id}            # 更新评论
DELETE /api/comments/{id}            # 删除评论

# 评论的回复（自引用关系）
POST   /api/comments/{id}/replies    # 回复评论
GET    /api/comments/{id}/replies    # 获取评论的回复列表

# ================================
# 用户 API
# ================================
GET    /api/users/{id}               # 获取用户信息
GET    /api/users/{id}/posts         # 获取用户的文章列表
GET    /api/users/{id}/comments      # 获取用户的评论列表

# ================================
# 认证 API（不是资源，是动作）
# ================================
POST   /api/auth/register            # 注册（例外：可以用动词）
POST   /api/auth/login               # 登录
POST   /api/auth/logout              # 登出
POST   /api/auth/refresh             # 刷新 Token
GET    /api/auth/me                  # 获取当前用户信息
```

---

## 4. 状态码的正确使用

### 4.1 常用状态码

#### 2xx 成功

| 状态码                | 含义  | 使用场景                       |
| ------------------ | --- | -------------------------- |
| **200 OK**         | 成功  | GET/PATCH/PUT 成功           |
| **201 Created**    | 已创建 | POST 创建资源成功                |
| **204 No Content** | 无内容 | DELETE 成功，或 PATCH 成功但不返回内容 |

```python
# ✅ 200 OK
GET /posts/123
Response: 200 OK
{
  "id": 123,
  "title": "文章标题",
  ...
}

# ✅ 201 Created
POST /posts
Response: 201 Created
Headers: Location: /posts/456
{
  "id": 456,
  "title": "新文章",
  ...
}

# ✅ 204 No Content
DELETE /posts/123
Response: 204 No Content
(无响应体)
```

#### 4xx 客户端错误

| 状态码 | 含义 | 使用场景 |
|--------|------|---------|
| **400 Bad Request** | 请求错误 | 参数验证失败 |
| **401 Unauthorized** | 未认证 | 缺少或无效的 Token |
| **403 Forbidden** | 无权限 | 有 Token 但权限不足 |
| **404 Not Found** | 资源不存在 | 请求的资源不存在 |
| **409 Conflict** | 冲突 | 资源已存在（如重复注册） |
| **422 Unprocessable Entity** | 无法处理的实体 | 语义错误（Pydantic 验证失败） |

```python
# ✅ 400 Bad Request - 参数类型错误
POST /posts
{
  "title": 123  # 应该是字符串
}
Response: 400 Bad Request
{
  "detail": "title must be a string"
}

# ✅ 401 Unauthorized - 缺少 Token
GET /posts/123
Headers: (没有 Authorization)
Response: 401 Unauthorized
{
  "detail": "Not authenticated"
}

# ✅ 403 Forbidden - 权限不足
DELETE /posts/123
Headers: Authorization: Bearer <user-token>
Response: 403 Forbidden
{
  "detail": "Only admin or author can delete posts"
}

# ✅ 404 Not Found
GET /posts/99999
Response: 404 Not Found
{
  "detail": "Post not found"
}

# ✅ 409 Conflict - 资源冲突
POST /users
{
  "email": "exist@example.com"  # 邮箱已存在
}
Response: 409 Conflict
{
  "detail": "Email already registered"
}

# ✅ 422 Unprocessable Entity - Pydantic 验证失败
POST /posts
{
  "title": "",  # 空标题
  "content": ""
}
Response: 422 Unprocessable Entity
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "ensure this value has at least 1 characters",
      "type": "value_error.any_str.min_length"
    }
  ]
}
```

#### 5xx 服务器错误

| 状态码 | 含义 | 使用场景 |
|--------|------|---------|
| **500 Internal Server Error** | 服务器错误 | 未捕获的异常 |
| **503 Service Unavailable** | 服务不可用 | 数据库连接失败等 |

```python
# ✅ 500 Internal Server Error
GET /posts/123
# 服务器代码抛出异常
Response: 500 Internal Server Error
{
  "detail": "Internal server error"
}

# ✅ 503 Service Unavailable
GET /posts
# 数据库无法连接
Response: 503 Service Unavailable
{
  "detail": "Database connection failed"
}
```

### 4.2 状态码选择决策树

```
请求成功？
├─ 是 → 用 2xx
│   ├─ 创建了新资源？
│   │   ├─ 是 → 201 Created
│   │   └─ 否 → 200 OK
│   └─ 不返回内容？
│       └─ 是 → 204 No Content
│
└─ 否 → 是谁的错？
    ├─ 客户端 → 用 4xx
    │   ├─ 请求格式错误？ → 400 Bad Request
    │   ├─ 未登录？ → 401 Unauthorized
    │   ├─ 无权限？ → 403 Forbidden
    │   ├─ 资源不存在？ → 404 Not Found
    │   ├─ 资源冲突？ → 409 Conflict
    │   └─ 数据验证失败？ → 422 Unprocessable Entity
    │
    └─ 服务器 → 用 5xx
        ├─ 代码异常？ → 500 Internal Server Error
        └─ 服务不可用？ → 503 Service Unavailable
```

---

## 5. 请求与响应格式

### 5.1 请求格式

#### Content-Type 选择

```python
# ✅ 推荐：application/json（最常用）
POST /posts
Content-Type: application/json
{
  "title": "文章标题",
  "content": "文章内容"
}

# ✅ 文件上传：multipart/form-data
POST /posts/123/cover
Content-Type: multipart/form-data
------WebKitFormBoundary
Content-Disposition: form-data; name="file"; filename="cover.jpg"
...

# ⚠️ 表单：application/x-www-form-urlencoded（少用）
POST /auth/login
Content-Type: application/x-www-form-urlencoded
username=admin&password=secret
```

### 5.2 响应格式

#### 统一的响应结构

```python
# ✅ 推荐：简洁的响应（FastAPI 默认）
GET /posts/123
Response: 200 OK
{
  "id": 123,
  "title": "文章标题",
  "content": "文章内容",
  "author": {
    "id": 456,
    "username": "alice"
  },
  "created_at": "2024-01-01T00:00:00Z"
}

# ❌ 不推荐：过度包装
{
  "code": 200,
  "message": "success",
  "data": {
    "id": 123,
    "title": "文章标题",
    ...
  }
}
```

**理由**：
- HTTP 状态码已经表达了成功/失败（200/400/500）
- 不需要在响应体中再包一层 `code`
- 简洁的响应更符合 REST 原则

#### 列表响应的分页信息

```python
# ✅ 推荐：分页元数据
GET /posts?page=2&size=20
Response: 200 OK
{
  "items": [
    {"id": 21, "title": "文章 21"},
    {"id": 22, "title": "文章 22"},
    ...
  ],
  "total": 100,
  "page": 2,
  "size": 20,
  "pages": 5
}
```

---

## 6. 错误处理设计

### 6.1 错误响应格式

```python
# ✅ FastAPI 默认格式（推荐）
Response: 422 Unprocessable Entity
{
  "detail": [
    {
      "loc": ["body", "title"],
      "msg": "field required",
      "type": "value_error.missing"
    }
  ]
}

# ✅ 自定义错误格式
Response: 400 Bad Request
{
  "detail": "Invalid post status",
  "error_code": "INVALID_STATUS",
  "timestamp": "2024-01-01T00:00:00Z"
}
```

### 6.2 错误码设计

```python
# 错误码分类（可选，适合大型项目）
{
  "detail": "Email already registered",
  "error_code": "AUTH_001",  # 认证类错误 001
  "error_type": "conflict"
}

# 错误码表（示例）
AUTH_001 = "Email already registered"
AUTH_002 = "Invalid credentials"
POST_001 = "Post not found"
POST_002 = "Invalid post status"
```

---

## 7. 分页与过滤

### 7.1 分页设计

```python
# ✅ 推荐：基于页码的分页（简单场景）
GET /posts?page=2&size=20

# ✅ 推荐：基于游标的分页（性能更好）
GET /posts?cursor=eyJpZCI6MTIzfQ&size=20

# ❌ 不推荐：用 limit/offset（数据库术语泄露）
GET /posts?limit=20&offset=40
```

### 7.2 过滤设计

```python
# ✅ 推荐：查询参数过滤
GET /posts?status=published&author_id=123&tag=python

# ✅ 推荐：日期范围过滤
GET /posts?created_after=2024-01-01&created_before=2024-12-31

# ✅ 推荐：排序
GET /posts?sort=-created_at,title  # - 表示降序
```

---

## 8. 版本控制策略

### 8.1 版本控制方式

```python
# 方式 1：URL 路径（推荐，最明确）
GET /api/v1/posts
GET /api/v2/posts

# 方式 2：请求头（灵活，但不够直观）
GET /api/posts
Headers: Accept: application/vnd.myapi.v2+json

# 方式 3：查询参数（不推荐）
GET /api/posts?version=2
```

### 8.2 版本策略

```python
# ✅ 推荐：主版本号变化表示破坏性更新
/api/v1/posts  → /api/v2/posts  # 响应格式完全不同

# ✅ 推荐：同一版本内保持向后兼容
/api/v1/posts  # 新增字段，但不删除旧字段
```

---

## 9. 常见误区与陷阱

### ❌ 陷阱 1：在 URL 中使用动词

```python
# ❌ 错误
GET /getPosts
POST /createPost
PUT /updatePost/123

# ✅ 正确
GET /posts
POST /posts
PUT /posts/123
```

### ❌ 陷阱 2：混用单复数

```python
# ❌ 错误
GET /post       # 单数
GET /users      # 复数
GET /tag/123    # 单数

# ✅ 正确：统一使用复数
GET /posts
GET /users
GET /tags/123
```

### ❌ 陷阱 3：用 POST 做所有操作

```python
# ❌ 错误（国内常见反模式）
POST /posts/get
POST /posts/update
POST /posts/delete

# ✅ 正确
GET    /posts
PATCH  /posts/123
DELETE /posts/123
```

### ❌ 陷阱 4：状态码使用不当

```python
# ❌ 错误：删除成功返回 200 + 空对象
DELETE /posts/123
Response: 200 OK
{}

# ✅ 正确：返回 204 No Content
DELETE /posts/123
Response: 204 No Content
(无响应体)

# ❌ 错误：创建成功返回 200
POST /posts
Response: 200 OK

# ✅ 正确：返回 201 Created
POST /posts
Response: 201 Created
Headers: Location: /posts/456
```

### ❌ 陷阱 5：过度包装响应

```python
# ❌ 错误：重复的状态信息
Response: 200 OK
{
  "code": 200,
  "status": "success",
  "message": "OK",
  "data": { ... }
}

# ✅ 正确：简洁的响应
Response: 200 OK
{
  "id": 123,
  "title": "文章标题",
  ...
}
```

---

## 10. 国内 vs 国际实践对比

### 10.1 为什么国内常见 GET + POST？

#### 原因 1：历史遗留

```html
<!-- 早期 HTML 表单只支持 GET 和 POST -->
<form method="GET">   ✅ 支持
<form method="POST">  ✅ 支持
<form method="PUT">   ❌ 不支持
<form method="DELETE">❌ 不支持
```

很多开发者从 PHP/JSP 时代过来，习惯了只用 GET/POST。

#### 原因 2：浏览器兼容性误解

```javascript
// 实际上，现代浏览器完全支持所有 HTTP 方法
fetch('/posts/123', {
  method: 'DELETE',  // ✅ 完全支持
  method: 'PATCH',   // ✅ 完全支持
})

// 但很多开发者以为不支持，所以用 POST 模拟
fetch('/posts/123', {
  method: 'POST',
  body: JSON.stringify({ _method: 'DELETE' })  // ❌ 不必要
})
```

#### 原因 3：防火墙/代理限制（真实原因）

```python
# 某些老旧的企业防火墙只允许 GET/POST
# 例如某些银行、政府机构的网络环境

# 请求：DELETE /posts/123
# 防火墙：❌ 拒绝（不在白名单中）

# 妥协方案：POST /posts/delete
# 防火墙：✅ 允许
```

#### 原因 4：团队经验不足

- 📚 缺少 REST 培训
- 🏃 "能用就行，不管规范"
- 📋 没有 Code Review

### 10.2 国际对比

| 地区/公司 | HTTP 方法使用 | REST 规范性 |
|-----------|-------------|-----------|
| **国内中小团队** | 主要 GET + POST | ⭐⭐ (20%) |
| **国内大厂** | 全方法 | ⭐⭐⭐⭐ (80%) |
| **国外科技公司** | 全方法 + HATEOAS | ⭐⭐⭐⭐⭐ (95%) |

**国内大厂的例子**：

```python
# 阿里云 API
GET    /instances       # ✅ 规范
POST   /instances       # ✅ 规范
PUT    /instances/xxx   # ✅ 规范
DELETE /instances/xxx   # ✅ 规范

# 腾讯云 API - 同样规范
```

### 10.3 我们的选择

**本项目采用标准 RESTful 设计**：

```python
# ✅ 使用完整的 HTTP 方法语义
GET    /api/posts
POST   /api/posts
PATCH  /api/posts/{id}
DELETE /api/posts/{id}

# ✅ 符合国际标准
# ✅ 易于维护和扩展
# ✅ 工具支持好（Postman/Swagger 等）
```

---

## 🎓 学习检验

### 思考题 1：发布文章

假设要设计"发布文章"功能（将草稿改为发布状态），以下哪个方案最符合 REST 原则？

**方案 A**：`POST /posts/123/publish`  
**方案 B**：`PATCH /posts/123` (body: `{"status": "published"}`)  
**方案 C**：`PUT /posts/123/status` (body: `"published"`)

<details>
<summary>点击查看答案</summary>

**答案：方案 B**

**理由**：
- ✅ PATCH 语义正确（部分更新资源）
- ✅ URL 简洁（直接操作资源）
- ✅ 通用性强（同一端点可更新其他字段）
- ✅ 符合我们的 CRUD 设计

**方案 A 的问题**：
- ❌ URL 中出现动词（publish）
- ❌ 不够通用（只能发布，不能改回草稿）

**方案 C 的问题**：
- ⚠️ 勉强可以，但不够简洁
- ⚠️ PUT 语义是"完全替换"，这里只改一个字段
</details>

### 思考题 2：文章点赞

设计"文章点赞"功能（用户可以点赞，也可以取消点赞），你会怎么设计？

<details>
<summary>点击查看答案</summary>

**推荐方案：把点赞当作子资源**

```python
# 点赞
POST /posts/123/likes
Response: 201 Created
{
  "user_id": 456,
  "post_id": 123,
  "created_at": "2024-01-01T00:00:00Z"
}

# 取消点赞
DELETE /posts/123/likes
Response: 204 No Content

# 查询点赞状态
GET /posts/123/likes
Response: 200 OK
{
  "is_liked": true,
  "total_likes": 42
}
```

**理由**：
- ✅ 点赞是一个独立的资源（可以有自己的 ID、时间戳等）
- ✅ 符合 REST 原则（创建/删除资源）
- ✅ 语义清晰（POST=点赞，DELETE=取消点赞）
</details>

---

## 📚 总结

### 核心要点

1. **资源导向**：URL 表示资源（名词），HTTP 方法表示操作（动词）
2. **HTTP 语义**：正确使用 GET/POST/PUT/PATCH/DELETE
3. **状态码**：用 HTTP 状态码表示结果，不要在响应体中重复
4. **简洁清晰**：URL 设计要简洁、一致、易于理解
5. **向后兼容**：API 版本升级要考虑兼容性

### 最佳实践

- ✅ 使用复数名词（/posts, /users）
- ✅ 使用 PATCH 做部分更新
- ✅ 返回 201 + Location 头（创建资源）
- ✅ 返回 204 No Content（删除成功）
- ✅ 使用查询参数做过滤和分页
- ✅ 提供清晰的错误信息

### 避免的陷阱

- ❌ URL 中使用动词
- ❌ 混用单复数
- ❌ 只用 GET + POST
- ❌ 过度包装响应
- ❌ 状态码使用不当

---

**🎉 恭喜！** 你已经掌握了 RESTful API 设计的核心原则！

接下来我们将把这些原则应用到实际的 FastAPI 代码中，构建标准、健壮的 Web API。💪
