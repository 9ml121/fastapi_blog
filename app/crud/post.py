"""
app/crud/post.py

文章相关的 CRUD 操作
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.exceptions import (
    PermissionDeniedError,
    ResourceConflictError,
    ResourceNotFoundError,
)
from app.core.pagination import PaginatedResponse, paginate_query
from app.crud import tag as tag_crud
from app.crud.user import get_user_by_id
from app.models.post import Post, PostStatus
from app.schemas.post import (
    PostCreate,
    PostFilters,
    PostPaginationParams,
    PostUpdate,
)


# ================================= 文章基础查询函数 =================================
def get_post_by_id(db: Session, *, post_id: UUID) -> Post | None:
    """通过文章 ID 查询文章

    Args:
        db: 数据库会话
        post_id: 文章 ID

    Returns:
        Post | None: 文章对象，如果不存在则返回 None
    """
    return db.get(Post, post_id)


def get_post_by_slug(db: Session, *, slug: str) -> Post | None:
    """通过文章 slug 查询文章

    Args:
        db: 数据库会话
        slug: 文章 slug

    Returns:
        Post | None: 文章对象，如果不存在则返回 None
    """
    return db.query(Post).filter(Post.slug == slug).first()


# =============================== 文章列表查询函数 ===========================
def get_published_posts_paginated(
    db: Session,
    *,
    filters_params: PostFilters | None = None,
    pagination_params: PostPaginationParams,
) -> PaginatedResponse[Post]:
    """已发布文章列表分页查询（支持置顶优先）

    Args:
        db: 数据库会话
        filters_params: 过滤条件,PostFilters模型
        pagination_params: 分页参数, PostPaginationParams模型,
        默认值为 PostPaginationParams(
            page=1, size=20, sort="published_at", order="desc",
            prioritize_featured=True
        )

    Returns:
        PaginatedResponse[PostResponse]: 已发布文章分页查询结果
    """
    query = select(Post).where(Post.status == PostStatus.PUBLISHED)

    # 应用过滤条件
    if filters_params:
        # 按作者过滤
        if filters_params.author_id is not None:
            query = query.where(Post.author_id == filters_params.author_id)

        # 按标签过滤（JOIN 操作：连接 posts、post_tags、tags 三个表）
        if filters_params.tag_name is not None:
            from app.models.tag import Tag

            query = query.join(Post.tags).where(Tag.name == filters_params.tag_name)

        # 按标题关键词过滤（模糊匹配，不区分大小写）
        if filters_params.title_contains is not None:
            query = query.where(
                func.lower(Post.title).like(
                    f"%{filters_params.title_contains.lower()}%"
                )
            )

        # 按发布时间范围过滤
        if filters_params.published_at_from is not None:
            query = query.where(Post.published_at >= filters_params.published_at_from)
        if filters_params.published_at_to is not None:
            query = query.where(Post.published_at <= filters_params.published_at_to)

    # 应用排序（置顶优先）
    if pagination_params.prioritize_featured:
        query = query.order_by(Post.is_featured.desc(), Post.published_at.desc())
    else:
        query = query.order_by(Post.published_at.desc())

    # 分页查询，返回数据列表和总记录数
    items, total = paginate_query(db, query, pagination_params, model=Post)

    return PaginatedResponse.create(items, total, pagination_params)


def get_user_drafts(db: Session, *, user_id: UUID) -> list[Post]:
    """用户草稿列表查询

    Args:
        db: 数据库会话
        user_id: 用户 ID

    Returns:
        list[Post]: 用户草稿列表
    """
    return (
        db.query(Post)
        .filter(Post.author_id == user_id, Post.status == PostStatus.DRAFT)
        .order_by(Post.created_at.desc())
        .all()  # 查询结构为空，会返回一个空列表
    )


def get_featured_posts(
    db: Session, pagination_params: PostPaginationParams
) -> PaginatedResponse[Post]:
    """获取置顶文章列表"""
    query = (
        select(Post)
        .where(Post.status == PostStatus.PUBLISHED, Post.is_featured.is_(True))
        .order_by(Post.published_at.desc())
    )

    items, total = paginate_query(db, query, pagination_params, model=Post)
    return PaginatedResponse.create(items, total, pagination_params)


# ============================= 文章创建函数 ===========================
def create_post(db: Session, *, post_in: PostCreate, author_id: UUID) -> Post:
    """创建新文章，自动处理slug生成、标签关联、摘要生成
    Args:
        db: 数据库会话。
        post_in: 文章创建数据,PostCreate模型
        author_id: 文章作者的用户 ID

    Returns:
        Post: 新创建的文章对象，包含完整的关联数据。
    """

    # 1. 从输入 schema 中提取数据
    post_in_data = post_in.model_dump(exclude={"tags"})
    tag_names = post_in.tags or []

    # 2. 处理 slug: 如果 slug 为空，就根据 title 自动生成一个
    if not post_in_data.get("slug"):
        post_in_data["slug"] = Post._generate_slug_from_title(post_in_data["title"])

    # 3. 创建 Post 对象, 并关联到指定作者
    post = Post(**post_in_data, author_id=author_id)

    # 4. 处理 summary：如果未提供摘要，则从文章内容自动生成
    if not post_in_data.get("summary"):
        post.set_summary_from_content()

    # 5. 将 Post 对象添加到会话中，使其变为 pending 状态
    db.add(post)

    # 6. 处理标签同步
    # ⚠️ tag_crud.get_or_create 是没有事务提交的
    for tag_name in tag_names:
        tag_obj = tag_crud.get_or_create_tag(db, name=tag_name)
        post.tags.append(tag_obj)

    # 7. 一次性提交事务，保证事务完整性。
    db.commit()
    db.refresh(post)
    return post


# ============================= 文章更新函数 ===========================
def update_post(
    db: Session, *, post_id: UUID, user_id: UUID, post_in: PostUpdate | dict
) -> Post:
    """更新文章，自动处理标签同步
    Args:
        db: 数据库会话
        post_id: 要更新的文章 ID
        user_id: 更新文章的用户 ID
        post_in: 文章更新数据, PostUpdate模型或字典

    Returns:
        Post: 更新后的文章对象，包含最新的关联数据。
    """
    # 1. 文章存在性检查
    post = get_post_by_id(db=db, post_id=post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    # 2. 权限检查：只有作者可以更新
    if post.author_id != user_id:
        raise PermissionDeniedError(message="无权限修改此文章")

    # 3. 如果输入是 Pydantic 模型，先转换为字典
    # ⚠️ exclude_unset=True 实现了 PATCH 语义
    update_data = (
        post_in if isinstance(post_in, dict) else post_in.model_dump(exclude_unset=True)
    )

    # 4. 分离 `tags` 字段，因为它需要特殊处理
    tag_names = update_data.pop("tags", None)

    # 5. 更新普通字段
    for field, value in update_data.items():
        setattr(post, field, value)

    # 6. 单独处理标签同步
    if tag_names is not None:
        # 将标签名列表转换为 Tag 对象列表
        tags = [tag_crud.get_or_create_tag(db, name=name) for name in tag_names]
        # 直接赋值给 relationship 属性，SQLAlchemy 会自动处理差异
        post.tags = tags

    # 7. 统一提交（一次性提交所有修改，确保事务原子性）
    db.add(post)
    db.commit()
    db.refresh(post)

    return post


def publish_post(db: Session, *, post_id: UUID, user_id: UUID) -> Post:
    """发布草稿文章

    Args:
        db: 数据库会话
        post_id: 文章 ID
        user_id: 发布文章的用户 ID

    Returns:
        更新后的文章对象 (status=published, published_at已设置)
    """
    post = get_post_by_id(db=db, post_id=post_id)
    # 检查存在性
    if not post:
        raise ResourceNotFoundError(resource="文章")

    # 检查权限：作者或管理员
    current_user = get_user_by_id(db=db, user_id=user_id)

    if post.author_id != user_id and current_user and not current_user.is_admin:
        raise PermissionDeniedError(message="无权限发布此文章")

    # 业务规则校验：只有草稿才能发布
    if post.status != PostStatus.DRAFT:
        raise ResourceConflictError(
            message=f"无法发布 {post.status} 状态的文章，只有草稿状态才能发布"
        )

    post.publish()  # 调用 Post 模型的 publish() 方法
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def archive_post(db: Session, *, post_id: UUID, user_id: UUID) -> Post:
    """归档文章

    Args:
        db: 数据库会话
        post_id: 文章 ID
        user_id: 归档文章的用户 ID

    Returns:
        更新后的文章对象 (status=archived)
    """
    post = get_post_by_id(db=db, post_id=post_id)
    # 检查存在性
    if not post:
        raise ResourceNotFoundError(resource="文章")

    # 检查权限：只有文章作者或者管理员可以归档
    current_user = get_user_by_id(db=db, user_id=user_id)

    if post.author_id != user_id and current_user and not current_user.is_admin:
        raise PermissionDeniedError(message="无权限归档此文章")

    # 业务规则校验：只有已发布文章才能归档
    if post.status != PostStatus.PUBLISHED:
        raise ResourceConflictError(
            message=f"无法归档 {post.status} 状态的文章，只有已发布状态才能归档"
        )

    post.archive()  # 调用 Post 模型的 archive() 方法
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def revert_post_to_draft(db: Session, *, post_id: UUID, user_id: UUID) -> Post:
    """将文章恢复为草稿状态

    Args:
        db: 数据库会话
        post_id: 文章 ID
        user_id: 恢复文章为草稿的用户 ID

    Returns:
        更新后的文章对象 (status=draft, published_at=None)
    """
    post = get_post_by_id(db=db, post_id=post_id)
    # 检查存在性
    if not post:
        raise ResourceNotFoundError(resource="文章")

    # 检查权限：只有文章作者或者管理员可以恢复为草稿
    current_user = get_user_by_id(db=db, user_id=user_id)

    if post.author_id != user_id and current_user and not current_user.is_admin:
        raise PermissionDeniedError(message="无权限恢复为草稿")

    # 业务规则校验：只有已发布或已归档文章才能恢复为草稿
    if post.status == PostStatus.DRAFT:
        raise ResourceConflictError(message="文章已是草稿状态，无需恢复")

    post.revert_to_draft()  # 调用 Post 模型的 revert_to_draft() 方法
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


def toggle_post_featured(db: Session, post_id: UUID, user_id: UUID) -> Post:
    """切换文章置顶状态

    Args:
        db: 数据库会话
        post_id: 文章ID
        user_id: 操作用户ID

    Returns:
        Post: 更新后的文章对象

    Raises:
        ResourceNotFoundError: 文章不存在
        PermissionDeniedError: 无权限操作
    """
    # 1. 验证文章存在性
    post = get_post_by_id(db=db, post_id=post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    # 2. 验证用户权限（必须是管理员）
    current_user = get_user_by_id(db=db, user_id=user_id)
    if not current_user or not current_user.is_admin:
        raise PermissionDeniedError(message="只有管理员可以置顶文章")

    # 3. 调用 post.toggle_featured()
    post.toggle_featured()

    # 4. 提交事务
    db.add(post)
    db.commit()
    db.refresh(post)
    return post


# ============================= 文章删除函数 ===========================
def delete_post(db: Session, *, post_id: UUID, user_id: UUID) -> None:
    """删除文章
    Args:
        db: 数据库会话
        post_id: 文章 ID
        user_id: 删除文章的用户 ID

    Returns:
        None
    """
    # 1. 文章存在性检查
    post = get_post_by_id(db=db, post_id=post_id)
    if not post:
        raise ResourceNotFoundError(resource="文章")

    # 2. 权限检查：只有文章作者或者管理员可以删除
    current_user = get_user_by_id(db=db, user_id=user_id)

    if post.author_id != user_id and current_user and not current_user.is_admin:
        raise PermissionDeniedError(message="无权限删除此文章")

    # 3. 删除文章
    db.delete(instance=post)
    db.commit()

    return None
