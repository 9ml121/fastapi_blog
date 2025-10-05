# SQLAlchemy 2.0 架构深度解析

> 📖 **学习目标**：理解 SQLAlchemy 的分层架构、Core 层与 ORM 层的使用场景和优劣势对比

---

## 📐 SQLAlchemy 整体架构

SQLAlchemy 采用**分层设计**，从底层到高层提供不同抽象级别的数据库操作方式：

```mermaid
graph TB
    subgraph "应用层"
        A[Python 应用代码]
    end
    
    subgraph "SQLAlchemy 架构"
        B[ORM Layer<br/>对象关系映射]
        C[Core Layer<br/>SQL表达式构建]
        D[Engine<br/>连接池 + 方言]
    end
    
    subgraph "数据库层"
        E[(Database<br/>PostgreSQL/MySQL/etc)]
    end
    
    A --> B
    A -.直接使用.-> C
    B --> C
    C --> D
    D --> E
    
    style B fill:#e1f5fe
    style C fill:#fff3e0
    style D fill:#f3e5f5
```

**三个核心层次：**

| 层次 | 抽象级别 | 特点 | 适用场景 |
|------|---------|------|---------|
| **ORM 层** | 高 | 面向对象，自动处理关系 | 常规业务逻辑 (95%) |
| **Core 层** | 中 | SQL 表达式构建器 | 复杂查询、性能优化 |
| **Engine 层** | 低 | 连接管理、SQL 方言 | 通常无需直接操作 |

---

## 🔍 Core 层详解

### 什么是 Core 层？

Core 层是 SQLAlchemy 的**SQL 表达式语言**，它提供了一种 Pythonic 的方式来构建 SQL 语句，但不涉及 Python 类和对象。

### Core 层架构图

```mermaid
graph LR
    A[Table 定义] --> B[SQL 表达式]
    B --> C[select/insert/update]
    C --> D[execute]
    D --> E[原始结果集]
    
    style A fill:#fff3e0
    style B fill:#fff3e0
    style C fill:#fff3e0
```

### Core 层语法示例

```python
from sqlalchemy import (
    create_engine, MetaData, Table, Column,
    Integer, String, select, insert
)

# 1️⃣ 创建引擎和元数据
engine = create_engine("postgresql://user:pass@localhost/db")
metadata = MetaData()

# 2️⃣ 定义表结构（类似 DDL）
users = Table(
    'users', metadata,
    Column('id', Integer, primary_key=True),
    Column('username', String(50), nullable=False),
    Column('email', String(100), unique=True)
)

posts = Table(
    'posts', metadata,
    Column('id', Integer, primary_key=True),
    Column('title', String(200)),
    Column('user_id', Integer)  # 外键手动管理
)

# 3️⃣ 构建查询（类似 SQL 但是 Python 风格）
with engine.connect() as conn:
    # SELECT * FROM users WHERE username = 'alice'
    stmt = select(users).where(users.c.username == 'alice')
    result = conn.execute(stmt)
    
    for row in result:
        print(row.id, row.username)  # 访问列
    
    # INSERT
    stmt = insert(users).values(username='bob', email='bob@example.com')
    conn.execute(stmt)
    conn.commit()
    
    # JOIN 查询
    stmt = (
        select(users.c.username, posts.c.title)
        .select_from(users.join(posts, users.c.id == posts.c.user_id))
        .where(users.c.username == 'alice')
    )
    result = conn.execute(stmt)
```

### Core 层特点分析

#### ✅ 优势

1. **精确控制 SQL**
   ```python
   # 可以构建复杂的查询，完全掌控生成的 SQL
   stmt = (
       select(users.c.username, func.count(posts.c.id).label('post_count'))
       .select_from(users.outerjoin(posts))
       .group_by(users.c.username)
       .having(func.count(posts.c.id) > 10)
       .order_by(desc('post_count'))
       .limit(100)
   )
   ```

2. **性能最优**
   - 无 ORM 开销，直接映射到 SQL
   - 适合批量操作和数据分析

3. **轻量级**
   - 不需要定义 Python 类
   - 适合脚本和临时查询

#### ❌ 劣势

1. **代码冗长**
   ```python
   # Core 层：需要手动构建查询
   stmt = select(users).where(users.c.username == name)
   result = conn.execute(stmt).fetchone()
   
   # vs ORM 层：简洁直观
   user = session.query(User).filter_by(username=name).first()
   ```

2. **关系管理困难**
   ```python
   # 外键约束需要手动定义
   Column('user_id', Integer, ForeignKey('users.id'))
   
   # JOIN 需要手动写
   users.join(posts, users.c.id == posts.c.user_id)
   ```

