"""
标签管理 API 端点

提供标签的查询功能（只读）

知识点：
1. 只读 API：标签由文章管理自动创建，不需要单独的 POST/PUT/DELETE
2. 计算属性：post_count 通过 ORM relationship 自动计算
3. 避免循环引用：TagWithPosts 使用简化的 PostInTag 避免与 PostResponse 循环引用
4. lazy="selectin"：Tag 模型的 posts relationship 使用 selectin 避免 N+1 查询
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.crud.tag import tag as tag_crud
from app.schemas.tag import TagResponse, TagWithPosts

# 创建路由器
router = APIRouter()


@router.get("/", response_model=list[TagResponse])
async def get_tags(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
) -> Any:
    """
    获取标签列表（支持分页）

    权限：公开访问，无需登录

    查询参数：
    - skip: 跳过的记录数（默认 0）
    - limit: 返回的最大记录数（默认 100）

    返回：
    - 标签列表，每个标签包含 post_count（文章数量）
    """
    tags = tag_crud.get_multi(db, skip=skip, limit=limit)
    return tags


@router.get("/{tag_slug}", response_model=TagWithPosts)
async def get_tag_by_slug(
    tag_slug: str,
    db: Session = Depends(get_db),
) -> Any:
    """
    通过 slug 获取标签详情（包含关联文章列表）

    权限：公开访问，无需登录

    路径参数：
    - tag_slug: 标签的 URL 友好标识符

    返回：
    - 标签详情，包含：
      - 标签基本信息
      - post_count: 文章总数
      - posts: 使用该标签的所有文章（简化信息）

    注意：
    - posts 字段使用简化的 PostInTag 模型，避免循环引用
    - 文章列表通过 Tag.posts relationship 自动加载（lazy="selectin"）
    """
    tag = tag_crud.get_by_slug(db, slug=tag_slug)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="标签不存在",
        )

    return tag
