from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field, TypeAdapter


# =========== 通用消息响应模型 ============
class MessageResponse(BaseModel):
    """通用消息响应"""

    message: str


# =========== 分页查询参数 ============
class PaginationParams(BaseModel):
    """分页查询参数

    Attributes:
        page: 页码（从1开始）
        size: 每页数量（1-100）
        sort: 排序字段
        order: 排序方向（asc/desc）

    """

    page: int = Field(default=1, ge=1, description="页码（从1开始）")
    size: int = Field(default=20, ge=1, le=100, description="每页数量（1-100）")
    sort: str = Field(default="created_at", description="排序字段")
    order: str = Field(default="desc", pattern="^(asc|desc)$", description="排序方向")

    @property
    def offset(self) -> int:
        """计算 OFFSET 值"""
        return (self.page - 1) * self.size

    @property
    def limit(self) -> int:
        """获取 LIMIT 值"""
        return self.size


# =========== 分页响应模型 ============
# 分页响应中数据项的类型，仅用于 API 层的 response_model 类型提示
ItemType = TypeVar("ItemType", bound=BaseModel)


class PaginatedResponse(BaseModel, Generic[ItemType]):
    """分页响应格式

    Attributes:
        items: 数据列表,泛型支持
        total: 总记录数
        page: 当前页码
        size: 每页数量
        pages: 总页数
        has_next: 是否有下一页
        has_prev: 是否有上一页

    继承：
    1. BaseModel - Pydantic 数据验证
    2. Generic[ItemType] - 泛型支持，ItemType只能是 pydantic 模型
    """

    items: list[ItemType] = Field(description="数据列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    size: int = Field(description="每页数量")
    pages: int = Field(description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_prev: bool = Field(description="是否有上一页")

    model_config = ConfigDict(from_attributes=True)

    @classmethod
    def create(
        cls,
        *,
        schema_class: type[ItemType],
        items: list[Any],
        total: int,
        params: PaginationParams,
    ) -> "PaginatedResponse[ItemType]":
        """创建分页响应

        Args:
            schema_class: Pydantic 模型类，用于将 ORM 模型转换为 Pydantic 模型
            items: 数据列表, 支持 sqlalchemy orm 模型
            total: 总记录数
            params: 分页参数

        Returns:
            PaginatedResponse: 分页响应对象
        """
        # 将 ORM 模型转换为 Pydantic 模型
        adapter = TypeAdapter(list[schema_class])
        items_pydantic = adapter.validate_python(items, from_attributes=True)

        # 计算总页数（向上取整）
        pages = (total + params.size - 1) // params.size if total > 0 else 0

        return cls(
            items=items_pydantic,
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
            has_next=params.page < pages,
            has_prev=params.page > 1,
        )
