"""
API v1 路由聚合器

将所有 v1 版本的业务端点路由聚合到一起
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth

# 创建 API v1 的主路由器
api_router = APIRouter()

# 注册认证相关路由
api_router.include_router(
    auth.router,
    prefix="/auth",  # 路由前缀: /auth
    tags=["认证"],  # Swagger 文档分组标签
)

# TODO(human): 未来添加其他业务模块路由
# 例如:
# api_router.include_router(
#     posts.router,
#     prefix="/posts",
#     tags=["文章管理"],
# )
