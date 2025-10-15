"""
测试评论管理 API 端点

测试覆盖:
- POST /posts/{post_id}/comments - 创建评论（顶级 + 回复）
- GET /posts/{post_id}/comments - 获取评论列表（树形结构）
- DELETE /posts/{post_id}/comments/{comment_id} - 删除评论
"""

from pprint import pprint  # noqa: F401

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
    - 评论5 (顶级)
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

    # 顶级评论5
    comment5 = comment_crud.create_with_author(
        db=session,
        obj_in=CommentCreate(content="可以用 Docker 部署"),
        author_id=sample_user.id,
        post_id=sample_post.id,
    )
    comments.append(comment5)

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
        """✅ 正常数据：测试成功创建顶级评论"""
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
        """✅ 正常数据：测试成功创建回复评论"""
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
        """✅ 异常数据：测试文章不存在 - 应返回 404"""
        fake_post_id = "00000000-0000-0000-0000-000000000000"

        response = client.post(
            f"/api/v1/posts/{fake_post_id}/comments",
            headers=auth_headers,
            json={"content": "评论内容"},
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["error"]["message"] == "文章不存在"

    def test_create_comment_parent_not_found(
        self,
        client: TestClient,
        sample_post: Post,
        auth_headers: dict,
    ):
        """✅ 异常数据：测试父评论不存在 - 应返回 404"""
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
        assert response.json()["error"]["message"] == "父评论不存在"

    def test_create_comment_cross_post_reply(
        self,
        client: TestClient,
        session: Session,
        sample_user: User,
        sample_post: Post,
        sample_comments: list[Comment],
        auth_headers: dict,
    ):
        """✅ 异常数据：测试跨文章回复 - 应返回 400

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
        assert response.json()["error"]["message"] == "父评论不属于该文章"

    def test_create_comment_unauthorized(
        self,
        client: TestClient,
        sample_post: Post,
    ):
        """✅ 异常数据：测试未登录创建评论 - 应返回 401"""
        response = client.post(
            f"/api/v1/posts/{sample_post.id}/comments",
            # 不提供 auth_headers
            json={"content": "未登录的评论"},
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_create_comment_content_too_long(
        self,
        client: TestClient,
        sample_post: Post,
        auth_headers: dict,
    ):
        """✅ 极端数据：测试超长评论内容 - 应返回 422"""
        # 创建超过1000字符的评论内容
        long_content = "这是一条超长评论内容。" * 200  # 约2000字符

        response = client.post(
            f"/api/v1/posts/{sample_post.id}/comments",
            headers=auth_headers,
            json={"content": long_content},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY

    def test_create_comment_special_characters(
        self,
        client: TestClient,
        sample_post: Post,
        auth_headers: dict,
    ):
        """✅ 极端数据：测试特殊字符和表情符号"""
        special_content = "测试特殊字符：@#$%^&*()_+{}|:<>?[]\\;'\",./ 还有表情😀🎉🚀"

        response = client.post(
            f"/api/v1/posts/{sample_post.id}/comments",
            headers=auth_headers,
            json={"content": special_content},
        )

        assert response.status_code == status.HTTP_201_CREATED
        data = response.json()
        assert data["content"] == special_content

    def test_create_comment_empty_content(
        self,
        client: TestClient,
        sample_post: Post,
        auth_headers: dict,
    ):
        """✅ 边界数据：测试空评论内容 - 应返回 422"""
        response = client.post(
            f"/api/v1/posts/{sample_post.id}/comments",
            headers=auth_headers,
            json={"content": ""},
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY


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
        """✅ 边界数据：测试获取空评论列表
        注意：参数没有传入 sample_comments fixture，所以评论列表为空
        """
        response = client.get(f"/api/v1/posts/{sample_post.id}/comments")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert isinstance(data, dict)
        assert "items" in data
        assert isinstance(data["items"], list)
        assert len(data["items"]) == 0

    def test_get_comments_tree_structure(
        self,
        client: TestClient,
        sample_post: Post,
        sample_comments: list[Comment],
    ):
        """✅ 正常数据：测试评论树形结构"""
        response = client.get(f"/api/v1/posts/{sample_post.id}/comments")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # 验证树形结构（只返回顶级评论）
        comments = data["items"]
        for comment in comments:
            # 顶级评论没有 parent_id 字段，但有 replies 字段
            assert "replies" in comment  # 包含回复字段

        # 验证回复也可以有回复（递归结构）
        for comment in comments:
            for reply in comment.get("replies", []):
                assert "replies" in reply

        # 验证返回默认的分页的数据格式
        assert data["page"] == 1
        assert data["size"] == 20  # 默认分页大小
        assert data["pages"] == 1  # 总共只有3 条顶级评论，所以只有1页
        assert data["has_next"] is False
        assert data["has_prev"] is False
        assert data["total"] == 3  # 总只返回 3 条顶级评论

    def test_get_comments_post_not_found(
        self,
        client: TestClient,
    ):
        """✅ 异常数据：测试文章不存在 - 应返回 404"""
        fake_post_id = "00000000-0000-0000-0000-000000000000"

        response = client.get(f"/api/v1/posts/{fake_post_id}/comments")

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["error"]["message"] == "文章不存在"

    def test_get_comments_large_dataset(
        self,
        client: TestClient,
        session: Session,
        sample_post: Post,
        sample_user: User,
    ):
        """✅ 极端数据：测试大量评论数据的分页性能"""
        # 创建大量评论数据（50条）
        for i in range(50):
            comment_crud.create_with_author(
                db=session,
                obj_in=CommentCreate(content=f"批量评论 {i + 1}"),
                author_id=sample_user.id,
                post_id=sample_post.id,
            )

        # 验证分页处理大量数据
        response = client.get(f"/api/v1/posts/{sample_post.id}/comments?page=1&size=10")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["page"] == 1
        assert data["size"] == 10
        assert data["pages"] == 5
        assert data["has_next"] is True
        assert data["has_prev"] is False
        assert data["total"] == 50
        assert len(data["items"]) == 10


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
        """✅ 正常数据：测试成功删除自己的评论"""
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
        """✅ 正常数据：测试删除评论会级联删除子评论"""
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
        """✅ 异常数据：测试删除不存在的评论 - 应返回 404"""
        fake_comment_id = "00000000-0000-0000-0000-000000000000"
        response = client.delete(
            f"/api/v1/posts/{sample_post.id}/comments/{fake_comment_id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_404_NOT_FOUND
        assert response.json()["error"]["message"] == "评论不存在"

    def test_delete_comment_wrong_post(
        self,
        client: TestClient,
        session: Session,
        sample_user: User,
        sample_post: Post,
        sample_comments: list[Comment],
        auth_headers: dict,
    ):
        """✅ 异常数据：测试评论不属于该文章 - 应返回 404"""
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
        assert response.json()["error"]["message"] == "评论不属于该文章"

    def test_delete_comment_forbidden(
        self,
        client: TestClient,
        session: Session,
        sample_post: Post,
        sample_comments: list[Comment],
    ):
        """✅ 异常数据：测试删除他人评论 - 应返回 403"""
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
        assert response.json()["error"]["message"] == "无权删除他人评论"

    def test_delete_comment_unauthorized(
        self,
        client: TestClient,
        sample_post: Post,
        sample_comments: list[Comment],
    ):
        """✅ 异常数据：测试未登录删除评论 - 应返回 401"""
        response = client.delete(
            f"/api/v1/posts/{sample_post.id}/comments/{sample_comments[0].id}",
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.json()["error"]["message"] == "Not authenticated"

    def test_delete_comment_invalid_uuid_format(
        self,
        client: TestClient,
        sample_post: Post,
        auth_headers: dict,
    ):
        """✅ 极端数据：测试无效的UUID格式 - 应返回 422"""
        invalid_comment_id = "invalid-uuid-format"

        response = client.delete(
            f"/api/v1/posts/{sample_post.id}/comments/{invalid_comment_id}",
            headers=auth_headers,
        )

        assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
