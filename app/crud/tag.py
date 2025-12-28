"""
app/crud/tag.py

标签相关的 CRUD 操作
"""

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import ResourceNotFoundError
from app.crud.pagination import paginate_query
from app.models.tag import Tag
from app.schemas.common import PaginationParams

# ================  Tag 查询方法 ================


def get_tag_by_id(db: Session, tag_id: UUID) -> Tag | None:
    """通过标签ID查询标签。

    Args:
        db: 数据库会话。
        tag_id: 要查询的标签ID。
    """
    return db.get(Tag, tag_id)


def get_tag_by_name(db: Session, name: str) -> Tag | None:
    """通过标签名称查询标签。

    Args:
        db: 数据库会话。
        name: 要查询的标签名称。

    Returns:
        找到的标签对象，如果不存在则返回 None。
    """

    return db.query(Tag).filter(Tag.name == name).first()


def get_tag_by_slug(db: Session, slug: str) -> Tag | None:
    """通过 slug 查询标签。

    Args:
        db: 数据库会话。
        slug: 要查询的标签 slug。

    Returns:
        找到的标签对象，如果不存在则返回 None。
    """
    return db.query(Tag).filter(Tag.slug == slug).first()


def get_tags(db: Session, pagination_params: PaginationParams) -> tuple[list[Tag], int]:
    """获取标签列表。

    Args:
        db: 数据库会话。
        pagination_params: 分页参数。
    """
    query = select(Tag)
    items, total = paginate_query(db, query, pagination_params, model=Tag)
    return items, total


# ================ TAg 创建方法 ================
def get_or_create_tag(db: Session, name: str) -> Tag:
    """获取一个标签，如果不存在则创建。

    此方法实现了 "Get or Create" 模式，确保数据库中标签名称的唯一性。
    创建新标签时，它会根据名称自动生成一个 slug。
    重要的是，此方法只将新对象添加到会话中，而不会提交事务，
    以便被更上层的业务逻辑统一管理。

    Args:
        db: 数据库会话。
        name: 要获取或创建的标签的名称。

    Returns:
        一个已存在或新创建的 Tag 对象。
    """
    normalized_name = Tag.normalize_name(name)
    tag = get_tag_by_name(db, name=normalized_name)

    if not tag:
        slug = Tag.generate_slug(normalized_name)
        # 手动创建实例，绕开会 commit 的 self.create()
        tag = Tag(name=normalized_name, slug=slug)
        db.add(tag)
        # 不在这里 commit，让调用者来决定何时 commit
        # flush可以让我们在当前事务中通过 tag.id 获取到新标签的 ID
        db.flush()
        db.refresh(tag)

    return tag


# ================ Tag 删除方法 ================


def delete_tag(db: Session, tag_id: UUID) -> None:
    """删除一个标签。

    Args:
        db: 数据库会话。
        tag_id: 要删除的标签ID。
    """
    tag = get_tag_by_id(db, tag_id)
    if not tag:
        raise ResourceNotFoundError(resource="标签")
    db.delete(tag)
    db.commit()
    return None
