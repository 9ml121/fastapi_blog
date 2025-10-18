"""
tests/test_crud/test_post.py

测试 Post CRUD 操作

测试覆盖：
- 基础 CRUD 操作（继承自 CRUDBase）
- 自定义业务方法（create_with_author, get_by_slug）
- Phase 6.1 新增方法（get_user_drafts, publish, archive, revert_to_draft）
- 边界情况和异常处理
"""

import uuid

import pytest
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceConflictError, ResourceNotFoundError
from app.crud.post import post as post_crud
from app.models.post import Post, PostStatus
from app.models.tag import Tag
from app.models.user import User
from app.schemas.post import PostCreate, PostUpdate


class TestCRUDPost:
    """测试 Post CRUD 的所有方法"""

    # ============ 创建测试：create_with_author ============

    def test_create_post_with_author_success(self, session: Session, sample_user: User):
        """✅ 正常数据：测试 create_with_author 方法成功创建文章

        测试场景：
        1. 创建包含标签的文章
        2. 验证文章基本信息正确
        3. 验证标签关联正确
        4. 验证新标签自动创建
        """
        # 1. 准备前置数据：一个已存在的标签
        existing_tag = Tag(name="existing_tag", slug="existing-tag")
        session.add(existing_tag)
        session.commit()

        # 2. 准备输入数据，包含一个已存在的和一个全新的标签
        post_in = PostCreate(
            title="Test Post with Tags",
            content="Content here...",
            tags=["existing_tag", "new_tag"],
        )

        # 3. 调用被测试的函数
        created_post = post_crud.create_with_author(
            db=session, obj_in=post_in, author_id=sample_user.id
        )

        # 4. 断言
        assert created_post.title == "Test Post with Tags"
        assert created_post.author_id == sample_user.id
        assert len(created_post.tags) == 2

        # 验证标签名称是否正确
        tag_names = sorted([tag.name for tag in created_post.tags])
        assert tag_names == ["Existing_tag", "New_tag"]

        # 验证新的标签确实被创建到了数据库中
        new_tag_from_db = session.query(Tag).filter(Tag.name == "New_tag").first()
        assert new_tag_from_db is not None
        assert new_tag_from_db.slug is not None

    def test_create_post_with_empty_tags(self, session: Session, sample_user: User):
        """✅ 边界数据：测试创建文章时标签为空列表"""
        post_in = PostCreate(
            title="Test Post Empty Tags",
            content="Content here...",
            tags=[],
        )

        created_post = post_crud.create_with_author(
            db=session, obj_in=post_in, author_id=sample_user.id
        )

        assert created_post.title == "Test Post Empty Tags"
        assert len(created_post.tags) == 0

    def test_create_post_with_none_tags(self, session: Session, sample_user: User):
        """✅ 边界数据：测试创建文章时标签为 None"""
        post_in = PostCreate(
            title="Test Post None Tags",
            content="Content here...",
            tags=None,
        )

        created_post = post_crud.create_with_author(
            db=session, obj_in=post_in, author_id=sample_user.id
        )

        assert created_post.title == "Test Post None Tags"
        assert len(created_post.tags) == 0

    def test_create_post_auto_generate_slug(self, session: Session, sample_user: User):
        """✅ 正常数据：测试自动生成 slug"""
        post_in = PostCreate(
            title="Test Post",
            content="test content",
            # 不提供 slug
        )

        created_post = post_crud.create_with_author(
            db=session, obj_in=post_in, author_id=sample_user.id
        )

        assert created_post.slug is not None
        assert len(created_post.slug) > 0
        assert created_post.slug == "Test-Post"  # slug 应该被处理过

    def test_create_post_with_custom_slug(self, session: Session, sample_user: User):
        """✅ 正常数据：测试使用自定义 slug"""
        custom_slug = "custom-slug-123"
        post_in = PostCreate(
            title="Test Post",
            content="Content",
            slug=custom_slug,
        )

        created_post = post_crud.create_with_author(
            db=session, obj_in=post_in, author_id=sample_user.id
        )

        assert created_post.slug == custom_slug

    def test_create_post_duplicate_slug(self, session: Session, sample_user: User):
        """✅ 异常数据：测试重复 slug 冲突"""
        duplicate_slug = "duplicate-slug"

        # 创建第一篇文章
        post_crud.create_with_author(
            db=session,
            obj_in=PostCreate(
                title="First Post", content="Content", slug=duplicate_slug
            ),
            author_id=sample_user.id,
        )

        # 尝试创建相同 slug 的文章
        from sqlalchemy.exc import IntegrityError

        with pytest.raises(IntegrityError):
            post_crud.create_with_author(
                db=session,
                obj_in=PostCreate(
                    title="Second Post", content="Content", slug=duplicate_slug
                ),
                author_id=sample_user.id,
            )

    def test_generic_create_fails_without_author(self, session: Session):
        """✅ 异常数据：测试通用 create 方法在没有 author_id 时应因数据库约束而失败"""
        import pytest
        from sqlalchemy.exc import IntegrityError

        post_in = PostCreate(
            title="Test Base Create Fail",
            content="Content for base create fail",
            slug="test-base-create-fail",
            tags=[],
        )

        # 断言：直接调用通用的 create 创建 Post 时，
        # 由于 Post 模型强制要求 author_id 非空，
        # 而通用 create 方法不知道如何提供它，
        # 因此在 commit 阶段一定会触发数据库的 IntegrityError。
        with pytest.raises(IntegrityError):
            post_crud.create(db=session, obj_in=post_in)

    # ============ 查询测试：get ============

    def test_get_post_by_id_success(self, session: Session, sample_post: Post):
        """✅ 正常数据：测试通过 ID 获取文章"""
        retrieved_post = post_crud.get(db=session, id=sample_post.id)

        assert retrieved_post is not None
        assert retrieved_post.id == sample_post.id
        assert retrieved_post.title == sample_post.title

    def test_get_post_by_id_not_found(self, session: Session):
        """✅ 异常数据：测试获取不存在的文章"""
        non_existent_id = uuid.uuid4()
        retrieved_post = post_crud.get(db=session, id=non_existent_id)

        assert retrieved_post is None

    # ============ 查询测试：get_by_slug ============

    def test_get_by_slug_success(self, session: Session, sample_post: Post):
        """✅ 正常数据：测试通过 slug 获取文章"""
        retrieved_post = post_crud.get_by_slug(db=session, slug=sample_post.slug)

        assert retrieved_post is not None
        assert retrieved_post.id == sample_post.id
        assert retrieved_post.slug == sample_post.slug

    def test_get_by_slug_not_found(self, session: Session):
        """✅ 异常数据：测试通过不存在的 slug 获取文章"""
        non_existent_slug = "non-existent-slug"
        retrieved_post = post_crud.get_by_slug(db=session, slug=non_existent_slug)

        assert retrieved_post is None

    # ============ 查询测试：get_multi ============

    def test_get_multi_posts_success(self, session: Session, sample_user: User):
        """✅ 正常数据：测试获取多篇文章"""
        # 创建多篇文章
        for i in range(5):
            post_in = PostCreate(title=f"Post {i}", content=f"Content {i}")
            post_crud.create_with_author(
                db=session, obj_in=post_in, author_id=sample_user.id
            )

        posts = post_crud.get_multi(db=session)
        assert len(posts) == 5

    def test_get_multi_posts_with_pagination(self, session: Session, sample_user: User):
        """✅ 正常数据：测试分页获取文章"""
        # 创建多篇文章
        for i in range(5):
            post_in = PostCreate(title=f"Post {i}", content=f"Content {i}")
            post_crud.create_with_author(
                db=session, obj_in=post_in, author_id=sample_user.id
            )

        # 测试分页
        paginated_posts = post_crud.get_multi(db=session, skip=2, limit=2)
        assert len(paginated_posts) == 2
        assert paginated_posts[0].title == "Post 2"

    def test_get_multi_posts_empty(self, session: Session):
        """✅ 边界数据：测试获取文章时数据库为空"""
        posts = post_crud.get_multi(db=session)
        assert posts == []

    # ============ 查询测试：get_user_drafts ============
    def test_get_user_drafts_success(
        self, session: Session, sample_user: User, sample_posts: Post
    ):
        """✅ 正常数据：测试获取用户草稿列表

        ⚠️使用 conftest.py 中的 sample_posts 数据
        """

        # 调用 get_user_drafts(user_id)
        drafts = post_crud.get_user_drafts(db=session, user_id=sample_user.id)
        # 1. 断言只返回草稿文章
        assert any(post.status == PostStatus.DRAFT for post in drafts)
        # 2. 断言按创建时间倒序排列
        assert drafts == sorted(drafts, key=lambda x: x.created_at, reverse=True)

    def test_get_user_drafts_empty(self, session: Session, sample_user: User):
        """✅ 边界数据：测试用户无草稿时返回空列表"""
        drafts = post_crud.get_user_drafts(db=session, user_id=sample_user.id)

        assert drafts == []

    # ============ 更新测试：update ============

    def test_update_post_success(self, session: Session, sample_post: Post):
        """✅ 正常数据：测试更新文章基本信息"""
        update_data = PostUpdate(title="Updated Title", summary="Updated summary")
        updated_post = post_crud.update(
            db=session, db_obj=sample_post, obj_in=update_data
        )

        assert updated_post.title == "Updated Title"
        assert updated_post.summary == "Updated summary"
        # 确保未提供更新的字段保持原样
        assert updated_post.content == sample_post.content

    def test_update_post_with_tags(self, session: Session, sample_user: User):
        """✅ 正常数据：测试更新文章标签"""
        # 1. 创建一个包含初始标签的文章
        post_in = PostCreate(
            title="Test Post with Tags",
            content="Content here...",
            tags=["tag1", "tag2"],
        )
        sample_post = post_crud.create_with_author(
            session, obj_in=post_in, author_id=sample_user.id
        )

        # 2. 更新标签
        update_data = PostUpdate(tags=["tag2", "tag3"])

        # 3. 调用 update 方法
        updated_post = post_crud.update(
            db=session, db_obj=sample_post, obj_in=update_data
        )

        # 4. 断言更新后的文章，其关联的标签名只包含 ["tag2", "tag3"]
        updated_tags_set = {tag.name for tag in updated_post.tags}
        assert updated_tags_set == {"Tag2", "Tag3"}

    def test_update_post_clear_tags(self, session: Session, sample_user: User):
        """✅ 正常数据：测试清空文章标签"""
        # 创建带标签的文章
        post_in = PostCreate(
            title="Test Post",
            content="Content",
            tags=["tag1", "tag2"],
        )
        sample_post = post_crud.create_with_author(
            session, obj_in=post_in, author_id=sample_user.id
        )

        # 清空标签
        update_data = PostUpdate(tags=[])
        updated_post = post_crud.update(
            db=session, db_obj=sample_post, obj_in=update_data
        )

        assert len(updated_post.tags) == 0

    def test_update_post_partial_update(self, session: Session, sample_post: Post):
        """✅ 正常数据：测试部分更新（PATCH 语义）"""
        original_content = sample_post.content
        original_summary = sample_post.summary

        # 只更新标题
        update_data = PostUpdate(title="Only Title Updated")
        updated_post = post_crud.update(
            db=session, db_obj=sample_post, obj_in=update_data
        )

        assert updated_post.title == "Only Title Updated"
        assert updated_post.content == original_content  # 未更新
        assert updated_post.summary == original_summary  # 未更新

    # ============ 状态转换测试：publish ============

    def test_publish_draft_success(self, session: Session, sample_post: Post):
        """✅ 正常数据：测试发布草稿成功"""
        # 断言文章状态为draft,published_at 为 None
        assert sample_post.status == PostStatus.DRAFT
        assert sample_post.published_at is None
        # 调用 publish 方法
        published_post = post_crud.publish(db=session, post_id=sample_post.id)
        # 断言文章状态变为已发布
        assert published_post.status == PostStatus.PUBLISHED
        # 断言 published_at 已设置
        assert published_post.published_at is not None

    def test_publish_post_not_found(self, session: Session):
        """✅ 异常数据：测试发布不存在的文章"""
        non_existent_id = uuid.uuid4()
        with pytest.raises(ResourceNotFoundError):
            post_crud.publish(db=session, post_id=non_existent_id)

    def test_publish_already_published(self, session: Session, sample_post: Post):
        """✅ 异常数据：测试重复发布（幂等性）"""
        # 第一次发布， 验证成功发布
        published_post = post_crud.publish(db=session, post_id=sample_post.id)
        assert published_post.status == PostStatus.PUBLISHED
        assert published_post.published_at is not None

        # 将published_post再次发布，应该抛出 ResourceConflictError 异常
        with pytest.raises(ResourceConflictError):
            post_crud.publish(db=session, post_id=published_post.id)

        # 断言文章状态和 published_at 不变
        assert published_post.status == PostStatus.PUBLISHED
        assert published_post.published_at is not None

    def test_publish_archived_post(self, session: Session, sample_post: Post):
        """✅ 异常数据：测试发布已归档的文章"""
        # 修改sample_post文章状态为已归档
        sample_post.status = PostStatus.ARCHIVED
        session.add(sample_post)
        session.commit()

        assert sample_post.status == PostStatus.ARCHIVED

        # 调用 publish 方法，应该抛出 ResourceConflictError 异常
        with pytest.raises(ResourceConflictError):
            post_crud.publish(db=session, post_id=sample_post.id)

        # 断言文章状态不变
        assert sample_post.status == PostStatus.ARCHIVED

    # ============ 状态转换测试：archive ============

    def test_archive_published_success(self, session: Session, sample_post: Post):
        """✅ 正常数据：测试归档已发布文章成功"""
        # 将 sample_post 发布
        published_post = post_crud.publish(db=session, post_id=sample_post.id)
        assert published_post.status == PostStatus.PUBLISHED
        assert published_post.published_at is not None

        # published_post 调用 archive 方法
        archived_post = post_crud.archive(db=session, post_id=published_post.id)
        # 断言文章状态变为归档
        assert archived_post.status == PostStatus.ARCHIVED
        # 断言 published_at 不变
        assert archived_post.published_at == sample_post.published_at
        # 断言文章 ID 不变
        assert archived_post.id == sample_post.id

    def test_archive_post_not_found(self, session: Session):
        """✅ 异常数据：测试归档不存在的文章"""
        with pytest.raises(ResourceNotFoundError):
            post_crud.archive(db=session, post_id=uuid.uuid4())

    def test_archive_draft_post(self, session: Session, sample_post: Post):
        """✅ 异常数据：测试归档草稿文章（业务规则）"""
        with pytest.raises(ResourceConflictError):
            post_crud.archive(db=session, post_id=sample_post.id)

    # ============ 状态转换测试：revert_to_draft ============

    def test_revert_published_to_draft(self, session: Session, sample_post: Post):
        """✅ 正常数据：测试将已发布文章回退为草稿"""
        # 先将 sample_post 发布
        published_post = post_crud.publish(db=session, post_id=sample_post.id)
        assert published_post.status == PostStatus.PUBLISHED
        assert published_post.published_at is not None

        # published_post 调用 revert_to_draft 方法
        reverted_post = post_crud.revert_to_draft(db=session, post_id=published_post.id)
        # 断言文章状态变为草稿
        assert reverted_post.status == PostStatus.DRAFT
        # 断言 published_at 变为 None
        assert reverted_post.published_at is None
        # 断言文章 ID 不变
        assert reverted_post.id == sample_post.id

    def test_revert_archived_to_draft(self, session: Session, sample_post: Post):
        """✅ 正常数据：测试将已归档文章回退为草稿"""
        # 修改 sample_post文章状态为已归档
        sample_post.status = PostStatus.ARCHIVED
        session.add(sample_post)
        session.commit()
        assert sample_post.status == PostStatus.ARCHIVED
        # 调用 revert_to_draft 方法
        reverted_post = post_crud.revert_to_draft(db=session, post_id=sample_post.id)
        # 断言文章状态变为草稿
        assert reverted_post.status == PostStatus.DRAFT

    def test_revert_post_not_found(self, session: Session):
        """✅ 异常数据：测试回退不存在的文章"""
        with pytest.raises(ResourceNotFoundError):
            post_crud.revert_to_draft(db=session, post_id=uuid.uuid4())

    def test_revert_already_draft(self, session: Session, sample_post: Post):
        """✅ 异常数据：测试回退已是草稿的文章"""
        with pytest.raises(ResourceConflictError):
            post_crud.revert_to_draft(db=session, post_id=sample_post.id)

    # ============ 删除测试：remove ============

    def test_remove_post_success(self, session: Session, sample_post: Post):
        """✅ 正常数据：测试删除文章成功"""
        post_id = sample_post.id
        removed_post = post_crud.remove(db=session, id=post_id)

        assert removed_post is not None
        assert removed_post.id == post_id

        # 验证文章确实已被删除
        post_in_db = post_crud.get(db=session, id=post_id)
        assert post_in_db is None

    def test_remove_post_not_found(self, session: Session):
        """✅ 异常数据：测试删除不存在的文章"""
        non_existent_id = uuid.uuid4()
        removed_post = post_crud.remove(db=session, id=non_existent_id)

        assert removed_post is None

    # ============ 分页查询测试：get_paginated ============

    # ⚠️ 分页逻辑会重构到 api层，暂时不用测试
