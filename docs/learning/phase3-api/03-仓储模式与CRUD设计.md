# 仓储模式 (Repository Pattern) 与 CRUD 设计

> **学习目标**：学习如何通过仓储模式将数据操作逻辑与业务逻辑解耦，构建一个清晰、可复用、易于测试的数据访问层。

## 📚 目录

1. [问题：为什么不应在 API 中直接操作数据库？](#1-问题为什么不应在-api-中直接操作数据库)
2. [解决方案：仓储模式 (Repository Pattern)](#2-解决方案仓储模式-repository-pattern)
3. [重构：应用仓储模式](#3-重构应用仓储模式)
4. [进阶：通用仓储基类 (Generic Repository)](#4-进阶通用仓储基类-generic-repository)
5. [总结与下一步](#5-总结与下一步)

---

## 1. 问题：为什么不应在 API 中直接操作数据库？

在项目初期，我们很容易图方便，将所有数据库操作代码都直接写在 API 路由函数里。让我们来看一个典型的“反面教材”：

```python
# api/endpoints/users.py (不好的设计)

@router.post("/users/")
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # 业务逻辑：检查邮箱是否已存在
    existing_user = db.query(User).filter(User.email == user_data.email).first()
    if existing_user:
        raise HTTPException(status_code=409, detail="邮箱已被注册")

    # 核心数据库操作：创建用户
    hashed_password = hash_password(user_data.password)
    db_user = User(
        username=user_data.username,
        email=user_data.email,
        password_hash=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    
    return db_user
```

这个函数现在做了**太多事**，它至少有三个严重的问题：

1.  **违反单一职责原则 (Single Responsibility Principle)**
    API 路由函数的核心职责是处理 HTTP 请求和响应、协调业务流程。现在它却深入地参与了数据库查询、对象创建、事务提交等底层数据操作，职责混乱。

2.  **代码无法复用 (Violates DRY - Don't Repeat Yourself)**
    如果未来我们有一个后台管理任务（例如，从命令行批量导入用户）也需要创建用户，我们唯一的选择就是复制粘贴这段数据库操作代码，这会导致代码冗余和维护噩梦。

3.  **极难测试 (Hard to Test)**
    想要测试“创建用户”这个核心逻辑，你必须启动一个完整的 Web 服务，发送一个真实的 HTTP 请求，并连接一个真实的数据库。你无法对这个逻辑进行简单、快速的单元测试。

---

## 2. 解决方案：仓储模式 (Repository Pattern)

为了解决以上问题，我们引入一个软件设计中的经典模式——**仓储模式**，来构建一个清晰的数据访问层 (Data Access Layer)。

### 2.1 它是什么？

一个“仓储”就是一个专门负责与**特定数据模型**（如 `User` 模型）进行所有数据库交互的模块。它将所有的数据操作细节（增删改查，即 CRUD）封装在内部，并向更高层（如 API 路由）提供简洁明了的接口。

### 2.2 一个生动的比喻

你可以把仓储想象成一个“数据仓库的管理员”。

-   **API 路由函数**：是“销售经理”。
-   **仓储 (CRUD 模块)**：是“仓库管理员”。
-   **数据库**：是“仓库”。

销售经理（API）不需要知道货物（数据）在仓库（数据库）的哪个货架、如何摆放。他只需要告诉仓库管理员（仓储）：“帮我拿编号为 A01 的货物”（`crud.user.get(id=A01)`）或者“把这个新货入库”（`crud.user.create(...)`）。所有的底层操作都由“仓库管理员”完成。

### 2.3 更新后的分层架构

```
┌─────────────────────────────────────────────┐
│  API 层 (FastAPI Routes)                     │  ← “销售经理”
│  - "给我一个用户" / "创建一个用户"            │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  业务逻辑/仓储层 (CRUD/Repository) ★ 新增 ★ │  ← “仓库管理员”
│  - `get_user()` / `create_user()`             │
│  - 封装所有 SQLAlchemy 查询细节             │
└─────────────────────────────────────────────┘
                    ↓
┌─────────────────────────────────────────────┐
│  数据模型层 (SQLAlchemy Models)              │  ← “仓库里的货物”
│  - 定义数据结构                             │
└─────────────────────────────────────────────┘
```

---

## 3. 重构：应用仓储模式

应用仓储模式后，我们的代码会变得清晰、解耦。

#### 步骤 1: 创建数据操作层 `app/crud/user.py`

```python
# app/crud/user.py (好的设计)

from sqlalchemy.orm import Session
from app.models.user import User
from app.schemas.user import UserCreate
from app.core.security import hash_password

# 只负责查询
def get_user_by_email(db: Session, email: str) -> User | None:
    return db.query(User).filter(User.email == email).first()

# 只负责创建
def create_user(db: Session, user_in: UserCreate) -> User:
    hashed_password = hash_password(user_in.password)
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=hashed_password,
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user
```

#### 步骤 2: 简化 API 路由层

```python
# api/endpoints/users.py (好的设计)

from app import crud # 导入我们的仓储模块

@router.post("/users/")
def create_user(user_data: UserCreate, db: Session = Depends(get_db)):
    # 职责清晰：API 层只负责业务流转和 HTTP 响应
    existing_user = crud.user.get_user_by_email(db, email=user_data.email)
    if existing_user:
        raise HTTPException(status_code=409, detail="邮箱已被注册")
    
    # 调用仓储函数来处理所有数据库细节
    return crud.user.create_user(db, user_in=user_data)
```

### 3.1 重构后的优势

-   **职责清晰**：API 层变得非常“薄”，只处理 HTTP 和业务流转，不关心数据如何存储。
-   **代码复用**：现在任何需要创建用户的地方，都可以通过 `crud.user.create_user()` 来完成，保证了逻辑的唯一性。
-   **易于测试**：我们可以单独为 `crud/user.py` 编写单元测试，只需模拟一个 `db: Session` 对象即可，无需启动 Web 服务，测试变得简单、快速。

---

## 4. 进阶：通用仓储基类 (Generic Repository)

当项目变大，你会发现很多模型的 CRUD 操作都非常类似（`get`, `get_multi`, `create`, `update`, `delete`）。为了进一步遵循 DRY 原则，我们可以创建一个通用的仓储基类。

```python
# app/crud/base.py

from typing import Any, Generic, Type, TypeVar
from pydantic import BaseModel
from sqlalchemy.orm import Session
from app.db.database import Base # 你的 SQLAlchemy Base

ModelType = TypeVar("ModelType", bound=Base)
CreateSchemaType = TypeVar("CreateSchemaType", bound=BaseModel)
UpdateSchemaType = TypeVar("UpdateSchemaType", bound=BaseModel)

class CRUDBase(Generic[ModelType, CreateSchemaType, UpdateSchemaType]):
    def __init__(self, model: Type[ModelType]):
        self.model = model

    def get(self, db: Session, id: Any) -> ModelType | None:
        return db.query(self.model).filter(self.model.id == id).first()

    def get_multi(
        self, db: Session, *, skip: int = 0, limit: int = 100
    ) -> list[ModelType]:
        return db.query(self.model).offset(skip).limit(limit).all()

    def create(self, db: Session, *, obj_in: CreateSchemaType) -> ModelType:
        db_obj = self.model(**obj_in.model_dump())
        db.add(db_obj)
        db.commit()
        db.refresh(db_obj)
        return db_obj

    # ...可以继续实现 update 和 delete
```

然后，具体的 `user` 仓储就可以继承这个基类，只编写特有的查询方法：

```python
# app/crud/user.py

from .base import CRUDBase
from app.models.user import User
from app.schemas.user import UserCreate, UserUpdate

class CRUDUser(CRUDBase[User, UserCreate, UserUpdate]):
    def get_by_email(self, db: Session, *, email: str) -> User | None:
        return db.query(User).filter(User.email == email).first()

# 导出一个实例
user = CRUDUser(User)
```

**注意**：这是一个更高级的模式，在当前项目中我们暂时先不采用，但理解这个思想对于构建大型应用非常有帮助。

---

## 5. 总结

-   **核心原则**：通过引入一个数据访问层（仓储/CRUD），将数据持久化逻辑与业务逻辑（API路由）分离开。
-   **核心收益**：代码更清晰、可复用性更高、更易于进行单元测试。

