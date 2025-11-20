# Phase 5 - API 完善与前端准备 - 代码讲解

> **文档用途**：记录 Phase 5 的核心代码设计思路和实现要点  
> **更新策略**：每完成一个模块，增量补充代码讲解  
> **创建时间**：2025-01-15

---

## Phase 5.2 - 基础设施

### 1. 自定义异常类设计（app/core/exceptions.py）

#### 1.1 设计目标

统一异常处理，实现：
- ✅ 统一错误响应格式（error + code + message + details）
- ✅ 语义化异常类名（提高代码可读性）
- ✅ 类型安全（编译时检查）
- ✅ 前端国际化支持（通过错误码）

#### 1.2 基类设计（AppError）

```python
class AppError(Exception):
    """应用异常基类"""
    
    def __init__(
        self,
        code: str,              # 错误码（前端国际化用）
        message: str,           # 用户友好的提示信息
        status_code: int = 400, # HTTP 状态码
        details: dict | None = None  # 可选的调试信息
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)
```

**设计要点**：

1. **code 字段的价值**：
   ```typescript
   // 前端国际化示例
   const ERROR_MESSAGES = {
     'zh-CN': { 'EMAIL_ALREADY_EXISTS': '该邮箱已被注册' },
     'en-US': { 'EMAIL_ALREADY_EXISTS': 'Email already exists' }
   }
   
   const errorCode = response.data.error.code
   const message = ERROR_MESSAGES[currentLanguage][errorCode]
   showError(message)
   ```

2. **message 字段的用途**：
   - 提供默认中文提示（方便开发调试）
   - 如果前端没有国际化配置，可直接展示

3. **details 字段的作用**：
   - 提供额外的调试信息（如字段名、错误值）
   - 生产环境可选择性隐藏敏感信息

---

#### 1.3 具体异常类设计模式

**模式 1：资源冲突类异常（固定错误码 + 动态 details）**

```python
class EmailAlreadyExistsError(AppError):
    """邮箱已存在异常"""
    
    def __init__(self, email: str):
        super().__init__(
            code="EMAIL_ALREADY_EXISTS",  # 固定错误码
            message="邮箱已被注册",         # 固定中文提示
            status_code=409,               # 409 Conflict
            details={"field": "email", "value": email}  # 动态信息
        )
```

**使用对比**：

```python
# ❌ 使用前（HTTPException）
if existing_user:
    raise HTTPException(status_code=409, detail="邮箱已被注册")

# 问题：
# 1. 没有错误码，前端无法国际化
# 2. detail 是字符串，格式不统一
# 3. 状态码分散在各处，不易维护

# ✅ 使用后（自定义异常）
if existing_user:
    raise EmailAlreadyExistsError(email=user_data.email)

# 优势：
# 1. 语义化：一看类名就知道什么错误
# 2. 类型安全：email 参数必须传入（编译时检查）
# 3. 格式统一：自动包含 code + details
# 4. 维护性：错误码集中在异常类中
```

**响应格式**：
```json
{
  "error": {
    "code": "EMAIL_ALREADY_EXISTS",
    "message": "邮箱已被注册",
    "details": {
      "field": "email",
      "value": "test@example.com"
    }
  }
}
```

---

**模式 2：可定制消息的异常（灵活提示）**

```python
class PermissionDeniedError(AppError):
    """权限不足异常"""
    
    def __init__(self, message: str = "权限不足"):  # 允许自定义消息
        super().__init__(
            code="PERMISSION_DENIED",
            message=message,
            status_code=403,
        )
```

**使用场景**：

```python
# 场景1：通用权限不足
if not current_user.is_superuser:
    raise PermissionDeniedError()  # 使用默认消息 "权限不足"

# 场景2：特定场景的详细提示
if post.author_id != current_user.id:
    raise PermissionDeniedError("只能删除自己的文章")

# 场景3：多级权限检查
if not current_user.has_permission("edit_post"):
    raise PermissionDeniedError("您没有编辑文章的权限，请联系管理员")
```

**设计权衡**：
- ✅ 灵活性：不同场景可以有不同提示
- ✅ 一致性：错误码始终是 `PERMISSION_DENIED`
- ⚠️ 注意：过多的自定义消息可能影响前端国际化（建议只在必要时使用）

---

#### 1.4 异常分类体系

