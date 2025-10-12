"""
tests/test_crud/test_post.py

测试 Post CRUD 操作
"""

from sqlalchemy.orm import Session

from app.crud.post import post as post_crud
from app.models.post import Post
from app.models.tag import Tag
from app.models.user import User
from app.schemas.post import PostCreate, PostUpdate


class TestPostCRUD:
    """测试 Post CRUD 的所有方法"""

    def test_generic_create_fails_without_author(self, session: Session):
        """测试：通用 create 方法在没有 author_id 时应因数据库约束而失败"""
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
        # 这个测试确保了我们的数据模型约束是有效的。
        with pytest.raises(IntegrityError):
            post_crud.create(db=session, obj_in=post_in)

    def test_create_post_with_author(self, session: Session, sample_user: User):
        """
        测试 create_with_author 方法，包含标签的 Get or Create 逻辑
        """
        # 1. 准备前置数据：一个已存在的标签
        existing_tag = Tag(name="existing_tag", slug="existing-tag")
        session.add(existing_tag)
        session.commit()

        # 2. 准备输入数据，包含一个已存在的和一个全新的标签（⚠️ 注意：没有 slug）
        post_in = PostCreate(
            title="Test Post with Tags",
            content="Content here...",
            tags=["existing_tag", "new_tag"],
        )

        # 3. 调用被测试的函数
        # 注意：这个测试能否通过，完全取决于你在 crud/post.py 中的实现
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
        assert new_tag_from_db.slug is not None  # 验证 slug 是否也已生成

    def test_get_post_by_id(self, session: Session, sample_post):
        """测试继承自 CRUDBase 的 get 方法"""
        retrieved_post = post_crud.get(db=session, id=sample_post.id)
        assert retrieved_post is not None
        assert retrieved_post.id == sample_post.id
        assert retrieved_post.title == sample_post.title

    def test_get_by_slug(self, session: Session, sample_post):
        """测试 CRUDPost 中自定义的 get_by_slug 方法"""
        retrieved_post = post_crud.get_by_slug(db=session, slug=sample_post.slug)
        assert retrieved_post is not None
        assert retrieved_post.id == sample_post.id
        assert retrieved_post.slug == sample_post.slug

    def test_get_multi_posts(self, session: Session, sample_user: User):
        """测试继承自 CRUDBase 的 get_multi 方法"""
        # 创建多篇文章
        for i in range(5):
            post_in = PostCreate(title=f"Post {i}", content=f"Content {i}")
            post_crud.create_with_author(
                db=session, obj_in=post_in, author_id=sample_user.id
            )

        posts = post_crud.get_multi(db=session)
        assert len(posts) == 5

        # 测试分页
        paginated_posts = post_crud.get_multi(db=session, skip=2, limit=2)
        assert len(paginated_posts) == 2
        assert paginated_posts[0].title == "Post 2"

    def test_update_post(self, session: Session, sample_post: Post):
        """测试继承自 CRUDBase 的 update 方法"""
        update_data = PostUpdate(title="Updated Title", summary="Updated summary")
        updated_post = post_crud.update(
            db=session, db_obj=sample_post, obj_in=update_data
        )

        assert updated_post.title == "Updated Title"
        assert updated_post.summary == "Updated summary"
        # 确保未提供更新的字段保持原样
        assert updated_post.content == sample_post.content

    def test_update_post_with_tags(self, session: Session, sample_user: User):
        """测试修改了标签的 update 方法"""
        # 1. 创建一个包含初始标签（例如 ["tag1", "tag2"]）的文章。
        post_in = PostCreate(
            title="Test Post with Tags",
            content="Content here...",
            tags=["tag1", "tag2"],
        )
        sample_post = post_crud.create_with_author(
            session, obj_in=post_in, author_id=sample_user.id
        )

        # 2. 调用 crud.post.update 方法，传入新的标签数据（例如 ["tag2", "tag3"]）。
        update_data = PostUpdate(tags=["tag2", "tag3"])

        # 3. 调用 post 重写的 update 方法
        updated_post = post_crud.update(
            db=session, db_obj=sample_post, obj_in=update_data
        )

        # 4. 断言更新后的文章，其关联的标签名只包含 ["tag2", "tag3"]。
        updated_tags_set = {tag.name for tag in updated_post.tags}
        assert updated_tags_set == {"Tag2", "Tag3"}

    def test_remove_post(self, session: Session, sample_post):
        """测试继承自 CRUDBase 的 remove 方法"""
        post_id = sample_post.id
        removed_post = post_crud.remove(db=session, id=post_id)

        assert removed_post is not None
        assert removed_post.id == post_id

        # 验证文章确实已被删除
        post_in_db = post_crud.get(db=session, id=post_id)
        assert post_in_db is None
