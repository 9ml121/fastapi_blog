"""
app/crud/post.py

文章相关的 CRUD 操作
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.pagination import PaginationParams, paginate_query
from app.core.exceptions import ResourceConflictError, ResourceNotFoundError
from app.crud.base import CRUDBase
from app.crud.tag import tag as tag_crud
from app.models.post import Post, PostStatus
from app.schemas.post import PostCreate, PostFilters, PostUpdate


class CRUDPost(CRUDBase[Post, PostCreate, PostUpdate]):
    """文章的 CRUD 操作类。

    继承自 CRUDBase，提供文章特有的业务逻辑，包括：
    - 基于 slug 的查询
    - 创建文章时自动处理 slug 生成和标签关联
    - 更新文章时同步标签关系
    """

    def get_by_slug(self, db: Session, *, slug: str) -> Post | None:
        """通过 URL slug 获取文章。

        Args:
            db: 数据库会话。
            slug: 文章的 URL 友好标识符。

        Returns:
            找到的文章对象，如果不存在则返回 None。
        """
        post = db.query(Post).filter(Post.slug == slug).first()

        return post

    def create_with_author(
        self, db: Session, *, obj_in: PostCreate, author_id: UUID
    ) -> Post:
        """创建新文章，并自动关联作者和标签。

        此方法会：
        1. 从输入 schema 中提取文章数据
        2. 如果未提供 slug，则根据标题自动生成
        3. 创建文章对象并关联到指定作者
        4. 处理标签关联（通过 get_or_create 确保标签唯一性）
        5. 一次性提交所有更改到数据库

        Args:
            db: 数据库会话。
            obj_in: 包含文章创建数据的 Pydantic schema。
            author_id: 文章作者的用户 ID。

        Returns:
            新创建的文章对象，包含完整的关联数据。

        Example:
            >>> post_in = PostCreate(
            ...     title="测试文章", content="内容", tags=["Python", "FastAPI"]
            ... )
            >>> new_post = post_crud.create_with_author(
            ...     db, obj_in=post_in, author_id=user.id
            ... )
        """

        # 1. 从输入 schema 中提取数据
        obj_in_data = obj_in.model_dump(exclude={"tags"})
        tag_names = obj_in.tags or []

        # 2. 处理 slug: 如果 slug 为空，就根据 title 自动生成一个
        if not obj_in_data.get("slug"):
            obj_in_data["slug"] = Post._generate_slug_from_title(obj_in_data["title"])

        # 3. 创建 Post 对象并添加到会话中，使其变为 pending 状态
        db_obj = self.model(**obj_in_data, author_id=author_id)
        db.add(db_obj)

        # 4. 处理标签同步
        # ⚠️ tag_crud.get_or_create 是没有事务提交的
        for tag_name in tag_names:
            tag_obj = tag_crud.get_or_create(db, name=tag_name)
            db_obj.tags.append(tag_obj)

        # 5. 一次性提交事务，保证事务完整性。
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(self, db: Session, *, db_obj: Post, obj_in: PostUpdate | dict) -> Post:
        """更新文章，同时智能处理标签同步。

        此方法会：
        1. 将普通字段（title, content 等）直接更新到对象
        2. 单独处理 tags 字段：
           - 如果 tags 未在输入中提供（None），则保持原有标签不变
           - 如果 tags 为空列表（[]），则清空所有标签
           - 如果 tags 为新列表，则完全替换为新标签
        3. 在一个事务中统一提交所有修改，确保原子性

        Args:
            db: 数据库会话。
            db_obj: 要更新的文章对象（从数据库查询得到）。
            obj_in: 包含更新数据的 Pydantic schema 或字典。

        Returns:
            更新后的文章对象，包含最新的关联数据。

        Note:
            ⚠️ 重要：整个更新过程在一个事务中完成，确保原子性。
            如果标签处理失败，所有修改（包括普通字段）都会回滚。

            使用 `exclude_unset=True` 确保只更新实际提供的字段，
            这样可以实现部分更新（PATCH 语义）而非完全替换（PUT 语义）。

        Example:
            >>> # 只更新标题，保持标签不变
            >>> post_crud.update(db, db_obj=post, obj_in=PostUpdate(title="新标题"))
            >>>
            >>> # 更新标题并替换标签
            >>> post_crud.update(
            ...     db, db_obj=post, obj_in=PostUpdate(title="新标题", tags=["新标签"])
            ... )
            >>>
            >>> # 清空所有标签
            >>> post_crud.update(db, db_obj=post, obj_in=PostUpdate(tags=[]))
        """

        # 1. 如果输入是 Pydantic 模型，先转换为字典
        # ⚠️ exclude_unset=True 实现了 PATCH 语义
        update_data = (
            obj_in
            if isinstance(obj_in, dict)
            else obj_in.model_dump(exclude_unset=True)
        )

        # 2. 分离 `tags` 字段，因为它需要特殊处理
        tag_names = update_data.pop("tags", None)

        # 3. 更新普通字段（不调用父类 update，避免提前 commit）
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        # 4. 处理标签同步
        if tag_names is not None:
            # 将标签名列表转换为 Tag 对象列表
            tags = [tag_crud.get_or_create(db, name=name) for name in tag_names]
            # 直接赋值给 relationship 属性，SQLAlchemy 会自动处理差异
            db_obj.tags = tags

        # 5. 统一提交（一次性提交所有修改，确保事务原子性）
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)

        return db_obj

    def get_paginated(
        self,
        db: Session,
        *,
        params: PaginationParams,
        filters: PostFilters | None = None,
    ) -> tuple[list[Post], int]:
        """获取分页的文章列表

        使用新的分页工具，支持：
        - 分页：page/size 参数，默认分页数量 20
        - 排序：sort/order 参数，默认按照 created_at 降序排序
        - 安全验证：自动验证排序字段
        - 多种过滤：按作者、标签、发布状态、标题关键词、发布时间范围过滤

        Args:
            db: 数据库会话
            params: 分页参数（包含页码、每页数量、排序字段、排序方向）
            filters: 过滤条件（PostFilters 对象）

        Returns:
            tuple: (文章列表, 总记录数)

        Example:
            >>> # 基础分页
            >>> params = PaginationParams(page=1, size=10)
            >>> posts, total = post_crud.get_paginated(db, params=params)

            >>> # 按作者分页
            >>> filters = PostFilters(author_id=user.id)
            >>> posts, total = post_crud.get_paginated(
            ...     db, params=params, filters=filters
            ... )

            >>> # 组合过滤：已发布的Python标签文章
            >>> filters = PostFilters(
            ...     tag_name="Python", statuses=[PostStatus.PUBLISHED]
            ... )
            >>> posts, total = post_crud.get_paginated(
            ...     db, params=params, filters=filters
            ... )

            >>> # 多状态过滤：查询草稿和归档文章
            >>> filters = PostFilters(statuses=[PostStatus.DRAFT, PostStatus.ARCHIVED])
            >>> posts, total = post_crud.get_paginated(
            ...     db, params=params, filters=filters
            ... )
        """
        # 构建基础查询
        query = select(Post)

        # 应用过滤条件
        if filters:
            # 按作者过滤
            if filters.author_id is not None:
                query = query.where(Post.author_id == filters.author_id)

            # 按标签过滤（需要 JOIN）
            if filters.tag_name is not None:
                from app.models.tag import Tag

                query = query.join(Post.tags).where(Tag.name == filters.tag_name)

            # 按发布状态过滤（支持多选）
            if filters.statuses is not None and len(filters.statuses) > 0:
                query = query.where(Post.status.in_(filters.statuses))

            # 按标题关键词过滤（模糊匹配，不区分大小写）
            if filters.title_contains is not None:
                query = query.where(
                    func.lower(Post.title).like(f"%{filters.title_contains.lower()}%")
                )

            # 按发布时间范围过滤
            if filters.published_at_from is not None:
                query = query.where(Post.published_at >= filters.published_at_from)
            if filters.published_at_to is not None:
                query = query.where(Post.published_at <= filters.published_at_to)

        # 使用分页工具执行查询
        # TODO: 分页查询不在 crud层中，应该由api层处理，重构中
        items, total = paginate_query(db, query, params, model=Post)

        return items, total

    def get_user_drafts(self, db: Session, *, user_id: UUID) -> list[Post]:
        """获取用户草稿列表

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
            .all()
        )

    def publish(self, db: Session, *, post_id: UUID) -> Post:
        """发布草稿

        此方法会：
        1. 查询指定的文章对象
        2. 调用 post.publish() 业务方法更新状态和时间
        3. 提交更改到数据库
        4. 返回更新后的文章对象

        Args:
            db: 数据库会话
            post_id: 文章 ID

        Returns:
            更新后的文章对象 (status=published, published_at已设置)
            如果文章不存在返回 None

        Example:
            >>> published_post = post_crud.publish(db, post_id=post.id)
            >>> if published_post:
            ...     print(f"文章已发布，发布时间: {published_post.published_at}")
        """
        db_obj = db.query(Post).filter(Post.id == post_id).first()
        # 检查存在性
        if not db_obj:
            raise ResourceNotFoundError(resource="文章")

        # 业务规则校验：只有草稿才能发布
        if db_obj.status != PostStatus.DRAFT:
            raise ResourceConflictError(
                message=f"无法发布 {db_obj.status} 状态的文章，只有草稿状态才能发布"
            )

        db_obj.publish()  # 调用 Post 模型的 publish() 方法
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def archive(self, db: Session, *, post_id: UUID) -> Post:
        """归档文章

        此方法会：
        1. 查询指定的文章对象
        2. 调用 post.archive() 业务方法更新状态
        3. 提交更改到数据库
        4. 返回更新后的文章对象

        Args:
            db: 数据库会话
            post_id: 文章 ID

        Returns:
            更新后的文章对象 (status=archived)
            如果文章不存在返回 None

        Example:
            >>> archived_post = post_crud.archive(db, post_id=post.id)
            >>> if archived_post:
            ...     print(f"文章已归档")
        """
        db_obj = db.query(Post).filter(Post.id == post_id).first()
        # 检查存在性
        if not db_obj:
            raise ResourceNotFoundError(resource="文章")

        # 业务规则校验：只有已发布文章才能归档
        if db_obj.status != PostStatus.PUBLISHED:
            raise ResourceConflictError(
                message=f"无法归档 {db_obj.status} 状态的文章，只有已发布状态才能归档"
            )

        db_obj.archive()  # 调用 Post 模型的 archive() 方法
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def revert_to_draft(self, db: Session, *, post_id: UUID) -> Post:
        """将文章恢复为草稿状态

        此方法会：
        1. 查询指定的文章对象
        2. 调用 post.revert_to_draft() 业务方法恢复为草稿
        3. 提交更改到数据库
        4. 返回更新后的文章对象

        Args:
            db: 数据库会话
            post_id: 文章 ID

        Returns:
            更新后的文章对象 (status=draft, published_at=None)
            如果文章不存在返回 None

        Example:
            >>> draft_post = post_crud.revert_to_draft(db, post_id=post.id)
            >>> if draft_post:
            ...     print(f"文章已恢复为草稿")
        """
        db_obj = db.query(Post).filter(Post.id == post_id).first()
        # 检查存在性
        if not db_obj:
            raise ResourceNotFoundError(resource="文章")

        # 业务规则校验：只有已发布或已归档文章才能恢复为草稿
        if db_obj.status == PostStatus.DRAFT:
            raise ResourceConflictError(message="文章已是草稿状态，无需恢复")

        db_obj.revert_to_draft()  # 调用 Post 模型的 revert_to_draft() 方法
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj


# Singleton实例模式：为每个CRUD类创建一个全局实例
post = CRUDPost(Post)
