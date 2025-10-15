# Phase 5 - 全局异常处理

> **文档用途**：全局异常处理的理论与实践
> **创建时间**：2025-10-11
> **更新策略**：根据项目实际需求更新异常类型和处理逻辑

---

## 📚 目录

1. [为什么需要统一异常处理](#1-为什么需要统一异常处理)
2. [异常处理设计](#2-异常处理设计)
3. [自定义异常实现](#3-自定义异常实现)
4. [全局异常处理器](#4-全局异常处理器)
5. [安全考虑](#5-安全考虑)
6. [测试策略](#6-测试策略)

---

## 1. 为什么需要统一异常处理？

### 1.1 当前问题

我们的错误响应格式不统一：

```python
# app/api/v1/endpoints/auth.py
raise HTTPException(status_code=409, detail="邮箱已被注册")
# 响应：{"detail": "邮箱已被注册"}

# app/api/v1/endpoints/users.py
raise HTTPException(status_code=409, detail="邮箱已被其他用户占用")
# 响应：{"detail": "邮箱已被其他用户占用"}

# 未捕获的数据库异常
IntegrityError: duplicate key value violates unique constraint
# 响应：500 Internal Server Error
# → 暴露了数据库表结构和约束信息！
```

### 1.2 前端开发者的痛点

```typescript
// 前端要处理多种错误格式
try {
    await api.register(userData);
} catch (error) {
    // 情况1：detail 字段
    if (error.response.data.detail) {
        showError(error.response.data.detail);
    }
    // 情况2：message 字段
    else if (error.response.data.message) {
        showError(error.response.data.message);
    }
    // 情况3：error 字段
    else if (error.response.data.error) {
        showError(error.response.data.error);
    }
    // 😫 还有其他情况吗？
}
```

### 1.3 统一异常处理的价值

1. **提升开发效率**：前端只需要处理一种错误格式
2. **改善用户体验**：错误信息一致且用户友好
3. **增强安全性**：避免暴露内部实现细节
4. **便于国际化**：错误码支持多语言
5. **简化维护**：集中管理所有错误处理逻辑

---

## 2. 异常处理设计

### 2.1 统一错误响应格式

#### 目标格式

```json
{
    "error": {
        "code": "EMAIL_ALREADY_EXISTS", // 错误码（方便前端国际化）
        "message": "邮箱已被注册", // 用户友好的错误信息
        "details": {
            // 可选的详细信息
            "field": "email",
            "value": "test@example.com"
        }
    }
}
```

#### 设计要点

1. **统一字段名**：始终是 `error` 对象
2. **错误码**：`code` 字段用于前端国际化和逻辑判断
3. **用户友好消息**：`message` 字段直接展示给用户
4. **可选详情**：`details` 字段提供调试信息（生产环境可隐藏）

### 2.2 前端国际化示例

```typescript
// 前端国际化配置
const ERROR_MESSAGES = {
    "zh-CN": {
        EMAIL_ALREADY_EXISTS: "该邮箱已被注册",
        INVALID_CREDENTIALS: "用户名或密码错误",
        UNAUTHORIZED: "请先登录",
    },
    "en-US": {
        EMAIL_ALREADY_EXISTS: "Email already exists",
        INVALID_CREDENTIALS: "Invalid username or password",
        UNAUTHORIZED: "Please login first",
    },
};

// 使用错误码获取对应语言的提示
const errorCode = response.data.error.code;
const message = ERROR_MESSAGES[currentLanguage][errorCode];
showError(message);
```

### 2.3 错误码分类

#### 按业务领域分类

```python
# 认证相关
EMAIL_ALREADY_EXISTS = "EMAIL_ALREADY_EXISTS"
USERNAME_ALREADY_EXISTS = "USERNAME_ALREADY_EXISTS"
INVALID_CREDENTIALS = "INVALID_CREDENTIALS"
UNAUTHORIZED = "UNAUTHORIZED"

# 授权相关
PERMISSION_DENIED = "PERMISSION_DENIED"
INSUFFICIENT_PRIVILEGES = "INSUFFICIENT_PRIVILEGES"

# 资源相关
RESOURCE_NOT_FOUND = "RESOURCE_NOT_FOUND"
RESOURCE_CONFLICT = "RESOURCE_CONFLICT"

# 验证相关
VALIDATION_ERROR = "VALIDATION_ERROR"
INVALID_INPUT = "INVALID_INPUT"

# 系统相关
INTERNAL_SERVER_ERROR = "INTERNAL_SERVER_ERROR"
SERVICE_UNAVAILABLE = "SERVICE_UNAVAILABLE"
```

---

## 3. 自定义异常实现

### 3.1 异常基类设计

#### 文件：`app/core/exceptions.py`

```python
"""应用自定义异常"""

class AppError(Exception):
    """应用异常基类

    所有自定义异常都应继承此类，以便被全局异常处理器统一处理。

    Attributes:
        code: 错误码，用于前端国际化和逻辑判断（如 "EMAIL_ALREADY_EXISTS"）
        message: 用户友好的错误信息，可以直接展示给用户
        status_code: HTTP 状态码（400、401、403、404、409、500 等）
        details: 可选的详细信息字典，用于调试或提供额外上下文
    """

    def __init__(
        self,
        code: str,
        message: str,
        status_code: int = 400,
        details: dict | None = None,
    ):
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details
        super().__init__(message)
```

### 3.2 具体业务异常

#### 认证相关异常

```python
# ============ 认证相关异常 ============

class EmailAlreadyExistsError(AppError):
    """邮箱已存在异常

    使用场景：用户注册或更新邮箱时，邮箱已被其他用户占用

    Example:
        >>> if existing_user:
        >>>     raise EmailAlreadyExistsError(email="test@example.com")
    """

    def __init__(self, email: str):
        super().__init__(
            code="EMAIL_ALREADY_EXISTS",
            message="邮箱已被注册",
            status_code=409,
            details={"field": "email", "value": email},
        )


class UsernameAlreadyExistsError(AppError):
    """用户名已存在异常

    使用场景：用户注册时，用户名已被占用

    Example:
        >>> if existing_user:
        >>>     raise UsernameAlreadyExistsError(username="johndoe")
    """

    def __init__(self, username: str):
        super().__init__(
            code="USERNAME_ALREADY_EXISTS",
            message="用户名已被使用",
            status_code=409,
            details={"field": "username", "value": username},
        )


class InvalidCredentialsError(AppError):
    """认证失败异常

    使用场景：用户登录时，用户名或密码错误

    安全考虑：
    - 统一错误信息"用户名或密码错误"，不泄露"用户不存在"或"密码错误"的具体原因
    - 防止用户名枚举攻击

    Example:
        >>> if not user or not verify_password(password, user.password_hash):
        >>>     raise InvalidCredentialsError()
    """

    def __init__(self):
        super().__init__(
            code="INVALID_CREDENTIALS",
            message="用户名或密码错误",
            status_code=401,
        )


class InvalidPasswordError(AppError):
    """密码错误异常

    使用场景：修改密码时，旧密码不正确

    Example:
        >>> if not verify_password(old_password, user.password_hash):
        >>>     raise InvalidPasswordError()
    """

    def __init__(self, message: str = "旧密码错误"):
        super().__init__(
            code="INVALID_PASSWORD",
            message=message,
            status_code=400,
        )
```

#### 授权相关异常

```python
# ============ 授权相关异常 ============

class UnauthorizedError(AppError):
    """未授权异常

    使用场景：用户未登录或 Token 无效

    Example:
        >>> if not current_user:
        >>>     raise UnauthorizedError()
    """

    def __init__(self, message: str = "请先登录"):
        super().__init__(
            code="UNAUTHORIZED",
            message=message,
            status_code=401,
        )


class PermissionDeniedError(AppError):
    """权限不足异常

    使用场景：用户已登录，但没有权限执行操作（如删除他人文章）

    Example:
        >>> if post.author_id != current_user.id and not current_user.is_superuser:
        >>>     raise PermissionDeniedError("只能删除自己的文章")
    """

    def __init__(self, message: str = "权限不足"):
        super().__init__(
            code="PERMISSION_DENIED",
            message=message,
            status_code=403,
        )
```

#### 资源相关异常

```python
# ============ 资源相关异常 ============

class ResourceNotFoundError(AppError):
    """资源不存在异常

    使用场景：查询的资源（用户、文章、评论）不存在

    Example:
        >>> if not post:
        >>>     raise ResourceNotFoundError(resource="文章")
    """

    def __init__(self, resource: str = "资源"):
        super().__init__(
            code="RESOURCE_NOT_FOUND",
            message=f"{resource}不存在",
            status_code=404,
        )


class ResourceConflictError(AppError):
    """资源冲突异常

    使用场景：操作导致资源状态冲突（如重复点赞、重复收藏）

    Example:
        >>> if existing_like:
        >>>     raise ResourceConflictError("您已经点赞过这篇文章")
    """

    def __init__(self, message: str = "资源状态冲突"):
        super().__init__(
            code="RESOURCE_CONFLICT",
            message=message,
            status_code=409,
        )
```

---

## 4. 全局异常处理器

### 4.1 异常处理器实现

#### 文件：`app/main.py`

```python
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from sqlalchemy.exc import IntegrityError
import logging

from app.core.exceptions import AppError

logger = logging.getLogger(__name__)

app = FastAPI()

# ============ 异常处理器 ============

@app.exception_handler(AppError)
async def app_exception_handler(request: Request, exc: AppError):
    """处理应用自定义异常"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": exc.details
            }
        }
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """处理 Pydantic 验证错误（422）"""
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "请求数据格式错误",
                "details": exc.errors()  # Pydantic 详细错误信息
            }
        }
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """处理 OAuth2 认证错误和其他使用 HTTPException 的地方

    处理 OAuth2 认证错误和其他使用 HTTPException 的地方，
    将它们转换为统一的错误格式。

    重要场景：
    1. OAuth2PasswordBearer：token 缺失或格式错误
    2. 权限检查：用户权限不足
    3. 其他使用 HTTPException 的场景

    Args:
        request: FastAPI 请求对象
        exc: HTTPException 实例

    Returns:
        统一格式的 JSON 响应
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


@app.exception_handler(IntegrityError)
async def database_integrity_error_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    """处理数据库完整性约束错误"""
    logger.error(f"Database integrity error: {exc}", exc_info=True)

    return JSONResponse(
        status_code=status.HTTP_409_CONFLICT,
        content={
            "error": {
                "code": "DATABASE_INTEGRITY_ERROR",
                "message": "数据冲突，可能违反唯一性约束",
                # 生产环境不要暴露详细错误
                "details": {"hint": "请检查邮箱或用户名是否已存在"}
            }
        },
    )


@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """兜底：处理所有未捕获的异常

    这是最后一道防线，捕获所有未预期的异常。

    重要：
    - 必须记录到日志，方便排查问题
    - 生产环境不要返回详细的异常信息（安全风险）

    Args:
        request: FastAPI 请求对象
        exc: 任意异常

    Returns:
        统一格式的 JSON 响应
    """
    # 记录详细错误到日志（包含堆栈跟踪）
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {exc}",
        exc_info=True,
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
                # "details": {
                #     "exception": str(exc),
                #     "type": type(exc).__name__
                # }  # 仅开发环境
            }
        },
    )
```

### 4.2 处理器优先级

异常处理器的执行顺序（从高到低）：

1. **最具体的异常**（`AppError`、`RequestValidationError`）
2. **特定异常**（`IntegrityError`、`HTTPException`）
3. **兜底处理器**（`Exception`）

### 4.3 修改现有代码使用新异常

#### 修改前（app/api/v1/endpoints/auth.py）

```python
if existing_user:
    raise HTTPException(status_code=409, detail="邮箱已被注册")
```

#### 修改后

```python
from app.core.exceptions import EmailAlreadyExistsError

if existing_user:
    raise EmailAlreadyExistsError(email=user_data.email)
```

#### 优势对比

| 方面       | HTTPException      | 自定义异常          |
| ---------- | ------------------ | ------------------- |
| 错误码     | ❌ 无              | ✅ 有（前端国际化） |
| 格式统一   | ❌ 需手动保证      | ✅ 自动统一         |
| 类型安全   | ❌ detail 是字符串 | ✅ 编译时检查       |
| 代码可读性 | ❌ 状态码分散      | ✅ 语义化类名       |
| 维护成本   | ❌ 分散在各处      | ✅ 集中管理         |

---

## 5. 安全考虑

### 5.1 生产环境 vs 开发环境

#### 环境配置

```python
# app/core/config.py
class Settings(BaseSettings):
    DEBUG: bool = False  # 生产环境设为 False

# app/main.py
from app.core.config import settings

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    logger.error(f"Unhandled exception: {exc}", exc_info=True)

    error_response = {
        "error": {
            "code": "INTERNAL_SERVER_ERROR",
            "message": "服务器内部错误，请稍后重试",
        }
    }

    # 只在开发环境返回详细错误
    if settings.DEBUG:
        error_response["error"]["details"] = {
            "exception": str(exc),
            "type": type(exc).__name__
        }

    return JSONResponse(
        status_code=500,
        content=error_response
    )
```

### 5.2 敏感信息泄露风险

#### ❌ 危险：暴露数据库结构

```python
IntegrityError: duplicate key value violates unique constraint "users_email_key"
# → 攻击者知道了表名是 "users"，字段名是 "email"
```

#### ✅ 安全：通用提示

```json
{
    "error": {
        "code": "DATABASE_INTEGRITY_ERROR",
        "message": "数据冲突，可能违反唯一性约束"
    }
}
```

### 5.3 日志记录策略

#### 生产环境日志

```python
import logging
import traceback

logger = logging.getLogger(__name__)

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    # 记录详细错误到日志（包含堆栈跟踪）
    logger.error(
        f"Unhandled exception: {type(exc).__name__}: {exc}",
        exc_info=True,
        extra={
            "url": str(request.url),
            "method": request.method,
            "user_agent": request.headers.get("user-agent"),
            "client_ip": request.client.host if request.client else None,
        },
    )

    # 返回通用错误信息给客户端
    return JSONResponse(
        status_code=500,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "服务器内部错误，请稍后重试",
            }
        }
    )
```

---

## 6. 测试策略

### 6.1 单元测试

#### 测试自定义异常类

```python
# tests/test_exceptions.py

import pytest
from app.core.exceptions import (
    EmailAlreadyExistsError,
    InvalidCredentialsError,
    ResourceNotFoundError,
)

class TestCustomExceptions:
    """测试自定义异常类"""

    def test_email_already_exists_error(self):
        """测试邮箱已存在异常"""
        exc = EmailAlreadyExistsError("test@example.com")

        assert exc.code == "EMAIL_ALREADY_EXISTS"
        assert exc.message == "邮箱已被注册"
        assert exc.status_code == 409
        assert exc.details == {"field": "email", "value": "test@example.com"}

    def test_invalid_credentials_error(self):
        """测试认证失败异常"""
        exc = InvalidCredentialsError()

        assert exc.code == "INVALID_CREDENTIALS"
        assert exc.message == "用户名或密码错误"
        assert exc.status_code == 401
        assert exc.details is None

    def test_resource_not_found_error(self):
        """测试资源不存在异常"""
        exc = ResourceNotFoundError("文章")

        assert exc.code == "RESOURCE_NOT_FOUND"
        assert exc.message == "文章不存在"
        assert exc.status_code == 404
```

### 6.2 集成测试

#### 测试异常处理器

```python
# tests/test_exception_handlers.py

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.core.exceptions import EmailAlreadyExistsError

client = TestClient(app)

class TestExceptionHandlers:
    """测试异常处理器"""

    def test_app_exception_handler(self):
        """测试应用异常处理器"""
        # 模拟抛出自定义异常
        with pytest.raises(EmailAlreadyExistsError):
            raise EmailAlreadyExistsError("test@example.com")

        # 在实际 API 中测试
        # 这里需要模拟一个会抛出异常的端点
        response = client.post("/api/v1/auth/register", json={
            "username": "testuser",
            "email": "existing@example.com",  # 假设这个邮箱已存在
            "password": "password123"
        })

        assert response.status_code == 409
        assert response.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"

    def test_validation_exception_handler(self):
        """测试验证异常处理器"""
        response = client.post("/api/v1/auth/register", json={
            "username": "test",
            "email": "invalid-email",  # 无效邮箱格式
            "password": "123"  # 密码太短
        })

        assert response.status_code == 422
        assert response.json()["error"]["code"] == "VALIDATION_ERROR"
        assert "details" in response.json()["error"]

    def test_global_exception_handler(self):
        """测试全局异常处理器"""
        # 模拟一个会抛出未捕获异常的端点
        response = client.get("/api/v1/test-unhandled-exception")

        assert response.status_code == 500
        assert response.json()["error"]["code"] == "INTERNAL_SERVER_ERROR"
        assert response.json()["error"]["message"] == "服务器内部错误，请稍后重试"
```

### 6.3 前端集成测试

#### 测试错误响应格式

```typescript
// tests/frontend/error-handling.test.ts

describe("Error Handling", () => {
    it("should handle EMAIL_ALREADY_EXISTS error", async () => {
        // 模拟服务器返回的错误
        const mockError = {
            error: {
                code: "EMAIL_ALREADY_EXISTS",
                message: "邮箱已被注册",
                details: { field: "email", value: "test@example.com" },
            },
        };

        // 测试错误处理逻辑
        const errorHandler = new ErrorHandler();
        const result = errorHandler.handleError(mockError);

        expect(result.code).toBe("EMAIL_ALREADY_EXISTS");
        expect(result.message).toBe("邮箱已被注册");
        expect(result.details).toEqual({
            field: "email",
            value: "test@example.com",
        });
    });

    it("should handle VALIDATION_ERROR", async () => {
        const mockError = {
            error: {
                code: "VALIDATION_ERROR",
                message: "请求数据格式错误",
                details: [
                    {
                        type: "value_error",
                        loc: ["email"],
                        msg: "field required",
                        input: null,
                    },
                ],
            },
        };

        const errorHandler = new ErrorHandler();
        const result = errorHandler.handleError(mockError);

        expect(result.code).toBe("VALIDATION_ERROR");
        expect(result.message).toBe("请求数据格式错误");
    });
});
```

---

## 7. 最佳实践总结

### 7.1 异常设计原则

1. **语义化命名**：异常类名应该清楚表达错误类型
2. **统一格式**：所有异常都使用相同的响应格式
3. **错误码规范**：使用一致的错误码命名规范
4. **安全优先**：避免暴露敏感信息
5. **用户友好**：提供清晰的错误信息

### 7.2 实施建议

1. **渐进式迁移**：逐步将现有 HTTPException 替换为自定义异常
2. **测试覆盖**：为所有异常类型编写测试
3. **文档维护**：保持错误码文档的更新
4. **监控告警**：监控异常频率，及时发现问题

### 7.3 常见陷阱

1. **忘记设置 status_code**：导致返回错误的 HTTP 状态码
2. **暴露敏感信息**：在 details 中包含数据库结构信息
3. **忽略日志记录**：生产环境无法排查问题
4. **异常处理顺序**：处理器注册顺序影响异常匹配

---

## 参考资源

-   [FastAPI 异常处理](https://fastapi.tiangolo.com/tutorial/handling-errors/)
-   [HTTP 状态码规范](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)
-   [RESTful API 错误处理最佳实践](https://restfulapi.net/error-handling/)
