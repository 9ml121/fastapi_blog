"""
评论管理 API 端点

提供评论的创建、查询、删除功能（嵌套在文章路由下）

知识点：
1. 嵌套路由：/posts/{post_id}/comments - 体现资源层级关系
2. 递归模型：CommentResponse 自动序列化评论树（replies）
3. 权限控制：创建需登录，删除需作者本人
4. 级联删除：删除评论会自动删除所有子评论（数据库层面）
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.core.pagination import PaginatedResponse, PaginationParams
from app.crud import comment as comment_crud
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentResponse

# 创建路由器
router = APIRouter()


# ================ 创建 API 端点 ================
@router.post(
    "/{post_id}/comments",
    response_model=CommentResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_comment(
    post_id: UUID,
    comment_in: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    创建评论（需要登录）

    支持两种场景：
    1. 顶级评论：直接回复文章（parent_id=null）
    2. 回复评论：回复某条已有评论（parent_id=xxx）

    权限：需要登录用户

    路径参数：
    - post_id: 文章 ID

    请求体：
    - content: 评论内容（1-1000 字符）
    - parent_id: 父评论 ID（可选，回复评论时提供）

    返回：
    - 创建成功的评论对象（包含作者信息）

    错误响应：
    - 404: 文章不存在
    - 404: 父评论不存在或不属于该文章
    """
    comment = comment_crud.create_comment(
        db=db,
        obj_in=comment_in,
        author_id=current_user.id,
        post_id=post_id,
    )

    return comment


# ================ 查询 API 端点 ================
@router.get("/{post_id}/comments", response_model=PaginatedResponse[CommentResponse])
async def get_comments(
    post_id: UUID,
    params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
) -> PaginatedResponse[CommentResponse]:
    """获取文章评论列表（支持分页、排序）

    **权限**: 公开访问，无需登录

    **路径参数**:
    - post_id: 文章 ID

    **查询参数**:
    - page: 页码（从1开始，默认1）
    - size: 每页数量（1-100，默认20）
    - sort: 排序字段（默认created_at）
    - order: 排序方向（asc/desc，默认desc）

    **返回**:
    - 200: 分页的评论列表,只返回顶级评论（parent_id=None），子评论通过 replies 递归获取
    - 404: 文章不存在
    - 422: 参数验证失败

    **示例**:
    - GET /api/v1/posts/123/comments/?page=1&size=10
    - GET /api/v1/posts/123/comments/?sort=created_at&order=desc

    """
    response = comment_crud.get_comment_by_post_id(db, post_id=post_id, params=params)
    return response  # type: ignore


# ================ 删除 API 端点 ================
@router.delete(
    "/{post_id}/comments/{comment_id}", status_code=status.HTTP_204_NO_CONTENT
)
async def delete_comment(
    post_id: UUID,
    comment_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Response:
    """
    删除评论（仅作者本人）

    权限：只能删除自己的评论

    路径参数：
    - post_id: 文章 ID
    - comment_id: 评论 ID

    返回：
    - 204 No Content（删除成功，无响应体）

    错误响应：
    - 404: 评论不存在
    - 404: 评论不属于该文章
    - 403: 无权删除他人评论

    注意：
    - 删除评论会级联删除所有子评论（数据库 CASCADE 配置）
    """
    comment_crud.delete_comment(
        db=db,
        comment_id=comment_id,
        post_id=post_id,
        user_id=current_user.id,
    )

    return Response(status_code=status.HTTP_204_NO_CONTENT)
