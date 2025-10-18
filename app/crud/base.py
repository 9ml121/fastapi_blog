"""
app/crud/base.py

通用的 CRUD (Create, Read, Update, Delete) 操作基类
"""

from typing import Any, Generic, TypeVar

from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db.database import Base

# 定义泛型类型变量
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)


class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """通用 CRUD 操作基类，支持泛型。

    这个基类为数据库模型提供了标准的 CRUD 操作（创建、读取、更新、删除），
    通过泛型支持任意 SQLAlchemy 模型和 Pydantic schema。

    Type Parameters:
        ModelType: SQLAlchemy 模型类型（继承自 Base）
        CreateSchemaType: 用于创建操作的 Pydantic schema 类型
        UpdateSchemaType: 用于更新操作的 Pydantic schema 类型

    Example:
        >>> class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
        ...     pass
        >>> user_crud = CRUDUser(User)
    """

    def __init__(self, model: type[ModelType]):
        """初始化 CRUD 操作基类。

        Args:
            model: 一个 SQLAlchemy model 类。
        """
        self.model = model

    def get(self, db: Session, id: Any) -> ModelType | None:
        """通过 ID 获取单个记录。

        Args:
            db: 数据库会话。
            id: 记录的 ID。

        Returns:
            找到的数据库对象，如果不存在则返回 None。
        """
        return db.get(self.model, id)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        """获取记录列表（支持分页）。

        .. deprecated:: 1.0.0
        已弃用。请使用app.api.pagination.paginate_query() 替代。

        Args:
            db: 数据库会话。
            skip: 跳过的记录数。
            limit: 返回的最大记录数。

        Returns:
            数据库对象列表。
        """
        # TODO: db.query -> Legacy 风格, 建议使用 db.execute 替代
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(
        self, db: Session, *, obj_in: CreateSchemaType, **kwargs: Any
    ) -> ModelType:
        """创建新记录。

        Args:
            db: 数据库会话。
            obj_in: 包含创建所需数据的 Pydantic schema。
            **kwargs: 覆盖或添加到创建数据中的额外关键字参数。

        Returns:
            新创建的数据库对象。
        """
        # 使用 Pydantic v2 的推荐方法
        obj_in_data = obj_in.model_dump()
        # 合并来自 schema 和 kwargs 的数据，kwargs 具有更高优先级
        create_data = {**obj_in_data, **kwargs}
        db_obj = self.model(**create_data)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType | dict[str, Any],
    ) -> ModelType:
        """更新现有记录。

        Args:
            db: 数据库会话。
            db_obj: 要更新的数据库对象。
            obj_in: 包含要更新数据的 Pydantic schema 或字典。

        Returns:
            更新后的数据库对象。
        """
        # 使用 Pydantic v2 的推荐方法
        update_data = (
            obj_in
            if isinstance(obj_in, dict)
            else obj_in.model_dump(exclude_unset=True)
        )
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: Any) -> ModelType | None:
        """通过 ID 删除记录。

        Args:
            db: 数据库会话。
            id: 要删除的记录的 ID。

        Returns:
            被删除的数据库对象，如果未找到则返回 None。
        """
        obj = db.get(self.model, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
