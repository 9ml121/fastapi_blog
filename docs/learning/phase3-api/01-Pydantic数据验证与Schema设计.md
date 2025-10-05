# Pydantic 数据验证与 Schema 设计

> **学习目标**：理解数据验证层的重要性，掌握 Pydantic 在 FastAPI 中的应用，学会设计优雅的 Schema 架构

## 📚 目录

1. [Pydantic 是什么](#1-pydantic-是什么)
2. [为什么需要数据验证层](#2-为什么需要数据验证层)
3. [Pydantic vs SQLAlchemy](#3-pydantic-vs-sqlalchemy)
4. [Schema 设计模式](#4-schema-设计模式)
5. [数据验证机制](#5-数据验证机制)
6. [FastAPI 集成](#6-fastapi-集成)
7. [最佳实践](#7-最佳实践)
8. [常见陷阱](#8-常见陷阱)

---

## 1. Pydantic 是什么

### 1.1 核心定义

**Pydantic** 是一个使用 Python 类型注解进行数据验证和设置管理的库。它的核心理念是：

> **"使用 Python 类型注解来定义数据的形状和验证规则"**

```python
from pydantic import BaseModel, EmailStr

class User(BaseModel):
    username: str
    email: EmailStr
    age: int
    is_active: bool = True  # 默认值
```

### 1.2 Pydantic 的三大功能

| 功能 | 说明 | 示例 |
|------|------|------|
| **数据验证** | 自动验证输入数据类型和格式 | `age` 必须是整数 |
| **数据解析** | 将 JSON/dict 自动转换为 Python 对象 | `{"age": "25"}` → `age=25` |
| **数据序列化** | 将 Python 对象转换为 JSON/dict | `user.model_dump()` |

### 1.3 为什么 FastAPI 选择 Pydantic

FastAPI 使用 Pydantic 作为核心数据验证库，主要原因：

1. ✅ **类型安全**：编译时类型检查（配合 mypy）
2. ✅ **自动验证**：运行时自动验证数据
3. ✅ **自动文档**：自动生成 OpenAPI/Swagger 文档
4. ✅ **高性能**：底层使用 Rust 编写的验证器（Pydantic V2）
5. ✅ **现代 Python**：充分利用类型注解特性

---

## 2. 为什么需要数据验证层

### 2.1 Web 应用的分层架构

一个典型的 Web 应用包含多个层次，每层有明确的职责：

```
┌─────────────────────────────────────────────┐
│  API 层 (FastAPI Routes)                     │  ← 接收 HTTP 请求
│  - 路由处理                                   │
│  - 请求/响应                                  │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  验证层 (Pydantic Schemas) ★ 我们在这里 ★   │  ← 数据验证和转换
│  - 数据验证                                   │
│  - 类型转换                                   │
│  - 序列化/反序列化                            │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  业务逻辑层 (CRUD/Services)                  │  ← 业务逻辑处理
│  - 业务规则                                   │
│  - 数据操作                                   │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  数据层 (SQLAlchemy Models)                  │  ← 数据库映射
│  - ORM 映射                                   │
│  - 数据库操作                                 │
└─────────────────────────────────────────────┘
```

### 2.2 为什么要分离验证层？

#### 问题场景：没有验证层

```python
# ❌ 不好的做法：直接使用 SQLAlchemy 模型处理 API 请求
@app.post("/users")
def create_user(user: User):  # User 是 SQLAlchemy 模型
    # 问题 1：暴露了数据库模型的所有字段（包括内部字段）
    # 问题 2：无法验证密码强度、邮箱格式等业务规则
    # 问题 3：客户端可以修改任何字段（如 is_superuser）
    # 问题 4：无法区分创建和更新的字段要求
    db.add(user)
    db.commit()
    return user  # 问题 5：返回时包含了密码哈希等敏感信息
```

#### 解决方案：使用 Pydantic Schema

```python
# ✅ 好的做法：使用专门的 Schema
class UserCreate(BaseModel):
    """用户注册时的数据验证"""
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)
    
    @field_validator('password')
    def validate_password_strength(cls, v):
        # 自定义密码强度验证
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含大写字母')
        return v

class UserResponse(BaseModel):
    """返回给客户端的用户数据"""
    id: UUID
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    # 注意：没有 password_hash、is_superuser 等敏感字段

@app.post("/users", response_model=UserResponse)
def create_user(user_data: UserCreate, db: Session):
    # 1. Pydantic 自动验证了数据
    # 2. 只包含允许的字段
    # 3. 密码强度已验证
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password)
    )
    db.add(db_user)
    db.commit()
    return db_user  # FastAPI 自动使用 UserResponse 过滤字段
```

### 2.3 职责分离的优势

| 层次 | 职责 | 技术 | 关注点 |
|------|------|------|--------|
| **Pydantic Schema** | 数据验证、转换、序列化 | Pydantic | **外部接口**（API 输入/输出） |
| **SQLAlchemy Model** | 数据库映射、持久化 | SQLAlchemy | **内部存储**（数据库结构） |

**核心原则**：
- Schema 关注"数据如何从外部进入系统"和"数据如何展示给外部"
- Model 关注"数据如何在数据库中存储"

---

## 3. Pydantic vs SQLAlchemy

### 3.1 核心区别对比

| 对比维度 | Pydantic Schema | SQLAlchemy Model |
|---------|----------------|------------------|
| **目的** | 数据验证和序列化 | 数据库 ORM 映射 |
| **使用场景** | API 输入/输出 | 数据库操作 |
| **生命周期** | 请求-响应期间 | 数据库会话期间 |
| **验证时机** | 实例化时（构造函数） | 提交数据库时 |
| **类型系统** | Python 类型注解 | SQLAlchemy 类型 |
| **继承基类** | `BaseModel` | `DeclarativeBase` |
| **序列化** | `model_dump()`, `model_dump_json()` | 需要手动实现 |
| **不可变性** | 支持（`model_config frozen=True`） | 可变对象 |

### 3.2 字段定义对比

```python
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String
from datetime import datetime
from uuid import UUID

# ============ Pydantic Schema ============
class UserCreate(BaseModel):
    """API 输入：用户注册"""
    username: str = Field(
        min_length=3, 
        max_length=50,
        description="用户名，3-50个字符"
    )
    email: EmailStr  # 自动验证邮箱格式
    password: str = Field(min_length=8)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "username": "johndoe",
                "email": "john@example.com",
                "password": "SecurePass123"
            }
        }
    }

class UserResponse(BaseModel):
    """API 输出：用户信息"""
    id: UUID
    username: str
    email: EmailStr
    is_active: bool
    created_at: datetime
    
    model_config = {"from_attributes": True}  # 允许从 ORM 对象创建

# ============ SQLAlchemy Model ============
class User(DeclarativeBase):
    """数据库模型：用户表"""
    __tablename__ = "users"
    
    id: Mapped[UUID] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))  # 注意：存储哈希值
    is_active: Mapped[bool] = mapped_column(default=True)
    is_superuser: Mapped[bool] = mapped_column(default=False)
    created_at: Mapped[datetime] = mapped_column(default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        default=datetime.utcnow, 
        onupdate=datetime.utcnow
    )
```

### 3.3 关键差异解析

#### 1️⃣ 密码处理

```python
# Pydantic Schema：接收明文密码
class UserCreate(BaseModel):
    password: str  # 明文，用于验证

# SQLAlchemy Model：存储密码哈希
class User(Base):
    password_hash: Mapped[str]  # 哈希值，永不暴露

# 转换过程
user_data = UserCreate(password="SecurePass123")
db_user = User(
    password_hash=hash_password(user_data.password)  # 转换为哈希
)
```

#### 2️⃣ 字段可见性

```python
# Schema 控制 API 可见字段
class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    # 没有 password_hash、is_superuser 等敏感字段

# Model 包含所有数据库字段
class User(Base):
    id: Mapped[UUID]
    username: Mapped[str]
    email: Mapped[str]
    password_hash: Mapped[str]      # 敏感
    is_superuser: Mapped[bool]       # 敏感
    deleted_at: Mapped[datetime]     # 内部使用
```

#### 3️⃣ 验证时机

```python
# Pydantic：实例化时立即验证
try:
    user = UserCreate(
        username="ab",  # 太短
        email="invalid-email",
        password="weak"
    )
except ValidationError as e:
    print(e)  # 立即抛出验证错误

# SQLAlchemy：提交数据库时才检查（数据库约束）
user = User(
    username="ab",  # 此时不报错
    email="invalid-email"
)
db.add(user)
db.commit()  # 这里才可能报数据库约束错误
```

---

## 4. Schema 设计模式

### 4.1 四种常见 Schema 模式

在实际项目中，我们通常为一个资源（如 User）设计 4 种不同的 Schema：

```python
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Optional
from datetime import datetime
from uuid import UUID

# ============ 1. Create Schema ============
class UserCreate(BaseModel):
    """
    用途：API 创建资源时的输入数据
    特点：
    - 包含必填字段
    - 不包含自动生成的字段（id, created_at）
    - 包含密码等仅在创建时需要的字段
    """
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)
    full_name: Optional[str] = Field(None, max_length=100)


# ============ 2. Update Schema ============
class UserUpdate(BaseModel):
    """
    用途：API 更新资源时的输入数据
    特点：
    - 所有字段都是可选的（部分更新）
    - 不包含不允许修改的字段（如 id, created_at）
    - 通常不包含密码（密码修改应该单独的端点）
    """
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = Field(None, max_length=100)
    is_active: Optional[bool] = None


# ============ 3. Response Schema ============
class UserResponse(BaseModel):
    """
    用途：API 返回给客户端的数据
    特点：
    - 包含客户端需要的所有字段
    - 不包含敏感字段（password_hash, deleted_at）
    - 包含自动生成的字段（id, created_at）
    """
    id: UUID
    username: str
    email: EmailStr
    full_name: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = ConfigDict(from_attributes=True)  # 允许从 ORM 对象创建


# ============ 4. InDB Schema ============
class UserInDB(UserResponse):
    """
    用途：内部使用，包含所有数据库字段
    特点：
    - 继承自 Response Schema
    - 额外包含敏感字段
    - 仅在内部业务逻辑中使用，不返回给客户端
    """
    password_hash: str
    is_superuser: bool
    deleted_at: Optional[datetime] = None
```

### 4.2 Schema 继承关系图

```
┌─────────────────────┐
│   UserBase          │  ← 基础字段（可选，用于复用）
│   - username        │
│   - email           │
│   - full_name       │
└─────────────────────┘
          ↓
    ┌─────┴─────┐
    ↓           ↓
┌─────────┐ ┌─────────┐
│ Create  │ │ Update  │  ← 输入 Schema
│ + pwd   │ │ (可选)  │
└─────────┘ └─────────┘

┌─────────────────────┐
│   UserResponse      │  ← 输出 Schema
│   + id              │
│   + created_at      │
│   + updated_at      │
└─────────────────────┘
          ↓
┌─────────────────────┐
│   UserInDB          │  ← 内部 Schema
│   + password_hash   │
│   + is_superuser    │
│   + deleted_at      │
└─────────────────────┘
```

### 4.3 实际应用示例

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

router = APIRouter()

# ============ 创建用户 ============
@router.post("/users", response_model=UserResponse, status_code=201)
def create_user(
    user_data: UserCreate,  # ← 使用 Create Schema 验证输入
    db: Session = Depends(get_db)
):
    # 1. Pydantic 自动验证了 user_data
    
    # 2. 检查用户名是否已存在
    if get_user_by_username(db, user_data.username):
        raise HTTPException(status_code=409, detail="用户名已存在")
    
    # 3. 创建数据库对象
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hash_password(user_data.password),  # 哈希密码
        full_name=user_data.full_name
    )
    
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    # 4. 返回时自动转换为 UserResponse
    #    （自动排除 password_hash 等敏感字段）
    return db_user


# ============ 更新用户 ============
@router.patch("/users/{user_id}", response_model=UserResponse)
def update_user(
    user_id: UUID,
    user_data: UserUpdate,  # ← 使用 Update Schema（所有字段可选）
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 只更新提供的字段（部分更新）
    update_data = user_data.model_dump(exclude_unset=True)  # 只包含设置的字段
    for field, value in update_data.items():
        setattr(db_user, field, value)
    
    db.commit()
    db.refresh(db_user)
    return db_user


# ============ 获取用户 ============
@router.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    # 自动转换为 UserResponse（排除敏感字段）
    return db_user
```

---

## 5. 数据验证机制

### 5.1 内置验证器

Pydantic 提供了丰富的内置验证功能：

```python
from pydantic import BaseModel, EmailStr, HttpUrl, Field, constr, conint
from typing import Optional
from datetime import datetime

class UserProfile(BaseModel):
    # ============ 字符串验证 ============
    username: str = Field(
        min_length=3,
        max_length=50,
        pattern=r'^[a-zA-Z0-9_]+$',  # 正则表达式
        description="用户名：3-50个字符，只允许字母、数字、下划线"
    )
    
    # 使用 constr（constrained string）
    display_name: constr(
        min_length=1,
        max_length=100,
        strip_whitespace=True  # 自动去除首尾空格
    )
    
    # ============ 邮箱验证 ============
    email: EmailStr  # 自动验证邮箱格式
    
    # ============ URL 验证 ============
    website: Optional[HttpUrl] = None  # 自动验证 URL 格式
    avatar_url: Optional[str] = Field(None, regex=r'^https?://.*\.(jpg|png|gif)$')
    
    # ============ 数字验证 ============
    age: int = Field(ge=0, le=150)  # ge: >=, le: <=
    score: float = Field(gt=0, lt=100)  # gt: >, lt: <
    
    # 使用 conint（constrained int）
    follower_count: conint(ge=0) = 0
    
    # ============ 日期验证 ============
    birth_date: datetime
    registered_at: datetime = Field(default_factory=datetime.utcnow)
    
    # ============ 枚举验证 ============
    from enum import Enum
    
    class Role(str, Enum):
        USER = "user"
        ADMIN = "admin"
        MODERATOR = "moderator"
    
    role: Role = Role.USER  # 只能是枚举中的值
    
    # ============ 列表验证 ============
    tags: list[str] = Field(default_factory=list, max_length=10)
    interests: set[str] = set()  # 自动去重
```

> [!NOTE]
> **💡 风格对比与选择：`constr` vs `Field`**
>
> 你可能注意到有两种方式可以约束字符串和整数：
> 1.  **`constr`/`conint` 风格**: `name: constr(min_length=1)`
> 2.  **`Field` 风格**: `name: str = Field(min_length=1)`
>
> **区别**：
> - `constr` 是一个返回“带约束的类型”的函数，是 Pydantic V1 的旧风格。
> - `Field` 是 Pydantic V2 推荐的现代风格，它将约束作为字段的元数据，更清晰、功能更强大（如支持 `description`, `example` 等）。
>
> **结论：在我们的项目中，应优先使用 `Field` 风格。**

### 5.2 自定义验证器

使用 `@field_validator` 装饰器创建自定义验证逻辑：

```python
from pydantic import BaseModel, field_validator, model_validator
from typing import Any

class UserCreate(BaseModel):
    username: str
    email: str
    password: str
    password_confirm: str
    
    # ============ 字段级验证器 ============
    @field_validator('username')
    @classmethod
    def validate_username(cls, v: str) -> str:
        """验证用户名格式"""
        if not v.isalnum() and '_' not in v:
            raise ValueError('用户名只能包含字母、数字和下划线')
        
        if v.lower() in ['admin', 'root', 'system']:
            raise ValueError('该用户名为保留用户名')
        
        return v.lower()  # 统一转为小写
    
    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """验证密码强度"""
        if len(v) < 8:
            raise ValueError('密码至少需要8个字符')
        
        if not any(c.isupper() for c in v):
            raise ValueError('密码必须包含至少一个大写字母')
        
        if not any(c.islower() for c in v):
            raise ValueError('密码必须包含至少一个小写字母')
        
        if not any(c.isdigit() for c in v):
            raise ValueError('密码必须包含至少一个数字')
        
        return v
    
    # ============ 模型级验证器 ============
    @model_validator(mode='after')
    def validate_passwords_match(self) -> 'UserCreate':
        """验证两次密码输入是否一致"""
        if self.password != self.password_confirm:
            raise ValueError('两次密码输入不一致')
        return self


# 使用示例
try:
    user = UserCreate(
        username="JohnDoe",
        email="john@example.com",
        password="SecurePass123",
        password_confirm="SecurePass123"
    )
    print(user.username)  # 输出: johndoe（已转小写）
except ValidationError as e:
    print(e.errors())
```

### 5.3 验证模式

```python
from pydantic import BaseModel, field_validator, ValidationInfo

class Product(BaseModel):
    name: str
    price: float
    discount_price: Optional[float] = None
    
    @field_validator('discount_price')
    @classmethod
    def validate_discount(cls, v: Optional[float], info: ValidationInfo) -> Optional[float]:
        """验证折扣价必须低于原价"""
        if v is not None:
            # 通过 info.data 访问其他字段的值
            price = info.data.get('price')
            if price is not None and v >= price:
                raise ValueError('折扣价必须低于原价')
        return v

# 测试
product = Product(name="Book", price=100, discount_price=80)  # ✅ 通过
# product = Product(name="Book", price=100, discount_price=120)  # ❌ 报错
```

---

## 6. FastAPI 集成

### 6.1 请求数据验证

FastAPI 自动使用 Pydantic 验证请求数据：

```python
from fastapi import FastAPI, HTTPException, status
from pydantic import ValidationError

app = FastAPI()

@app.post("/users", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def create_user(user_data: UserCreate):  # ← Pydantic 自动验证
    """
    FastAPI 的处理流程：
    1. 接收 HTTP 请求的 JSON 数据
    2. 尝试创建 UserCreate 实例
    3. 自动运行所有验证器
    4. 验证失败 → 返回 422 错误（带详细错误信息）
    5. 验证成功 → 将实例传递给函数
    """
    # 这里的 user_data 已经是验证过的 UserCreate 对象
    # 可以安全使用
    return create_user_in_db(user_data)


# 客户端发送无效数据时的响应示例：
# POST /users
# {"username": "ab", "email": "invalid", "password": "weak"}
#
# 响应 422:
# {
#   "detail": [
#     {
#       "type": "string_too_short",
#       "loc": ["body", "username"],
#       "msg": "String should have at least 3 characters",
#       "input": "ab"
#     },
#     {
#       "type": "value_error",
#       "loc": ["body", "email"],
#       "msg": "value is not a valid email address",
#       "input": "invalid"
#     }
#   ]
# }
```

### 6.2 响应数据序列化

使用 `response_model` 控制响应数据：

```python
@app.get("/users/{user_id}", response_model=UserResponse)
def get_user(user_id: UUID, db: Session = Depends(get_db)):
    """
    response_model 的作用：
    1. 自动过滤字段（只返回 UserResponse 中定义的字段）
    2. 数据验证（确保返回的数据符合 schema）
    3. 生成 OpenAPI 文档
    4. 序列化（将 ORM 对象转换为 JSON）
    """
    db_user = get_user_by_id(db, user_id)
    if not db_user:
        raise HTTPException(status_code=404)
    
    # db_user 可能包含 password_hash 等敏感字段
    # 但 FastAPI 只会返回 UserResponse 中定义的字段
    return db_user  # ← 自动转换为 UserResponse
```

### 6.3 配置序列化

```python
from pydantic import BaseModel, ConfigDict

class UserResponse(BaseModel):
    id: UUID
    username: str
    email: EmailStr
    created_at: datetime
    
    # ============ 配置选项 ============
    model_config = ConfigDict(
        # 允许从 ORM 对象创建（重要！）
        from_attributes=True,
        
        # JSON 序列化配置
        json_encoders={
            datetime: lambda v: v.isoformat(),  # 自定义日期格式
            UUID: lambda v: str(v)  # UUID 转字符串
        },
        
        # 字段别名（API 字段名 vs Python 属性名）
        populate_by_name=True,  # 允许使用原名称或别名
        
        # 示例数据（用于 API 文档）
        json_schema_extra={
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "username": "johndoe",
                "email": "john@example.com",
                "created_at": "2024-01-01T00:00:00Z"
            }
        }
    )

# from_attributes=True 的作用：
class User:  # SQLAlchemy 模型
    id = UUID("550e8400-e29b-41d4-a716-446655440000")
    username = "johndoe"
    email = "john@example.com"
    password_hash = "hashed..."  # 不在 UserResponse 中
    created_at = datetime(2024, 1, 1)

db_user = User()
# 使用 from_attributes=True 可以直接从对象属性创建
response = UserResponse.model_validate(db_user)
# 等价于：
# response = UserResponse(
#     id=db_user.id,
#     username=db_user.username,
#     email=db_user.email,
#     created_at=db_user.created_at
# )
```

---

## 7. 最佳实践

### 7.1 Schema 组织结构

推荐的项目结构：

```
app/
├── schemas/
│   ├── __init__.py
│   ├── user.py          # 用户相关 schemas
│   ├── post.py          # 文章相关 schemas
│   ├── comment.py       # 评论相关 schemas
│   └── common.py        # 通用 schemas（分页、响应等）
```

```python
# app/schemas/common.py
from pydantic import BaseModel
from typing import Generic, TypeVar, List

T = TypeVar('T')

class PaginationParams(BaseModel):
    """分页参数"""
    page: int = Field(1, ge=1, description="页码")
    page_size: int = Field(20, ge=1, le=100, description="每页数量")

class PaginatedResponse(BaseModel, Generic[T]):
    """分页响应"""
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int

class MessageResponse(BaseModel):
    """通用消息响应"""
    message: str
```

### 7.2 复用基类

```python
# app/schemas/user.py
from pydantic import BaseModel, EmailStr, Field
from typing import Optional

class UserBase(BaseModel):
    """用户基础字段（复用）"""
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    full_name: Optional[str] = None

class UserCreate(UserBase):
    """创建用户（继承 + 添加密码）"""
    password: str = Field(min_length=8)

class UserUpdate(BaseModel):
    """更新用户（所有字段可选）"""
    username: Optional[str] = Field(None, min_length=3, max_length=50)
    email: Optional[EmailStr] = None
    full_name: Optional[str] = None

class UserResponse(UserBase):
    """用户响应（继承 + 添加系统字段）"""
    id: UUID
    is_active: bool
    created_at: datetime
    
    model_config = ConfigDict(from_attributes=True)
```

### 7.3 使用类型别名

```python
from typing import Annotated
from pydantic import Field

# 定义常用类型别名
Username = Annotated[str, Field(min_length=3, max_length=50, pattern=r'^[a-zA-Z0-9_]+$')]
Password = Annotated[str, Field(min_length=8)]
Email = EmailStr

class UserCreate(BaseModel):
    username: Username  # 复用验证规则
    email: Email
    password: Password
```

### 7.4 环境配置管理

```python
# app/core/config.py
from pydantic_settings import BaseSettings
from pydantic import Field, PostgresDsn

class Settings(BaseSettings):
    """应用配置（从环境变量加载）"""
    
    # 应用配置
    app_name: str = "FastAPI Blog"
    debug: bool = False
    api_v1_prefix: str = "/api/v1"
    
    # 数据库配置
    database_url: PostgresDsn = Field(
        ...,  # 必填
        description="PostgreSQL 数据库连接 URL"
    )
    
    # JWT 配置
    secret_key: str = Field(
        ...,
        min_length=32,
        description="JWT 密钥，至少32个字符"
    )
    access_token_expire_minutes: int = 30
    
    # CORS 配置
    cors_origins: list[str] = ["http://localhost:3000"]
    
    model_config = ConfigDict(
        env_file=".env",  # 从 .env 文件加载
        env_file_encoding="utf-8",
        case_sensitive=False  # 环境变量不区分大小写
    )

# 使用
settings = Settings()
print(settings.database_url)  # 从环境变量 DATABASE_URL 加载
```

---

## 8. 常见陷阱

### 8.1 忘记设置 `from_attributes=True`

```python
# ❌ 错误示例
class UserResponse(BaseModel):
    id: UUID
    username: str
    # 忘记设置 model_config

# 使用时报错
db_user = get_user_by_id(db, user_id)
response = UserResponse.model_validate(db_user)  # ❌ ValidationError!

# ✅ 正确示例
class UserResponse(BaseModel):
    id: UUID
    username: str
    
    model_config = ConfigDict(from_attributes=True)  # ✅ 添加这个

# 现在可以正常使用
response = UserResponse.model_validate(db_user)  # ✅ 成功
```

### 8.2 循环引用问题

```python
# ❌ 错误示例：循环引用
# user.py
from .post import PostResponse

class UserResponse(BaseModel):
    id: UUID
    posts: list[PostResponse]  # ❌ 引用 PostResponse

# post.py
from .user import UserResponse  # ❌ 循环引用

class PostResponse(BaseModel):
    id: UUID
    author: UserResponse

# ✅ 解决方案1：使用 TYPE_CHECKING 和 model_rebuild()
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from .post import PostResponse

class UserResponse(BaseModel):
    id: UUID
    posts: list['PostResponse'] = []  # 使用字符串引用

# 在模块末尾重建模型
from .post import PostResponse
UserResponse.model_rebuild()

# ✅ 解决方案2：嵌套定义
class UserResponse(BaseModel):
    id: UUID
    username: str

class PostResponse(BaseModel):
    id: UUID
    title: str
    author: UserResponse  # 单向引用，避免循环
```

### 8.3 可选字段的默认值陷阱

```python
# ❌ 错误示例：可变默认值
class UserUpdate(BaseModel):
    tags: list[str] = []  # ❌ 危险！所有实例共享同一个列表

user1 = UserUpdate()
user1.tags.append("admin")
user2 = UserUpdate()
print(user2.tags)  # ['admin'] ← 意外修改了 user2！

# ✅ 正确示例：使用 default_factory
from pydantic import Field

class UserUpdate(BaseModel):
    tags: list[str] = Field(default_factory=list)  # ✅ 每个实例独立的列表

user1 = UserUpdate()
user1.tags.append("admin")
user2 = UserUpdate()
print(user2.tags)  # [] ← 正确
```

### 8.4 过度验证

```python
# ❌ 不好的做法：在 Schema 中做业务逻辑验证
class UserCreate(BaseModel):
    username: str
    email: EmailStr
    
    @field_validator('username')
    @classmethod
    def username_must_be_unique(cls, v):
        # ❌ 不应该在这里查询数据库
        if db.query(User).filter(User.username == v).first():
            raise ValueError('用户名已存在')
        return v

# ✅ 好的做法：在 API 层做业务逻辑验证
@app.post("/users")
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # ✅ 在这里检查业务规则
    if get_user_by_username(db, user_data.username):
        raise HTTPException(status_code=409, detail="用户名已存在")
    
    return create_user_in_db(db, user_data)
```

---

## 9. 总结

### 核心要点

1. **职责分离**：
   - Pydantic Schema = 数据验证 + 序列化（外部接口）
   - SQLAlchemy Model = 数据持久化（内部存储）

2. **四种 Schema 模式**：
   - `Create`：创建资源的输入
   - `Update`：更新资源的输入（字段可选）
   - `Response`：返回给客户端的输出
   - `InDB`：内部使用，包含敏感字段

3. **验证时机**：
   - Pydantic：实例化时立即验证
   - SQLAlchemy：数据库提交时验证约束

4. **最佳实践**：
   - 使用 `from_attributes=True` 允许从 ORM 创建
   - 复用基类减少重复代码
   - 使用 `Field()` 添加验证规则和文档
   - 自定义验证器只做格式验证，不做业务逻辑

### 下一步

阅读完本文档后，你应该能够：
- ✅ 理解为什么需要独立的数据验证层
- ✅ 区分 Pydantic Schema 和 SQLAlchemy Model 的职责
- ✅ 设计符合 RESTful 规范的 Schema 结构
- ✅ 使用验证器实现复杂的数据验证逻辑
- ✅ 在 FastAPI 中正确使用 Pydantic

**准备好动手实践了吗？**
接下来我们将创建博客系统的 User Schemas，应用这些概念！🚀

---

## 参考资源

- [Pydantic 官方文档](https://docs.pydantic.dev/)
- [FastAPI 数据验证教程](https://fastapi.tiangolo.com/tutorial/body/)
- [Pydantic V2 迁移指南](https://docs.pydantic.dev/latest/migration/)
