# 数据模型开发规范

## 🎯 规范目标

本项目采用**现代 SQLAlchemy 2.0+ 语法**作为数据模型开发标准，确保：
- 类型安全和 IDE 支持
- 代码可读性和可维护性  
- 团队开发的一致性
- 未来技术栈的前瞻性

## 📋 强制规范

### 1. 基础语法要求

#### ✅ 必须使用
```python
from sqlalchemy.orm import Mapped, mapped_column, relationship
from typing import Optional, List
from uuid import UUID

class User(Base):
    # 使用类型注解
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    username: Mapped[str] = mapped_column(String(50), unique=True)
    avatar: Mapped[Optional[str]] = mapped_column(String(255), default=None)
```

#### ❌ 禁止使用
```python
from sqlalchemy import Column

class User(Base):
    # 传统语法仅用于学习对比，项目中禁用
    id = Column(UUID(as_uuid=True), primary_key=True)
    username = Column(String(50), unique=True)
```

### 2. 必需导入模块

```python
"""
标准导入模板 - 所有模型文件必须包含
"""
import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, List
from uuid import UUID

from sqlalchemy import String, Text, Boolean, DateTime, Integer, Enum as SQLEnum, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.database import Base
```

## 🏗️ 模型结构规范

### 1. 类定义模板

```python
class ModelName(Base):
    """
    模型简述
    
    设计要点：
    1. 关键设计决策1
    2. 关键设计决策2
    """
    
    __tablename__ = "table_name"

    def __init__(self, **kwargs):
        """初始化实例，设置默认值"""
        kwargs.setdefault('field_name', default_value)
        super().__init__(**kwargs)

    # 字段定义（按重要性排序）
    # 关系定义
    # 业务方法
    # 魔术方法
```

### 2. 字段定义顺序

**严格按以下顺序组织字段：**

1. **主键字段**
2. **核心业务字段**
3. **状态和配置字段** 
4. **关联外键字段**
5. **时间戳字段**
6. **关系定义**

```python
class Post(Base):
    __tablename__ = "posts"

    # 1. 主键
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)

    # 2. 核心业务字段
    title: Mapped[str] = mapped_column(String(200))
    content: Mapped[str] = mapped_column(Text)
    slug: Mapped[str] = mapped_column(String(200), unique=True, index=True)

    # 3. 状态和配置
    status: Mapped[PostStatus] = mapped_column(SQLEnum(PostStatus), default=PostStatus.DRAFT)
    is_featured: Mapped[bool] = mapped_column(Boolean, default=False)

    # 4. 关联外键
    author_id: Mapped[UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    # 5. 时间戳
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    # 6. 关系定义
    author: Mapped["User"] = relationship(back_populates="posts")
```

## 🔧 字段定义规范

### 1. 主键规范

**所有表必须使用 UUID 主键：**

```python
id: Mapped[UUID] = mapped_column(
    primary_key=True,
    default=uuid.uuid4,
    comment="唯一标识"
)
```

### 2. 字符串字段规范

```python
# 短文本：指定明确长度
username: Mapped[str] = mapped_column(String(50))

# 长文本：使用 Text
content: Mapped[str] = mapped_column(Text)

# 可空字符串：明确使用 Optional
avatar: Mapped[Optional[str]] = mapped_column(String(255), default=None)
```

### 3. 枚举字段规范

```python
class PostStatus(str, Enum):
    """继承 str 以支持 JSON 序列化"""
    DRAFT = "draft"
    PUBLISHED = "published"

# 枚举字段定义
status: Mapped[PostStatus] = mapped_column(
    SQLEnum(PostStatus),
    default=PostStatus.DRAFT,
    index=True  # 状态字段建议加索引
)
```

### 4. 时间字段规范

```python
# 自动时间戳：创建时间
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),
    comment="创建时间"
)

# 自动时间戳：更新时间
updated_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True), 
    server_default=func.now(),
    onupdate=func.now(),
    comment="更新时间"
)

# 可空时间：业务时间
published_at: Mapped[Optional[datetime]] = mapped_column(
    DateTime(timezone=True),
    default=None,
    comment="发布时间"
)
```

### 5. 外键关联规范

```python
# 外键定义
author_id: Mapped[UUID] = mapped_column(
    ForeignKey("users.id", ondelete="CASCADE"),  # 指定删除策略
    nullable=False,  # 明确是否可空
    index=True,      # 外键建议加索引
    comment="作者ID"
)

# 关系定义
author: Mapped["User"] = relationship(
    back_populates="posts",
    lazy="select"  # 明确指定加载策略
)
```

