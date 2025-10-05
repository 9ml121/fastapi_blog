"""
测试数据库模型操作

验证所有模型的 CRUD 操作、关系映射和业务方法是否正常工作。
这是在真实数据库上进行的集成测试。

使用方法：
    uv run python scripts/test_models.py
"""

from datetime import UTC, datetime

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import Comment, Post, PostStatus, PostView, Tag, User, UserRole

# 创建数据库引擎
engine = create_engine(settings.DATABASE_URL, echo=False)


def print_section(title: str) -> None:
    """打印分隔线"""
    print(f"\n{'=' * 80}")
    print(f"  {title}")
    print("=" * 80)


def test_user_crud() -> User:
    """测试 User 模型的 CRUD 操作"""
    print_section("1. 测试 User 模型 CRUD")

    with Session(engine) as session:
        # Create
        user = User(
            username="testuser",
            email="test@example.com",
            password_hash="hashed_password_123",
            nickname="测试用户",
            role=UserRole.USER,
        )
        session.add(user)
        session.commit()
        session.refresh(user)

        print(f"✅ 创建用户: {user}")
        print(f"   - ID: {user.id}")
        print(f"   - Username: {user.username}")
        print(f"   - Email: {user.email}")
        print(f"   - Nickname: {user.nickname}")
        print(f"   - Role: {user.role.value}")
        print(f"   - Created at: {user.created_at}")

        # Read
        found_user = session.query(User).filter_by(username="testuser").first()
        assert found_user is not None
        print(f"\n✅ 查询用户成功: {found_user.username}")

        # Update
        found_user.nickname = "更新后的昵称"
        session.commit()
        session.refresh(found_user)
        print(f"✅ 更新用户昵称: {found_user.nickname}")

        # 测试业务方法
        found_user.verify_email()
        session.commit()
        print(f"✅ 验证邮箱: is_verified={found_user.is_verified}")

        return found_user


def test_post_crud(user: User) -> Post:
    """测试 Post 模型的 CRUD 操作"""
    print_section("2. 测试 Post 模型 CRUD 和业务方法")

    with Session(engine) as session:
        # 重新获取 user（避免 DetachedInstanceError）
        user = session.get(User, user.id)

        # Create
        post = Post(
            title="FastAPI 博客系统开发教程",
            content="# 这是文章内容\n\n详细的开发教程...",
            author_id=user.id,
            status=PostStatus.DRAFT,
        )
        session.add(post)
        session.commit()
        session.refresh(post)

        print(f"✅ 创建文章: {post.title}")
        print(f"   - ID: {post.id}")
        print(f"   - Slug: {post.slug}")
        print(f"   - Status: {post.status.value}")
        print(f"   - Author: {post.author.username}")
        print(f"   - Word count: {post.word_count}")
        print(f"   - Reading time: {post.reading_time} 分钟")

        # 测试业务方法：发布文章
        post.publish()
        session.commit()
        session.refresh(post)
        print(f"\n✅ 发布文章:")
        print(f"   - Status: {post.status.value}")
        print(f"   - Published at: {post.published_at}")
        print(f"   - Display title: {post.display_title}")

        # 测试业务方法：生成摘要
        post.set_summary_from_content(max_length=50)
        session.commit()
        print(f"✅ 生成摘要: {post.summary}")

        return post


def test_tag_relationship(post: Post) -> list[Tag]:
    """测试 Post-Tag 多对多关系"""
    print_section("3. 测试 Post-Tag 多对多关系")

    with Session(engine) as session:
        post = session.get(Post, post.id)

        # 创建标签
        tag1 = Tag(name="Python", slug="python", description="Python 编程语言")
        tag2 = Tag(name="FastAPI", slug="fastapi", description="FastAPI 框架")
        tag3 = Tag(
            name="数据库设计",
            slug=Tag.generate_slug("数据库设计"),
            description="数据库架构和设计",
        )

        session.add_all([tag1, tag2, tag3])
        session.commit()

        # 关联标签
        post.tags.extend([tag1, tag2, tag3])
        session.commit()

        print(f"✅ 为文章 '{post.title}' 添加 {len(post.tags)} 个标签:")
        for tag in post.tags:
            print(f"   - {tag.name} (slug: {tag.slug})")

        # 从标签查询文章
        session.refresh(tag1)
        print(f"\n✅ 标签 '{tag1.name}' 关联的文章:")
        for p in tag1.posts:
            print(f"   - {p.title}")

        return [tag1, tag2, tag3]


