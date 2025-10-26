"""
API v1 路由聚合器

将所有 v1 版本的业务端点路由聚合到一起
"""

from fastapi import APIRouter

from app.api.v1.endpoints import auth, comments, favorites, likes, posts, tags, users

# 创建 API v1 的主路由器
api_router = APIRouter()

# 注册认证相关路由
api_router.include_router(
    auth.router,
    prefix="/auth",  # 路由前缀: /auth
    tags=["🔐 认证"],  # Swagger 文档分组标签（与 main.py 的 openapi_tags 对应）
)

# 注册用户资料管理路由
api_router.include_router(
    users.router,
    prefix="/users",
    tags=["👤 用户管理"],
)

# 注册文章管理路由
api_router.include_router(
    posts.router,
    prefix="/posts",
    tags=["📄 文章管理"],
)

# 注册标签管理路由
api_router.include_router(
    tags.router,
    prefix="/tags",
    tags=["🏷️ 标签管理"],
)

# 注册评论管理路由（嵌套在文章路由下）
api_router.include_router(
    comments.router,
    prefix="/posts",  # 前缀：/posts，实际路由：/posts/{post_id}/comments
    tags=["💬 评论管理"],
)

# 注册点赞管理路由（嵌套在文章路由下）
api_router.include_router(
    likes.router,
    prefix="/posts",  # 前缀：/posts，实际路由：/posts/{post_id}/likes
    tags=["👍 点赞管理"],
)

# 注册收藏管理路由（嵌套在文章路由下）
api_router.include_router(
    favorites.router,
    prefix="/posts",  # 前缀：/posts，实际路由：/posts/{post_id}/favorites
    tags=["🌟 收藏管理"],
)