## 🔗 关系定义规范

### 1. 一对多关系

```python
# 父模型 (User)
posts: Mapped[List["Post"]] = relationship(
    back_populates="author",
    cascade="all, delete-orphan"  # 级联删除
)

# 子模型 (Post)  
author: Mapped["User"] = relationship(back_populates="posts")
```

### 2. 多对多关系

```python
# 中间表定义 (独立文件)
post_tags = Table(
    "post_tags",
    Base.metadata,
    Column("post_id", UUID, ForeignKey("posts.id"), primary_key=True),
    Column("tag_id", UUID, ForeignKey("tags.id"), primary_key=True),
)

# 关系定义
class Post(Base):
    tags: Mapped[List["Tag"]] = relationship(
        secondary=post_tags,
        back_populates="posts"
    )

class Tag(Base):
    posts: Mapped[List["Post"]] = relationship(
        secondary=post_tags,
        back_populates="tags"
    )
```

## 🔧 默认值设置规范

### 1. 三种默认值设置方式

**明确区分不同层次的默认值设置，避免重复配置：**

#### A. `__init__` 方法 - 复杂业务逻辑默认值

```python
def __init__(self, **kwargs):
    """
    初始化实例，只处理复杂的业务逻辑默认值
    
    简单的固定默认值通过 mapped_column(default=...) 设置
    这里只处理需要计算或有复杂逻辑的默认值
    """
    # 复杂逻辑：如果没有提供昵称，使用用户名作为昵称
    if 'nickname' not in kwargs and 'username' in kwargs:
        kwargs['nickname'] = kwargs['username']
    
    # 复杂逻辑：如果提供了标题但没有提供 slug，自动生成
    if 'title' in kwargs and 'slug' not in kwargs:
        kwargs['slug'] = self._generate_slug_static(kwargs['title'])
    
    super().__init__(**kwargs)
```

**适用场景：**
- 需要根据其他字段计算的默认值
- 复杂的业务逻辑默认值
- 需要调用方法生成的默认值

#### B. `default` 参数 - 固定默认值

```python
# 简单固定值
status: Mapped[PostStatus] = mapped_column(
    SQLEnum(PostStatus),
    default=PostStatus.DRAFT,  # 固定默认值
    comment="文章状态"
)

# Python 函数生成
id: Mapped[UUID] = mapped_column(
    primary_key=True,
    default=uuid.uuid4,  # 每次调用生成新值
    comment="唯一标识"
)
```

**适用场景：**
- 固定的常量默认值
- Python 函数生成的默认值
- ORM 层面的默认值处理

#### C. `server_default` 参数 - 数据库层默认值

```python
# 数据库时间戳函数
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),  # 数据库函数
    comment="创建时间"
)

# 数据库序列或其他函数
sequence_id: Mapped[int] = mapped_column(
    Integer,
    server_default=text("nextval('post_sequence')"),
    comment="序列号"
)
```

**适用场景：**
- 时间戳字段（确保数据库时区准确性）
- 数据库函数生成的值
- 需要支持直接 SQL 操作的字段
- 数据完整性保证

### 2. 默认值选择原则

**按优先级选择：**

1. **优先使用 `default`** - 适合大多数场景的固定默认值
2. **复杂逻辑用 `__init__`** - 需要计算或条件判断时
3. **时间戳用 `server_default`** - 确保准确性和一致性

**❌ 错误：重复设置默认值**
```python
class User(Base):
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.USER  # ORM 层默认值
    )
    
    def __init__(self, **kwargs):
        kwargs.setdefault('role', UserRole.USER)  # ❌ 重复设置
        super().__init__(**kwargs)
```

**✅ 正确：选择合适的层次**
```python
class User(Base):
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.USER,  # 只在 ORM 层设置
        comment="用户角色"
    )
    
    def __init__(self, **kwargs):
        # 只处理复杂逻辑，不重复设置简单默认值
        if 'nickname' not in kwargs and 'username' in kwargs:
            kwargs['nickname'] = kwargs['username']
        super().__init__(**kwargs)
```

### 3. 默认值最佳实践

**执行优先级：** `__init__` > `default` > `server_default`