```python
# ============ 认证相关异常（401 Unauthorized）============

InvalidCredentialsError    # 登录失败：用户名或密码错误
InvalidPasswordError       # 修改密码失败：旧密码错误
UnauthorizedError         # 未登录：需要认证但未提供 Token

# ============ 授权相关异常（403 Forbidden）============

PermissionDeniedError     # 权限不足：已登录但无权限执行操作

# ============ 资源相关异常（404/409）============

ResourceNotFoundError          # 资源不存在（404 Not Found）
EmailAlreadyExistsError       # 邮箱冲突（409 Conflict）
UsernameAlreadyExistsError    # 用户名冲突（409 Conflict）
ResourceConflictError         # 通用冲突（409 Conflict）
```

**分类原则**：

1. **按 HTTP 状态码分类**：
   - 401：认证失败（未登录、Token 无效、密码错误）
   - 403：授权失败（已登录但权限不足）
   - 404：资源不存在
   - 409：资源冲突（重复、状态冲突）

2. **按业务场景分类**：
   - 认证：用户登录、密码验证
   - 授权：权限检查
   - 资源：CRUD 操作中的各种错误

3. **通用异常 vs 特定异常**：
   ```python
   # 特定异常：语义明确，推荐使用
   raise EmailAlreadyExistsError(email="test@example.com")
   
   # 通用异常：适用于无法预知的冲突场景
   raise ResourceConflictError("您已经点赞过这篇文章")
   ```

---

#### 1.5 安全考虑

**1. 防止信息泄露**

```python
class InvalidCredentialsError(AppError):
    """认证失败异常
    
    安全考虑：
    - 统一错误信息"用户名或密码错误"
    - 不泄露"用户不存在"或"密码错误"的具体原因
    - 防止用户名枚举攻击
    """
    
    def __init__(self):
        super().__init__(
            code="INVALID_CREDENTIALS",
            message="用户名或密码错误",  # 统一提示
            status_code=401,
        )
```

**为什么不能区分"用户不存在"和"密码错误"？**

```python
# ❌ 不安全的实现
if not user:
    raise HTTPException(status_code=404, detail="用户不存在")
if not verify_password(password, user.password_hash):
    raise HTTPException(status_code=401, detail="密码错误")

# 攻击者可以枚举用户名：
# → 尝试登录 "admin" → 返回"密码错误" → 用户存在！
# → 尝试登录 "test123" → 返回"用户不存在" → 用户不存在

# ✅ 安全的实现
if not user or not verify_password(password, user.password_hash):
    raise InvalidCredentialsError()  # 统一返回"用户名或密码错误"
```

---

**2. 敏感信息过滤**

```python
class EmailAlreadyExistsError(AppError):
    def __init__(self, email: str):
        super().__init__(
            code="EMAIL_ALREADY_EXISTS",
            message="邮箱已被注册",
            status_code=409,
            details={"field": "email", "value": email}  # 包含邮箱值
        )

# 生产环境考虑：
# → 如果 email 是敏感信息（如内部邮箱），考虑脱敏
# → details={"field": "email", "value": "t***@example.com"}
```

---

#### 1.6 代码质量要点

**1. 类型注解**

```python
# ✅ 完整的类型注解
def __init__(self, email: str):
    super().__init__(
        code="EMAIL_ALREADY_EXISTS",
        message="邮箱已被注册",
        status_code=409,
        details={"field": "email", "value": email}
    )

# mypy 可以检查：
raise EmailAlreadyExistsError(email=123)  # 类型错误！
```

**2. 文档字符串**

```python
class EmailAlreadyExistsError(AppError):
    """邮箱已存在异常

    使用场景：用户注册或更新邮箱时，邮箱已被其他用户占用

    Example:
        >>> if existing_user:
        >>>     raise EmailAlreadyExistsError(email="test@example.com")
    """
```

**3. 命名规范**

```python
# ✅ 遵循 PEP-8 和 ruff 规范
class AppError(Exception):  # 异常类以 Error 结尾
    pass

# ❌ ruff 会报错
class AppException(Exception):  # N818: Exception name should end with Error
    pass
```

---

### ★ Insight ─────────────────────────────────────

**1. 异常类设计的本质**

异常类不只是抛出错误，更是**业务逻辑的一部分**。通过语义化的异常类名（如 `EmailAlreadyExistsError`），代码的可读性大幅提升：

```python
# ❌ 难以理解
raise HTTPException(status_code=409, detail="邮箱已被注册")

# ✅ 一目了然
raise EmailAlreadyExistsError(email=user_data.email)
```

---

**2. 错误码的价值**

