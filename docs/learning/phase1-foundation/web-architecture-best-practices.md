# 现代 Web 项目架构设计最佳实践

> 本文档详细讲解分层架构的设计原理、实践方法和常见陷阱，帮助你深入理解现代 Web 应用的架构精髓。

## 目录

- [1. 架构概览](#1-架构概览)
- [2. 分层架构详解](#2-分层架构详解)
- [3. 数据流转全景](#3-数据流转全景)
- [4. 设计原则](#4-设计原则)
- [5. 实战对比](#5-实战对比)
- [6. 常见陷阱](#6-常见陷阱)
- [7. 最佳实践清单](#7-最佳实践清单)

---

## 1. 架构概览

### 1.1 为什么需要分层？

**问题场景**：
```python
# ❌ 没有分层的代码（所有逻辑混在一起）
@app.post("/users")
async def create_user(username: str, password: str):
    # 验证逻辑
    if len(password) < 8:
        raise ValueError("密码太短")

    # 业务逻辑
    hashed = bcrypt.hash(password)

    # 数据库操作
    user = User(username=username, password_hash=hashed)
    db.add(user)
    db.commit()

    # 返回响应
    return {"id": user.id, "username": user.username}
```

**问题分析**：
- ❌ API 路由函数承担了 4 种职责（验证、业务、存储、响应）
- ❌ 无法复用逻辑（其他 API 创建用户要重写一遍）
- ❌ 难以测试（必须启动整个 Web 服务才能测试数据库操作）
- ❌ 难以维护（改密码规则要改 API 函数）

**分层架构解决方案**：
```
┌─────────────────────────────────────┐
│  API Layer (路由层)                 │  ← 处理 HTTP 请求/响应
├─────────────────────────────────────┤
│  Schema Layer (数据验证层)          │  ← 验证输入/输出格式
├─────────────────────────────────────┤
│  CRUD Layer (数据操作层)            │  ← 封装数据库操作
├─────────────────────────────────────┤
│  Model Layer (数据模型层)           │  ← 定义数据库表结构
└─────────────────────────────────────┘
```

### 1.2 本项目的分层结构

```
app/
├── api/          # API 路由层 - 处理 HTTP 请求
├── schemas/      # 数据验证层 - 定义输入输出格式
├── crud/         # 数据操作层 - 封装数据库 CRUD
├── models/       # 数据模型层 - SQLAlchemy ORM 模型
├── core/         # 核心工具 - 配置、安全、依赖注入
└── db/           # 数据库连接 - 会话管理
```

---

## 2. 分层架构详解

### 2.1 Model Layer（数据模型层）

**职责**：定义数据库表结构，是数据的"蓝图"

```python
# app/models/user.py
class User(Base):
    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))

    # 关系定义
    posts: Mapped[list["Post"]] = relationship(back_populates="author")
```

**关键特点**：
- ✅ **只关心数据结构**：字段类型、约束、索引、关系
- ✅ **ORM 映射**：Python 类 ↔ 数据库表
- ✅ **业务无关**：不包含业务逻辑（如"创建用户需要验证邮箱"）
- ✅ **持久化层**：是应用和数据库的桥梁

**反面案例**（违反单一职责）：
```python
# ❌ 错误：Model 不应包含业务逻辑
class User(Base):
    def create_with_welcome_email(self, email):
        self.email = email
        send_email(email, "欢迎注册")  # 业务逻辑不该在这里
```

---

### 2.2 Schema Layer（数据验证层）

**职责**：定义 API 的输入输出格式，是数据的"合同"

```python
# app/schemas/user.py

# 输入 Schema - 定义"什么数据可以进来"
class UserCreate(BaseModel):
    username: str = Field(min_length=3, max_length=50)
    email: EmailStr
    password: str = Field(min_length=8)

    @field_validator("password")
    def password_complexity(cls, v: str) -> str:
        if not any(char.isdigit() for char in v):
            raise ValueError("密码必须包含数字")
        return v

# 输出 Schema - 定义"什么数据可以出去"
class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    # 注意：不包含 password_hash（敏感信息）

    model_config = ConfigDict(from_attributes=True)
```

**关键特点**：
- ✅ **数据验证**：类型检查、长度限制、格式验证、自定义规则
- ✅ **API 契约**：前后端约定的数据格式
- ✅ **安全过滤**：排除敏感字段（如密码哈希）
- ✅ **文档生成**：Pydantic 自动生成 OpenAPI 文档

**三种常见 Schema**：

| Schema 类型 | 用途 | 特点 |
|------------|------|------|
| `UserCreate` | API 输入（POST） | 包含密码，所有字段必填 |
| `UserUpdate` | API 输入（PATCH） | 所有字段可选（部分更新）|
| `UserResponse` | API 输出 | 排除敏感信息，添加计算字段 |

---

### 2.3 CRUD Layer（数据操作层）

**职责**：封装所有数据库操作逻辑，是数据的"操作员"

```python
# app/crud/user.py

def get_user_by_id(db: Session, *, user_id: UUID) -> User | None:
    """通过 ID 查询用户"""
    return db.query(User).filter(
        User.id == user_id,
        User.deleted_at.is_(None)  # 软删除过滤
    ).first()

def create_user(db: Session, *, user_in: UserCreate) -> User:
    """创建用户"""
    # 1. 提取数据（排除密码）
    user_data = user_in.model_dump(exclude={"password"})

    # 2. 密码哈希处理
    hashed_password = hash_password(user_in.password)

    # 3. 创建 ORM 对象
    db_user = User(**user_data, password_hash=hashed_password)

    # 4. 数据库操作
    db.add(db_user)
    db.commit()
    db.refresh(db_user)

    return db_user

def update_user(db: Session, *, user_id: UUID, user_in: UserUpdate) -> User | None:
    """更新用户信息（部分更新）"""
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        return None

    # 只更新提供的字段
    update_data = user_in.model_dump(exclude_unset=True)

    # 特殊处理：密码需要哈希
    if "password" in update_data:
        hashed_password = hash_password(update_data.pop("password"))
        update_data["password_hash"] = hashed_password

    # 逐个更新字段
    for field, value in update_data.items():
        setattr(user, field, value)

    db.commit()
    db.refresh(user)
    return user
```

**关键特点**：
- ✅ **业务逻辑集中**：密码哈希、软删除过滤、关联查询
- ✅ **可复用**：同一个函数可被多个 API 调用
- ✅ **易测试**：不依赖 HTTP 层，可直接单元测试
- ✅ **统一异常处理**：数据库异常在这里统一捕获

**设计模式**：
- **Repository Pattern**：CRUD 层就是仓储模式的实现
- **单一数据源**：所有数据操作都通过 CRUD，不直接在 API 里写 SQL

---

### 2.4 API Layer（路由层）

**职责**：处理 HTTP 请求和响应，是应用的"入口"

```python
# app/api/users.py

@router.post("/users", response_model=UserResponse, status_code=201)
async def create_user(
    user_in: UserCreate,  # Schema 自动验证
    db: Session = Depends(get_db)  # 依赖注入
):
    """
    创建新用户

    - **username**: 用户名（3-50字符）
    - **email**: 邮箱地址
    - **password**: 密码（至少8字符，含数字）
    """
    # 1. 业务校验（CRUD 层没有的）
    if crud.user.get_user_by_email(db, email=user_in.email):
        raise HTTPException(status_code=400, detail="邮箱已存在")

    # 2. 调用 CRUD 层
    user = crud.user.create_user(db=db, user_in=user_in)

    # 3. 返回响应（自动按 UserResponse 序列化）
    return user

@router.get("/users/{user_id}", response_model=UserResponse)
async def get_user(
    user_id: UUID,
    db: Session = Depends(get_db)
):
    """获取用户信息"""
    user = crud.user.get_user_by_id(db, user_id=user_id)
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    return user
```

**关键特点**：
- ✅ **HTTP 关注点**：状态码、异常处理、响应格式
- ✅ **业务编排**：调用多个 CRUD 函数完成复杂业务
- ✅ **权限控制**：检查用户权限（通过依赖注入）
- ✅ **文档生成**：FastAPI 自动生成 API 文档

---

## 3. 数据流转全景

### 3.1 创建用户的完整流程

```
📱 客户端
   │ POST /api/users
   │ {"username": "john", "email": "john@example.com", "password": "Pass123"}
   ↓
┌──────────────────────────────────────────────────┐
│ 1. API Layer (api/users.py)                     │
│    - 接收 HTTP 请求                               │
│    - 提取请求体                                   │
└──────────────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────────────┐
│ 2. Schema Layer (schemas/user.py)                │
│    - Pydantic 自动验证                            │
│    - 检查：username 长度、email 格式、password 复杂度│
│    - 验证失败 → 返回 422 错误                      │
└──────────────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────────────┐
│ 3. API Layer - 业务校验                          │
│    - 检查邮箱是否已存在                           │
│    - 已存在 → 返回 400 错误                       │
└──────────────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────────────┐
│ 4. CRUD Layer (crud/user.py)                     │
│    - 哈希密码：Pass123 → $2b$12$...              │
│    - 构造 User 对象                               │
│    - 准备数据库操作                               │
└──────────────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────────────┐
│ 5. Model Layer (models/user.py)                  │
│    - ORM 对象 → SQL 语句                          │
│    - INSERT INTO users (id, username, ...)       │
└──────────────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────────────┐
│ 6. Database                                       │
│    - 执行 SQL                                     │
│    - 返回新记录                                   │
└──────────────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────────────┐
│ 7. CRUD Layer - 返回                              │
│    - 刷新 ORM 对象（获取数据库生成的字段）          │
│    - 返回 User 对象                                │
└──────────────────────────────────────────────────┘
   ↓
┌──────────────────────────────────────────────────┐
│ 8. API Layer - 响应                               │
│    - User 对象 → UserResponse                     │
│    - 排除 password_hash                           │
│    - 返回 JSON                                    │
└──────────────────────────────────────────────────┘
   ↓
📱 客户端收到响应
   {"id": "uuid-xxx", "username": "john", "email": "john@example.com"}
```

### 3.2 数据对象转换链

```python
# 整个流程中的数据形态变化：

# 1. HTTP 请求体（JSON 字符串）
'{"username": "john", "email": "john@example.com", "password": "Pass123"}'

# 2. Pydantic Schema 对象（验证后）
UserCreate(username="john", email="john@example.com", password="Pass123")

# 3. 字典（CRUD 层处理）
{"username": "john", "email": "john@example.com"}  # 密码被排除

# 4. ORM Model 对象（包含哈希密码）
User(id=UUID(...), username="john", email="...", password_hash="$2b$12$...")

# 5. 数据库记录（SQL）
INSERT INTO users (id, username, email, password_hash) VALUES (...)

# 6. ORM Model 对象（从数据库返回）
User(id=UUID(...), username="john", ...)  # 包含 created_at 等数据库生成字段

# 7. Response Schema 对象（安全输出）
UserResponse(id=UUID(...), username="john", email="...")  # 排除密码

# 8. HTTP 响应体（JSON）
'{"id": "uuid-xxx", "username": "john", "email": "john@example.com"}'
```

---

## 4. 设计原则

### 4.1 SOLID 原则在分层架构中的体现

#### **S - 单一职责原则 (Single Responsibility)**

每一层只负责一件事：

```python
# ✅ 正确：职责清晰
class UserCreate(BaseModel):
    """只负责数据验证"""
    username: str
    password: str

def create_user(db, user_in):
    """只负责数据库操作"""
    # ...

# ❌ 错误：Schema 混入业务逻辑
class UserCreate(BaseModel):
    username: str

    def save_to_db(self):  # 不应该在这里
        db.add(self)
```

#### **O - 开闭原则 (Open-Closed)**

对扩展开放，对修改关闭：

```python
# ✅ 正确：新增功能不修改原有代码
def create_user(db, user_in: UserCreate):
    # 基础创建逻辑
    pass

def create_user_with_email_verification(db, user_in: UserCreate):
    user = create_user(db, user_in)  # 复用原有逻辑
    send_verification_email(user.email)  # 扩展新功能
    return user
```

#### **L - 里氏替换原则 (Liskov Substitution)**

子类可以替换父类：

```python
# ✅ 正确：所有 Schema 都可以作为验证器
class UserBase(BaseModel):
    username: str

class UserCreate(UserBase):  # 可以替换 UserBase
    password: str

class UserUpdate(UserBase):  # 可以替换 UserBase
    password: str | None = None
```

#### **I - 接口隔离原则 (Interface Segregation)**

不应该强迫客户端依赖不需要的接口：

```python
# ✅ 正确：不同场景使用不同 Schema
class UserCreate(BaseModel):
    """注册需要密码"""
    username: str
    password: str

class UserUpdate(BaseModel):
    """更新不一定需要密码"""
    username: str | None = None
    nickname: str | None = None
    # password 可以分离到专门的 PasswordUpdate

# ❌ 错误：一个 Schema 处理所有场景
class UserSchema(BaseModel):
    username: str | None = None  # 创建时必填，更新时可选
    password: str | None = None  # 太模糊
```

#### **D - 依赖倒置原则 (Dependency Inversion)**

依赖抽象而非具体实现：

```python
# ✅ 正确：API 依赖 CRUD 接口，不关心具体实现
@router.post("/users")
def create_user_api(user_in: UserCreate, db: Session = Depends(get_db)):
    # 只依赖 create_user 函数签名，不关心内部实现
    user = crud.user.create_user(db=db, user_in=user_in)
    return user

# CRUD 实现可以随时修改，不影响 API
def create_user(db: Session, *, user_in: UserCreate) -> User:
    # 可以换成 asyncpg、SQLModel 等，只要返回类型一致
    pass
```

### 4.2 DRY 原则（Don't Repeat Yourself）

**不要重复自己 - 在分层中的应用**：

```python
# ✅ 正确：逻辑只写一次，到处复用
# crud/user.py
def get_user_by_email(db, email):
    return db.query(User).filter(User.email == email).first()

# api/auth.py
def login(email, password):
    user = crud.user.get_user_by_email(db, email)  # 复用
    # ...

# api/users.py
def check_email_exists(email):
    user = crud.user.get_user_by_email(db, email)  # 复用
    # ...

# ❌ 错误：每个 API 都写一遍查询
def login(email, password):
    user = db.query(User).filter(User.email == email).first()  # 重复

def check_email(email):
    user = db.query(User).filter(User.email == email).first()  # 重复
```

---

## 5. 实战对比

### 5.1 案例：修改密码功能

#### **方案A：没有分层**（混乱）

```python
@app.post("/users/{user_id}/password")
async def change_password(user_id: UUID, old_pass: str, new_pass: str):
    # 验证逻辑
    if len(new_pass) < 8:
        raise HTTPException(400, "密码太短")

    # 数据库操作
    user = db.query(User).filter(User.id == user_id).first()

    # 业务逻辑
    if not bcrypt.verify(old_pass, user.password_hash):
        raise HTTPException(401, "旧密码错误")

    # 更新密码
    user.password_hash = bcrypt.hash(new_pass)
    db.commit()

    return {"message": "密码已更新"}

# 问题：
# 1. 如果另一个 API 也需要改密码，代码要复制一遍
# 2. 验证规则散落在 API 里，难以统一管理
# 3. 测试必须启动整个 Web 服务
```

#### **方案B：分层架构**（清晰）

```python
# 1. Schema 层 - 定义数据格式
class PasswordUpdate(BaseModel):
    old_password: str
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    def password_complexity(cls, v):
        if not any(c.isdigit() for c in v):
            raise ValueError("必须包含数字")
        return v

# 2. CRUD 层 - 封装业务逻辑
def update_password(
    db: Session, *,
    user_id: UUID,
    old_password: str,
    new_password: str
) -> User | None:
    """更新密码（验证旧密码）"""
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        return None

    # 验证旧密码
    if not verify_password(old_password, user.password_hash):
        return None

    # 更新新密码
    user.password_hash = hash_password(new_password)
    db.commit()
    db.refresh(user)
    return user

# 3. API 层 - 处理 HTTP
@router.post("/users/{user_id}/password")
async def change_password(
    user_id: UUID,
    password_in: PasswordUpdate,  # Schema 自动验证
    current_user: User = Depends(get_current_user),  # 权限检查
    db: Session = Depends(get_db)
):
    # 权限检查：只能改自己的密码
    if current_user.id != user_id:
        raise HTTPException(403, "无权修改他人密码")

    # 调用 CRUD
    user = crud.user.update_password(
        db=db,
        user_id=user_id,
        old_password=password_in.old_password,
        new_password=password_in.new_password
    )

    if not user:
        raise HTTPException(400, "旧密码错误或用户不存在")

    return {"message": "密码已更新"}

# 优势：
# 1. Schema 统一管理验证规则
# 2. CRUD 可被其他 API 复用（如管理员重置密码）
# 3. 可以单独测试 CRUD 层，不需要 HTTP
# 4. 每层职责清晰，易于维护
```

### 5.2 案例：软删除用户

#### **对比：分层带来的可测试性**

```python
# ❌ 没有分层：难以测试
@app.delete("/users/{user_id}")
async def delete_user(user_id: UUID):
    user = db.query(User).filter(User.id == user_id).first()
    user.deleted_at = datetime.now()
    db.commit()
    return {"message": "已删除"}

# 测试必须这样写：
async def test_delete_user():
    async with AsyncClient(app=app) as client:  # 启动整个应用
        response = await client.delete(f"/users/{user_id}")
        assert response.status_code == 200

# ✅ 分层：每层独立测试
# CRUD 层
def delete_user(db: Session, *, user_id: UUID) -> User | None:
    user = get_user_by_id(db, user_id=user_id)
    if not user:
        return None
    user.deleted_at = datetime.now()
    db.commit()
    return user

# 测试 CRUD（快速、简单）
def test_delete_user_crud(session):
    user = create_user(session, user_in=UserCreate(...))
    deleted_user = crud.user.delete_user(session, user_id=user.id)
    assert deleted_user.deleted_at is not None

# 测试 API（只测 HTTP 逻辑）
async def test_delete_user_api(client, test_user):
    response = await client.delete(f"/users/{test_user.id}")
    assert response.status_code == 200
```

---

## 6. 常见陷阱

### 6.1 跨层调用

```python
# ❌ 错误：Schema 直接访问数据库
class UserCreate(BaseModel):
    username: str

    def save(self):  # 不要这样！
        db.add(User(**self.dict()))
        db.commit()

# ✅ 正确：Schema 只负责验证，数据库操作在 CRUD 层
class UserCreate(BaseModel):
    username: str

def create_user(db, user_in: UserCreate):
    db.add(User(**user_in.dict()))
    db.commit()
```

### 6.2 层级泄漏

```python
# ❌ 错误：API 直接操作 SQLAlchemy Query
@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    return db.query(User).filter(User.is_active == True).all()
    # 如果换了 ORM（如 Tortoise），这里要全改

# ✅ 正确：通过 CRUD 层隔离
def get_active_users(db: Session) -> list[User]:
    return db.query(User).filter(User.is_active == True).all()

@router.get("/users")
def list_users(db: Session = Depends(get_db)):
    return crud.user.get_active_users(db)
    # 换 ORM 只需要改 CRUD 层
```

### 6.3 过度设计

```python
# ❌ 错误：简单查询也封装
def get_all_users(db):
    return db.query(User).all()  # 就一行代码，没必要封装

# ✅ 正确：有业务逻辑才封装
def get_active_users(db):
    return db.query(User).filter(
        User.is_active == True,
        User.deleted_at.is_(None)  # 业务规则：过滤软删除
    ).all()
```

### 6.4 Schema 滥用

```python
# ❌ 错误：一个 Schema 处理所有场景
class UserSchema(BaseModel):
    id: UUID | None = None  # 创建时没有，返回时有
    username: str | None = None  # 创建时必填，更新时可选
    password: str | None = None  # 返回时不应该有

# ✅ 正确：不同场景用不同 Schema
class UserCreate(BaseModel):
    username: str
    password: str

class UserUpdate(BaseModel):
    username: str | None = None

class UserResponse(BaseModel):
    id: UUID
    username: str
    # 不包含 password
```

---

## 7. 最佳实践清单

### 7.1 Model 层最佳实践

- ✅ **只定义结构**：字段、类型、约束、索引
- ✅ **关系清晰**：明确 `back_populates` 和 `cascade`
- ✅ **使用现代语法**：`Mapped[Type]` + `mapped_column()`
- ❌ **不要**：业务方法（如 `save_to_db()`）
- ❌ **不要**：验证逻辑（那是 Schema 的事）

### 7.2 Schema 层最佳实践

- ✅ **输入输出分离**：`UserCreate` vs `UserResponse`
- ✅ **安全过滤**：输出 Schema 排除敏感字段
- ✅ **验证器**：使用 `@field_validator` 自定义规则
- ✅ **可选字段**：更新 Schema 所有字段都用 `Optional`
- ❌ **不要**：包含数据库操作
- ❌ **不要**：在 Schema 里调用 CRUD

### 7.3 CRUD 层最佳实践

- ✅ **单一数据源**：所有数据操作都通过 CRUD
- ✅ **关键字参数**：`def create(db, *, user_in)` 提高可读性
- ✅ **类型注解**：明确输入输出类型
- ✅ **异常处理**：捕获数据库异常并转换
- ✅ **事务管理**：在 CRUD 里 commit/rollback
- ❌ **不要**：处理 HTTP 请求
- ❌ **不要**：直接返回 JSON（返回 ORM 对象）

### 7.4 API 层最佳实践

- ✅ **依赖注入**：用 `Depends()` 获取 db、用户等
- ✅ **响应模型**：明确 `response_model=UserResponse`
- ✅ **状态码**：用合适的 HTTP 状态码
- ✅ **异常处理**：用 `HTTPException`
- ✅ **业务编排**：调用多个 CRUD 完成复杂流程
- ❌ **不要**：直接写 SQL 查询
- ❌ **不要**：在路由函数里做数据验证（用 Schema）

---

## 8. 进阶话题

### 8.1 什么时候可以打破规则？

**小项目（<10个表）可以简化**：
```python
# 可以合并 CRUD 到 Model
class User(Base):
    @classmethod
    def create(cls, username, password):
        # ...

# 可以只用一个 Schema
class UserSchema(BaseModel):
    username: str
```

**但中大型项目必须严格分层**：
- 团队协作（不同人负责不同层）
- 复杂业务（需要业务逻辑复用）
- 长期维护（需要清晰的职责边界）

### 8.2 其他流行框架的分层

| 框架 | Model | Schema/Serializer | CRUD/Service | API |
|------|-------|------------------|--------------|-----|
| **Django** | models.py | serializers.py | - | views.py |
| **Spring Boot** | Entity | DTO | Repository | Controller |
| **Rails** | Model | Serializer | - | Controller |
| **NestJS** | Entity | DTO | Service | Controller |

**共同点**：
- 都有数据模型层（持久化）
- 都有数据验证层（输入输出格式）
- 都有控制层（处理请求）

**差异**：
- 有些框架把 CRUD 和 Model 合并（ActiveRecord 模式）
- 有些框架有独立的 Service 层（业务逻辑）

### 8.3 扩展阅读

- **Clean Architecture**（整洁架构）- Robert C. Martin
- **Domain-Driven Design**（领域驱动设计）- Eric Evans
- **FastAPI 官方文档** - [SQL Databases](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- **Repository Pattern** - Martin Fowler

---

## 总结

**分层架构的核心价值**：

1. **职责清晰**：每层只做一件事
2. **易于测试**：每层可独立测试
3. **可维护性**：改一层不影响其他层
4. **可复用性**：CRUD 可被多个 API 调用
5. **团队协作**：不同层可由不同人开发

**记忆口诀**：
- **Model = 数据库蓝图**（定义表结构）
- **Schema = API 合同**（定义数据格式）
- **CRUD = 数据操作员**（封装数据库操作）
- **API = 应用入口**（处理 HTTP 请求）

**最后建议**：
- 🎯 学习时：理解每层职责，严格遵守
- 🚀 实战时：小项目可简化，大项目必须分层
- 📚 进阶时：学习 DDD、Clean Architecture 等高级模式

---

**下一步**：在实际开发中观察数据流转，体会分层带来的好处！
