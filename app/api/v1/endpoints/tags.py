"""
标签管理 API 端点

提供标签的查询功能（只读）

知识点：
1. 只读 API：标签由文章管理自动创建，不需要单独的 POST/PUT/DELETE
2. 计算属性：post_count 通过 ORM relationship 自动计算
3. 避免循环引用：TagWithPosts 使用简化的 PostInTag 避免与 PostResponse 循环引用
4. lazy="selectin"：Tag 模型的 posts relationship 使用 selectin 避免 N+1 查询
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.core.pagination import PaginatedResponse, PaginationParams
from app.crud import tag as tag_crud
from app.schemas.tag import TagResponse, TagWithPosts

# 创建路由器
router = APIRouter()


@router.get("/", response_model=PaginatedResponse[TagResponse])
async def get_tags(
    pagination_params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
) -> PaginatedResponse[TagResponse]:
    """获取标签列表（支持分页）

     **权限**：公开访问，无需登录

     **查询参数**：
    【分页参数】
     - page: 页码（从1开始，默认1）
     - size: 每页数量（1-100，默认20）
     - sort: 排序字段（默认created_at）
     - order: 排序方向（asc/desc，默认desc）

     **返回**：PaginatedResponse[TagResponse]
     - 分页的标签列表，每个标签包含 post_count（文章数量）

     **示例**:
     GET /api/v1/tags/?page=1&size=10&sort=created_at&order=desc

    """
    tags, total = tag_crud.get_tags(db, pagination_params=pagination_params)

    items = PaginatedResponse.create(items=tags, total=total, params=pagination_params)

    return items  # type: ignore


@router.get("/{tag_slug}", response_model=TagWithPosts)
async def get_tag_by_slug(
    tag_slug: str,
    db: Session = Depends(get_db),
) -> TagWithPosts:
    """通过 slug 获取标签详情（包含关联文章列表）

    **使用场景**：用户点击标签后，访问该标签的详情页，查看该标签下的所有文章。

    **权限**：公开访问，无需登录

    **路径参数**：
    - tag_slug: 标签的 URL 友好标识符

    **返回**：
    - 标签详情，包含：
      - 标签基本信息
      - 文章总数
      - 使用该标签的所有文章（简化信息）
    """
    tag = tag_crud.get_tag_by_slug(db, slug=tag_slug)
    if not tag:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="标签不存在",
        )

    return tag  # type: ignore