`code` 字段是前后端的"契约"：
- 前端通过 `code` 做国际化，不依赖中文 `message`
- 前端通过 `code` 做逻辑判断（如特定错误显示特殊 UI）
- 后端修改中文提示，不影响前端逻辑

```typescript
// 前端根据错误码处理不同逻辑
switch (error.code) {
  case 'EMAIL_ALREADY_EXISTS':
    showEmailConflictDialog()  // 显示"找回密码"对话框
    break
  case 'INVALID_CREDENTIALS':
    incrementFailedLoginCount()  // 累计登录失败次数
    break
}
```

---

**3. 类型安全的力量**

使用自定义异常类，TypeScript 前端和 Python 后端都能在编译时检查错误处理逻辑：

```python
# Python 后端：mypy 检查
raise EmailAlreadyExistsError(email=123)  # 类型错误！

# TypeScript 前端：
interface ErrorResponse {
  error: {
    code: 'EMAIL_ALREADY_EXISTS' | 'INVALID_CREDENTIALS' | ...
    message: string
    details?: Record<string, any>
  }
}

// 编译时检查错误码是否正确
if (error.code === 'EMAIL_EXIST') {  // 拼写错误，编译失败！
  // ...
}
```

─────────────────────────────────────────────────

---

---

### 2. CORS 中间件配置（app/main.py）

#### 2.1 什么是 CORS？

**CORS（Cross-Origin Resource Sharing，跨域资源共享）** 是浏览器的安全机制，用于控制跨域请求。

**同源的定义**：

| 组成部分 | 说明 | 示例 |
|---------|-----|------|
| 协议 | http vs https | `http://` 和 `https://` = 不同源 |
| 域名 | 完整域名 | `example.com` 和 `api.example.com` = 不同源 |
| 端口 | 端口号 | `:3000` 和 `:8000` = 不同源 |

**判断示例**：

```javascript
// 前端运行在：http://localhost:3000

// ❌ 跨域（端口不同）
fetch('http://localhost:8000/api/users')  // 浏览器拦截！

// ❌ 跨域（域名不同）
fetch('http://127.0.0.1:3000/api/users')  // 也算跨域！

// ✅ 同源
fetch('http://localhost:3000/api/users')
```

---

#### 2.2 FastAPI CORS 配置

```python
from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React/Vue 开发服务器
        "http://localhost:5173",  # Vite 开发服务器
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        # 生产环境添加实际域名
    ],
    allow_credentials=True,  # 允许携带 Cookie 和 Authorization 头
    allow_methods=["*"],     # 允许所有 HTTP 方法
    allow_headers=["*"],     # 允许所有请求头
)
```

**配置参数详解**：

| 参数 | 说明 | 推荐值 | ⚠️ 安全注意 |
|-----|------|-------|-----------|
| `allow_origins` | 允许的前端域名列表 | 明确列举域名 | **生产环境禁用 `["*"]`！** |
| `allow_credentials` | 是否允许携带凭据 | `True` | 如果为 True，`allow_origins` 不能是 `["*"]` |
| `allow_methods` | 允许的 HTTP 方法 | `["*"]` 或 `["GET", "POST", ...]` | 一般允许全部即可 |
| `allow_headers` | 允许的请求头 | `["*"]` 或 `["Authorization", ...]` | 建议允许全部 |

---

#### 2.3 CORS 工作流程

**简单请求**（GET、POST，不带自定义头）：

```http
# 1. 浏览器发送请求，自动添加 Origin 头
GET /api/users HTTP/1.1
Host: localhost:8000
Origin: http://localhost:3000

# 2. 服务器检查 Origin，决定是否允许
HTTP/1.1 200 OK
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Credentials: true

# 3. 浏览器检查响应头：
#    - 如果有 Access-Control-Allow-Origin → 允许
#    - 如果没有 → 拦截并报错
```

**预检请求**（PUT、DELETE、带 Authorization 头）：

```http
# 1. 浏览器先发送 OPTIONS 预检请求
OPTIONS /api/users/me HTTP/1.1
Origin: http://localhost:3000
Access-Control-Request-Method: PATCH
Access-Control-Request-Headers: Authorization

# 2. 服务器返回允许的方法和头
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, PATCH, DELETE
Access-Control-Allow-Headers: Authorization, Content-Type
Access-Control-Max-Age: 86400  # 缓存 24 小时

# 3. 浏览器检查通过后，才发送真正的请求
PATCH /api/users/me HTTP/1.1
Authorization: Bearer <token>
```

