"""
Tag 模型测试套件

测试覆盖：
1. 基础 CRUD 操作
2. 数据库约束（唯一性、NOT NULL）
3. 多对多关系（Tag-Post）
4. 业务方法（normalize_name, generate_slug）
5. 计算属性（post_count）
6. 边界情况（重复标签、空值等）
"""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.post import Post
from app.models.tag import Tag
from app.models.user import User


class TestTagModel:
    """Tag 模型测试类"""

    # ============ 基础 CRUD 操作测试 ============

    def test_create_tag(self, session: Session):
        """测试创建标签"""
        tag = Tag(
            name="Python",
            slug="python",
            description="Python 编程语言相关内容",
        )
        session.add(tag)
        session.commit()
        session.refresh(tag)

        assert tag.id is not None
        assert tag.name == "Python"
        assert tag.slug == "python"
        assert tag.description == "Python 编程语言相关内容"
        assert tag.created_at is not None
        assert tag.updated_at is not None

    def test_read_tag(self, session: Session):
        """测试查询标签"""
        tag = Tag(name="FastAPI", slug="fastapi")
        session.add(tag)
        session.commit()

        # 通过 ID 查询
        retrieved_tag = session.query(Tag).filter_by(id=tag.id).first()
        assert retrieved_tag is not None
        assert retrieved_tag.name == "FastAPI"

        # 通过 slug 查询（常见场景）
        tag_by_slug = session.query(Tag).filter_by(slug="fastapi").first()
        assert tag_by_slug is not None
        assert tag_by_slug.id == tag.id

    def test_update_tag(self, session: Session):
        """测试更新标签"""
        tag = Tag(name="Web", slug="web")
        session.add(tag)
        session.commit()

        # 更新描述
        tag.description = "Web 开发相关技术"
        session.commit()
        session.refresh(tag)

        assert tag.description == "Web 开发相关技术"

    def test_delete_tag(self, session: Session):
        """测试删除标签（硬删除）"""
        tag = Tag(name="Temp", slug="temp")
        session.add(tag)
        session.commit()
        tag_id = tag.id

        # 硬删除
        session.delete(tag)
        session.commit()

        # 验证已删除
        deleted_tag = session.query(Tag).filter_by(id=tag_id).first()
        assert deleted_tag is None

    # ============ 数据库约束测试 ============

    def test_tag_name_required(self, session: Session):
        """测试标签名称不能为空"""
        with pytest.raises(IntegrityError):
            tag = Tag(name=None, slug="test")  # 违反 NOT NULL 约束
            session.add(tag)
            session.commit()

    def test_tag_slug_required(self, session: Session):
        """测试 slug 不能为空"""
        with pytest.raises(IntegrityError):
            tag = Tag(name="Test", slug=None)  # 违反 NOT NULL 约束
            session.add(tag)
            session.commit()

    def test_tag_name_unique(self, session: Session):
        """测试标签名称唯一性约束"""
        tag1 = Tag(name="Python", slug="python")
        session.add(tag1)
        session.commit()

        # 尝试创建相同名称的标签
        with pytest.raises(IntegrityError):
            tag2 = Tag(name="Python", slug="python2")  # name 重复
            session.add(tag2)
            session.commit()

    def test_tag_slug_unique(self, session: Session):
        """测试 slug 唯一性约束"""
        tag1 = Tag(name="Python", slug="python")
        session.add(tag1)
        session.commit()

        # 尝试创建相同 slug 的标签
        with pytest.raises(IntegrityError):
            tag2 = Tag(name="Python Lang", slug="python")  # slug 重复
            session.add(tag2)
            session.commit()

    # ============ 多对多关系测试（Tag ↔ Post）============

    def test_tag_posts_relationship(self, session: Session, sample_post_data):
        """测试 Tag -> Post 多对多关系"""
        # 1. 创建一个标签
        tag = Tag(name="TestTag", slug="test-tag")
        session.add(tag)
        session.commit()
        # 2. 使用工厂函数创建 2 篇文章
        post1 = Post(**sample_post_data())
        post2 = Post(**sample_post_data())
        # 3. 将标签添加到两篇文章：post1.tags.append(tag), post2.tags.append(tag)
        post1.tags.append(tag)
        post2.tags.append(tag)
        # 4. session.commit() 和 session.refresh(tag)
        session.add_all([post1, post2])
        session.commit()
        session.refresh(tag)
        # 5. 验证 len(tag.posts) == 2
        assert len(tag.posts) == 2
        # 6. 验证 tag.posts 包含这两篇文章
        assert post1 in tag.posts
        assert post2 in tag.posts

    def test_post_tags_relationship(self, session: Session, sample_user: User, sample_post: Post):
        """测试 Post -> Tag 多对多关系"""
        # TODO(human): 实现测试 - 一篇文章关联多个标签
        # 提示：
        # 1. 创建 3 个标签（如 Python, FastAPI, Web）
        tag1 = Tag(name="Python", slug="Python")
        tag2 = Tag(name="FastAPI", slug="FastAPI")
        tag3 = Tag(name="Web", slug="Web")
        # 2. 将标签添加到 sample_post：sample_post.tags.append(tag1), ...
        sample_post.tags.extend([tag1, tag2, tag3])
        # 3. session.commit() 和 session.refresh(sample_post)
        session.add_all([tag1, tag2, tag3])
        session.commit()
        session.refresh(sample_post)
        # 4. 验证 len(sample_post.tags) == 3
        assert len(sample_post.tags) == 3
        # 5. 验证所有标签都在 sample_post.tags 中
        assert tag1 in sample_post.tags
        assert tag2 in sample_post.tags
        assert tag3 in sample_post.tags

    def test_remove_tag_from_post(self, session: Session, sample_user: User, sample_post: Post):
        """测试从文章中移除标签"""
        # TODO(human): 实现测试 - 移除文章的标签
        # 提示：
        # 1. 创建 2 个标签并添加到 sample_post
        tag1 = Tag(name="ToDelete", slug="to-delete")
        tag2 = Tag(name="ToKeep", slug="to-keep")
        sample_post.tags.extend([tag1, tag2])
        # 2. session.commit()
        session.add_all([tag1, tag2])
        session.commit()
        session.refresh(sample_post)

        # 3. 从文章中移除一个标签：sample_post.tags.remove(tag1)
        sample_post.tags.remove(tag1)
        # 4. session.commit() 和 session.refresh(sample_post)
        session.commit()
        session.refresh(sample_post)
        # 5. 验证 len(sample_post.tags) == 1
        assert len(sample_post.tags) == 1
        # 6. 验证被移除的标签不在 sample_post.tags 中
        assert tag1 not in sample_post.tags

        # 7. 验证标签本身仍存在于数据库中（未被删除）
        assert tag1 in session.query(Tag).all()
        assert tag2 in session.query(Tag).all()

    def test_delete_tag_removes_associations(self, session: Session, sample_user: User, sample_post: Post):
        """测试删除标签时自动删除关联关系"""
        tag = Tag(name="ToDelete", slug="to-delete")
        session.add(tag)
        sample_post.tags.append(tag)
        session.commit()

        # 验证关联存在
        session.refresh(sample_post)
        assert len(sample_post.tags) == 1

        # 删除标签
        session.delete(tag)
        session.commit()

        # 验证关联已删除，但文章仍存在
        session.refresh(sample_post)
        assert len(sample_post.tags) == 0
        assert session.query(Post).filter_by(id=sample_post.id).first() is not None

    def test_delete_post_removes_associations(self, session: Session, sample_post: Post):
        """测试删除文章时自动删除关联关系"""
        # TODO(human): 实现测试 - 删除文章时自动删除关联
        # 提示：
        # 1. 创建一个标签和一篇文章
        tag = Tag(name="ToDelete", slug="to-delete")
        # 2. 建立关联：post.tags.append(tag)
        sample_post.tags.append(tag)
        # 3. session.commit()
        session.add_all([tag, sample_post])
        session.commit()

        # 4. 删除文章：session.delete(post)
        session.delete(sample_post)

        # 5. session.commit() 和 session.refresh(tag)
        session.commit()
        session.refresh(tag)
        # 6. 验证 len(tag.posts) == 0（关联已删除）
        assert len(tag.posts) == 0

        # 7. 验证标签仍存在于数据库中（未被级联删除）
        assert tag in session.query(Tag).all()

    # ============ 业务方法测试 ============

    def test_normalize_name(self):
        """测试标签名称标准化"""
        # 测试去除多余空格
        assert Tag.normalize_name("  python   programming  ") == "Python programming"

        # 测试首字母大写
        assert Tag.normalize_name("web development") == "Web development"

        # 测试单个单词
        assert Tag.normalize_name("python") == "Python"

        # 测试已标准化的输入
        assert Tag.normalize_name("FastAPI") == "Fastapi"

    def test_generate_slug(self):
        """测试 slug 生成"""
        # TODO(human): 实现测试 - 测试 slug 生成功能
        # 提示：测试以下场景
        # 1. 英文标签：Tag.generate_slug("Python Programming") == "python-programming"
        assert Tag.generate_slug("Python Programming") == "python-programming"
        # 2. 中文标签：Tag.generate_slug("Web开发") == "web开发"
        assert Tag.generate_slug("Web开发") == "web开发"
        # 3. 混合标签：Tag.generate_slug("Vue3 & React") == "vue3-react"
        assert Tag.generate_slug("Vue3 & React") == "vue3-react"
        # 4. 多个空格：Tag.generate_slug("A  B  C") == "a-b-c"
        assert Tag.generate_slug("A  B  C") == "a-b-c"
        # 5. 特殊字符：Tag.generate_slug("C++") == "c"
        assert Tag.generate_slug("C++") == "c"

    # ============ 计算属性测试 ============

    def test_post_count_property(self, session: Session, sample_post_data):
        """测试 post_count 属性"""
        # TODO(human): 实现测试 - 测试文章数量统计
        # 提示：
        # 1. 创建一个标签
        tag = Tag(name="TestTag", slug="test-tag")
        session.add(tag)
        session.commit()
        # 2. 初始 tag.post_count 应该为 0
        assert tag.post_count == 0
        # 3. 创建 3 篇文章并添加该标签
        post1 = Post(**sample_post_data())
        post2 = Post(**sample_post_data())
        post3 = Post(**sample_post_data())
        post1.tags.append(tag)
        post2.tags.append(tag)
        post3.tags.append(tag)
        # 4. session.commit() 和 session.refresh(tag)
        session.add_all([post1, post2, post3])
        session.commit()
        session.refresh(tag)
        # 5. 验证 tag.post_count == 3
        assert tag.post_count == 3

    # ============ 字符串表示测试 ============

    def test_tag_repr(self, session: Session):
        """测试 __repr__ 方法"""
        tag = Tag(name="Python", slug="python")
        session.add(tag)
        session.commit()
        session.refresh(tag)

        repr_str = repr(tag)
        assert "Tag" in repr_str
        assert "Python" in repr_str
        assert "python" in repr_str
        assert str(tag.id) in repr_str

    # ============ 边界情况测试 ============

    def test_tag_with_empty_description(self, session: Session):
        """测试空描述的标签"""
        tag = Tag(name="Test", slug="test", description=None)
        session.add(tag)
        session.commit()

        assert tag.description is None

    def test_tag_with_very_long_name(self, session: Session):
        """测试超长标签名称"""
        long_name = "A" * 50  # 正好 50 字符（字段限制）
        tag = Tag(name=long_name, slug="long-tag")
        session.add(tag)
        session.commit()

        assert len(tag.name) == 50

    def test_tag_name_case_sensitivity(self, session: Session):
        """测试标签名称区分大小写"""
        tag1 = Tag(name="Python", slug="python-1")
        tag2 = Tag(name="python", slug="python-2")

        session.add_all([tag1, tag2])
        session.commit()

        # 数据库应该将它们视为不同的标签（区分大小写）
        tags = session.query(Tag).filter(Tag.name.in_(["Python", "python"])).all()
        assert len(tags) == 2
