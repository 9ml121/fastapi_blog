"""
应用自定义异常

设计思路：
1. AppException 作为基类，统一异常格式（code + message + status_code + details）
2. 具体业务异常继承基类，预设错误码和状态码
3. 所有异常都会被全局异常处理器捕获，返回统一格式

使用示例：
>>> if existing_user:
>>>     raise EmailAlreadyExistsError(email=user_data.email)

响应格式：
{
  "error": {
    "code": "EMAIL_ALREADY_EXISTS",
    "message": "邮箱已被注册",
    "details": {"field": "email", "value": "test@example.com"}
  }
}
"""


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
