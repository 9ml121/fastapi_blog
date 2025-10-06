# FastAPI 依赖注入与认证依赖详解

## 📚 学习目标

通过本文档，你将掌握：

1. ✅ 理解依赖注入（DI）设计模式的核心概念
2. ✅ 掌握 FastAPI 的 `Depends` 机制和工作原理
3. ✅ 学会设计多层认证依赖（链式依赖）
4. ✅ 理解 OAuth2PasswordBearer 和 token 提取
5. ✅ 掌握认证系统的最佳实践和安全设计

---

## 1️⃣ 依赖注入基础

### 什么是依赖注入？

**依赖注入（Dependency Injection, DI）** 是一种设计模式，核心思想：

> **不在函数内部创建依赖对象，而是从外部传入**

#### 传统方式 vs 依赖注入

```python
# ❌ 传统方式：函数内部硬编码依赖
def get_user_posts(user_id: int):
    db = create_database_connection()  # 紧耦合
    logger = create_logger()           # 难以测试
    cache = create_cache_client()      # 无法替换

    user = db.query(User).filter(User.id == user_id).first()
    logger.info(f"Fetching posts for user {user_id}")
    return user.posts


# ✅ 依赖注入：依赖从外部传入
def get_user_posts(
    user_id: int,
    db: Session,        # 注入数据库
    logger: Logger,     # 注入日志
    cache: Cache        # 注入缓存
):
    user = db.query(User).filter(User.id == user_id).first()
    logger.info(f"Fetching posts for user {user_id}")
    return user.posts
```

### 依赖注入的优势

| 优势 | 说明 | 示例 |
|------|------|------|
| **可测试性** | 可以注入 mock 对象进行单元测试 | 测试时注入假的数据库 |
| **解耦合** | 函数不依赖具体实现，只依赖接口 | 可以切换 PostgreSQL → MySQL |
| **可配置** | 根据环境注入不同依赖 | 开发环境用 SQLite，生产用 PostgreSQL |
| **复用性** | 依赖可以在多处复用 | 同一个 `get_db()` 用于所有路由 |

### 控制反转（IoC）

依赖注入是**控制反转（Inversion of Control, IoC）** 的一种实现：

```python
# ❌ 传统方式：函数控制依赖的创建
def process_order(order_id: int):
    payment_service = PaymentService()  # 函数控制
    payment_service.process(order_id)


# ✅ 依赖注入：外部控制依赖的创建
def process_order(order_id: int, payment_service: PaymentService):
    payment_service.process(order_id)

# 调用方控制使用哪个支付服务
process_order(123, StripePaymentService())    # Stripe
process_order(456, AlipayPaymentService())    # Alipay
```

**控制权转移**：从函数内部 → 外部调用者

---

## 2️⃣ FastAPI 的 Depends 机制

### 基础用法

FastAPI 提供了 **自动依赖注入** 功能：

```python
from fastapi import Depends, FastAPI
from sqlalchemy.orm import Session

app = FastAPI()

# 1. 定义依赖函数
def get_db():
    db = SessionLocal()
    try:
        yield db  # 返回数据库会话
    finally:
        db.close()  # 请求结束后自动关闭


# 2. 在路由中使用依赖
@app.get("/users/{user_id}")
def read_user(user_id: int, db: Session = Depends(get_db)):
    # FastAPI 自动调用 get_db()，将结果注入到 db 参数
    user = db.query(User).filter(User.id == user_id).first()
    return user
```

### 工作原理

**执行流程**：

```
1. 请求到达 → 2. FastAPI 检查参数 → 3. 发现 Depends(get_db)
                                          ↓
6. 响应返回 ← 5. 执行 finally ← 4. 执行 try/yield
```

**关键特性**：

1. **自动执行**：FastAPI 自动调用依赖函数
2. **参数注入**：将返回值注入到路由函数参数
3. **资源清理**：`finally` 块确保资源释放（如数据库连接）

### yield 语句的作用

```python
def get_db():
    db = SessionLocal()
    try:
        yield db           # ← 这里暂停，返回 db 给路由函数
        # 路由函数执行...
        # 路由函数返回后，继续执行
    finally:
        db.close()         # ← 确保关闭数据库连接
```

**yield 的优势**：
- **资源管理**：类似上下文管理器（`with` 语句）
- **异常安全**：即使路由函数抛出异常，`finally` 也会执行
- **代码简洁**：不需要手动 `try-finally`

---

## 3️⃣ 链式依赖（依赖的依赖）

### 什么是链式依赖？

依赖函数本身也可以有依赖：

