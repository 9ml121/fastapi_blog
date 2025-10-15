"""
test_api 模块的专用 fixture

包含 API 测试所需的复杂测试数据 fixture
"""

from datetime import datetime, timedelta

import pytest
from sqlalchemy.orm import Session

from app.crud.comment import comment as comment_crud
from app.crud.post import post as post_crud
from app.crud.user import create_user
from app.models.comment import Comment
from app.models.post import Post, PostStatus
from app.models.user import User
from app.schemas.comment import CommentCreate
from app.schemas.post import PostCreate
from app.schemas.user import UserCreate


@pytest.fixture
def sample_users(session: Session, sample_user: User) -> list[User]:
    """创建额外的测试用户

    创建 4 个额外的测试用户，用于：
    - 测试用户 API 端点
    - 作为文章和评论的作者
    - 避免与 sample_user 冲突
    """
    users = [sample_user]
    user_templates = [
        {
            "username": "author_1",
            "email": "author1@example.com",
            "password": "testpassword123",
        },
        {
            "username": "author_2",
            "email": "author2@example.com",
            "password": "testpassword123",
        },
        {
            "username": "commenter_1",
            "email": "commenter1@example.com",
            "password": "testpassword123",
        },
        {
            "username": "commenter_2",
            "email": "commenter2@example.com",
            "password": "testpassword123",
        },
    ]

    for template in user_templates:
        user_data = UserCreate(**template)
        user = create_user(session, user_in=user_data)
        users.append(user)

    return users


@pytest.fixture
def sample_posts(session: Session, sample_users: list[User]) -> list[Post]:
    """创建多样化的测试文章数据

    创建 15 篇文章，包含：
    - 不同作者（使用 sample_users 中的前3个用户）
    - 不同标签（Python, FastAPI, Web开发, 教程, 实战）
    - 不同发布状态（已发布、草稿）
    - 不同发布时间（分散在最近30天内）
    - 不同标题内容（便于测试模糊搜索）
    """
    # 使用前3个用户作为文章作者
    all_authors = sample_users[:3]

    # 定义测试数据模板
    post_templates = [
        # 已发布的文章
        {
            "title": "Python 入门教程",
            "content": "Python 是一门简单易学的编程语言...",
            "summary": "Python 基础语法介绍",
            "tags": ["Python", "教程"],
            "status": PostStatus.PUBLISHED,
            "published_at_offset": -25,  # 25天前发布
        },
        {
            "title": "FastAPI 快速开发指南",
            "content": "FastAPI 是现代 Python Web 框架...",
            "summary": "FastAPI 核心特性介绍",
            "tags": ["FastAPI", "Web开发"],
            "status": PostStatus.PUBLISHED,
            "published_at_offset": -20,
        },
        {
            "title": "Web 开发最佳实践",
            "content": "现代 Web 开发需要考虑很多因素...",
            "summary": "Web 开发经验总结",
            "tags": ["Web开发", "实战"],
            "status": PostStatus.PUBLISHED,
            "published_at_offset": -15,
        },
        {
            "title": "Python 数据分析实战",
            "content": "使用 Python 进行数据分析...",
            "summary": "数据分析项目实战",
            "tags": ["Python", "实战"],
            "status": PostStatus.PUBLISHED,
            "published_at_offset": -10,
        },
        {
            "title": "FastAPI 性能优化技巧",
            "content": "如何优化 FastAPI 应用性能...",
            "summary": "性能优化经验分享",
            "tags": ["FastAPI", "性能"],
            "status": PostStatus.PUBLISHED,
            "published_at_offset": -5,
        },
        # 草稿文章
        {
            "title": "Django vs FastAPI 对比",
            "content": "Django 和 FastAPI 的详细对比...",
            "summary": "框架对比分析",
            "tags": ["Django", "FastAPI"],
            "status": PostStatus.DRAFT,
            "published_at_offset": None,
        },
        {
            "title": "Python 异步编程详解",
            "content": "深入理解 Python 异步编程...",
            "summary": "异步编程概念解析",
            "tags": ["Python", "异步"],
            "status": PostStatus.DRAFT,
            "published_at_offset": None,
        },
        {
            "title": "Web 安全防护指南",
            "content": "Web 应用安全防护措施...",
            "summary": "安全防护最佳实践",
            "tags": ["Web开发", "安全"],
            "status": PostStatus.DRAFT,
            "published_at_offset": None,
        },
        # 更多文章...
        {
            "title": "Python 机器学习入门",
            "content": "机器学习基础概念介绍...",
            "summary": "ML 入门指南",
            "tags": ["Python", "机器学习"],
            "status": PostStatus.PUBLISHED,
            "published_at_offset": -3,
        },
        {
            "title": "FastAPI 部署实战",
            "content": "如何部署 FastAPI 应用到生产环境...",
            "summary": "部署经验分享",
            "tags": ["FastAPI", "部署"],
            "status": PostStatus.PUBLISHED,
            "published_at_offset": -1,
        },
        {
            "title": "Python 代码规范指南",
            "content": "Python 代码编写规范...",
            "summary": "代码规范最佳实践",
            "tags": ["Python", "规范"],
            "status": PostStatus.DRAFT,
            "published_at_offset": None,
        },
        {
            "title": "Web 前端技术栈",
            "content": "现代前端技术栈介绍...",
            "summary": "前端技术概览",
            "tags": ["Web开发", "前端"],
            "status": PostStatus.PUBLISHED,
            "published_at_offset": -7,
        },
        {
            "title": "Python 测试驱动开发",
            "content": "TDD 开发方法论...",
            "summary": "TDD 实践指南",
            "tags": ["Python", "测试"],
            "status": PostStatus.DRAFT,
            "published_at_offset": None,
        },
        {
            "title": "FastAPI 中间件使用",
            "content": "FastAPI 中间件配置和使用...",
            "summary": "中间件使用技巧",
            "tags": ["FastAPI", "中间件"],
            "status": PostStatus.PUBLISHED,
            "published_at_offset": -12,
        },
        {
            "title": "Python 并发编程",
            "content": "Python 并发编程模式...",
            "summary": "并发编程实践",
            "tags": ["Python", "并发"],
            "status": PostStatus.DRAFT,
            "published_at_offset": None,
        },
    ]

    posts = []
    base_time = datetime.now()

    for i, template in enumerate(post_templates):
        # 轮换分配作者
        author = all_authors[i % len(all_authors)]

        # 创建文章
        post_in = PostCreate(
            title=template["title"],
            content=template["content"],
            summary=template["summary"],
            tags=template["tags"],
        )

        post = post_crud.create_with_author(
            db=session, obj_in=post_in, author_id=author.id
        )

        # 手动设置发布状态和发布时间
        post.status = template["status"]
        if template["published_at_offset"] is not None:
            post.published_at = base_time + timedelta(
                days=template["published_at_offset"]
            )

        session.add(post)
        posts.append(post)

    session.commit()
    return posts