3. **返回原始数据**
   ```python
   # 返回的是 Row 对象，不是业务对象
   row = result.fetchone()
   print(row.username)  # 只有数据，没有行为
   ```

### Core 层适用场景

| 场景 | 为什么用 Core 层？ | 示例 |
|------|------------------|------|
| **复杂统计查询** | SQL 表达力更强 | 多表 JOIN + GROUP BY + 子查询 |
| **批量数据导入** | 性能优先 | `bulk_insert_mappings()` |
| **数据仓库/ETL** | 数据处理而非对象 | 数据清洗、聚合计算 |
| **性能瓶颈优化** | 绕过 ORM 开销 | N+1 查询优化 |
| **动态表结构** | 运行时构建表 | 多租户系统 |

---

## 🎯 ORM 层详解

### 什么是 ORM 层？

ORM (Object-Relational Mapping) 将**数据库表映射为 Python 类**，让你用面向对象的方式操作数据库。

### ORM 层架构图

```mermaid
graph TB
    subgraph "Python 世界"
        A[User 类<br/>Python 对象]
        B[Post 类<br/>Python 对象]
    end
    
    subgraph "映射层"
        C[Declarative Base<br/>映射配置]
    end
    
    subgraph "数据库世界"
        D[(users 表)]
        E[(posts 表)]
    end
    
    A --> C
    B --> C
    C --> D
    C --> E
    
    A -.relationship.-> B
    D -.foreign key.-> E
    
    style A fill:#e1f5fe
    style B fill:#e1f5fe
    style C fill:#c5cae9
```

### ORM 层语法示例（SQLAlchemy 2.0 现代语法）

```python
from sqlalchemy import create_engine, String, ForeignKey
from sqlalchemy.orm import (
    DeclarativeBase, Mapped, mapped_column,
    relationship, Session
)
from typing import List

# 1️⃣ 声明基类
class Base(DeclarativeBase):
    pass

# 2️⃣ 定义模型（类即表结构）
class User(Base):
    __tablename__ = "users"
    
    # 现代语法：类型注解 + mapped_column
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100))
    
    # 关系定义：自动处理 JOIN
    posts: Mapped[List["Post"]] = relationship(back_populates="author")
    
    def __repr__(self):
        return f"<User(username='{self.username}')>"

class Post(Base):
    __tablename__ = "posts"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    
    # 双向关系
    author: Mapped["User"] = relationship(back_populates="posts")

# 3️⃣ 使用 ORM 操作数据库
engine = create_engine("postgresql://user:pass@localhost/db")
Base.metadata.create_all(engine)  # 自动创建表

with Session(engine) as session:
    # 创建对象
    user = User(username="alice", email="alice@example.com")
    session.add(user)
    session.commit()
    
    # 查询对象
    user = session.query(User).filter_by(username="alice").first()
    print(user.username)  # 访问属性
    
    # 自动处理关系
    post = Post(title="Hello World", author=user)  # 自动设置 user_id
    session.add(post)
    session.commit()
    
    # 自动 JOIN 查询
    print(user.posts)  # [<Post(title='Hello World')>]
    print(post.author.username)  # 'alice'
```

### ORM 层特点分析

#### ✅ 优势

1. **面向对象，符合直觉**
   ```python
   # 像操作 Python 对象一样操作数据库
   user = User(username="alice", email="alice@example.com")
   user.posts.append(Post(title="Hello"))  # 自动维护关系
   session.add(user)
   session.commit()
   ```

2. **关系自动管理**
   ```python
   class User(Base):
       posts: Mapped[List["Post"]] = relationship(back_populates="author")
   
   # 自动 JOIN，无需手写 SQL
   user = session.get(User, 1)
   for post in user.posts:  # 自动查询关联的 posts
       print(post.title)
   ```

3. **类型安全（SQLAlchemy 2.0）**
   ```python
   id: Mapped[int] = mapped_column(primary_key=True)
   username: Mapped[str]  # IDE 自动补全和类型检查
   ```

4. **业务逻辑封装**
   ```python
   class User(Base):
       # ... 表定义 ...
       
       def verify_password(self, password: str) -> bool:
           """业务方法：验证密码"""
           return pwd_context.verify(password, self.password_hash)
   ```

#### ❌ 劣势

1. **性能开销**
   ```python
   # N+1 查询问题
   users = session.query(User).all()  # 1 次查询
   for user in users:
       print(user.posts)  # N 次查询！
   
   # 解决方案：显式加载
   users = session.query(User).options(joinedload(User.posts)).all()
   ```

