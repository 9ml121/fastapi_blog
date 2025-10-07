# FastAPI 路由设计完整指南

> **学习目标**: 掌握 FastAPI 路由系统的设计原理、模块化组织方式和 RESTful API 最佳实践

## 📋 目录

1. [路由系统的本质](#1-路由系统的本质)
2. [FastAPI 三层路由架构](#2-fastapi-三层路由架构)
3. [APIRouter 深度解析](#3-apirouter-深度解析)
4. [请求处理完整流程](#4-请求处理完整流程)
5. [HTTP 状态码语义](#5-http-状态码语义)
6. [RESTful API 设计原则](#6-restful-api-设计原则)
7. [实战案例：认证系统 API](#7-实战案例认证系统-api)

---

## 1. 路由系统的本质

### 1.1 什么是路由?

**路由(Routing)** 是 Web 框架的核心机制,负责将 HTTP 请求分发到对应的处理函数。

**类比餐厅点餐系统**:
```
客户请求: "我要一份宫保鸡丁"
  ↓
菜单(路由表): 宫保鸡丁 → 川菜厨师
  ↓
厨师(处理函数): 按菜谱制作 → 返回成品
```

**Web 应用中的路由**:
```
HTTP 请求: POST /api/v1/auth/register
  ↓
路由表: /api/v1/auth/register → register() 函数
  ↓
处理函数: 验证数据 → 创建用户 → 返回 JSON
```

### 1.2 为什么需要路由系统?

#### ❌ 没有路由系统的混乱代码

```python
# 所有逻辑挤在一个函数里 - 噩梦级代码!
def handle_request(request):
    if request.path == "/register" and request.method == "POST":
        # 100 行注册逻辑
        pass
    elif request.path == "/login" and request.method == "POST":
        # 100 行登录逻辑
        pass
    elif request.path == "/posts" and request.method == "GET":
        # 100 行文章列表逻辑
        pass
    # ... 300 个 elif 后,代码无法维护
```

**问题**:
- ❌ 所有逻辑混在一起,难以理解
- ❌ 修改一个功能可能影响其他功能
- ❌ 无法进行模块化开发
- ❌ 测试困难,必须测试整个巨型函数

#### ✅ 使用路由系统的优雅代码

```python
# 每个功能独立为一个函数
@app.post("/api/v1/auth/register")
async def register(user_data: UserCreate):
    # 只关注注册逻辑
    return {"msg": "注册成功"}

@app.post("/api/v1/auth/login")
async def login(credentials: LoginForm):
    # 只关注登录逻辑
    return {"access_token": "..."}
```

**优势**:
- ✅ **单一职责**: 每个函数只做一件事
- ✅ **职责分离**: URL 路径、HTTP 方法、业务逻辑清晰分离
- ✅ **可维护性**: 修改注册逻辑不影响登录
- ✅ **可测试性**: 可以独立测试每个函数

---

## 2. FastAPI 三层路由架构

### 2.1 推荐的项目结构

```
fastapi_blog/
├── app/
│   ├── main.py              # 第1层: 应用入口
│   ├── api/
│   │   └── v1/
│   │       ├── api.py       # 第2层: 路由聚合器
│   │       └── endpoints/
│   │           ├── auth.py  # 第3层: 业务路由
│   │           ├── posts.py
│   │           └── users.py
│   ├── schemas/             # 数据验证层
│   ├── crud/                # 数据库操作层
│   └── models/              # 数据模型层
```

### 2.2 三层架构详解

#### 第3层: endpoints/auth.py - 业务逻辑层

```python
"""
职责: 定义具体的 API 端点和业务逻辑
范围: 只关注 auth 相关的路由 (register, login, logout...)
"""
from fastapi import APIRouter

router = APIRouter()

@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_data: UserCreate,
    db: Session = Depends(get_db)
):
    """用户注册"""
    # 业务逻辑
    return created_user

@router.post("/login")
async def login(form_data: OAuth2PasswordRequestForm = Depends()):
    """用户登录"""
    # 业务逻辑
    return {"access_token": token}
```

**关键点**:
- 路径只写相对路径 (`/register` 而非 `/api/v1/auth/register`)
- 使用 `APIRouter()` 而非 `FastAPI()` 实例
- 专注单一模块的业务逻辑

#### 第2层: v1/api.py - 路由聚合层

```python
"""
职责: 汇总所有业务路由,添加统一配置
范围: 整个 v1 版本的所有 API
"""
from fastapi import APIRouter
from app.api.v1.endpoints import auth, posts, users

api_router = APIRouter()

# 汇总各模块路由
api_router.include_router(
    auth.router,
    prefix="/auth",      # 添加前缀: /auth/register
    tags=["认证"]         # Swagger 文档分组
)

api_router.include_router(
    posts.router,
    prefix="/posts",
    tags=["文章管理"]
)

api_router.include_router(
    users.router,
    prefix="/users",
    tags=["用户管理"]
)
```

**关键点**:
- 通过 `prefix` 添加模块前缀
- 通过 `tags` 在 Swagger UI 中分组显示
- 可以为整组路由添加公共依赖或中间件

#### 第1层: main.py - 应用入口层

```python
"""
职责: 创建 FastAPI 应用,注册顶级路由
范围: 全局配置、中间件、事件处理
"""
from fastapi import FastAPI
from app.api.v1.api import api_router

app = FastAPI(
    title="FastAPI 博客系统",
    description="学习现代 Web 开发的教学项目",
    version="1.0.0"
)

# 注册 API 路由
app.include_router(
    api_router,
    prefix="/api/v1"     # 版本控制前缀
)

# 全局配置
@app.on_event("startup")
async def startup():
    print("应用启动")
```

### 2.3 完整的 URL 路径组成

当用户访问 `POST /api/v1/auth/register` 时:

```
/api/v1          ← main.py 注册时的 prefix
    /auth        ← api.py 注册 auth.router 时的 prefix
        /register ← auth.py 中 @router.post("/register")

最终路径: /api/v1/auth/register
```

**三层拼接示意**:

```python
# endpoints/auth.py
@router.post("/register")        # 相对路径
         ↓
# v1/api.py
include_router(auth.router, prefix="/auth")   # + /auth
         ↓
# main.py
include_router(api_router, prefix="/api/v1") # + /api/v1
         ↓
# 最终 URL
POST /api/v1/auth/register
```

### 2.4 为什么要分三层?

| 层级 | 职责 | 修改频率 | 影响范围 |
|------|------|----------|----------|
| **endpoints/** | 具体业务逻辑 | 高 (经常添加新功能) | 单个模块 |
| **api.py** | 路由组织 | 中 (新增模块时) | 整个 API 版本 |
| **main.py** | 应用配置 | 低 (很少改动) | 全局 |

**设计原则**:
- ✅ **单一职责**: 每层只负责一件事
- ✅ **开闭原则**: 对扩展开放(易添加新路由),对修改封闭(不影响已有代码)
- ✅ **依赖倒置**: 上层依赖下层,但通过接口隔离

---

## 3. APIRouter 深度解析

### 3.1 APIRouter vs FastAPI 实例

#### FastAPI 实例
```python
from fastapi import FastAPI

app = FastAPI()  # 应用级别,全局唯一

@app.get("/")
async def root():
    return {"msg": "Hello"}
```

#### APIRouter 实例
```python
from fastapi import APIRouter

router = APIRouter()  # 可以有多个,模块化使用

@router.get("/items")
async def get_items():
    return {"items": []}
```

### 3.2 APIRouter 的核心特性

#### 特性1: 模块化路由

```python
# auth.py - 认证相关
auth_router = APIRouter()

@auth_router.post("/register")
async def register():
    pass

# posts.py - 文章相关
posts_router = APIRouter()

@posts_router.get("/")
async def list_posts():
    pass
```

#### 特性2: 公共配置

```python
# 为整个 router 设置公共配置
router = APIRouter(
    prefix="/admin",              # 所有路由自动加 /admin 前缀
    tags=["管理员"],               # Swagger 文档标签
    dependencies=[Depends(verify_admin)],  # 公共依赖(权限检查)
    responses={404: {"description": "未找到"}}  # 公共响应文档
)

@router.get("/users")  # 实际路径: /admin/users,且自动验证管理员权限
async def admin_list_users():
    pass
```

#### 特性3: 嵌套路由

```python
# 创建子路由
sub_router = APIRouter(prefix="/comments")

@sub_router.get("/")
async def list_comments():
    pass

# 包含到主路由
posts_router = APIRouter(prefix="/posts")
posts_router.include_router(sub_router)  # /posts/comments/

# 注册到应用
app.include_router(posts_router, prefix="/api/v1")
# 最终路径: /api/v1/posts/comments/
```

### 3.3 路由参数详解

```python
@router.post(
    "/register",                      # 路径
    response_model=UserResponse,      # 响应数据模型(自动序列化+文档)
    status_code=201,                  # 成功时的状态码
    summary="用户注册",                # API 摘要(显示在文档)
    description="创建新用户账号",      # 详细描述
    tags=["认证"],                     # 标签(可覆盖 router 的 tags)
    responses={                       # 可能的响应(用于文档)
        201: {"description": "注册成功"},
        409: {"description": "邮箱已存在"}
    },
    deprecated=False                  # 是否标记为已废弃
)
async def register(user_data: UserCreate):
    pass
```

---

## 4. 请求处理完整流程

### 4.1 从请求到响应的 7 个阶段

```
客户端发送: POST /api/v1/auth/register
         ↓
┌─────────────────────────────────────┐
│ 1. 路由匹配                          │
│    FastAPI 根据 URL + HTTP 方法      │
│    找到对应的处理函数                │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ 2. 请求数据解析                      │
│    - 解析 JSON body                 │
│    - 解析 URL 参数                  │
│    - 解析 Headers                   │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ 3. 数据验证 (Pydantic)              │
│    自动验证请求数据:                 │
│    - 类型检查 (str, int, email...)  │
│    - 必填字段检查                    │
│    - 自定义验证规则                  │
│    ❌ 验证失败 → 返回 422 错误      │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ 4. 依赖注入 (Depends)               │
│    自动调用并注入依赖:               │
│    - get_db() → 数据库会话          │
│    - get_current_user() → 当前用户  │
│    ❌ 依赖失败 → 抛出异常           │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ 5. 业务逻辑执行                      │
│    处理函数内的代码:                 │
│    - 调用 CRUD 操作数据库           │
│    - 执行业务规则                    │
│    - 调用外部服务                    │
│    ❌ 业务异常 → HTTPException      │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ 6. 响应序列化 (Pydantic)            │
│    将返回值转换为 JSON:              │
│    - 根据 response_model 过滤字段   │
│    - 自动转换数据类型                │
│    - 排除敏感字段 (如密码)           │
└─────────────────────────────────────┘
         ↓
┌─────────────────────────────────────┐
│ 7. HTTP 响应                        │
│    返回给客户端:                     │
│    - Status Code: 201               │
│    - Headers: Content-Type: json    │
│    - Body: {"id": "...", ...}       │
└─────────────────────────────────────┘
```

### 4.2 实际代码示例

```python
@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    user_data: UserCreate,           # 阶段3: 自动验证
    db: Session = Depends(get_db)    # 阶段4: 自动注入
):
    # 阶段5: 业务逻辑
    # 检查邮箱是否已存在
    existing = await crud.user.get_user_by_email(db, user_data.email)
    if existing:
        raise HTTPException(status_code=409, detail="邮箱已被注册")
    
    # 创建用户
    new_user = await crud.user.create_user(db, user_data)
    
    # 阶段6: 返回值自动序列化为 UserResponse (排除密码字段)
    return new_user
```

**请求流程示例**:

```json
// 客户端发送
POST /api/v1/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "username": "testuser",
  "password": "SecurePass123!"
}

// 服务器响应 (阶段6自动过滤了 hashed_password)
HTTP/1.1 201 Created
Content-Type: application/json

{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "testuser",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-10-06T10:30:00Z"
  // 注意: 没有 hashed_password 字段!
}
```

### 4.3 自动化的魔法

FastAPI 自动为你处理:
- ✅ **JSON 解析**: 自动将请求体解析为 Python 对象
- ✅ **类型转换**: "123" → 123, "true" → True
- ✅ **数据验证**: 邮箱格式、必填字段、值范围
- ✅ **错误响应**: 验证失败自动返回 422 + 详细错误信息
- ✅ **API 文档**: 自动生成 Swagger UI 和 ReDoc
- ✅ **类型提示**: IDE 自动补全和类型检查

---

## 5. HTTP 状态码语义

### 5.1 状态码分类

HTTP 状态码分为 5 大类:

| 类别 | 范围 | 含义 | 由谁决定 |
|------|------|------|----------|
| **1xx** | 100-199 | 信息性响应 | 服务器自动 |
| **2xx** | 200-299 | 成功 | ✅ 你需要选择 |
| **3xx** | 300-399 | 重定向 | 服务器/框架 |
| **4xx** | 400-499 | 客户端错误 | ✅ 你需要选择 |
| **5xx** | 500-599 | 服务器错误 | 通常自动 |

### 5.2 常用成功状态码 (2xx)

| 状态码 | 名称 | 语义 | 使用场景 |
|--------|------|------|----------|
| **200** | OK | 请求成功 | GET 获取资源、POST 操作成功 |
| **201** | Created | 创建成功 | POST 创建新资源 (注册用户、发表文章) |
| **204** | No Content | 成功但无内容 | DELETE 删除成功、PUT 更新成功 |

**示例**:

```python
# 200 OK - 获取资源
@router.get("/posts/{post_id}", status_code=200)  # 200 是默认值,可省略
async def get_post(post_id: UUID):
    return post

# 201 Created - 创建资源
@router.post("/posts", status_code=201)
async def create_post(post_data: PostCreate):
    return created_post

# 204 No Content - 删除成功
@router.delete("/posts/{post_id}", status_code=204)
async def delete_post(post_id: UUID):
    # 返回 None 或不返回
    return
```

### 5.3 常用客户端错误码 (4xx)

| 状态码 | 名称 | 语义 | 使用场景 |
|--------|------|------|----------|
| **400** | Bad Request | 请求格式错误 | 缺少必需参数、数据格式错误 |
| **401** | Unauthorized | 未认证 | 未提供 token、token 无效 |
| **403** | Forbidden | 无权限 | 已登录但权限不足 |
| **404** | Not Found | 资源不存在 | 用户ID不存在、文章已删除 |
| **409** | Conflict | 资源冲突 | 邮箱已注册、用户名重复 |
| **422** | Unprocessable Entity | 数据验证失败 | Pydantic 自动返回 |

**示例**:

```python
# 404 Not Found
@router.get("/users/{user_id}")
async def get_user(user_id: UUID, db: Session = Depends(get_db)):
    user = await crud.user.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user

# 409 Conflict - 资源冲突
@router.post("/register")
async def register(user_data: UserCreate, db: Session = Depends(get_db)):
    existing = await crud.user.get_user_by_email(db, user_data.email)
    if existing:
        raise HTTPException(status_code=409, detail="邮箱已被注册")
    return created_user

# 403 Forbidden - 权限不足
@router.delete("/users/{user_id}")
async def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser)  # 需要管理员权限
):
    # 只有管理员能删除用户
    return {"msg": "删除成功"}
```

### 5.4 状态码选择决策树

```
客户端发送请求
    ↓
请求格式正确? ──No→ 400 Bad Request
    ↓ Yes
需要认证? ──Yes→ 提供了有效 token? ──No→ 401 Unauthorized
    ↓ No                    ↓ Yes
数据验证通过? ──No→ 422 Unprocessable Entity
    ↓ Yes
资源存在? ──No→ 404 Not Found
    ↓ Yes
有权限? ──No→ 403 Forbidden
    ↓ Yes
资源冲突? ──Yes→ 409 Conflict (如邮箱已存在)
    ↓ No
执行操作
    ↓
操作类型?
    ├─ 查询 → 200 OK
    ├─ 创建 → 201 Created
    ├─ 更新 → 200 OK 或 204 No Content
    └─ 删除 → 204 No Content
```

### 5.5 常见错误状态码对比

| 场景 | ❌ 错误选择 | ✅ 正确选择 | 原因 |
|------|------------|------------|------|
| 邮箱已注册 | 400 | **409** | 资源冲突,不是格式错误 |
| 没有 token | 403 | **401** | 未认证,不是权限不足 |
| 普通用户访问管理员API | 401 | **403** | 已认证但权限不足 |
| Pydantic 验证失败 | 400 | **422** | FastAPI 约定用 422 |
| 用户 ID 不存在 | 400 | **404** | 资源不存在,不是格式错误 |

---

## 6. RESTful API 设计原则

### 6.1 什么是 RESTful?

**REST** (Representational State Transfer) 是一种 API 设计风格,核心思想:
- **资源导向**: URL 代表资源 (名词),HTTP 方法代表操作 (动词)
- **无状态**: 每个请求独立,服务器不保存客户端状态
- **统一接口**: 使用标准 HTTP 方法

### 6.2 RESTful URL 设计

#### ✅ 好的 URL 设计

```
GET    /api/v1/posts           # 获取文章列表
GET    /api/v1/posts/123       # 获取单篇文章
POST   /api/v1/posts           # 创建文章
PUT    /api/v1/posts/123       # 完整更新文章
PATCH  /api/v1/posts/123       # 部分更新文章
DELETE /api/v1/posts/123       # 删除文章

GET    /api/v1/posts/123/comments    # 获取文章的评论
POST   /api/v1/posts/123/comments    # 为文章添加评论
```

**设计原则**:
- ✅ 使用名词复数 (`/posts` 而非 `/post`)
- ✅ 使用 HTTP 方法表达操作 (GET, POST, PUT, DELETE)
- ✅ 资源嵌套表达关系 (`/posts/123/comments`)
- ✅ 使用小写字母和连字符 (`/blog-posts`)

#### ❌ 不好的 URL 设计

```
GET  /api/getPostList          # ❌ URL 中不要有动词
POST /api/createNewPost        # ❌ 应该用 POST /posts
GET  /api/deletePost?id=123    # ❌ 删除应该用 DELETE 方法
GET  /api/post/update/123      # ❌ 混乱的结构
```

### 6.3 HTTP 方法语义

| 方法 | 语义 | 幂等性 | 安全性 | 使用场景 |
|------|------|--------|--------|----------|
| **GET** | 读取资源 | ✅ | ✅ | 获取数据 |
| **POST** | 创建资源 | ❌ | ❌ | 注册、发表文章 |
| **PUT** | 完整更新 | ✅ | ❌ | 替换整个资源 |
| **PATCH** | 部分更新 | ❌ | ❌ | 更新部分字段 |
| **DELETE** | 删除资源 | ✅ | ❌ | 删除数据 |

**幂等性**: 多次执行结果相同
- `GET /posts/123` 多次调用,结果一样 ✅
- `POST /posts` 多次调用,创建多个资源 ❌
- `DELETE /posts/123` 多次调用,第一次删除,之后 404 ✅

### 6.4 PUT vs PATCH

```python
# PUT - 完整替换资源
PUT /api/v1/users/123
{
  "username": "newname",
  "email": "new@example.com",
  "bio": "新简介"
  # 必须提供所有字段!未提供的字段会被清空
}

# PATCH - 部分更新
PATCH /api/v1/users/123
{
  "bio": "新简介"
  # 只更新提供的字段,其他字段保持不变
}
```

**选择建议**:
- ✅ **首选 PATCH**: 大多数更新操作都是部分更新
- ⚠️ **慎用 PUT**: 需要客户端提供完整数据

---

## 7. 实战案例:认证系统 API

### 7.1 需求分析

我们要实现的 3 个认证 API:

| API | 功能 | 请求 | 响应 |
|-----|------|------|------|
| `POST /register` | 用户注册 | UserCreate | UserResponse + 201 |
| `POST /login` | 用户登录 | 用户名+密码 | access_token + 200 |
| `GET /me` | 获取当前用户 | Authorization头 | UserResponse + 200 |

### 7.2 完整认证流程

```
1️⃣ 注册流程
   POST /api/v1/auth/register
   Body: {"email": "...", "password": "..."}
        ↓
   验证邮箱未被注册
        ↓
   创建用户 (密码哈希)
        ↓
   201 Created + 用户信息

2️⃣ 登录流程
   POST /api/v1/auth/login
   Body: {"username": "...", "password": "..."}
        ↓
   验证用户名和密码
        ↓
   生成 JWT token
        ↓
   200 OK + {"access_token": "eyJ..."}

3️⃣ 访问受保护资源
   GET /api/v1/auth/me
   Header: Authorization: Bearer eyJ...
        ↓
   解析 token → 获取 user_id
        ↓
   查询数据库获取用户
        ↓
   200 OK + 用户信息
```

### 7.3 目录结构

```
app/
├── api/
│   ├── deps.py              # 依赖注入 (已完成)
│   └── v1/
│       ├── api.py           # 路由聚合 (待创建)
│       └── endpoints/
│           └── auth.py      # 认证路由 (待创建)
├── crud/
│   └── user.py              # User CRUD (已完成)
├── schemas/
│   └── user.py              # UserCreate, UserResponse (已完成)
├── core/
│   └── security.py          # JWT 函数 (已完成)
└── main.py                  # 应用入口 (待更新)
```

### 7.4 API 设计详解

#### API 1: 用户注册

```python
@router.post(
    "/register",
    response_model=UserResponse,  # 响应模型:排除密码
    status_code=201,              # 创建成功
    summary="用户注册",
    responses={
        201: {"description": "注册成功"},
        409: {"description": "邮箱或用户名已存在"}
    }
)
async def register(
    user_data: UserCreate,         # 请求体:自动验证
    db: Session = Depends(get_db)  # 依赖注入:数据库会话
):
    """
    用户注册流程:
    1. 验证邮箱未被注册
    2. 验证用户名未被使用
    3. 创建用户 (密码自动哈希)
    4. 返回用户信息 (排除密码)
    """
    # 检查邮箱
    if await crud.user.get_user_by_email(db, user_data.email):
        raise HTTPException(status_code=409, detail="邮箱已被注册")
    
    # 检查用户名
    if await crud.user.get_user_by_username(db, user_data.username):
        raise HTTPException(status_code=409, detail="用户名已被使用")
    
    # 创建用户
    new_user = await crud.user.create_user(db, user_data)
    return new_user  # 自动序列化为 UserResponse
```

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/register" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "SecurePass123!"
  }'
```

#### API 2: 用户登录

```python
@router.post(
    "/login",
    summary="用户登录",
    responses={
        200: {"description": "登录成功"},
        401: {"description": "用户名或密码错误"}
    }
)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),  # OAuth2 标准表单
    db: Session = Depends(get_db)
):
    """
    用户登录流程:
    1. 验证用户名和密码
    2. 生成 JWT access token
    3. 返回 token (用于后续请求认证)
    """
    # 认证用户 (防时序攻击)
    user = await crud.user.authenticate_user(
        db,
        form_data.username,
        form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=401,
            detail="用户名或密码错误"
        )
    
    # 生成 JWT token
    access_token = create_access_token(data={"sub": str(user.id)})
    
    return {
        "access_token": access_token,
        "token_type": "bearer"  # OAuth2 标准格式
    }
```

**请求示例**:
```bash
curl -X POST "http://localhost:8000/api/v1/auth/login" \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=SecurePass123!"
```

**响应**:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

#### API 3: 获取当前用户信息

```python
@router.get(
    "/me",
    response_model=UserResponse,
    summary="获取当前用户信息",
    responses={
        200: {"description": "成功"},
        401: {"description": "未认证或 token 无效"}
    }
)
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)  # 依赖注入:自动验证 token
):
    """
    获取当前登录用户的信息
    
    需要在 Header 中提供有效的 JWT token:
    Authorization: Bearer <access_token>
    """
    return current_user  # 自动序列化为 UserResponse
```

**请求示例**:
```bash
curl -X GET "http://localhost:8000/api/v1/auth/me" \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
```

**响应**:
```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "email": "user@example.com",
  "username": "testuser",
  "is_active": true,
  "is_superuser": false,
  "created_at": "2025-10-06T10:30:00Z"
}
```

### 7.5 依赖注入的魔法

```python
# deps.py 中的依赖
async def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=403, detail="账号已被禁用")
    return current_user

# auth.py 中使用
@router.get("/me")
async def get_current_user_info(
    current_user: User = Depends(get_current_active_user)
    # ↑ FastAPI 自动:
    # 1. 从 Header 提取 token
    # 2. 调用 get_current_user() 解析 token
    # 3. 调用 get_current_active_user() 验证状态
    # 4. 注入 current_user 参数
):
    return current_user
```

**依赖链**:
```
get_current_active_user
    ↓ 依赖
get_current_user
    ↓ 依赖
decode_access_token
    ↓ 依赖
get_db
```

---

## 📚 总结

### 核心概念

1. **路由系统**: URL → 处理函数的映射,实现关注点分离
2. **三层架构**: endpoints (业务) → api (聚合) → main (入口)
3. **APIRouter**: 模块化路由,支持嵌套和公共配置
4. **请求流程**: 路由匹配 → 验证 → 依赖注入 → 业务逻辑 → 序列化
5. **状态码**: 2xx成功、4xx客户端错误、5xx服务器错误
6. **RESTful**: 资源导向,URL用名词,HTTP方法表达操作

### 设计原则

- ✅ **单一职责**: 每个路由函数只做一件事
- ✅ **职责分离**: 路由 vs 数据验证 vs 业务逻辑 vs 数据库操作
- ✅ **声明式**: 用装饰器和类型注解描述 API,框架自动处理细节
- ✅ **依赖注入**: 数据库连接、认证等通过 Depends 自动注入
- ✅ **自动化**: 数据验证、序列化、文档生成全自动

### 下一步

- [ ] 创建 `app/api/v1/endpoints/auth.py` 实现认证路由
- [ ] 创建 `app/api/v1/api.py` 聚合路由
- [ ] 更新 `app/main.py` 注册 API 路由
- [ ] 编写端到端测试验证完整流程

---

**💡 记住**: FastAPI 的魔法在于**声明式编程** - 你只需描述"是什么",框架自动处理"怎么做"!