@pytest.fixture
def sample_comments(
    session: Session, sample_posts: list[Post], sample_users: list[User]
) -> list[Comment]:
    """创建多样化的测试评论数据

    为每篇文章创建不同数量和类型的评论，包含：
    - 不同作者（使用 sample_users 中的所有用户）
    - 顶级评论和回复评论（树形结构）
    - 不同发布时间（分散在最近7天内）
    - 不同内容（便于测试模糊搜索）
    """
    # 使用所有用户作为评论作者
    all_commenters = sample_users

    # 定义评论数据模板（简化版本，避免重复）
    comment_templates = [
        # 文章1的评论
        {
            "content": "这篇文章写得很好，学到了很多！",
            "post_index": 0,
            "parent_id": None,  # 顶级评论
            "author_index": 0,
            "time_offset": -6,
        },
        {
            "content": "感谢分享，期待更多这样的教程",
            "post_index": 0,
            "parent_id": None,
            "author_index": 1,
            "time_offset": -5,
        },
        {
            "content": "我也觉得很有帮助，特别是Python部分",
            "post_index": 0,
            "parent_id": None,
            "author_index": 2,
            "time_offset": -4,
        },
        # 文章2的评论
        {
            "content": "FastAPI 确实比 Django 更现代",
            "post_index": 1,
            "parent_id": None,
            "author_index": 1,
            "time_offset": -5,
        },
        {
            "content": "同意，性能也更好",
            "post_index": 1,
            "parent_id": None,
            "author_index": 2,
            "time_offset": -4,
        },
        {
            "content": "但是学习曲线可能更陡峭",
            "post_index": 1,
            "parent_id": None,
            "author_index": 0,
            "time_offset": -3,
        },
        # 文章3的评论
        {
            "content": "Web开发最佳实践总结得很全面",
            "post_index": 2,
            "parent_id": None,
            "author_index": 2,
            "time_offset": -4,
        },
        {
            "content": "特别是安全方面的建议很有价值",
            "post_index": 2,
            "parent_id": None,
            "author_index": 0,
            "time_offset": -3,
        },
        # 文章4的评论
        {
            "content": "数据分析实战案例很实用",
            "post_index": 3,
            "parent_id": None,
            "author_index": 1,
            "time_offset": -3,
        },
        {
            "content": "Python在数据分析方面确实强大",
            "post_index": 3,
            "parent_id": None,
            "author_index": 2,
            "time_offset": -2,
        },
        # 文章5的评论
        {
            "content": "性能优化技巧很实用",
            "post_index": 4,
            "parent_id": None,
            "author_index": 0,
            "time_offset": -2,
        },
        {
            "content": "特别是缓存策略部分",
            "post_index": 4,
            "parent_id": None,
            "author_index": 1,
            "time_offset": -1,
        },
        # 添加一些回复评论来测试树形结构
        {
            "content": "是的，Python确实很实用",
            "post_index": 0,
            "parent_id": "dynamic",  # 动态引用第3条评论
            "author_index": 0,
            "time_offset": -3,
        },
        {
            "content": "确实需要一些时间适应",
            "post_index": 1,
            "parent_id": "dynamic",  # 动态引用第6条评论
            "author_index": 1,
            "time_offset": -2,
        },
    ]

    comments = []
    base_time = datetime.now()

    for i, template in enumerate(comment_templates):
        # 获取对应的文章和作者
        post = sample_posts[template["post_index"]]
        author = all_commenters[template["author_index"]]

        # 处理动态 parent_id 引用
        parent_id = template["parent_id"]
        if parent_id == "dynamic":
            if i == 13:  # "是的，Python确实很实用" 回复第3条评论
                parent_id = comments[2].id if len(comments) > 2 else None
            elif i == 14:  # "确实需要一些时间适应" 回复第6条评论
                parent_id = comments[5].id if len(comments) > 5 else None
            else:
                parent_id = None

        # 创建评论
        comment_in = CommentCreate(
            content=template["content"],
            parent_id=parent_id,
        )

        comment = comment_crud.create_with_author(
            db=session,
            obj_in=comment_in,
            author_id=author.id,
            post_id=post.id,
        )

        # 手动设置发布时间
        comment.created_at = base_time + timedelta(days=template["time_offset"])

        session.add(comment)
        comments.append(comment)

    session.commit()
    return comments