2. **复杂查询受限**
   ```python
   # 某些复杂 SQL 用 ORM 难以表达
   # 比如：窗口函数、递归 CTE、复杂子查询
   # 这时候仍需回退到 Core 层或原生 SQL
   ```

3. **学习曲线**
   - 需要理解 Session、映射、懒加载等概念
   - 调试时需要了解生成的 SQL

### ORM 层适用场景

| 场景 | 为什么用 ORM 层？ | 示例 |
|------|-----------------|------|
| **常规 CRUD** | 代码简洁直观 | 用户注册、文章发布 |
| **关系密集型** | 自动管理外键和 JOIN | 博客系统、社交网络 |
| **业务逻辑封装** | 模型方法 | `user.verify_password()` |
| **单元测试** | Mock 方便 | 测试业务逻辑 |
| **快速开发** | 减少样板代码 | MVP 原型 |

---

## ⚖️ Core 层 vs ORM 层对比

### 代码对比：实现同一功能

**任务**：查询用户名为 `alice` 且发帖数 > 10 的用户

#### Core 层实现

```python
from sqlalchemy import select, func

stmt = (
    select(users.c.id, users.c.username)
    .select_from(
        users.join(posts, users.c.id == posts.c.user_id)
    )
    .where(users.c.username == 'alice')
    .group_by(users.c.id, users.c.username)
    .having(func.count(posts.c.id) > 10)
)

with engine.connect() as conn:
    result = conn.execute(stmt)
    for row in result:
        print(row.username)  # 返回原始数据
```

**特点**：
- ✅ SQL 映射清晰
- ❌ 代码冗长
- ❌ 返回字典/元组

#### ORM 层实现

```python
from sqlalchemy import func

user = (
    session.query(User)
    .join(User.posts)
    .filter(User.username == 'alice')
    .group_by(User.id)
    .having(func.count(Post.id) > 10)
    .first()
)

print(user.username)  # 返回对象
print(user.posts)     # 可访问关联数据
```

**特点**：
- ✅ 代码简洁
- ✅ 返回业务对象
- ✅ 自动处理关系

### 性能对比

```mermaid
graph LR
    A[1000条数据<br/>批量插入] --> B[Core: 0.5s]
    A --> C[ORM: 1.2s]
    
    D[复杂查询<br/>3表JOIN+聚合] --> E[Core: 0.3s]
    D --> F[ORM: 0.4s]
    
    style B fill:#c8e6c9
    style C fill:#ffccbc
    style E fill:#c8e6c9
    style F fill:#fff9c4
```

**结论**：Core 层性能优势明显，但差距在可接受范围（除非极端场景）

---

## 🏗️ 实际项目如何选择？

### 混合使用策略（推荐）

```python
# 主要使用 ORM 层
class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str]

# 常规操作用 ORM
user = session.get(User, 1)
user.username = "new_name"
session.commit()

# 性能关键场景用 Core
from sqlalchemy import select, func

# 统计查询：直接用 Core 层
stmt = select(func.count(User.id)).where(User.created_at > last_month)
count = session.scalar(stmt)

# 批量更新：用 Core 避免加载对象
from sqlalchemy import update
stmt = update(User).where(User.last_login < old_date).values(is_active=False)
session.execute(stmt)
session.commit()
```

### 决策流程图

```mermaid
graph TD
    A[需要数据库操作] --> B{是常规 CRUD?}
    B -->|是| C[使用 ORM 层]
    B -->|否| D{是复杂统计查询?}
    D -->|是| E[使用 Core 层]
    D -->|否| F{性能是瓶颈?}
    F -->|是| E
    F -->|否| G{需要关系管理?}
    G -->|是| C
    G -->|否| H[优先 ORM<br/>必要时 Core]
    
    style C fill:#e1f5fe
    style E fill:#fff3e0
```

### 使用比例建议

```
📊 典型 Web 应用：
━━━━━━━━━━━━━━━━━━━━ 90% ORM 层
━━ 10% Core 层

📊 数据密集型应用：
━━━━━━━━━━━━ 60% ORM 层
━━━━━━━━ 40% Core 层

📊 数据分析/ETL：
━━━━ 20% ORM 层
━━━━━━━━━━━━━━━━ 80% Core 层
```

---

## 🧩 与 Pydantic 的分层协作

### 为什么不在 SQLAlchemy 中做数据校验？

SQLAlchemy **可以**做校验，但职责划分不清晰：

