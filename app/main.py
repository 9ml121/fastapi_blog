"""
FastAPI 应用主入口

配置说明：
1. CORS 中间件：允许前端跨域请求 TODO:目前是硬编码，后续上线修改为从环境变量读取
2. 全局异常处理器：统一错误响应格式
3. OpenAPI 元数据：优化 API 文档（Swagger UI）
"""

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError

from app.api.v1.api import api_router
from app.core.exceptions import AppError
from app.crud import notification as notification_crud
from app.db import SessionLocal

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# 创建 FastAPI 应用实例
@asynccontextmanager
async def lifespan(app: FastAPI):
    """使用了 FastAPI 最新的 lifespan 事件管理器，
    来定义在应用程序“生命周期”的开始和结束阶段需要执行的操作。

    它是一种更现代、更推荐的方式，用于替代旧版的 @app.on_event("startup")
    和 @app.on_event("shutdown") 装饰器。
    """

    await _cleanup_notifications_on_startup()
    yield


app = FastAPI(
    title="FastAPI 博客系统 API",
    description="""
    ## 📝 博客系统 API 文档

    这是一个现代化的博客系统后端 API，提供以下功能：

    * **🔐 用户认证** - 注册、登录、JWT Token
    * **👤 用户管理** - 个人资料、密码修改
    * **📄 文章管理** - 发布、编辑、删除文章（即将推出）
    * **💬 评论系统** - 发表、回复评论（即将推出）

    ### 🔐 认证方式

    大部分 API 需要 JWT Token 认证：
    1. 调用 `POST /api/v1/auth/login` 获取 access_token
    2. 在请求头中添加：`Authorization: Bearer <your_token>`
    3. 或点击右上角 🔓 按钮，输入 token（会自动添加到所有请求）

    ### 📊 通用响应格式

    **成功响应**：
    ```json
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "username": "johndoe",
      ...
    }
    ```

    **错误响应**：
    ```json
    {
      "error": {
        "code": "EMAIL_ALREADY_EXISTS",
        "message": "邮箱已被注册",
        "details": {"field": "email", "value": "test@example.com"}
      }
    }
    ```

    ### 🚀 快速开始

    1. 注册账号：`POST /api/v1/auth/register`
    2. 登录获取 token：`POST /api/v1/auth/login`
    3. 点击右上角 🔓，输入 token
    4. 开始测试需要认证的 API！
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
    lifespan=lifespan,
    # 定义统一错误响应 schema
    responses={
        422: {
            "description": "请求数据格式错误",
            "content": {
                "application/json": {
                    "example": {
                        "error": {
                            "code": "VALIDATION_ERROR",
                            "message": "请求数据格式错误",
                            "details": [
                                {"loc": ["body", "email"], "msg": "邮箱格式错误"}
                            ],
                        }
                    }
                }
            },
        }
    },
)

# ============ CORS 中间件配置 ============
# 允许前端跨域访问 API
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",  # React/Vue 开发服务器
        "http://localhost:5173",  # Vite 开发服务器
        "http://127.0.0.1:3000",
        "http://127.0.0.1:5173",
        # 生产环境需要添加实际域名：
        # "https://yourdomain.com",
        # "https://www.yourdomain.com",
    ],
    allow_credentials=True,  # 允许携带 Cookie 和 Authorization 头
    allow_methods=["*"],  # 允许所有 HTTP 方法（GET, POST, PUT, DELETE, PATCH）
    allow_headers=["*"],  # 允许所有请求头
)


# ============ 全局异常处理器 ============


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """处理应用自定义异常

    将自定义异常统一转换为标准 JSON 响应格式：
    {
      "error": {
        "code": "EMAIL_ALREADY_EXISTS",
        "message": "邮箱已被注册",
        "details": {...}
      }
    }

    Args:
        request: FastAPI 请求对象
        exc: 自定义异常实例

    Returns:
        统一格式的 JSON 响应
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


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """处理 Pydantic 验证错误（422）

    当请求数据不符合 Pydantic Schema 定义时触发。
    例如：邮箱格式错误、必填字段缺失、类型不匹配等。

    Args:
        request: FastAPI 请求对象
        exc: Pydantic 验证异常

    Returns:
        统一格式的 JSON 响应
    """
    # 安全地序列化错误详情，避免 ValueError 等对象序列化问题
    import json

    try:
        details = exc.errors()
        # 验证是否可以序列化，如果不能则使用简化版本
        json.dumps(details)  # 测试序列化
    except (TypeError, ValueError):
        # 如果序列化失败，使用简化的错误信息
        details = [
            {
                "loc": error.get("loc", []),
                "msg": error.get("msg", "验证错误"),
                "type": error.get("type", "validation_error"),
            }
            for error in exc.errors()
        ]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "请求数据格式错误",
                "details": details,
            }
        },
    )


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    """处理 FastAPI HTTPException

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
            "error": {"code": "HTTP_ERROR", "message": exc.detail, "details": None}
        },
        headers=getattr(exc, "headers", None),
    )


@app.exception_handler(IntegrityError)
async def database_integrity_error_handler(
    request: Request, exc: IntegrityError
) -> JSONResponse:
    """处理数据库完整性约束错误

    当违反数据库约束时触发（如唯一键冲突、外键约束）。
    这是兜底处理，理想情况下应该在业务层提前检查。

    安全考虑：
    - 生产环境不要暴露详细的数据库错误信息
    - 记录详细错误到日志供调试

    Args:
        request: FastAPI 请求对象
        exc: SQLAlchemy 完整性错误

    Returns:
        统一格式的 JSON 响应
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
                # ⚠️ 生产环境不要暴露详细错误
                # "details": {"exception": str(exc)}  # 仅开发环境
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


# 注册 API v1 路由
app.include_router(api_router, prefix="/api/v1")


@app.get("/")
async def root():
    return {"message": "欢迎访问博客系统 API"}


@app.get("/health")
async def health_check():
    return {"status": "ok"}


async def _cleanup_notifications_on_startup() -> None:
    """后台任务：应用启动后清理过期通知

    FastAPI 应用启动时执行的后台任务。
    其核心目标是异步地、非阻塞地清理掉数据库中过期的通知记录
    """

    def _run_sync_cleanup() -> int:
        with SessionLocal() as session:
            return notification_crud.cleanup_old_notifications(session)

    async def _run_async_cleanup() -> None:
        try:
            # 1. 使用 asyncio.to_thread 将同步阻塞的数据库操作移到后台线程，
            # 避免阻塞主事件循环。
            deleted_count = await asyncio.to_thread(_run_sync_cleanup)
            if deleted_count:
                logger.info("Cleaned %d stale notifications", deleted_count)
        except Exception:
            logger.exception("Failed to cleanup stale notifications on startup")

    # 2.使用 asyncio.create_task 实现了“发射后不管”，
    # 让清理任务在后台运行，不拖慢应用的启动速度。
    asyncio.create_task(_run_async_cleanup())


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)

# 也可以直接使用 uv 运行：
# uv run uvicorn app.main:app --reload