```python
# 依赖 1：数据库会话
def get_db() -> Session:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 依赖 2：当前用户（依赖 get_db）
def get_current_user(db: Session = Depends(get_db)) -> User:
    # 这里可以使用 db 查询用户
    token = "..."  # 从请求中提取 token
    user = db.query(User).filter(...).first()
    return user


# 依赖 3：活跃用户（依赖 get_current_user）
def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    if not current_user.is_active:
        raise HTTPException(status_code=400, detail="Inactive user")
    return current_user


# 路由：使用最终依赖
@app.get("/me")
def read_current_user(current_user: User = Depends(get_current_active_user)):
    return current_user
```

### 执行顺序

```
HTTP 请求
  ↓
1. get_db() 执行 → 返回 db
  ↓
2. get_current_user(db) 执行 → 返回 user
  ↓
3. get_current_active_user(user) 执行 → 验证并返回 user
  ↓
4. read_current_user(user) 执行 → 返回响应
  ↓
5. 依次执行所有 finally 块（资源清理）
```

### 依赖缓存

**重要特性**：同一个请求中，相同的依赖只执行一次！

```python
# 路由函数
def some_route(
    db1: Session = Depends(get_db),
    db2: Session = Depends(get_db),
):
    assert db1 is db2  # True！是同一个实例
    # get_db() 只执行了一次，结果被缓存并复用
```

**好处**：
- 性能优化（避免重复创建）
- 一致性保证（同一请求用同一个数据库会话）

---

## 4️⃣ 认证依赖设计

### OAuth2 密码流程

FastAPI 提供了 `OAuth2PasswordBearer` 来提取 token：

```python
from fastapi.security import OAuth2PasswordBearer

# 定义 OAuth2 scheme
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")

# 使用方式
def get_current_user(token: str = Depends(oauth2_scheme)):
    # token 自动从 Authorization header 中提取
    # 格式：Authorization: Bearer <token>
    ...
```

### OAuth2PasswordBearer 工作原理

```python
class OAuth2PasswordBearer:
    def __init__(self, tokenUrl: str):
        self.tokenUrl = tokenUrl  # 登录 URL（用于 Swagger 文档）

    def __call__(self, request: Request):
        # 从请求头提取 token
        authorization = request.headers.get("Authorization")
        if not authorization:
            raise HTTPException(401, "Not authenticated")

        # 解析 "Bearer <token>" 格式
        scheme, _, token = authorization.partition(" ")
        if scheme.lower() != "bearer":
            raise HTTPException(401, "Invalid authentication scheme")

        return token  # 返回纯 token 字符串
```

**关键点**：
1. **自动提取 token**：从 `Authorization: Bearer <token>` 中提取
2. **自动报错**：如果没有 token 或格式错误，自动返回 401
3. **Swagger 集成**：`tokenUrl` 用于生成 API 文档的"登录"按钮

### 认证依赖的四层设计

我们的认证系统采用**四层依赖设计**：

```python
# 第 0 层：数据库依赖（基础设施）
def get_db() -> Session:
    """获取数据库会话"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# 第 1 层：Token 提取
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="api/v1/auth/login")


# 第 2 层：用户认证（任何状态的用户）
def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """从 token 解码并获取用户"""
    # 1. 解码 token
    payload = decode_access_token(token)
    if not payload:
        raise HTTPException(401, "Invalid token")

    # 2. 从 payload 提取用户 ID
    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(401, "Invalid token payload")

    # 3. 从数据库查询用户
    user = crud.user.get_user_by_id(db, user_id=UUID(user_id))
    if not user:
        raise HTTPException(401, "User not found")

    return user


# 第 3 层：活跃用户验证（业务逻辑）
def get_current_active_user(
    current_user: User = Depends(get_current_user)
) -> User:
    """验证用户是否活跃"""
    if not current_user.is_active:
        raise HTTPException(400, "Inactive user")
    return current_user


# 第 4 层：管理员权限验证（权限控制）
def get_current_superuser(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """验证用户是否为管理员"""
    if not current_user.is_superuser:
        raise HTTPException(403, "Not enough permissions")
    return current_user
```

### 为什么需要分层？

| 层级 | 依赖函数 | 职责 | 适用场景 |
|------|---------|------|---------|
| 0 | `get_db` | 提供数据库会话 | 所有需要数据库的操作 |
| 1 | `oauth2_scheme` | 提取 token | - |
| 2 | `get_current_user` | 解码 token，查询用户 | 查看个人信息（允许禁用用户） |
| 3 | `get_current_active_user` | 验证用户活跃状态 | 普通业务（发文章、评论） |
| 4 | `get_current_superuser` | 验证管理员权限 | 管理后台（删除用户、审核） |

