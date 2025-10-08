"""
app/crud/post.py

文章相关的 CRUD 操作
"""

from uuid import UUID

from sqlalchemy.orm import Session

from app.crud.base import CRUDBase
from app.crud.tag import tag as tag_crud
from app.models.post import Post
from app.schemas.post import PostCreate, PostUpdate


class CRUDPost(CRUDBase[Post, PostCreate, PostUpdate]):
    def get_by_slug(self, db: Session, *, slug: str) -> Post | None:
        """通过 slug 获取文章"""
        return db.query(Post).filter(Post.slug == slug).first()

    def create_with_author(self, db: Session, *, obj_in: PostCreate, author_id: UUID) -> Post:
        """
        创建新文章，并关联作者和标签
        """
        # 1. 从输入 schema 中提取数据
        obj_in_data = obj_in.model_dump(exclude={"tags"})
        tag_names = obj_in.tags or []

        # 2. 处理 slug: 如果 slug 为空，就根据 title 自动生成一个
        if not obj_in_data.get("slug"):
            obj_in_data["slug"] = Post._generate_slug_from_title(obj_in_data["title"])

        # 3. 创建 Post 对象并添加到会话中，使其变为 pending 状态
        db_obj = self.model(**obj_in_data, author_id=author_id)
        db.add(db_obj)

        # 4. 处理并关联标签
        for tag_name in tag_names:
            tag_obj = tag_crud.get_or_create(db, name=tag_name)
            db_obj.tags.append(tag_obj)

        # 5. 提交事务，一次性保存所有内容
        db.commit()
        db.refresh(db_obj)
        return db_obj


post = CRUDPost(Post)
