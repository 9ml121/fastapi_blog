"""
app/crud/tag.py

标签相关的 CRUD 操作
"""

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.models.tag import Tag
from app.schemas.tag import TagCreate, TagUpdate


class CRUDTag(CRUDBase[Tag, TagCreate, TagUpdate]):
    def get_by_name(self, db: Session, *, name: str) -> Tag | None:
        """通过标签名称查询标签。

          Args:
              db: 数据库会话。
              name: 要查询的标签名称。

          Returns:
              找到的标签对象，如果不存在则返回 None。
          """

        return db.query(Tag).filter(Tag.name == name).first()

    def get_or_create(self, db: Session, *, name: str) -> Tag:
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
        tag = self.get_by_name(db, name=normalized_name)

        if not tag:
            slug = Tag.generate_slug(normalized_name)
            # 手动创建实例，绕开会 commit 的 self.create()
            tag = self.model(name=normalized_name, slug=slug)
            db.add(tag)
            # 不在这里 commit，让调用者来决定何时 commit
            # flush可以让我们在当前事务中通过 tag.id 获取到新标签的 ID
            db.flush()
            db.refresh(tag)

        return tag


tag = CRUDTag(Tag)