**设计原则**：
1. **单一职责**：每层只负责一个验证步骤
2. **最小权限**：接口只使用必要的依赖（不滥用 `get_current_superuser`）
3. **易于测试**：可以单独测试每一层

---

## 5️⃣ 实战示例

### 不同权限的 API 端点

```python
# 公开接口：无需认证
@app.get("/posts")
def list_posts(db: Session = Depends(get_db)):
    """任何人都可以查看文章列表"""
    posts = db.query(Post).all()
    return posts


# 需要登录：普通用户
@app.get("/me")
def read_current_user(current_user: User = Depends(get_current_active_user)):
    """查看个人信息（需要登录且账户活跃）"""
    return current_user


# 需要登录：创建资源
@app.post("/posts")
def create_post(
    post_in: PostCreate,
    current_user: User = Depends(get_current_active_user),
    db: Session = Depends(get_db)
):
    """发表文章（需要登录且账户活跃）"""
    post = crud.post.create_post(db, post_in, author_id=current_user.id)
    return post


# 需要管理员：危险操作
@app.delete("/users/{user_id}")
def delete_user(
    user_id: UUID,
    current_user: User = Depends(get_current_superuser),
    db: Session = Depends(get_db)
):
    """删除用户（需要管理员权限）"""
    crud.user.delete_user(db, user_id=user_id)
    return {"message": "User deleted"}
```

### 错误处理

依赖中抛出的 `HTTPException` 会自动转换为 HTTP 响应：

```python
def get_current_user(...):
    if not payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},  # OAuth2 标准
        )
```

**HTTP 响应**：
```json
// Status: 401 Unauthorized
{
  "detail": "Could not validate credentials"
}

// Headers:
WWW-Authenticate: Bearer
```

---

## 6️⃣ 高级技巧

### 1. 类依赖

使用类来组织复杂的依赖逻辑：

```python
class Pagination:
    def __init__(self, skip: int = 0, limit: int = 10):
        self.skip = skip
        self.limit = limit

@app.get("/users")
def list_users(
    pagination: Pagination = Depends(),
    db: Session = Depends(get_db)
):
    users = db.query(User).offset(pagination.skip).limit(pagination.limit).all()
    return users

# 请求：GET /users?skip=10&limit=20
# FastAPI 自动从查询参数创建 Pagination(skip=10, limit=20)
```

### 2. 全局依赖

为所有路由应用依赖：

```python
app = FastAPI(dependencies=[Depends(verify_api_key)])

# 所有路由都会先执行 verify_api_key
```

### 3. 依赖覆盖（测试专用）

测试时替换依赖：

```python
# 测试代码
def override_get_db():
    return fake_db

app.dependency_overrides[get_db] = override_get_db

# 现在所有使用 get_db 的路由都会使用 fake_db
```

### 4. 子依赖（Sub-dependencies）

依赖可以无限嵌套：

```python
def verify_token(token: str = Depends(oauth2_scheme)):
    return decode_token(token)

def verify_user(payload: dict = Depends(verify_token), db: Session = Depends(get_db)):
    return get_user_from_db(payload, db)

def verify_permissions(user: User = Depends(verify_user)):
    if not user.has_permission:
        raise HTTPException(403)
    return user
```

---

## 7️⃣ 安全最佳实践

### 1. 最小权限原则

```python
# ✅ 正确：普通接口用 get_current_active_user
@app.post("/posts")
def create_post(current_user: User = Depends(get_current_active_user)):
    ...

# ❌ 错误：普通接口不应该要求管理员权限
@app.post("/posts")
def create_post(current_user: User = Depends(get_current_superuser)):
    ...  # 这样普通用户无法发文章！
```

### 2. 明确的错误信息

```python
# ✅ 正确：区分不同的认证错误
if not token:
    raise HTTPException(401, "Missing authentication token")
if not user:
    raise HTTPException(401, "User not found")
if not user.is_active:
    raise HTTPException(400, "User account is disabled")

# ❌ 错误：所有错误用同一个消息（难以调试）
if any_error:
    raise HTTPException(401, "Authentication failed")
```

### 3. Token 过期处理

```python
def get_current_user(token: str = Depends(oauth2_scheme)):
    payload = decode_access_token(token)
    if not payload:
        # decode_access_token 已经检查了过期
        raise HTTPException(
            401,
            detail="Token expired or invalid",
            headers={"WWW-Authenticate": "Bearer"}
        )
    ...
```

### 4. 防止信息泄露

```python
# ✅ 正确：不泄露用户是否存在
if not user or not verify_password(password, user.password_hash):
    raise HTTPException(401, "Incorrect username or password")

# ❌ 错误：泄露用户存在性
if not user:
    raise HTTPException(401, "User does not exist")  # 攻击者可枚举用户名
if not verify_password(password, user.password_hash):
    raise HTTPException(401, "Incorrect password")
```