```python
# ❌ 反模式：在 ORM 模型中做业务校验
class User(Base):
    __tablename__ = "users"
    email: Mapped[str]
    
    @validates('email')
    def validate_email(self, key, address):
        if '@' not in address:
            raise ValueError("Invalid email")
        return address
```

**问题**：
1. 错误发现太晚（数据已到数据库层）
2. 违反单一职责原则
3. 难以复用（绑定在模型上）

### 推荐的三层架构

```mermaid
graph TB
    subgraph "请求流向"
        A[HTTP 请求] --> B[Pydantic Schema]
        B -->|校验通过| C[CRUD 业务层]
        C --> D[SQLAlchemy Model]
        D --> E[(Database)]
    end
    
    subgraph "职责划分"
        B1[📋 数据校验<br/>格式检查<br/>类型转换]
        C1[🔧 业务逻辑<br/>密码哈希<br/>权限检查]
        D1[💾 数据持久化<br/>数据库约束<br/>关系维护]
    end
    
    B -.职责.-> B1
    C -.职责.-> C1
    D -.职责.-> D1
    
    style B fill:#e8f5e9
    style C fill:#fff3e0
    style D fill:#e1f5fe
```

### 完整代码示例

```python
# 1️⃣ Pydantic Schema - API 层
from pydantic import BaseModel, EmailStr, field_validator

class UserCreate(BaseModel):
    """接收用户输入，负责数据校验"""
    username: str
    email: EmailStr  # 自动校验邮箱格式
    password: str
    
    @field_validator('password')
    def validate_password(cls, v):
        if len(v) < 8:
            raise ValueError('密码至少 8 位')
        if not any(c.isupper() for c in v):
            raise ValueError('需要包含大写字母')
        return v

# 2️⃣ SQLAlchemy Model - 数据层
class User(Base):
    """数据库模型，负责持久化"""
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    password_hash: Mapped[str] = mapped_column(String(255))  # 存哈希值

# 3️⃣ CRUD 业务层 - 数据转换
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"])

def create_user(session: Session, user_in: UserCreate) -> User:
    """业务层：处理数据转换和哈希"""
    db_user = User(
        username=user_in.username,
        email=user_in.email,
        password_hash=pwd_context.hash(user_in.password)  # 哈希密码
    )
    session.add(db_user)
    session.commit()
    session.refresh(db_user)
    return db_user

# 4️⃣ FastAPI 路由
@app.post("/users/", response_model=UserResponse)
def register(user_in: UserCreate, session: Session = Depends(get_session)):
    """
    数据流：
    1. Pydantic 自动校验 user_in（格式、类型）
    2. 业务层处理密码哈希
    3. SQLAlchemy 持久化到数据库
    """
    return create_user(session, user_in)
```

### 三层职责对比表

| 层次 | 工具 | 主要职责 | 示例 |
|------|------|---------|------|
| **API 层** | Pydantic | 数据校验、格式转换 | 邮箱格式检查、密码长度 |
| **业务层** | Python 代码 | 业务逻辑、数据转换 | 密码哈希、权限判断 |
| **数据层** | SQLAlchemy | 持久化、数据库约束 | 唯一约束、外键关系 |

---

## 📚 总结与最佳实践

### 核心要点

1. **SQLAlchemy 双层架构**
   - Core 层：精确控制 SQL，性能优先
   - ORM 层：面向对象，开发效率高

2. **选择策略**
   ```
   默认使用 ORM 层 → 遇到性能瓶颈或复杂查询 → 局部使用 Core 层
   ```

3. **与 Pydantic 配合**
   - Pydantic 做输入校验（API 层）
   - SQLAlchemy 做数据持久化（数据层）
   - 分层清晰，职责单一

### 学习路径建议

```mermaid
graph LR
    A[1. 学习 ORM 基础] --> B[2. 理解 Session 机制]
    B --> C[3. 掌握关系映射]
    C --> D[4. 了解 Core 层]
    D --> E[5. 性能优化技巧]
    
    style A fill:#e1f5fe
    style E fill:#fff3e0
```

### 延伸阅读

- 🔗 [SQLAlchemy 2.0 官方文档](https://docs.sqlalchemy.org/en/20/)
- 🔗 [FastAPI + SQLAlchemy 最佳实践](https://fastapi.tiangolo.com/tutorial/sql-databases/)
- 🔗 [N+1 查询问题详解](https://docs.sqlalchemy.org/en/20/orm/queryguide/relationships.html)

---

> 💡 **记住**：好的架构不是追求完美，而是在**代码可读性**、**开发效率**和**性能**之间找到平衡点！