**FastAPI CORSMiddleware 自动处理**：
- ✅ 自动响应 OPTIONS 预检请求
- ✅ 自动添加 CORS 响应头
- ✅ 无需手动处理

---

#### 2.4 安全风险警告

```python
# ❌ 危险配置（生产环境绝对禁止）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],              # 允许任何网站访问！
    allow_credentials=True,           # 还允许携带凭据！
)

# 风险：
# → 任何恶意网站都能调用你的 API
# → 可能导致 CSRF 攻击
# → 用户数据泄露

# ✅ 安全配置
allow_origins=[
    "https://yourdomain.com",      # 只允许自己的域名
]
```

**生产环境最佳实践**：

```python
# 方案 1：环境变量配置（推荐）
import os

CORS_ORIGINS = os.getenv("CORS_ORIGINS", "").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,  # 从环境变量读取
    allow_credentials=True,
)

# 方案 2：根据环境区分
if os.getenv("ENV") == "development":
    allow_origins = ["http://localhost:3000", "http://localhost:5173"]
else:  # production
    allow_origins = ["https://yourdomain.com"]
```

---

### 3. 全局异常处理器（app/main.py）

#### 3.1 异常处理器的作用

统一捕获和处理各种异常，返回标准格式的 JSON 响应。

**处理器优先级**：
1. 最具体的异常（`AppError`、`RequestValidationError`、`HTTPException`）
2. 特定异常（`IntegrityError`）
3. 兜底处理器（`Exception`）

**为什么需要 HTTPException 处理器？**

FastAPI 中某些内置功能会抛出 `HTTPException`，而不是我们的自定义异常：
- `OAuth2PasswordBearer`：Token 格式错误或缺失
- 权限检查：用户权限不足
- 其他使用 `HTTPException` 的地方

由于 `HTTPException` 不被 `global_exception_handler` 捕获（它有特定的处理顺序），需要专门的处理器来统一格式。

---

#### 3.2 处理器实现详解

**处理器 1：自定义异常处理器**

```python
@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """处理应用自定义异常

    将自定义异常统一转换为标准 JSON 响应格式
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details,
            }
        },
    )
```

**触发场景**：

```python
# 任何地方抛出自定义异常
raise EmailAlreadyExistsError(email="test@example.com")

# 自动转换为统一格式响应
{
  "error": {
    "code": "EMAIL_ALREADY_EXISTS",
    "message": "邮箱已被注册",
    "details": {"field": "email", "value": "test@example.com"}
  }
}
```

---

**处理器 2：Pydantic 验证错误处理器**

```python
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """处理 Pydantic 验证错误（422）
    
    当请求数据不符合 Pydantic Schema 定义时触发
    """
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "请求数据格式错误",
                "details": exc.errors(),  # Pydantic 详细错误信息
            }
        },
    )
```

**触发场景**：

```python
# 前端发送错误数据
POST /api/v1/auth/register
{
  "username": "ab",          # 太短（min_length=3）
  "email": "invalid-email",  # 格式错误
  "password": "123"          # 太短（min_length=8）
}

# 返回详细验证错误
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "请求数据格式错误",
    "details": [
      {
        "loc": ["body", "username"],
        "msg": "String should have at least 3 characters",
        "type": "string_too_short"
      },
      {
        "loc": ["body", "email"],
        "msg": "value is not a valid email address",
        "type": "value_error.email"
      },
      ...
    ]
  }
}
```

**前端处理示例**：

```typescript
// 根据 details 高亮错误字段
const errors = response.data.error.details
errors.forEach(err => {
  const fieldName = err.loc[1]  // "username"
  const message = err.msg        // "String should have at least 3 characters"
  showFieldError(fieldName, message)
})
```

---

**处理器 3：HTTPException 处理器**

```python
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """处理 FastAPI HTTPException

    处理 OAuth2 认证错误和其他使用 HTTPException 的地方，
    将它们转换为统一的错误格式。

    重要场景：
    1. OAuth2PasswordBearer：token 缺失或格式错误
    2. 权限检查：用户权限不足
    3. 其他使用 HTTPException 的场景
    """
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "details": None
            }
        },
        headers=getattr(exc, 'headers', None)
    )
```

**触发场景**：

