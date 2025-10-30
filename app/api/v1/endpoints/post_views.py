"""
文章浏览统计API端点

提供文章浏览记录和统计功能的API接口
"""

from uuid import UUID

from fastapi import APIRouter, Depends, Request
from sqlalchemy.orm import Session

import app.crud.post as post_crud
import app.crud.post_view as post_view_crud
from app.api.deps import get_current_active_user, get_current_user_optional, get_db
from app.core.exceptions import ResourceNotFoundError
from app.models.user import User
from app.schemas.post_view import (
    PostViewCreate,
    PostViewStatsQuery,
    PostViewStatsResponse,
    PostViewStatusResponse,
)

# 注册文章浏览统计路由
router = APIRouter()


# ============================= 记录文章浏览 ===========================
@router.post("/{post_id}/view", response_model=PostViewStatusResponse)
async def record_post_view(
    post_id: UUID,
    view_data: PostViewCreate,
    request: Request,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
) -> PostViewStatusResponse:
    """记录文章浏览并更新浏览计数

    **功能说明：**
    - 支持登录用户和匿名用户浏览
    - 自动获取IP地址和User-Agent
    - 集成多层防刷机制
    - 更新文章浏览计数

    **防刷策略：**
    1. 登录用户：有会话ID则严格防刷，无会话ID则用户级别防刷
    2. 匿名用户：会话ID或IP地址防刷
    3. 时间窗口：默认24小时

    **权限：**
    - 公开访问，无需登录
    - 只有已发布文章可以记录浏览统计

    **路径参数：**
    - post_id: 文章的UUID

    **请求体参数：**
    - session_id: 会话标识符（可选）
    - ip_address: IP地址（可选，自动获取）
    - user_agent: 用户代理（可选，自动获取）
    - skip_duplicate_check: 是否跳过防刷检查，默认False

    **返回：**
    - 200: 浏览记录成功
    - 404: 文章不存在
    - 403: 文章未发布，无法记录浏览

    **示例：**
        POST /api/v1/posts/123e4567-e89b-12d3/view
        {
            "session_id": "abc123def456789012345678901234",
            "skip_duplicate_check": false
        }
    """
    # 获取客户端信息（如果请求体中没有提供）
    client_ip = view_data.ip_address or _get_client_ip(request)
    user_agent = view_data.user_agent or request.headers.get("User-Agent")

    # 调用CRUD层记录浏览并获取完整状态信息
    result = post_view_crud.record_post_view(
        db=db,
        post_id=post_id,
        user_id=current_user.id if current_user else None,
        session_id=view_data.session_id,
        ip_address=client_ip,
        user_agent=user_agent,
        skip_duplicate_check=view_data.skip_duplicate_check,
    )

    return PostViewStatusResponse(**result)


# ============================= 获取文章浏览统计 ===========================
@router.get("/{post_id}/view-stats", response_model=PostViewStatsResponse)
async def get_post_view_stats(
    post_id: UUID,
    query: PostViewStatsQuery = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PostViewStatsResponse:
    """获取文章浏览统计数据

    **功能说明：**
    - 提供详细的浏览统计信息
    - 支持自定义时间范围
    - 区分登录用户和匿名用户数据
    - 计算PV、UV等关键指标

    **统计维度：**
    - 总浏览次数 (PV)
    - 独立访客数 (UV)
    - 登录用户浏览次数
    - 匿名用户浏览次数
    - 独立登录用户数

    **权限：**
    - 需要登录
    - 仅文章作者和管理员可查看统计数据

    **路径参数：**
    - post_id: 文章的UUID

    **查询参数：**
    - days: 统计天数（默认30天）
    - include_anonymous: 是否包含匿名用户数据（默认true）

    **返回：**
    - 200: 统计数据获取成功
    - 404: 文章不存在
    - 403: 无权限查看统计数据

    **示例：**
        GET /api/v1/posts/123e4567-e89b-12d3/view-stats?days=30&include_anonymous=true
    """
    # 检查权限（只有文章作者和管理员可查看统计）
    post = post_crud.get_post_by_id(db=db, post_id=post_id)
    if post is None:
        raise ResourceNotFoundError(resource="文章")

    # 权限检查：文章作者或管理员
    if not (post.author_id == current_user.id or current_user.is_admin):
        raise ResourceNotFoundError(resource="统计数据")

    # 获取浏览统计数据
    stats = post_view_crud.get_post_view_stats(
        db=db,
        post_id=post_id,
        days=query.days,
        include_anonymous=query.include_anonymous,
    )

    return PostViewStatsResponse(**stats)


# ============================= 获取用户浏览状态 ===========================
@router.get("/{post_id}/view-status", response_model=PostViewStatusResponse)
async def get_post_view_status(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> PostViewStatusResponse:
    """获取用户对文章的浏览状态

    **功能说明：**
    - 检查当前用户是否已浏览过指定文章
    - 返回文章的总浏览次数
    - 显示用户最近浏览时间

    **使用场景：**
    - 文章详情页显示用户浏览状态
    - 个性化推荐系统
    - 用户阅读历史追踪

    **权限：**
    - 需要登录

    **路径参数：**
    - post_id: 文章的UUID

    **返回：**
    - 200: 浏览状态获取成功
    - 404: 文章不存在

    **示例：**
        GET /api/v1/posts/123e4567-e89b-12d3/view-status
    """
    # 获取文章信息
    post = post_crud.get_post_by_id(db=db, post_id=post_id)
    if post is None:
        raise ResourceNotFoundError(resource="文章")

    # 检查用户是否已浏览过
    is_viewed = post_view_crud.check_user_viewed_post(
        db=db, post_id=post_id, user_id=current_user.id
    )

    # 获取最近浏览时间
    last_viewed_at = None
    if is_viewed:
        latest_view = post_view_crud.get_latest_post_view(
            db=db, post_id=post_id, user_id=current_user.id
        )
        if latest_view:
            last_viewed_at = latest_view.viewed_at

    return PostViewStatusResponse(
        post_id=post_id,
        is_viewed=is_viewed,
        view_count=post.view_count,
        last_viewed_at=last_viewed_at,
    )


# ============================= 辅助函数 ===========================
def _get_client_ip(request: Request) -> str:
    """获取客户端真实IP地址

    Args:
        request: FastAPI请求对象

    Returns:
        str: 客户端IP地址
    """
    # 优先获取代理服务器的X-Forwarded-For头部
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # X-Forwarded-For可能包含多个IP，取第一个
        return forwarded_for.split(",")[0].strip()

    # 其次获取X-Real-IP头部
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip

    # 最后使用连接的客户端IP
    if request.client:
        return request.client.host

    return "unknown"