```python
class Post(Base):
    # 固定默认值 → default
    status: Mapped[PostStatus] = mapped_column(
        SQLEnum(PostStatus),
        default=PostStatus.DRAFT
    )
    
    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0
    )
    
    # 数据库函数 → server_default
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    
    # 复杂逻辑 → __init__
    def __init__(self, **kwargs):
        if 'title' in kwargs and 'slug' not in kwargs:
            kwargs['slug'] = self._generate_slug_static(kwargs['title'])
        super().__init__(**kwargs)
```

## 🎨 方法定义规范

### 1. 必需魔术方法

```python
def __repr__(self) -> str:
    """开发调试用的字符串表示"""
    return f"<{self.__class__.__name__}(id={self.id}, key_field='{self.key_field}')>"

def __str__(self) -> str:
    """用户友好的字符串表示"""  
    return self.title  # 或其他有意义的字段
```

### 2. 属性方法 (@property)

```python
@property
def is_published(self) -> bool:
    """业务状态检查"""
    return self.status == PostStatus.PUBLISHED

@property 
def display_name(self) -> str:
    """计算属性"""
    return f"{self.title} ({self.created_at.year})"
```

### 3. 业务方法

```python
def publish(self) -> None:
    """业务操作：发布文章"""
    self.status = PostStatus.PUBLISHED
    if not self.published_at:
        self.published_at = datetime.utcnow()

def archive(self) -> None:
    """业务操作：归档文章"""
    self.status = PostStatus.ARCHIVED
```

## 📝 注释和文档规范

### 1. 类文档字符串

```python
class User(Base):
    """
    用户模型
    
    设计要点：
    1. 使用 UUID 作为主键，支持分布式系统
    2. 支持用户名和邮箱双重登录方式  
    3. 密码只存储哈希值，不存储明文
    4. 使用枚举类型管理用户角色
    5. 包含软删除和邮箱验证功能
    
    关联关系：
    - 一对多：User -> Post (用户发布文章)
    - 一对多：User -> Comment (用户发表评论)
    """
```

### 2. 字段注释

```python
# 使用 comment 参数为数据库字段添加注释
username: Mapped[str] = mapped_column(
    String(50),
    unique=True,
    index=True,
    comment="用户名（唯一，用于登录）"
)
```

## 🧪 测试规范

### 1. 每个模型必须有对应测试文件

```
tests/
├── test_models_user.py
├── test_models_post.py
├── test_models_comment.py
└── test_models_tag.py
```

### 2. 测试内容要求

- 模型实例化测试
- 字段约束测试
- 关系加载测试  
- 业务方法测试

## 📂 文件组织规范

### 1. models 目录结构

```
app/models/
├── __init__.py             # 统一导出
├── user.py                 # 现代语法（项目正式使用）
├── user_traditional.py     # 传统语法（学习对比用）
├── post.py                 # 文章模型
├── comment.py              # 评论模型
├── tag.py                  # 标签模型
├── post_view.py            # 浏览记录模型
└── associations.py         # 中间表定义
```

### 2. __init__.py 导出规范

```python
"""
统一导出所有模型，便于导入使用
"""
from .user import User, UserRole
from .post import Post, PostStatus
from .comment import Comment
from .tag import Tag
from .post_view import PostView

__all__ = [
    "User", "UserRole",
    "Post", "PostStatus", 
    "Comment",
    "Tag",
    "PostView",
]
```

## ⚠️ 常见陷阱和注意事项

### 1. 类型注解陷阱

```python
# ❌ 错误：没有使用 Mapped
username: str = mapped_column(String(50))

# ✅ 正确：必须使用 Mapped
username: Mapped[str] = mapped_column(String(50))
```

### 2. 可空性陷阱

```python
# ❌ 错误：类型和数据库定义不一致
avatar: Mapped[str] = mapped_column(String(255), nullable=True)

# ✅ 正确：类型层面明确可空性
avatar: Mapped[Optional[str]] = mapped_column(String(255), default=None)
```

### 3. 关系定义陷阱

```python
# ❌ 错误：忘记使用双向 back_populates
author: Mapped["User"] = relationship()

# ✅ 正确：明确双向关系
author: Mapped["User"] = relationship(back_populates="posts")
```

## 🚀 迁移策略

1. **新模型**：直接使用现代语法
2. **现有模型**：`user.py` 为正式版本，`user_traditional.py` 作为学习对比 
3. **统一标准**：后续所有模型都使用现代语法
4. **逐步重构**：条件允许时，逐步迁移传统语法模型

---

**🎯 总结：现代语法是项目标准，传统语法仅用于学习理解！**