```python
# 场景1：OAuth2PasswordBearer Token 格式错误
Authorization: "invalid_token_string"  # 没有 "Bearer " 前缀
# → HTTPException(status_code=401, detail="Not authenticated")

# 场景2：OAuth2PasswordBearer Token 缺失
# 请求头中没有 Authorization
# → HTTPException(status_code=401, detail="Not authenticated")

# 场景3：权限检查失败
if not current_user.is_superuser:
    raise HTTPException(status_code=403, detail="Not enough permissions")
```

**响应格式**：
```json
{
  "error": {
    "code": "HTTP_ERROR",
    "message": "Not authenticated",
    "details": null
  }
}
```

**为什么需要这个处理器？**

1. **OAuth2PasswordBearer 的特殊性**：
   - `OAuth2PasswordBearer` 是 FastAPI 内置的认证依赖
   - 它会自动抛出 `HTTPException`，不是我们的自定义异常
   - 没有专门的处理器，会返回 FastAPI 默认格式：`{"detail": "Not authenticated"}`

2. **统一错误格式**：
   - 前端期望所有错误都是 `{"error": {"code": "...", "message": "...", "details": "...}}` 格式
   - HTTPException 处理器确保格式一致

3. **兼容性考虑**：
   - 保留 `exc.headers`（如 `WWW-Authenticate` 头）
   - 使用 `getattr(exc, 'headers', None)` 安全获取

---

**处理器 4：数据库完整性错误处理器**

```python
@app.exception_handler(IntegrityError)
async def database_integrity_error_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    """处理数据库完整性约束错误
    
    当违反数据库约束时触发（如唯一键冲突、外键约束）
    """
    # 记录详细错误到日志
    logger.error(
        f"Database integrity error: {exc}",
        exc_info=True,
        extra={
            "url": str(request.url),
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": {
                "code": "DATABASE_INTEGRITY_ERROR",
                "message": "数据冲突，可能违反唯一性约束",
                "details": {"hint": "请检查邮箱或用户名是否已存在"},
            }
        },
    )
```

**为什么需要这个处理器？**

```python
# 理想情况：业务层提前检查
existing_user = crud_user.get_user_by_email(db, email=user_data.email)
if existing_user:
    raise EmailAlreadyExistsError(email=user_data.email)

# 但可能有遗漏的场景，数据库约束是最后一道防线
db.add(new_user)
db.commit()  # 如果邮箱重复，抛出 IntegrityError

# IntegrityError 处理器捕获并返回友好提示
# → 不暴露数据库详细错误（安全）
# → 记录到日志（方便排查）
```

---

**处理器 5：兜底异常处理器**

```python
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底：处理所有未捕获的异常
    
    这是最后一道防线，捕获所有未预期的异常
    """
    # 记录详细错误到日志（包含堆栈跟踪）
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {exc}",
        exc_info=True,  # 包含完整堆栈跟踪
        extra={
            "url": str(request.url),
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "服务器内部错误，请稍后重试",
                # ⚠️ 生产环境不要返回 exc 的详细信息！
            }
        },
    )
```

**为什么不能返回详细错误？**

```python
# ❌ 不安全（暴露敏感信息）
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "服务器内部错误",
    "details": {
      "exception": "psycopg2.OperationalError: FATAL: password authentication failed for user 'postgres'",
      "traceback": "/app/db/session.py:15 in get_db..."
    }
  }
}

# 攻击者获取信息：
# → 数据库类型：PostgreSQL
# → 数据库用户名：postgres
# → 文件路径：/app/db/session.py

# ✅ 安全（通用提示）
{
  "error": {
    "code": "INTERNAL_SERVER_ERROR",
    "message": "服务器内部错误，请稍后重试"
  }
}

# 详细错误记录到日志，只有开发者能看到
```

---

#### 3.3 日志记录最佳实践

```python
# 完整的日志记录示例
logger.error(
    f"Unhandled exception: {type(exc).__name__}: {exc}",
    exc_info=True,  # 包含完整堆栈跟踪
    extra={
        "url": str(request.url),      # 请求 URL
        "method": request.method,     # HTTP 方法
        "user_id": getattr(request.state, "user_id", None),  # 当前用户 ID（如果有）
    },
)

# 日志输出示例：
# ERROR: Unhandled exception: ValueError: invalid literal for int()
#   File: /app/api/v1/endpoints/posts.py:45
#   url: /api/v1/posts/abc
#   method: GET
#   user_id: 550e8400-e29b-41d4-a716-446655440000
#   Traceback (most recent call last):
#     ...
```

