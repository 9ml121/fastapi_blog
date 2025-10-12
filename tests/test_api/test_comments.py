"""
测试评论管理 API 端点

测试覆盖:
- POST /posts/{post_id}/comments - 创建评论（顶级 + 回复）
- GET /posts/{post_id}/comments - 获取评论列表（树形结构）
- DELETE /posts/{post_id}/comments/{comment_id} - 删除评论
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.security import create_access_token
from app.crud.comment import comment as comment_crud
from app.crud.post import post as post_crud
from app.models.comment import Comment
from app.models.post import Post
from app.models.user import User
from app.schemas.comment import CommentCreate
from app.schemas.post import PostCreate

# ============================================
# Fixtures - 测试数据
# ============================================


@pytest.fixture
def sample_post(session: Session, sample_user: User) -> Post:
    """创建一篇测试文章"""
    post = post_crud.create_with_author(
        db=session,
        obj_in=PostCreate(
            title="FastAPI 评论系统",
            content="实现一个功能完整的评论系统",
            tags=["FastAPI", "评论"],
        ),
        author_id=sample_user.id,
    )
    return post


@pytest.fixture
def sample_comments(
    session: Session, sample_post: Post, sample_user: User
) -> list[Comment]:
    """创建测试评论数据（树形结构）

    结构:
    - 评论1 (顶级)
      - 评论2 (回复评论1)
      - 评论3 (回复评论1)
    - 评论4 (顶级)
    """
    comments = []

    # 顶级评论1
    comment1 = comment_crud.create_with_author(
        db=session,
        obj_in=CommentCreate(content="这篇文章写得很好！"),
        author_id=sample_user.id,
        post_id=sample_post.id,
    )
    comments.append(comment1)

    # 回复评论1
    comment2 = comment_crud.create_with_author(
        db=session,
        obj_in=CommentCreate(content="同意楼上", parent_id=comment1.id),
        author_id=sample_user.id,
        post_id=sample_post.id,
    )
    comments.append(comment2)

    comment3 = comment_crud.create_with_author(
        db=session,
        obj_in=CommentCreate(content="@楼上 感谢支持", parent_id=comment1.id),
        author_id=sample_user.id,
        post_id=sample_post.id,
    )
    comments.append(comment3)

    # 顶级评论4
    comment4 = comment_crud.create_with_author(
        db=session,
        obj_in=CommentCreate(content="请问如何部署？"),
        author_id=sample_user.id,
        post_id=sample_post.id,
    )
    comments.append(comment4)

    return comments


# ============================================
# 测试类：POST /posts/{post_id}/comments - 创建评论
# ============================================


class TestCreateComment:
    """测试创建评论 API"""

    def test_create_top_level_comment_success(
        self,
        client: TestClient,
        sample_post: Post,
        sample_user: User,
        auth_headers: dict,
    ):
        """测试成功创建顶级评论"""
        response = client.post(
            f"/api/v1/posts/{sample_post.id}/comments",
            headers=auth_headers,
            json={"content": "这是一条顶级评论"},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        # 验证返回数据
        assert data["content"] == "这是一条顶级评论"
        assert "id" in data
        assert "author" in data
        assert data["author"]["username"] == sample_user.username
        assert "created_at" in data

    def test_create_reply_comment_success(
        self,
        client: TestClient,
        sample_post: Post,
        sample_comments: list[Comment],
        auth_headers: dict,
    ):
        """测试成功创建回复评论"""
        parent_comment = sample_comments[0]

        response = client.post(
            f"/api/v1/posts/{sample_post.id}/comments",
            headers=auth_headers,
            json={
                "content": "回复第一条评论",
                "parent_id": str(parent_comment.id),
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()

        assert data["content"] == "回复第一条评论"

    def test_create_comment_post_not_found(
        self,
        client: TestClient,
        auth_headers: dict,
    ):
        """测试文章不存在 - 应返回 404"""
        fake_post_id = "00000000-0000-0000-0000-000000000000"

        response = client.post(
            f"/api/v1/posts/{fake_post_id}/comments",
            headers=auth_headers,
            json={"content": "评论内容"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "文章不存在"

    def test_create_comment_parent_not_found(
        self,
        client: TestClient,
        sample_post: Post,
        auth_headers: dict,
    ):
        """测试父评论不存在 - 应返回 404"""
        fake_parent_id = "00000000-0000-0000-0000-000000000000"

        response = client.post(
            f"/api/v1/posts/{sample_post.id}/comments",
            headers=auth_headers,
            json={
                "content": "回复评论",
                "parent_id": fake_parent_id,
            },
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "父评论不存在"

    def test_create_comment_cross_post_reply(
        self,
        client: TestClient,
        session: Session,
        sample_user: User,
        sample_post: Post,
        sample_comments: list[Comment],
        auth_headers: dict,
    ):
        """测试跨文章回复 - 应返回 400

        场景：尝试在文章B下回复文章A的评论
        """
        # 创建第二篇文章
        post2 = post_crud.create_with_author(
            db=session,
            obj_in=PostCreate(
                title="另一篇文章",
                content="不同的文章",
            ),
            author_id=sample_user.id,
        )

        # 尝试在文章2下回复文章1的评论
        parent_from_post1 = sample_comments[0]

        response = client.post(
            f"/api/v1/posts/{post2.id}/comments",  # 文章2
            headers=auth_headers,
            json={
                "content": "跨文章回复",
                "parent_id": str(parent_from_post1.id),  # 文章1的评论
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.json()["detail"] == "父评论不属于该文章"

    def test_create_comment_unauthorized(
        self,
        client: TestClient,
        sample_post: Post,
    ):
        """测试未登录创建评论 - 应返回 401"""
        response = client.post(
            f"/api/v1/posts/{sample_post.id}/comments",
            # 不提供 auth_headers
            json={"content": "未登录的评论"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


# ============================================
# 测试类：GET /posts/{post_id}/comments - 获取评论列表
# ============================================


class TestGetComments:
    """测试获取评论列表 API"""

    def test_get_comments_empty(
        self,
        client: TestClient,
        sample_post: Post,
    ):
        """测试获取空评论列表"""
        response = client.get(f"/api/v1/posts/{sample_post.id}/comments")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_comments_tree_structure(
        self,
        client: TestClient,
        sample_post: Post,
        sample_comments: list[Comment],
    ):
        """测试评论树形结构"""
        response = client.get(f"/api/v1/posts/{sample_post.id}/comments")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 应该只返回 2 个顶级评论（评论1 和 评论4）
        assert len(data) == 2

        # 提取所有顶级评论的内容（不依赖顺序）
        top_level_contents = {comment["content"] for comment in data}
        assert "这篇文章写得很好！" in top_level_contents
        assert "请问如何部署？" in top_level_contents

        # 找到有回复的评论（评论1）
        comment_with_replies = next(
            c for c in data if c["content"] == "这篇文章写得很好！"
        )
        assert len(comment_with_replies["replies"]) == 2

        # 验证回复的内容
        replies = comment_with_replies["replies"]
        reply_contents = {r["content"] for r in replies}
        assert "同意楼上" in reply_contents
        assert "@楼上 感谢支持" in reply_contents

        # 验证回复也可以有回复（递归结构）
        for reply in replies:
            assert "replies" in reply

        # 找到没有回复的评论（评论4）
        comment_without_replies = next(
            c for c in data if c["content"] == "请问如何部署？"
        )
        assert len(comment_without_replies["replies"]) == 0

    def test_get_comments_post_not_found(
        self,
        client: TestClient,
    ):
        """测试文章不存在 - 应返回 404"""
        fake_post_id = "00000000-0000-0000-0000-000000000000"

        response = client.get(f"/api/v1/posts/{fake_post_id}/comments")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "文章不存在"


# ============================================
# 测试类：DELETE /posts/{post_id}/comments/{comment_id} - 删除评论
# ============================================


class TestDeleteComment:
    """测试删除评论 API"""

    def test_delete_comment_success(
        self,
        client: TestClient,
        sample_post: Post,
        sample_comments: list[Comment],
        auth_headers: dict,
    ):
        """测试成功删除自己的评论"""
        comment_to_delete = sample_comments[0]

        response = client.delete(
            f"/api/v1/posts/{sample_post.id}/comments/{comment_to_delete.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT

    def test_delete_comment_cascade(
        self,
        client: TestClient,
        session: Session,
        sample_post: Post,
        sample_comments: list[Comment],
        auth_headers: dict,
    ):
        """测试删除评论会级联删除子评论"""
        # 删除评论1（有 2 个子评论）
        comment_to_delete = sample_comments[0]
        response = client.delete(
            f"/api/v1/posts/{sample_post.id}/comments/{comment_to_delete.id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_204_NO_CONTENT
        # 2. 查询数据库验证评论1、评论2、评论3 都不存在
        assert not comment_crud.get(session, id=comment_to_delete.id)
        assert not comment_crud.get(session, id=sample_comments[1].id)
        assert not comment_crud.get(session, id=sample_comments[2].id)
        # 3. 验证评论4 仍然存在（不应该被删除）
        assert comment_crud.get(session, id=sample_comments[3].id)

    def test_delete_comment_not_found(
        self,
        client: TestClient,
        sample_post: Post,
        auth_headers: dict,
    ):
        """测试删除不存在的评论 - 应返回 404"""
        fake_comment_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(
            f"/api/v1/posts/{sample_post.id}/comments/{fake_comment_id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "评论不存在"

    def test_delete_comment_wrong_post(
        self,
        client: TestClient,
        session: Session,
        sample_user: User,
        sample_post: Post,
        sample_comments: list[Comment],
        auth_headers: dict,
    ):
        """测试评论不属于该文章 - 应返回 404"""
        # 创建第二篇文章
        other_post = post_crud.create_with_author(
            db=session,
            obj_in=PostCreate(
                title="测试文章2",
                content="这是测试文章2的内容",
            ),
            author_id=sample_user.id,
        )

        # 尝试用文章2的ID删除文章1的评论
        response = client.delete(
            f"/api/v1/posts/{other_post.id}/comments/{sample_comments[0].id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["detail"] == "评论不属于该文章"

    def test_delete_comment_forbidden(
        self,
        client: TestClient,
        session: Session,
        sample_post: Post,
        sample_comments: list[Comment],
    ):
        """测试删除他人评论 - 应返回 403"""
        from app.crud.user import create_user
        from app.schemas.user import UserCreate

        user_in = UserCreate(
            username="other_user",
            email="other@example.com",
            password="Password123!",
        )
        other_user = create_user(db=session, user_in=user_in)
        token = create_access_token(data={"sub": str(other_user.id)})
        auth_headers = {"Authorization": f"Bearer {token}"}

        response = client.delete(
            f"/api/v1/posts/{sample_post.id}/comments/{sample_comments[0].id}",
            headers=auth_headers,
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN
        assert response.json()["detail"] == "无权删除他人评论"

    def test_delete_comment_unauthorized(
        self,
        client: TestClient,
        sample_post: Post,
        sample_comments: list[Comment],
    ):
        """测试未登录删除评论 - 应返回 401"""
        response = client.delete(
            f"/api/v1/posts/{sample_post.id}/comments/{sample_comments[0].id}",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["detail"] == "Not authenticated"
