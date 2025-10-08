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
    def __init__(self, model: type[ModelType]):
        """
        通用 CRUD 操作基类

        :param model: 一个 SQLAlchemy model 类
        """
        self.model = model

    def get(self, db: Session, id: Any) -> ModelType | None:
        """
        通过 ID 获取单个记录

        :param db: 数据库会话
        :param id: 记录的 ID
        :return: 数据库对象或 None
        """
        return db.get(self.model, id)

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        """
        获取记录列表（支持分页）

        :param db: 数据库会话
        :param skip: 跳过的记录数
        :param limit: 返回的最大记录数
        :return: 数据库对象列表
        """
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType, **kwargs: Any) -> ModelType:
        """
        创建新记录

        :param db: 数据库会话
        :param obj_in: Pydantic schema，包含创建所需的数据
        :param kwargs: 覆盖或添加到创建数据中的额外关键字参数
        :return: 新创建的数据库对象
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
        self, db: Session, *, db_obj: ModelType, obj_in: UpdateSchemaType | dict[str, Any]
    ) -> ModelType:
        """
        更新现有记录

        :param db: 数据库会话
        :param db_obj: 要更新的数据库对象
        :param obj_in: Pydantic schema 或字典，包含要更新的数据
        :return: 更新后的数据库对象
        """
        # 使用 Pydantic v2 的推荐方法
        update_data = obj_in if isinstance(obj_in, dict) else obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    def remove(self, db: Session, *, id: Any) -> ModelType | None:
        """
        通过 ID 删除记录

        :param db: 数据库会话
        :param id: 要删除的记录的 ID
        :return: 被删除的数据库对象，如果未找到则返回 None
        """
        obj = db.get(self.model, id)
        if obj:
            db.delete(obj)
            db.commit()
        return obj