**日志的价值**：
- ✅ 问题排查：快速定位错误来源
- ✅ 监控告警：集成到监控系统（如 Sentry）
- ✅ 数据分析：统计错误频率和类型

---

### 4. OpenAPI 元数据优化（app/main.py）

#### 4.1 FastAPI 元数据配置

```python
app = FastAPI(
    title="FastAPI 博客系统 API",
    description="""
    ## 📝 博客系统 API 文档

    这是一个现代化的博客系统后端 API，提供以下功能：

    * **🔐 用户认证** - 注册、登录、JWT Token
    * **👤 用户管理** - 个人资料、密码修改
    ...
    """,
    version="1.0.0",
    contact={
        "name": "开发团队",
        "email": "dev@example.com",
    },
    license_info={
        "name": "MIT License",
        "url": "https://opensource.org/licenses/MIT",
    },
    openapi_tags=[
        {
            "name": "🔐 认证",
            "description": "用户注册、登录、JWT Token 管理",
        },
        {
            "name": "👤 用户管理",
            "description": "个人资料查看、更新、密码修改",
        },
    ],
)
```

**元数据参数说明**：

| 参数 | 用途 | 示例 |
|-----|------|-----|
| `title` | API 标题 | "FastAPI 博客系统 API" |
| `description` | 详细说明（支持 Markdown） | 功能介绍、使用指南 |
| `version` | API 版本 | "1.0.0" |
| `contact` | 联系方式 | 邮箱、GitHub 链接 |
| `license_info` | 许可证信息 | MIT、Apache 2.0 等 |
| `openapi_tags` | 端点分组标签 | 认证、用户、文章、评论 |

---

#### 4.2 description 最佳实践

```python
description="""
## 📝 博客系统 API 文档

这是一个现代化的博客系统后端 API，提供以下功能：

* **🔐 用户认证** - 注册、登录、JWT Token
* **👤 用户管理** - 个人资料、密码修改

### 🔐 认证方式

大部分 API 需要 JWT Token 认证：
1. 调用 `POST /api/v1/auth/login` 获取 access_token
2. 在请求头中添加：`Authorization: Bearer <your_token>`
3. 或点击右上角 🔓 按钮，输入 token

### 📊 通用响应格式

**成功响应**：
\```json
{
  "id": "550e8400-e29b-41d4-a716-446655440000",
  "username": "johndoe",
  ...
}
\```

**错误响应**：
\```json
{
  "error": {
    "code": "EMAIL_ALREADY_EXISTS",
    "message": "邮箱已被注册",
    "details": {...}
  }
}
\```

### 🚀 快速开始

1. 注册账号：`POST /api/v1/auth/register`
2. 登录获取 token：`POST /api/v1/auth/login`
3. 点击右上角 🔓，输入 token
4. 开始测试需要认证的 API！
"""
```

**设计要点**：
- ✅ 使用 Markdown 格式（## 标题、** 加粗、` 代码）
- ✅ 包含快速开始指南（降低上手成本）
- ✅ 说明认证方式（前端对接必须）
- ✅ 提供响应格式示例（统一前后端理解）

---

### ★ Insight ─────────────────────────────────────

**1. CORS 的本质**

CORS 不是后端的限制，而是浏览器的安全机制。后端只是通过响应头告诉浏览器"允许这个跨域请求"。

**关键理解**：
- 浏览器发起跨域请求 → 自动添加 Origin 头
- 后端返回响应 → 包含 Access-Control-Allow-Origin 头
- 浏览器检查响应头 → 决定是否允许前端访问响应

**注意**：curl、Postman 等工具**不会检查 CORS**，因为它们不是浏览器！

---

**2. 异常处理的分层思想**

```
应用层（业务逻辑）
    ↓ 抛出 EmailAlreadyExistsError
异常处理层（全局处理器）
    ↓ 转换为统一 JSON 格式
前端展示层
    ↓ 根据 error.code 显示友好提示
```

**价值**：
- ✅ 业务层只关注业务逻辑，不关心响应格式
- ✅ 异常处理层统一格式，前端无需适配多种格式
- ✅ 前端根据错误码做国际化和逻辑判断

---

**3. API 文档即产品**

优秀的 API 文档能让前端开发者"自助"：
- ✅ 快速开始指南 → 5 分钟上手
- ✅ 认证说明 → 知道如何传 Token
- ✅ 响应格式示例 → 知道如何处理响应
- ✅ 错误码列表 → 知道如何处理错误

**结果**：减少 80% 的前后端沟通成本！

─────────────────────────────────────────────────
