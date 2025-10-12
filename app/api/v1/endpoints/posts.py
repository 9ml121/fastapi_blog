"""
文章管理 API 端点

提供文章的创建、查询、更新、删除等功能

知识点：
1. RESTful 设计：使用标准 HTTP 方法表达操作语义
   （POST=创建, GET=查询, PATCH=更新, DELETE=删除）
2. 依赖注入链：db → current_user → current_active_user，每层只负责一个验证步骤
3. Response Model：FastAPI 自动将 ORM 对象转为 Pydantic Schema，过滤敏感字段
4. 异常处理：用 HTTPException 返回标准错误响应（状态码 + detail）
"""

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user, get_db
from app.crud.post import post as post_crud
from app.models.user import User
from app.schemas.post import PostCreate, PostResponse, PostUpdate

# 创建路由器
router = APIRouter()


@router.post(path="/", response_model=PostResponse, status_code=status.HTTP_201_CREATED)
async def create_post(
    post_in: PostCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    创建新文章

    工作流程：
    1. 验证用户已登录且账户活跃（依赖注入自动处理）
    2. 调用 CRUD 层创建文章，自动关联作者和标签
    3. 返回创建的文章详情（包含作者和标签信息）

    权限：需要登录且账户活跃

    注意：
    - 如果未提供 slug，会根据 title 自动生成
    - 如果 slug 重复，返回 409 Conflict
    - 标签会自动创建（如果不存在）
    """
    try:
        new_post = post_crud.create_with_author(
            db=db,
            obj_in=post_in,
            author_id=current_user.id,
        )
        return new_post
    except IntegrityError:
        # 数据库唯一约束冲突（如 slug 重复）
        # 显式抑制异常链， from None 转换所有数据库异常！
        # ⚠️ 避免隐式异常链暴露数据库内部错误！
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="文章 slug 已存在，请使用其他 slug",
        ) from None


@router.get("/", response_model=list[PostResponse])
async def get_posts(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    # 注意：不需要 current_user！
) -> Any:
    """
    获取文章列表（支持分页）

    权限：公开访问，无需登录

    查询参数：
    - skip: 跳过的记录数（默认 0）
    - limit: 返回的最大记录数（默认 100）
    """
    # 调用 CRUD 方法
    return post_crud.get_multi(db, skip=skip, limit=limit)


@router.get("/{post_id}", response_model=PostResponse)
async def get_post(
    post_id: UUID,
    db: Session = Depends(get_db),
) -> Any:
    """
    获取单篇文章详情

    权限：公开访问，无需登录

    路径参数：
    - post_id: 文章的 UUID

    返回：
    - 200: 文章详情
    - 404: 文章不存在
    """
    post = post_crud.get(db, id=post_id)
    if not post:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="文章不存在",
        )

    return post


@router.patch("/{post_id}", response_model=PostResponse)
async def update_post(
    post_id: UUID,
    post_in: PostUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> Any:
    """
    更新文章（部分更新）

    权限：需要登录且是文章作者

    路径参数：
    - post_id: 文章的 UUID

    请求体：
    - 所有字段可选（PATCH 语义）
    - tags: 如果提供，会完全替换原有标签

    返回：
    - 200: 更新后的文章详情
    - 404: 文章不存在
    - 403: 无权限修改此文章
    """
    # 1. 获取文章
    post = post_crud.get(db, id=post_id)
    if not post:
        raise HTTPException(404, "文章不存在")

    # 2. 检查权限：只有作者可以更新
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限修改此文章",
        )

    # 3. 执行更新
    updated_post = post_crud.update(db=db, db_obj=post, obj_in=post_in)

    return updated_post


@router.delete("/{post_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_post(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """
    删除文章

    权限：需要登录且是文章作者

    路径参数：
    - post_id: 文章的 UUID

    返回：
    - 204: 删除成功（无响应体）
    - 404: 文章不存在
    - 403: 无权限删除此文章
    """
    # 1. 获取文章并检查存在性
    post = post_crud.get(db, id=post_id)
    if not post:
        raise HTTPException(404, "文章不存在")

    # 2. 检查权限：只有作者可以删除
    if post.author_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权限删除此文章",
        )

    # 3. 执行删除
    post_crud.remove(db, id=post_id)

    # FastAPI 自动返回 204
    return None