---

## 8️⃣ 常见问题

### Q1: 为什么用 `yield` 而不是 `return`？

**A:** `yield` 支持资源清理：

```python
# ✅ 使用 yield：确保数据库连接关闭
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()  # 无论是否异常，都会执行

# ❌ 使用 return：无法清理资源
def get_db():
    db = SessionLocal()
    return db
    # 数据库连接永远不会关闭！
```

### Q2: 依赖缓存会导致问题吗？

**A:** 只在同一请求内缓存，不同请求是独立的：

```python
# 请求 1：
#   get_db() 执行 → db1
#   get_current_user(db1) → user1
#   some_route(db1, user1)

# 请求 2：
#   get_db() 再次执行 → db2（新的实例）
#   get_current_user(db2) → user2
#   some_route(db2, user2)
```

### Q3: 依赖执行顺序如何确定？

**A:** 按依赖关系的**拓扑排序**执行：

```python
def route(
    a: int = Depends(dep_a),  # dep_a 依赖 dep_c
    b: int = Depends(dep_b),  # dep_b 依赖 dep_c
    c: int = Depends(dep_c),  # dep_c 无依赖
):
    ...

# 执行顺序：dep_c → dep_a → dep_b → route
# （dep_c 被缓存，只执行一次）
```

### Q4: 如何测试依赖注入的代码？

**A:** 使用 `app.dependency_overrides`：

```python
# 生产代码
def get_db():
    return real_database

@app.get("/users")
def get_users(db: Session = Depends(get_db)):
    return db.query(User).all()


# 测试代码
def test_get_users():
    def fake_get_db():
        return fake_database

    app.dependency_overrides[get_db] = fake_get_db

    response = client.get("/users")
    assert response.status_code == 200
```

---

## 9️⃣ 总结

### 核心要点

1. **依赖注入本质**：控制反转 + 参数传递
2. **FastAPI Depends**：自动执行依赖函数，注入结果
3. **链式依赖**：依赖的依赖，形成责任链
4. **认证分层**：token 提取 → 用户认证 → 状态验证 → 权限验证
5. **资源管理**：`yield` 确保清理，类似上下文管理器

### 设计模式对应

| 设计模式 | 在依赖注入中的体现 |
|---------|-------------------|
| **工厂模式** | 依赖函数返回对象实例 |
| **策略模式** | 可以注入不同的实现 |
| **装饰器模式** | 依赖层层包装，增强功能 |
| **责任链模式** | 链式依赖，逐层验证 |
| **单例模式** | 依赖缓存（请求级单例） |

### 认证依赖架构图

```
┌─────────────────┐
│   HTTP 请求     │
└────────┬────────┘
         │
         ▼
┌─────────────────────────┐
│  OAuth2PasswordBearer   │  ← 提取 token
│  (从 Authorization 提取) │
└────────┬────────────────┘
         │
         ▼
┌─────────────────────────┐
│   get_current_user      │  ← 解码 token，查询用户
│   (任何状态的用户)       │
└────────┬────────────────┘
         │
         ▼
┌──────────────────────────┐
│ get_current_active_user  │  ← 验证 is_active
│ (活跃用户)                │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│  get_current_superuser   │  ← 验证 is_superuser
│  (管理员)                 │
└────────┬─────────────────┘
         │
         ▼
┌─────────────────────────┐
│     路由函数             │
│  (处理业务逻辑)          │
└─────────────────────────┘
```

### 下一步

学习完依赖注入原理后，我们将：

1. ✅ 创建 `app/api/deps.py` 文件
2. ✅ 实现四层认证依赖函数
3. ✅ 编写完整的依赖测试套件
4. ✅ 将依赖应用到 API 路由中

---

## 📚 扩展阅读

1. [FastAPI 依赖注入官方文档](https://fastapi.tiangolo.com/tutorial/dependencies/)
2. [OAuth2 密码流程](https://oauth.net/2/grant-types/password/)
3. [依赖注入模式详解](https://martinfowler.com/articles/injection.html)
4. [Python 上下文管理器](https://docs.python.org/3/reference/datamodel.html#context-managers)

---

**🎓 学习检验**

你可以自问：
1. 依赖注入解决了什么问题？
2. FastAPI 的 `Depends()` 是如何工作的？
3. 为什么需要 `yield` 而不是 `return`？
4. 认证依赖为什么要分成多层？
5. 如何测试使用依赖注入的代码？

如果都能回答，说明你已经掌握了依赖注入的核心概念！🚀
