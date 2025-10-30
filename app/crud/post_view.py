"""
app/crud/post_view.py

文章浏览记录相关的 CRUD 操作

MVP版本：聚焦核心功能，支持浏览记录创建和基础统计查询
"""

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    PermissionDeniedError,
    ResourceNotFoundError,
)
from app.models.post import Post, PostStatus
from app.models.post_view import PostView


def record_post_view(
    db: Session,
    *,
    post_id: UUID,
    user_id: UUID | None = None,
    session_id: str | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None,
    skip_duplicate_check: bool = False,
) -> dict:
    """记录文章浏览并返回完整状态信息（增强防刷版本）

    支持多层防刷策略：
    1. 登录用户：只按 user_id 在时间窗口内判断是否为重复浏览
    2. 匿名用户：会话ID或IP地址防刷

    Args:
        db: 数据库会话
        post_id: 文章ID
        user_id: 用户ID（可选，支持匿名浏览）
        session_id: 会话标识符（可选，用于防刷）
        ip_address: IP地址（可选，用于匿名用户防刷）
        user_agent: 用户代理字符串
        skip_duplicate_check: 是否跳过防刷检查（默认False）

    Returns:
        dict: 包含状态信息的字典：
        - post_id: 文章ID
        - view_count: 文章浏览次数
        - is_viewed: 当前用户是否已浏览过此文章
        - last_viewed_at: 最近浏览时间

    Raises:
        ResourceNotFoundError: 文章不存在
        PermissionDeniedError: 只有已发布的文章才能记录浏览统计
    """
    # 1. 验证文章存在性
    post = db.get(Post, post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    # 2. 权限检查 - 只有已发布文章才记录浏览统计
    if post.status != PostStatus.PUBLISHED:
        raise PermissionDeniedError(message="只有已发布的文章才能记录浏览统计")

    # 3. 防刷检查（可选跳过）
    if not skip_duplicate_check:
        is_duplicate = PostView.is_duplicate_view(
            db,
            post_id=post_id,
            user_id=user_id,
            session_id=session_id,
            ip_address=ip_address,
        )
        if is_duplicate:
            # 如果是重复浏览，直接返回现有的浏览状态信息
            latest_view = get_latest_post_view(
                db,
                post_id=post_id,
                user_id=user_id,
                session_id=session_id,
                ip_address=ip_address,
            )

            if latest_view:
                return {
                    "post_id": post_id,
                    "view_count": post.view_count,
                    "is_viewed": True,
                    "last_viewed_at": latest_view.viewed_at,
                }

    # 4. 创建浏览记录
    post_view = PostView(
        post_id=post_id,
        user_id=user_id,
        session_id=session_id,
        ip_address=ip_address,
        user_agent=user_agent,
    )

    db.add(post_view)

    # 5. 更新文章浏览计数（使用数据库层面的原子操作，避免高并发场景下浏览计数丢失问题）
    # ❌ 不能使用 post.increment_view_count()
    # ❌ 不推荐使用db.execute(text(...)) 原生SQL方式，因为 SQLite 存储 UUID 去掉连字符，需要转换格式  # noqa: E501
    # db.execute(
    #     text("UPDATE posts SET view_count = view_count + 1 WHERE id = :post_id"),
    #     {"post_id": post_id},
    # )
    # ✅ 推荐使用sqlalchemy ORM方式
    db.query(Post).filter(Post.id == post_id).update(
        {Post.view_count: Post.view_count + 1}, synchronize_session=False
    )

    # 6. 提交事务
    db.commit()
    db.refresh(post_view)

    # 7. 刷新文章对象以获取最新的 view_count
    db.refresh(post)

    return {
        "post_id": post_id,
        "view_count": post.view_count,
        "is_viewed": True,
        "last_viewed_at": post_view.viewed_at,
    }


def get_post_view_stats(
    db: Session,
    *,
    post_id: UUID,
    days: int = 30,
    include_anonymous: bool = True,
) -> dict:
    """获取文章浏览统计数据

    Args:
        db: 数据库会话
        post_id: 文章ID
        days: 统计天数（正数，支持任意时间段）
        include_anonymous: 是否包含匿名用户数据

    Returns:
        dict: 包含以下字段的浏览统计数据：
        - total_views: 总浏览次数 (PV)
        - unique_visitors: 独立访客数 (UV)
        - logged_in_views: 登录用户浏览次数
        - anonymous_views: 匿名用户浏览次数
        - unique_logged_in_users: 独立登录用户数
        - days_analyzed: 实际统计的天数
        - analysis_date: 统计分析的日期
        - start_date: 统计开始日期
    """
    # 基本参数验证（防止明显错误）
    if days <= 0:
        raise ValueError("统计天数必须是正数")
    # 允许用户统计任意时间段，从1天到文章整个生命周期

    start_date = datetime.now(UTC) - timedelta(days=days)

    # 验证文章存在
    post = db.get(Post, post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    # 构建基础查询
    query = select(PostView).where(
        PostView.post_id == post_id, PostView.viewed_at >= start_date
    )

    # 是否包含匿名用户
    if not include_anonymous:
        query = query.where(PostView.user_id.isnot(None))

    # 执行查询
    views = db.execute(query).scalars().all()

    # 计算统计数据
    total_views = len(views)

    # 计算独立访客数（基于用户ID和IP的组合）
    unique_visitors = set()
    for view in views:
        if view.user_id:
            unique_visitors.add(f"user_{view.user_id}")
        elif view.ip_address:
            unique_visitors.add(f"ip_{view.ip_address}")
        else:
            unique_visitors.add(f"unknown_{view.id}")

    # 分别统计登录用户和匿名用户的浏览次数
    logged_in_views = len([view for view in views if view.user_id])
    anonymous_views = total_views - logged_in_views

    # 计算独立登录用户数
    unique_logged_in_users = len({view.user_id for view in views if view.user_id})

    return {
        "post_id": post_id,
        "total_views": total_views,  # 总浏览次数，pv
        "unique_visitors": len(unique_visitors),  # 独立访客数, uv
        "logged_in_views": logged_in_views,  # 登录用户浏览次数
        "anonymous_views": anonymous_views,  # 匿名用户浏览次数
        "unique_logged_in_users": unique_logged_in_users,  # 独立登录用户数
        "days_analyzed": days,  # 统计天数
        "analysis_date": datetime.now(UTC),  # 分析日期
        "start_date": start_date,  # 统计开始日期
    }


def get_user_view_history(
    db: Session,
    *,
    user_id: UUID,
    limit: int = 20,
    offset: int = 0,
) -> list[PostView]:
    """获取用户浏览历史

    Args:
        db: 数据库会话
        user_id: 用户ID
        limit: 返回记录数量限制
        offset: 分页偏移量

    Returns:
        list[PostView]: 用户的浏览记录列表
    """
    query = (
        select(PostView)
        .where(PostView.user_id == user_id)
        .order_by(PostView.viewed_at.desc())
        .limit(limit)
        .offset(offset)
    )

    return list(db.execute(query).scalars().all())


def get_post_view_count(db: Session, *, post_id: UUID) -> int:
    """获取文章浏览记录总数

    Args:
        db: 数据库会话
        post_id: 文章ID

    Returns:
        int: 浏览记录总数
    """
    count_query = select(func.count(PostView.id)).where(PostView.post_id == post_id)
    return db.execute(count_query).scalar() or 0


def update_post_view_count_sync(db: Session, post_id: UUID) -> int:
    """同步更新文章浏览计数

    从PostView表重新计算并更新Post表的view_count字段
    主要用于数据修复和同步

    Args:
        db: 数据库会话
        post_id: 文章ID

    Returns:
        int: 更新后的浏览计数
    """
    # 验证文章存在
    post = db.get(Post, post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    # 计算实际浏览记录数
    actual_count = get_post_view_count(db, post_id=post_id)

    # 更新Post表的view_count字段
    post.view_count = actual_count
    db.add(post)
    db.commit()
    db.refresh(post)

    return post.view_count


def check_user_viewed_post(
    db: Session,
    *,
    post_id: UUID,
    user_id: UUID | None = None,
) -> bool:
    """检查用户是否已浏览过文章

    Args:
        db: 数据库会话
        post_id: 文章ID
        user_id: 用户ID（可选）

    Returns:
        bool: 用户是否已浏览过文章
    """
    if not user_id:
        return False

    query = (
        select(PostView)
        .where(PostView.post_id == post_id, PostView.user_id == user_id)
        .limit(1)
    )

    result = db.execute(query).first()
    return result is not None


def get_latest_post_view(
    db: Session,
    *,
    post_id: UUID,
    user_id: UUID | None = None,
    session_id: str | None = None,
    ip_address: str | None = None,
) -> PostView | None:
    """获取最近一次文章浏览记录，和PostView.is_duplicate_view() 保持一致的优先级：
    1. 登录用户：只按 user_id 查询
    2. 匿名用户：会话ID或IP地址防刷

    Args:
        db: 数据库会话
        post_id: 文章ID
        user_id: 用户ID（可选）
        session_id: 会话标识符（可选）
        ip_address: IP地址（可选）

    Returns:
        PostView | None: 最近的浏览记录，如果没有则返回None
    """

    query = select(PostView).where(PostView.post_id == post_id)

    # 场景 1：登录用户，只按 user_id 查询
    if user_id:
        query = query.where(PostView.user_id == user_id)
    # 场景 2：匿名用户 + 会话ID
    elif session_id:
        query = query.where(
            PostView.user_id.is_(None), PostView.session_id == session_id
        )
    # 场景 3：匿名用户 + IP地址
    elif ip_address:
        query = query.where(
            PostView.user_id.is_(None), PostView.ip_address == ip_address
        )
    else:
        return None

    query = query.order_by(PostView.viewed_at.desc()).limit(1)

    return db.execute(query).scalar_one_or_none()


def generate_session_id() -> str:
    """生成安全的会话标识符

    使用secrets模块生成安全的随机字符串，用于会话级别防刷。

    Returns:
        str: 32字符的会话标识符

    Example:
        >>> session_id = generate_session_id()
        >>> len(session_id)
        32
    """
    return secrets.token_urlsafe(24)[:32]  # 生成32字符的会话ID
