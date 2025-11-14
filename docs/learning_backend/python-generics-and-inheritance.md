# Python 泛型编程与类继承实战指南

> **文档用途**：基于项目实战代码，系统学习 Python 泛型编程和类继承
> **代码示例**：来自 `app/crud/base.py` 和 `app/api/pagination.py` > **创建时间**：2025-10-14

---

## 📚 目录

1. [泛型编程基础](#1-泛型编程基础)
2. [TypeVar 类型变量](#2-typevar-类型变量)
3. [Generic 泛型类](#3-generic-泛型类)
4. [泛型函数](#4-泛型函数)
5. [类型约束 (bound)](#5-类型约束-bound)
6. [多重继承](#6-多重继承)
7. [实战案例分析](#7-实战案例分析)
8. [最佳实践](#8-最佳实践)

---

## 1. 泛型编程基础

### 1.1 什么是泛型？

**泛型（Generics）** 允许你编写可以处理多种类型的代码，同时保持类型安全。

**对比示例**：

```python
# ❌ 没有泛型：类型不安全
def get_first_item(items: list) -> Any:
    return items[0] if items else None

result = get_first_item([1, 2, 3])  # result 类型是 Any
print(result + 10)  # IDE 无法检查类型错误

# ✅ 使用泛型：类型安全
from typing import TypeVar, List

T = TypeVar('T')

def get_first_item(items: List[T]) -> T | None:
    return items[0] if items else None

result = get_first_item([1, 2, 3])  # result 类型是 int
print(result + 10)  # ✅ IDE 知道这是 int，提供智能提示
```

### 1.2 为什么需要泛型？

**1. 类型安全**：

```python
# 编译时发现错误，而不是运行时
numbers: List[int] = [1, 2, 3]
first: int = get_first_item(numbers)  # ✅ 类型正确
first.upper()  # ❌ mypy 报错：int 没有 upper 方法
```

**2. 代码复用**：

```python
# 一个函数处理多种类型
get_first_item([1, 2, 3])        # 处理 int
get_first_item(["a", "b", "c"])  # 处理 str
get_first_item([User(), User()]) # 处理 User
```

**3. IDE 智能提示**：

```python
users = [User(name="Alice"), User(name="Bob")]
first_user = get_first_item(users)
first_user.  # IDE 自动提示 User 的所有属性和方法
```

---

## 2. TypeVar 类型变量

### 2.1 基础用法

**TypeVar** 用于声明类型变量，可以代表任意类型。

```python
from typing import TypeVar

# 基础 TypeVar
T = TypeVar('T')  # 可以是任何类型

# 使用 TypeVar
def identity(value: T) -> T:
    """返回原值（保持类型）"""
    return value

# 类型推断
x: int = identity(42)        # T = int
y: str = identity("hello")   # T = str
```

### 2.2 项目实战：base.py 中的 TypeVar

**代码位置**：`app/crud/base.py`

```python
from typing import TypeVar
from pydantic import BaseModel
from app.db.database import Base

# 定义三个类型变量
ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
```

**设计分析**：

| TypeVar            | 作用              | 约束                 | 示例           |
| ------------------ | ----------------- | -------------------- | -------------- |
| `ModelType`        | 数据库模型类型    | 必须继承 `Base`      | `User`, `Post` |
| `CreateSchemaType` | 创建数据的 Schema | 必须继承 `BaseModel` | `UserCreate`   |
| `UpdateSchemaType` | 更新数据的 Schema | 必须继承 `BaseModel` | `UserUpdate`   |

**为什么要分开定义？**

```python
# 不同操作需要不同的 Schema
class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    pass

# 创建：使用 UserCreate
user = crud_user.create(db, obj_in=UserCreate(username="alice"))

# 更新：使用 UserUpdate
user = crud_user.update(db, db_obj=user, obj_in=UserUpdate(email="new@example.com"))
```

### 2.3 项目实战：pagination.py 中的 TypeVar

**代码位置**：`app/api/pagination.py`

```python
from typing import TypeVar
from app.db.database import Base

ItemType = TypeVar("ItemType")  # 泛型数据项类型
ModelType = TypeVar("ModelType", bound=Base)  # 数据库模型类型
```

**设计分析**：

| TypeVar     | 作用           | 约束            | 使用场景                          |
| ----------- | -------------- | --------------- | --------------------------------- |
| `ItemType`  | 任意数据项类型 | 无约束          | `PaginatedResponse[Post]`         |
| `ModelType` | 数据库模型类型 | 必须继承 `Base` | `paginate_query(..., model=Post)` |

---

## 3. Generic 泛型类

### 3.1 基础用法

**Generic** 让类支持泛型参数。

```python
from typing import Generic, TypeVar

T = TypeVar('T')

class Box(Generic[T]):
    """一个可以装任何类型的盒子"""
    def __init__(self, item: T):
        self.item = item

    def get(self) -> T:
        return self.item

# 使用泛型类
int_box: Box[int] = Box(42)
str_box: Box[str] = Box("hello")

print(int_box.get() + 10)     # ✅ 类型安全：int
print(str_box.get().upper())  # ✅ 类型安全：str
```

### 3.2 项目实战：CRUDBase 泛型类

**代码位置**：`app/crud/base.py`

```python
class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    """通用 CRUD 操作基类，支持泛型"""

    def __init__(self, model: type[ModelType]):
        self.model = model

    def get(self, db: Session, id: Any) -> ModelType | None:
        """获取单个记录"""
        return db.get(self.model, id)

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        """创建记录"""
        obj_in_data = obj_in.model_dump()
        db_obj = self.model(**obj_in_data)
        db.add(db_obj)
        db.commit()
        return db_obj

    def update(
        self,
        db: Session,
        *,
        db_obj: ModelType,
        obj_in: UpdateSchemaType
    ) -> ModelType:
        """更新记录"""
        update_data = obj_in.model_dump(exclude_unset=True)
        for field, value in update_data.items():
            setattr(db_obj, field, value)
        db.commit()
        return db_obj
```

**使用示例**：

```python
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

# 定义具体的 CRUD 类
class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """用户 CRUD 操作

    类型参数：
    - ModelType = User
    - CreateSchemaType = UserCreate
    - UpdateSchemaType = UserUpdate
    """
    pass

# 使用
crud_user = CRUDUser(User)

# 创建用户
user = crud_user.create(
    db,
    obj_in=UserCreate(username="alice", email="alice@example.com")
)
# user 的类型是 User，IDE 有完整提示

# 更新用户
updated_user = crud_user.update(
    db,
    db_obj=user,
    obj_in=UserUpdate(email="new@example.com")
)
# updated_user 的类型是 User
```

**类型安全的好处**：

```python
# ✅ 正确：UserCreate 是 CreateSchemaType
crud_user.create(db, obj_in=UserCreate(...))

# ❌ 错误：PostCreate 不是 CreateSchemaType
crud_user.create(db, obj_in=PostCreate(...))  # mypy 报错
```

### 3.3 项目实战：PaginatedResponse 泛型类

**代码位置**：`app/api/pagination.py`

```python
class PaginatedResponse(BaseModel, Generic[ItemType]):
    """分页响应格式（泛型）

    可以包装任何类型的数据列表
    """
    items: list[ItemType] = Field(description="数据列表")
    total: int = Field(description="总记录数")
    page: int = Field(description="当前页码")
    size: int = Field(description="每页数量")
    pages: int = Field(description="总页数")
    has_next: bool = Field(description="是否有下一页")
    has_prev: bool = Field(description="是否有上一页")

    @classmethod
    def create(
        cls,
        items: list[ItemType],
        total: int,
        params: PaginationParams,
    ) -> "PaginatedResponse[ItemType]":
        """创建分页响应"""
        pages = (total + params.size - 1) // params.size if total > 0 else 0
        return cls(
            items=items,
            total=total,
            page=params.page,
            size=params.size,
            pages=pages,
            has_next=params.page < pages,
            has_prev=params.page > 1,
        )
```

**使用示例**：

```python
# 文章分页
posts_response: PaginatedResponse[Post] = PaginatedResponse.create(
    items=[post1, post2, post3],  # list[Post]
    total=100,
    params=PaginationParams(page=1, size=20)
)
# posts_response.items[0] 的类型是 Post
posts_response.items[0].title  # ✅ IDE 提示 Post 的属性

# 用户分页
users_response: PaginatedResponse[User] = PaginatedResponse.create(
    items=[user1, user2, user3],  # list[User]
    total=50,
    params=PaginationParams(page=1, size=10)
)
# users_response.items[0] 的类型是 User
users_response.items[0].username  # ✅ IDE 提示 User 的属性
```

---

## 4. 泛型函数

### 4.1 基础用法

```python
from typing import TypeVar, List

T = TypeVar('T')

def reverse_list(items: List[T]) -> List[T]:
    """反转列表（保持类型）"""
    return items[::-1]

# 类型推断
numbers = reverse_list([1, 2, 3])      # List[int]
strings = reverse_list(["a", "b"])     # List[str]
```

### 4.2 项目实战：get_sortable_columns

**代码位置**：`app/api/pagination.py`

```python
def get_sortable_columns(model: type[ModelType]) -> dict[str, Any]:
    """动态获取模型的可排序字段

    使用 SQLAlchemy 的 inspect 功能，只返回真正的数据库列，
    排除关系字段和其他非列属性，防止 SQL 注入。

    Args:
        model: SQLAlchemy 模型类（必须继承 Base）

    Returns:
        dict: {字段名: 列对象} 的映射
    """
    sortable_fields = {}
    mapper = inspect(model)

    for column in mapper.columns:
        sortable_fields[column.name] = column

    return sortable_fields
```

**使用示例**：

```python
# 获取 Post 模型的可排序字段
post_fields = get_sortable_columns(Post)
print(post_fields.keys())
# dict_keys(['id', 'title', 'content', 'created_at', 'updated_at'])

# 获取 User 模型的可排序字段
user_fields = get_sortable_columns(User)
print(user_fields.keys())
# dict_keys(['id', 'username', 'email', 'created_at'])
```

### 4.3 项目实战：apply_safe_sorting

**代码位置**：`app/api/pagination.py`

```python
def apply_safe_sorting(
    query: Select[tuple[ModelType]],
    model: type[ModelType],
    sort_field: str,
    sort_order: str,
) -> Select[tuple[ModelType]]:
    """安全地应用排序

    通过模型反射验证排序字段是否为真实的数据库列，
    防止 SQL 注入和访问非法字段。

    Args:
        query: SQLAlchemy 查询对象
        model: 模型类
        sort_field: 排序字段名
        sort_order: 排序方向 ('asc' 或 'desc')

    Returns:
        添加排序的查询对象

    Raises:
        ValueError: 如果字段不存在或不可排序
    """
    # 动态获取可排序字段
    sortable_fields = get_sortable_columns(model)

    if sort_field not in sortable_fields:
        available_fields = ", ".join(sorted(sortable_fields.keys()))
        raise ValueError(
            f"Field '{sort_field}' is not sortable. "
            f"Available fields: {available_fields}"
        )

    # 获取列对象
    column = sortable_fields[sort_field]

    # 应用排序
    if sort_order == "desc":
        query = query.order_by(desc(column))
    else:
        query = query.order_by(asc(column))

    return query
```

**类型安全优势**：

```python
# ✅ 正确：Post 是 ModelType
query = select(Post)
query = apply_safe_sorting(query, Post, "created_at", "desc")

# ❌ 错误：str 不是 ModelType (bound=Base)
query = apply_safe_sorting(query, str, "name", "asc")  # mypy 报错
```

---

## 5. 类型约束 (bound)

### 5.1 什么是 bound？

**bound** 约束 TypeVar 必须是某个类的子类。

```python
from typing import TypeVar

# 无约束：可以是任何类型
T = TypeVar('T')

# 有约束：必须是 Animal 或其子类
Animal = TypeVar('Animal', bound='AnimalBase')

class AnimalBase:
    def make_sound(self) -> str:
        return "..."

class Dog(AnimalBase):
    def make_sound(self) -> str:
        return "Woof!"

class Cat(AnimalBase):
    def make_sound(self) -> str:
        return "Meow!"

# 泛型函数（有约束）
def get_sound(animal: Animal) -> str:
    return animal.make_sound()  # ✅ 编译器知道 animal 有 make_sound 方法

# 使用
get_sound(Dog())  # ✅ Dog 是 AnimalBase 的子类
get_sound(Cat())  # ✅ Cat 是 AnimalBase 的子类
get_sound("dog")  # ❌ str 不是 AnimalBase 的子类
```

### 5.2 项目实战：bound=Base

**代码位置**：`app/crud/base.py` 和 `app/api/pagination.py`

```python
from app.db.database import Base

# 约束：必须是 SQLAlchemy 模型
ModelType = TypeVar("ModelType", bound=Base)
```

**为什么需要 bound=Base？**

```python
# ✅ 正确：Post 继承自 Base
class Post(Base):
    __tablename__ = "posts"
    id = Column(Integer, primary_key=True)

def paginate_query(..., model: type[ModelType], ...):
    # 编译器知道 model 是 SQLAlchemy 模型
    # 可以安全地使用 inspect(model) 等 SQLAlchemy 功能
    mapper = inspect(model)  # ✅ 类型安全

# ❌ 错误：str 不继承自 Base
paginate_query(..., model=str, ...)  # mypy 报错
```

### 5.3 项目实战：bound=BaseModel

**代码位置**：`app/crud/base.py`

```python
from pydantic import BaseModel

# 约束：必须是 Pydantic 模型
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)
```

**为什么需要 bound=BaseModel？**

```python
def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
    # 编译器知道 obj_in 是 Pydantic 模型
    # 可以安全地调用 model_dump() 方法
    obj_in_data = obj_in.model_dump()  # ✅ 类型安全

    # 如果没有 bound=BaseModel，编译器不知道 obj_in 有什么方法
    # obj_in.model_dump()  # ❌ mypy 报错
```

---

## 6. 多重继承

### 6.1 什么是多重继承？

**多重继承** 允许一个类同时继承多个父类。

```python
class A:
    def method_a(self):
        return "A"

class B:
    def method_b(self):
        return "B"

class C(A, B):  # 多重继承
    pass

c = C()
c.method_a()  # 继承自 A
c.method_b()  # 继承自 B
```

### 6.2 项目实战：PaginatedResponse

**代码位置**：`app/api/pagination.py`

```python
class PaginatedResponse(BaseModel, Generic[ItemType]):
    """分页响应格式

    继承：
    1. BaseModel - Pydantic 数据验证
    2. Generic[ItemType] - 泛型支持
    """
    items: list[ItemType]
    total: int
    # ...
```

**为什么需要多重继承？**

**1. 继承 BaseModel**：

```python
# ✅ 获得 Pydantic 的功能
response = PaginatedResponse(
    items=[post1, post2],
    total=100,
    page=1,
    size=20,
    pages=5,
    has_next=True,
    has_prev=False
)

# Pydantic 自动验证
response.model_dump()      # 转换为字典
response.model_dump_json() # 转换为 JSON
```

**2. 继承 Generic[ItemType]**：

```python
# ✅ 获得泛型能力
posts_response: PaginatedResponse[Post] = ...
users_response: PaginatedResponse[User] = ...
```

### 6.3 继承顺序的重要性

**MRO（Method Resolution Order）**：

```python
class PaginatedResponse(BaseModel, Generic[ItemType]):
    pass

# MRO: PaginatedResponse -> BaseModel -> Generic[ItemType] -> object
print(PaginatedResponse.__mro__)
```

**规则**：

-   Pydantic 的 `BaseModel` 必须在 `Generic` 之前
-   保证 Pydantic 的验证功能优先

---

## 7. 实战案例分析

### 7.1 案例 1：CRUDUser 完整流程

**步骤 1：定义模型**

```python
# app/models/user.py
from app.db.database import Base

class User(Base):
    __tablename__ = "users"
    id = Column(UUID, primary_key=True)
    username = Column(String(50), unique=True)
    email = Column(String(100), unique=True)
```

**步骤 2：定义 Schema**

```python
# app/schemas/user.py
from pydantic import BaseModel, EmailStr

class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str

class UserUpdate(BaseModel):
    email: EmailStr | None = None
    nickname: str | None = None
```

**步骤 3：定义 CRUD 类**

```python
# app/crud/user.py
from app.crud.base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    """用户 CRUD 操作

    类型参数：
    - ModelType = User
    - CreateSchemaType = UserCreate
    - UpdateSchemaType = UserUpdate

    继承的方法：
    - get(db, id) -> User | None
    - create(db, obj_in: UserCreate) -> User
    - update(db, db_obj: User, obj_in: UserUpdate) -> User
    - remove(db, id) -> User | None
    """
    pass

# 创建实例
crud_user = CRUDUser(User)
```

**步骤 4：使用 CRUD**

```python
# API 端点中使用
@router.post("/users", response_model=UserResponse)
def create_user(
    user_in: UserCreate,
    db: Session = Depends(get_db)
) -> User:
    # ✅ 类型安全：user_in 是 UserCreate
    user = crud_user.create(db, obj_in=user_in)
    # ✅ 类型安全：user 是 User
    return user
```

### 7.2 案例 2：分页查询完整流程

**步骤 1：定义分页参数**

```python
params = PaginationParams(
    page=1,
    size=20,
    sort="created_at",
    order="desc"
)
```

**步骤 2：构建查询**

```python
from sqlalchemy import select

query = select(Post)
```

**步骤 3：执行分页查询**

```python
items, total = paginate_query(
    db=db,
    query=query,
    params=params,
    model=Post  # ✅ 类型约束：必须是 Base 的子类
)
# items 的类型是 list[Post]
# total 的类型是 int
```

**步骤 4：创建分页响应**

```python
response = PaginatedResponse[Post].create(
    items=items,
    total=total,
    params=params
)
# response 的类型是 PaginatedResponse[Post]
```

**步骤 5：API 端点中使用**

```python
@router.get("/posts", response_model=PaginatedResponse[PostResponse])
def get_posts(
    db: Session = Depends(get_db),
    params: PaginationParams = Depends()
) -> PaginatedResponse[PostResponse]:
    query = select(Post)
    items, total = paginate_query(db, query, params, model=Post)
    return PaginatedResponse.create(items, total, params)
```

---

## 8. 最佳实践

### 8.1 命名规范

| 类型             | 命名规范                  | 示例                                   |
| ---------------- | ------------------------- | -------------------------------------- |
| **泛型 TypeVar** | `XxxType` 后缀            | `ItemType`, `ModelType`                |
| **约束 TypeVar** | 描述性名称                | `CreateSchemaType`, `UpdateSchemaType` |
| **泛型类**       | PascalCase + `Generic[T]` | `PaginatedResponse[ItemType]`          |

### 8.2 类型注解完整性

**✅ 好的实践**：

```python
def paginate_query(
    db: Session,
    query: Select[tuple[ModelType]],  # 明确类型
    params: PaginationParams,
    model: type[ModelType],
    *,
    count_query: Select[tuple[int]] | None = None,
) -> tuple[list[ModelType], int]:  # 明确返回类型
    pass
```

**❌ 不好的实践**：

```python
def paginate_query(db, query, params, model, *, count_query=None):
    # 没有类型注解，失去类型安全
    pass
```

### 8.3 泛型约束的使用

**何时使用 bound**：

```python
# ✅ 使用 bound：需要调用特定方法
ModelType = TypeVar("ModelType", bound=Base)

def inspect_model(model: type[ModelType]):
    # 编译器知道 model 继承自 Base
    mapper = inspect(model)  # ✅ 类型安全

# ❌ 不使用 bound：不知道类型有什么方法
T = TypeVar("T")

def inspect_model(model: type[T]):
    mapper = inspect(model)  # ❌ mypy 报错
```

### 8.4 多重继承顺序

**规则**：Pydantic 的 `BaseModel` 必须在 `Generic` 之前

```python
# ✅ 正确顺序
class PaginatedResponse(BaseModel, Generic[ItemType]):
    pass

# ❌ 错误顺序
class PaginatedResponse(Generic[ItemType], BaseModel):
    pass  # 可能导致 Pydantic 功能失效
```

### 8.5 类型安全检查

**使用 mypy 检查**：

```bash
# 检查单个文件
uv run mypy app/crud/base.py

# 检查整个项目
uv run mypy app tests
```

---

## 9. 常见问题

### Q1：什么时候使用泛型？

**A**：当你需要编写可以处理多种类型的代码，同时保持类型安全时使用泛型。

**典型场景**：

-   CRUD 基类（处理不同模型）
-   分页响应（包装不同数据）
-   工具函数（处理不同类型）

### Q2：TypeVar 和 Generic 的区别？

**A**：

-   `TypeVar` 是类型变量，用于声明泛型参数
-   `Generic` 是泛型基类，用于定义泛型类

```python
T = TypeVar('T')  # 声明类型变量

class Box(Generic[T]):  # 使用 Generic 定义泛型类
    def __init__(self, item: T):
        self.item = item
```

### Q3：为什么需要 bound 约束？

**A**：`bound` 约束确保类型变量只能是特定类的子类，这样编译器知道该类型有哪些方法和属性。

```python
# 有约束：编译器知道 model 的方法
ModelType = TypeVar("ModelType", bound=Base)

# 无约束：编译器不知道 T 有什么方法
T = TypeVar("T")
```

### Q4：多重继承会有性能问题吗？

**A**：多重继承本身不会有性能问题，但要注意 MRO（方法解析顺序）可能导致的逻辑问题。

---

## 10. 总结

### 10.1 核心概念

| 概念         | 用途         | 项目示例                        |
| ------------ | ------------ | ------------------------------- |
| **TypeVar**  | 声明类型变量 | `ModelType`, `ItemType`         |
| **Generic**  | 定义泛型类   | `CRUDBase[M, C, U]`             |
| **bound**    | 约束类型变量 | `bound=Base`, `bound=BaseModel` |
| **多重继承** | 组合多个功能 | `BaseModel, Generic[T]`         |

### 10.2 设计模式

**1. 泛型 CRUD 基类模式**：

```python
class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    # 一个基类，处理所有模型的 CRUD 操作
    pass
```

**2. 泛型分页响应模式**：

```python
class PaginatedResponse(BaseModel, Generic[ItemType]):
    # 一个响应类，包装任意类型的数据列表
    pass
```

### 10.3 最佳实践清单

-   ✅ 为所有公共函数和方法添加类型注解
-   ✅ 使用 `bound` 约束 TypeVar 的类型
-   ✅ 遵循命名规范（`XxxType` 后缀）
-   ✅ 多重继承时注意顺序（BaseModel 在前）
-   ✅ 使用 mypy 进行类型检查
-   ✅ 在文档注释中说明泛型参数的含义

---

## 参考资源

-   [Python Typing 官方文档](https://docs.python.org/3/library/typing.html)
-   [PEP 484 - Type Hints](https://www.python.org/dev/peps/pep-0484/)
-   [Pydantic Generic Models](https://docs.pydantic.dev/latest/concepts/models/#generic-models)
-   [SQLAlchemy Type Annotations](https://docs.sqlalchemy.org/en/20/orm/extensions/mypy.html)

---

**下一步学习**：

-   [SQLAlchemy ORM 模型定义](./sqlalchemy教程/03-SQLAlchemy-ORM模型定义实战详解.md)
-   [Pydantic 数据验证](03-Pydantic数据验证与Schema设计.md)
-   [FastAPI 依赖注入](05-FastAPI依赖注入与认证依赖.md)
