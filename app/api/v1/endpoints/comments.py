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

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.crud.comment import comment as comment_crud
from app.crud.post import post as post_crud
from app.models.user import User
from app.schemas.comment import CommentCreate, CommentResponse

# 创建路由器
router = APIRouter()


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
    # 1. 验证文章存在
    post = post_crud.get(db, id=post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在",
        )

    # 2. 如果是回复评论，验证父评论存在且属于该文章
    if comment_in.parent_id:
        parent_comment = comment_crud.get(db, id=comment_in.parent_id)
        if not parent_comment:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="父评论不存在",
            )
        # 验证父评论属于同一文章（防止跨文章回复）
        if parent_comment.post_id != post_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="父评论不属于该文章",
            )

    # 3. 创建评论
    comment = comment_crud.create_with_author(
        db=db,
        obj_in=comment_in,
        author_id=current_user.id,
        post_id=post_id,
    )

    return comment


@router.get("/{post_id}/comments", response_model=list[CommentResponse])
async def get_comments(
    post_id: UUID,
    db: Session = Depends(get_db),
) -> Any:
    """
    获取文章的所有评论（树形结构）

    权限：公开访问，无需登录

    路径参数：
    - post_id: 文章 ID

    返回：
    - 顶级评论列表（每个评论递归包含 replies 子评论）
    - 按创建时间倒序排列（最新评论在前）

    注意：
    - 只返回顶级评论（parent_id=None），子评论通过 replies 字段递归获取
    - 使用 lazy="selectin" 避免 N+1 查询，总查询次数为 2 次
    """
    # 1. 验证文章存在
    post = post_crud.get(db, id=post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在",
        )

    # 2. 获取评论列表
    comments = comment_crud.get_by_post(db, post_id=post_id)
    return comments


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
    # 1. 查询评论
    comment = comment_crud.get(db, id=comment_id)
    if not comment:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不存在",
        )

    # 2. 验证评论属于该文章
    if comment.post_id != post_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="评论不属于该文章",
        )

    # 3. 权限检查：只能删除自己的评论
    if comment.user_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权删除他人评论",
        )

    # 4. 删除评论（级联删除所有子评论）
    comment_crud.remove(db, id=comment_id)

    return Response(status_code=status.HTTP_204_NO_CONTENT)
