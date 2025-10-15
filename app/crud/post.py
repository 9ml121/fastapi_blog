"""
app/crud/post.py

文章相关的 CRUD 操作
"""

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.api.pagination import PaginationParams, paginate_query
from app.crud.base import CRUDBase
from app.crud.tag import tag as tag_crud
from app.models.post import Post
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
        return db.query(Post).filter(Post.slug == slug).first()

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

        # 4. 处理并关联标签
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
        #    这里直接使用 setattr 更新字段，复制自父类逻辑
        for field, value in update_data.items():
            setattr(db_obj, field, value)

        # 4. 处理标签同步
        if tag_names is not None:
            # 将标签名列表转换为 Tag 对象列表
            tags = [tag_crud.get_or_create(db, name=name) for name in tag_names]
            # 直接赋值给 relationship 属性，SQLAlchemy 会自动处理差异
            db_obj.tags = tags

        # 5. 统一提交（一次性提交所有修改，确保事务原子性）
        #    ✅ 要么全部成功，要么全部失败（回滚）
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
        - 多种过滤：按作者、标签、发布状态、标题关键词过滤

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
            >>> filters = PostFilters(tag_name="Python", is_published=True)
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

            # 按发布状态过滤
            if filters.is_published is not None:
                from app.models.post import PostStatus

                if filters.is_published:
                    query = query.where(Post.status == PostStatus.PUBLISHED)
                else:
                    query = query.where(Post.status != PostStatus.PUBLISHED)

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
        items, total = paginate_query(db, query, params, model=Post)

        return items, total


# Singleton实例模式：为每个CRUD类创建一个全局实例
post = CRUDPost(Post)