def test_comment_relationship(user: User, post: Post) -> list[Comment]:
    """测试 Comment 模型和自引用关系"""
    print_section("4. 测试 Comment 模型和自引用关系")

    with Session(engine) as session:
        user = session.get(User, user.id)
        post = session.get(Post, post.id)

        # 创建顶级评论
        comment1 = Comment(
            content="这篇文章写得太好了！", user_id=user.id, post_id=post.id
        )
        session.add(comment1)
        session.commit()
        session.refresh(comment1)

        print(f"✅ 创建顶级评论: {comment1.content}")
        print(f"   - is_top_level: {comment1.is_top_level}")

        # 创建回复评论
        reply1 = Comment(
            content="谢谢！很高兴能帮到你。",
            user_id=user.id,
            post_id=post.id,
            parent_id=comment1.id,
        )
        reply2 = Comment(
            content="期待下一篇文章！",
            user_id=user.id,
            post_id=post.id,
            parent_id=comment1.id,
        )
        session.add_all([reply1, reply2])
        session.commit()

        # 刷新获取回复
        session.refresh(comment1)
        print(f"\n✅ 评论回复关系:")
        print(f"   - 顶级评论: {comment1.content}")
        print(f"   - 回复数量: {comment1.reply_count}")
        for reply in comment1.replies:
            print(f"     └─ {reply.content}")

        # 测试业务方法
        comment1.approve()
        session.commit()
        print(f"\n✅ 审核通过: is_approved={comment1.is_approved}")

        return [comment1, reply1, reply2]


def test_post_view(user: User, post: Post) -> None:
    """测试 PostView 模型和防刷功能"""
    print_section("5. 测试 PostView 模型和防刷功能")

    with Session(engine) as session:
        user = session.get(User, user.id)
        post = session.get(Post, post.id)

        # 第一次浏览
        is_dup = PostView.is_duplicate(session, user.id, post.id)
        print(f"✅ 首次浏览检测: is_duplicate={is_dup}")

        if not is_dup:
            view1 = PostView(
                user_id=user.id,
                post_id=post.id,
                ip_address="192.168.1.100",
                user_agent="Mozilla/5.0",
            )
            session.add(view1)
            session.commit()
            print(f"✅ 创建浏览记录: {view1}")

        # 5分钟内再次浏览（应该被识别为重复）
        is_dup = PostView.is_duplicate(session, user.id, post.id)
        print(f"✅ 5分钟内再次浏览: is_duplicate={is_dup}")

        # 创建匿名浏览
        anon_view = PostView(user_id=None, post_id=post.id, ip_address="192.168.1.200")
        session.add(anon_view)
        session.commit()
        print(f"✅ 创建匿名浏览记录: is_anonymous={anon_view.is_anonymous}")

        # 查询文章的浏览记录
        session.refresh(post)
        print(f"\n✅ 文章总浏览记录: {len(post.post_views)} 条")
        for view in post.post_views:
            user_info = f"user_id={view.user_id}" if view.user_id else "anonymous"
            print(f"   - {user_info}, viewed_at={view.viewed_at}, ip={view.ip_address}")


def test_cascade_delete(user: User, post: Post) -> None:
    """测试级联删除"""
    print_section("6. 测试级联删除")

    with Session(engine) as session:
        post = session.get(Post, post.id)
        post_id = post.id
        post_title = post.title

        # 记录删除前的数据
        comment_count = len(post.comments)
        tag_count = len(post.tags)
        view_count = len(post.post_views)

        print(f"删除前统计:")
        print(f"   - 文章: {post_title}")
        print(f"   - 评论数: {comment_count}")
        print(f"   - 标签数: {tag_count}")
        print(f"   - 浏览数: {view_count}")

        # 删除文章（应该级联删除评论、浏览记录、标签关联）
        session.delete(post)
        session.commit()

        # 验证级联删除
        deleted_post = session.get(Post, post_id)
        print(f"\n✅ 文章已删除: {deleted_post is None}")

        # 验证评论被级联删除
        remaining_comments = (
            session.query(Comment).filter_by(post_id=post_id).count()
        )
        print(f"✅ 评论已级联删除: {remaining_comments} 条剩余")

        # 验证浏览记录被级联删除
        remaining_views = session.query(PostView).filter_by(post_id=post_id).count()
        print(f"✅ 浏览记录已级联删除: {remaining_views} 条剩余")


def cleanup_test_data(user: User) -> None:
    """清理测试数据"""
    print_section("7. 清理测试数据")

    with Session(engine) as session:
        user = session.get(User, user.id)
        if user:
            user_id = user.id
            username = user.username

            # 删除用户（级联删除所有关联数据）
            session.delete(user)
            session.commit()

            print(f"✅ 删除用户: {username} (ID: {user_id})")
            print(f"✅ 所有关联数据已级联删除")

        # 删除标签
        deleted_tags = session.query(Tag).delete()
        session.commit()
        print(f"✅ 删除标签: {deleted_tags} 个")


def main() -> None:
    """主测试流程"""
    print("\n" + "=" * 80)
    print("  🚀 开始测试数据库模型操作")
    print("=" * 80)

    try:
        # 1. 测试 User CRUD
        user = test_user_crud()

        # 2. 测试 Post CRUD 和业务方法
        post = test_post_crud(user)

        # 3. 测试 Post-Tag 多对多关系
        tags = test_tag_relationship(post)

        # 4. 测试 Comment 自引用关系
        comments = test_comment_relationship(user, post)

        # 5. 测试 PostView 防刷功能
        test_post_view(user, post)

        # 6. 测试级联删除
        test_cascade_delete(user, post)

        # 7. 清理测试数据
        cleanup_test_data(user)

        print_section("✅ 所有测试通过！")
        print("\n🎉 数据库模型操作正常！可以开始 API 开发了。\n")

    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback

        traceback.print_exc()
        raise


if __name__ == "__main__":
    main()
