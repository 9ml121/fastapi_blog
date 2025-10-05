# SQLAlchemy 最佳实践与常见陷阱

> 基于博客项目实战总结，帮助开发者避免常见问题，写出高质量的 ORM 代码

## 🎯 核心原则

### 1. 设计哲学：业务驱动，性能为先

**❌ 错误思维：数据库表驱动**
```python
# 直接按数据库表结构写模型
class User(Base):
    user_id = Column(Integer, primary_key=True)  # 数据库风格命名
    user_name = Column(String)
    user_email = Column(String)
```

**✅ 正确思维：业务逻辑驱动**
```python
# 从业务角度设计模型
class User(Base):
    id: Mapped[UUID] = mapped_column(primary_key=True)  # 业务含义清晰
    username: Mapped[str] = mapped_column(String(50), unique=True)
    email: Mapped[str] = mapped_column(String(100), unique=True)
    
    @property
    def display_name(self) -> str:  # 业务方法
        return self.nickname or self.username
```

## 🔥 常见陷阱与解决方案

### 陷阱 1: N+1 查询问题

**🚨 问题场景：博客列表页**
```python
# 危险代码 - 会产生 N+1 查询
posts = session.query(Post).limit(10).all()  # 1 次查询
for post in posts:
    print(f"{post.title} - {post.author.username}")  # 每个 post 1 次查询！
# 总共：1 + 10 = 11 次数据库查询
```

**💡 解决方案对比：**

#### 方案A：模型层面解决（推荐）
```python
# 在关系定义中优化
class Post(Base):
    author: Mapped["User"] = relationship(
        back_populates="posts",
        lazy="joined"  # 👈 自动 JOIN，一次查询解决
    )

# 使用时无需特殊处理
posts = session.query(Post).limit(10).all()  # 1 次 JOIN 查询
for post in posts:
    print(f"{post.title} - {post.author.username}")  # 无额外查询！
```

#### 方案B：查询层面解决
```python
# 在特定查询中解决
from sqlalchemy.orm import joinedload

posts = session.query(Post).options(
    joinedload(Post.author)  # 显式指定 JOIN
).limit(10).all()
```

#### 方案C：批量预加载
```python
from sqlalchemy.orm import selectinload

posts = session.query(Post).options(
    selectinload(Post.author)  # 使用 IN 查询批量加载
).limit(10).all()
```

**性能对比：**
| 方案 | 查询次数 | 适用场景 | 维护性 |
|------|----------|----------|--------|
| 默认 lazy="select" | 1 + N | 很少访问关联数据 | ❌ 容易忽略 |
| lazy="joined" | 1 | 经常访问关联数据 | ✅ 自动优化 |
| joinedload | 1 | 特定查询优化 | ⚠️ 需要记住 |
| selectinload | 2 | 一对多关系 | ⚠️ 需要记住 |

### 陷阱 2: 时区处理不当

**🚨 常见错误：**
```python
# 错误：未考虑时区
created_at = Column(DateTime, default=datetime.now)  # 服务器时区

# 错误：混用 aware 和 naive 时间
created_at = Column(DateTime(timezone=True), default=datetime.now)  # naive 时间存入 tz 字段
```

**✅ 正确做法：**
```python
# 方案1：使用数据库函数（推荐）
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now(),  # 数据库生成，时区准确
    comment="创建时间"
)

# 方案2：使用 UTC 时间
from datetime import datetime, timezone

def utc_now():
    return datetime.now(timezone.utc)

created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    default=utc_now,  # 明确使用 UTC 时间
    comment="创建时间"
)
```

### 陷阱 3: 默认值设置重复和混乱

**🚨 常见错误：重复设置默认值**
```python
# 危险：在多个层次重复设置相同的默认值
class User(Base):
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.USER,  # ORM 层默认值
        comment="用户角色"
    )
    
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,  # ORM 层默认值
        comment="账户是否激活"
    )
    
    def __init__(self, **kwargs):
        # ❌ 错误：重复设置相同的默认值
        kwargs.setdefault('role', UserRole.USER)      # 重复！
        kwargs.setdefault('is_active', True)          # 重复！
        kwargs.setdefault('is_verified', False)       # 重复！
        super().__init__(**kwargs)
```

**✅ 正确做法：明确区分默认值层次**

#### 方案A：三层默认值架构（推荐）

```python
class Post(Base):
    __tablename__ = "posts"
    
    # 1. 固定默认值 → default 参数
    status: Mapped[PostStatus] = mapped_column(
        SQLEnum(PostStatus),
        default=PostStatus.DRAFT,  # 简单固定默认值
        comment="文章状态"
    )
    
    view_count: Mapped[int] = mapped_column(
        Integer,
        default=0,  # 简单固定默认值
        comment="浏览次数"
    )
    
    # 2. 数据库函数 → server_default 参数
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),  # 数据库生成，确保准确性
        comment="创建时间"
    )
    
    # 3. 复杂逻辑 → __init__ 方法
    def __init__(self, **kwargs):
        """只处理复杂的业务逻辑默认值"""
        # 复杂逻辑：标题自动生成 slug
        if 'title' in kwargs and 'slug' not in kwargs:
            kwargs['slug'] = self._generate_slug_static(kwargs['title'])
        
        super().__init__(**kwargs)
    
    @staticmethod
    def _generate_slug_static(title: str) -> str:
        """静态工具方法：生成 URL 友好的 slug"""
        import re
        from datetime import datetime
        
        if not title:
            return f"文章-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # 处理中英文混合标题
        cleaned = re.sub(r'[^\w\u4e00-\u9fff\s\-]', '', title)
        cleaned = re.sub(r'\s+', '-', cleaned.strip())
        cleaned = re.sub(r'-+', '-', cleaned).strip('-')
        
        # 长度控制
        if len(cleaned) > 50:
            truncated = cleaned[:47]
            if '-' in truncated[-10:]:
                last_dash = truncated.rfind('-')
                cleaned = truncated[:last_dash]
            else:
                cleaned = truncated + "..."
        
        return cleaned if len(cleaned) >= 1 else f"文章-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
```

#### 默认值类型和使用场景

| 类型 | 使用场景 | 执行时机 | 优势 | 劣势 |
|------|----------|----------|------|------|
| `__init__` | 复杂业务逻辑、条件计算 | Python 对象创建时 | 灵活、可调用方法 | 只对构造函数生效 |
| `default` | 固定值、Python函数 | ORM INSERT 时 | 覆盖所有 ORM 操作 | 无法处理复杂逻辑 |
| `server_default` | 数据库函数、时间戳 | 数据库 INSERT 时 | 支持直接SQL操作 | 依赖数据库功能 |

#### 方案B：实际使用效果对比

```python
# 测试三种默认值的执行效果
def test_default_values():
    # 场景1：通过构造函数创建（触发所有默认值）
    post1 = Post(title="FastAPI入门教程", content="内容...")
    # 结果：
    # - slug: "FastAPI入门教程" (来自 __init__ 的复杂逻辑)
    # - status: PostStatus.DRAFT (来自 default)  
    # - view_count: 0 (来自 default)
    # - created_at: 数据库时间 (来自 server_default)
    
    # 场景2：明确指定值（覆盖默认值）
    post2 = Post(
        title="高级教程", 
        slug="advanced-tutorial",  # 明确指定，不会自动生成
        status=PostStatus.PUBLISHED  # 明确指定，覆盖默认值
    )
    
    # 场景3：直接 SQL 插入（绕过 Python）
    session.execute(text("""
        INSERT INTO posts (id, title, content) 
        VALUES (gen_random_uuid(), '直接插入', '内容')
    """))
    # 结果：
    # - slug: NULL (没有 Python 逻辑处理)
    # - status: 'draft' (来自 default，如果数据库约束需要)
    # - created_at: 数据库时间 (来自 server_default)
```

#### 方案C：优化策略总结

**📋 默认值设置决策树：**

```
是否需要默认值？
├─ 是 → 是否需要复杂计算？
│   ├─ 是 → 使用 __init__ 方法
│   └─ 否 → 是否需要数据库函数？
│       ├─ 是 → 使用 server_default
│       └─ 否 → 使用 default 参数
└─ 否 → 设为可空字段 Optional[Type]
```

**🎯 最佳实践原则：**

1. **避免重复**：同一个字段只在一个层次设置默认值
2. **选择合适层次**：根据复杂度和使用场景选择
3. **优先级明确**：`__init__` > `default` > `server_default`
4. **文档清晰**：在代码中注释说明选择原因

### 陷阱 4: 可变对象默认值陷阱

**🚨 可变对象陷阱：**
```python
# 危险！所有实例共享同一个列表
class User(Base):
    tags = Column(JSON, default=[])  # ❌ 共享引用问题
    metadata = Column(JSON, default={})  # ❌ 共享引用问题
```

**✅ 正确做法：**
```python
# 使用工厂函数
class User(Base):
    tags: Mapped[List[str]] = mapped_column(
        JSON,
        default=list,  # 👈 工厂函数，每次创建新列表
        comment="用户标签"
    )
    
    metadata: Mapped[dict] = mapped_column(
        JSON,
        default=dict,  # 👈 工厂函数，每次创建新字典
        comment="用户元数据"
    )

# 或者在构造方法中设置
def __init__(self, **kwargs):
    if 'tags' not in kwargs:
        kwargs['tags'] = []
    super().__init__(**kwargs)
```

### 陷阱 4: 关系定义不对称

**🚨 常见错误：**
```python
# User 模型中
posts = relationship("Post", back_populates="user")  # ❌ 字段名不匹配

# Post 模型中  
author = relationship("User", back_populates="posts")  # ❌ 不对称
```

**✅ 正确做法：**
```python
# User 模型中
posts: Mapped[List["Post"]] = relationship(
    back_populates="author"  # 👈 对应 Post.author
)

# Post 模型中
author: Mapped["User"] = relationship(
    back_populates="posts"   # 👈 对应 User.posts
)
```

### 陷阱 5: 索引策略不当

**🚨 常见问题：**
```python
# 忘记为外键建索引
author_id = Column(UUID, ForeignKey("users.id"))  # ❌ 连接查询慢

# 为不常用字段建索引
description = Column(Text, index=True)  # ❌ 浪费空间

# 重复索引
email = Column(String, unique=True, index=True)  # ❌ unique 已包含索引
```

**✅ 最佳实践：**
```python
# 外键必须有索引
author_id: Mapped[UUID] = mapped_column(
    ForeignKey("users.id", ondelete="CASCADE"),
    index=True,  # 👈 外键索引，提升 JOIN 性能
    comment="作者用户 ID"
)

# 常用查询字段建索引
status: Mapped[PostStatus] = mapped_column(
    SQLEnum(PostStatus),
    index=True,  # 👈 经常按状态筛选
    comment="文章状态"
)

# unique 字段无需额外 index
email: Mapped[str] = mapped_column(
    String(100),
    unique=True,  # 👈 已包含索引功能
    comment="邮箱地址"
)
```

## 💡 默认值设置最佳实践深入解析

### 1. 基于博客项目的实际应用

**我们的博客项目优化前后对比：**

#### 优化前的问题代码
```python
class User(Base):
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.USER  # ORM 层默认值
    )
    
    def __init__(self, **kwargs):
        kwargs.setdefault('role', UserRole.USER)      # ❌ 重复设置
        kwargs.setdefault('is_active', True)          # ❌ 重复设置  
        kwargs.setdefault('is_verified', False)       # ❌ 重复设置
        super().__init__(**kwargs)
```

#### 优化后的规范代码
```python
class User(Base):
    role: Mapped[UserRole] = mapped_column(
        SQLEnum(UserRole),
        default=UserRole.USER,  # 只在 ORM 层设置固定默认值
        comment="用户角色"
    )
    
    def __init__(self, **kwargs):
        """只处理复杂的业务逻辑默认值"""
        # 复杂逻辑：昵称默认使用用户名
        if 'nickname' not in kwargs and 'username' in kwargs:
            kwargs['nickname'] = kwargs['username']
        super().__init__(**kwargs)

class Post(Base):
    def __init__(self, **kwargs):
        """只处理复杂的业务逻辑默认值"""
        # 复杂逻辑：标题自动生成 slug
        if 'title' in kwargs and 'slug' not in kwargs:
            kwargs['slug'] = self._generate_slug_static(kwargs['title'])
        super().__init__(**kwargs)
    
    @staticmethod
    def _generate_slug_static(title: str) -> str:
        """静态工具方法：支持 __init__ 中调用"""
        import re
        from datetime import datetime
        
        if not title:
            return f"文章-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        
        # 处理中英文混合标题的 slug 生成
        # 保留中文、英文、数字、空格、连字符
        cleaned = title.strip()
        return cleaned[:50] if len(cleaned) >= 1 else f"文章-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
```

### 2. 静态方法在默认值设置中的应用

**为什么需要静态方法？**

在 `__init__` 方法中，实例还未完全初始化，调用实例方法可能会有问题。静态方法不依赖实例状态，更安全可靠。

```python
# ❌ 问题：在 __init__ 中调用实例方法
def __init__(self, **kwargs):
    if 'title' in kwargs and 'slug' not in kwargs:
        kwargs['slug'] = self.generate_slug(kwargs['title'])  # 风险
    super().__init__(**kwargs)

# ✅ 解决方案：使用静态方法
def __init__(self, **kwargs):
    if 'title' in kwargs and 'slug' not in kwargs:
        kwargs['slug'] = self._generate_slug_static(kwargs['title'])  # 安全
    super().__init__(**kwargs)
```

### 3. 默认值设置决策指南

**📋 快速决策流程：**

```
需要设置默认值？
├─ 固定常量值 → 使用 default 参数
├─ 时间戳 → 使用 server_default=func.now()
├─ 需要计算/条件判断 → 使用 __init__ 方法
└─ 不需要 → 设为 Optional[Type]
```

**🎯 实际应用示例：**

```python
# 时间戳：数据库函数保证准确性
created_at: Mapped[datetime] = mapped_column(
    DateTime(timezone=True),
    server_default=func.now()  # ✅ 数据库层面最准确
)

# 固定枚举值：ORM 层面设置
status: Mapped[PostStatus] = mapped_column(
    SQLEnum(PostStatus),
    default=PostStatus.DRAFT  # ✅ 简单固定默认值
)

# 复杂逻辑：Python 应用层处理
def __init__(self, **kwargs):
    if 'title' in kwargs and 'slug' not in kwargs:
        kwargs['slug'] = self._generate_slug_static(kwargs['title'])  # ✅ 复杂计算
    super().__init__(**kwargs)
```

### 4. 团队开发规范

**✅ 代码审查检查清单：**
- [ ] 同一字段没有在多个层次重复设置默认值
- [ ] `__init__` 中只包含复杂逻辑，不包含简单固定值
- [ ] 时间戳字段使用 `server_default=func.now()`
- [ ] 在 `__init__` 中调用的是静态方法
- [ ] 复杂逻辑有适当的注释说明

## ✨ 性能优化最佳实践

### 1. 查询优化策略

#### A. 选择合适的 lazy 策略
```python
# 博客系统中的实际应用
class Post(Base):
    # 多对一：经常一起查询 → joined
    author: Mapped["User"] = relationship(
        back_populates="posts",
        lazy="joined"  # 显示文章列表时总是需要作者信息
    )

class User(Base):
    # 一对多：按需查询 → select (默认)
    posts: Mapped[List["Post"]] = relationship(
        back_populates="author"
        # lazy="select" 是默认值，按需加载文章列表
    )
```

#### B. 批量操作优化
```python
# ❌ 低效：逐个插入
for data in post_list:
    post = Post(**data)
    session.add(post)
    session.commit()  # 每次都提交

# ✅ 高效：批量插入
posts = [Post(**data) for data in post_list]
session.add_all(posts)
session.commit()  # 一次性提交

# ✅ 更高效：批量插入（大数据量）
session.bulk_insert_mappings(Post, post_list)
session.commit()
```

### 2. 内存优化策略

#### A. 查询字段选择
```python
# ❌ 查询所有字段
posts = session.query(Post).all()

# ✅ 只查询需要的字段
post_summaries = session.query(
    Post.id, Post.title, Post.created_at
).all()

# ✅ 使用 defer 延迟加载大字段
posts = session.query(Post).options(
    defer(Post.content)  # 延迟加载大文本字段
).all()
```

#### B. 分页查询
```python
# ✅ 标准分页
def get_posts_paginated(page: int, size: int = 20):
    offset = (page - 1) * size
    return session.query(Post).offset(offset).limit(size).all()

# ✅ 游标分页（更高效）
def get_posts_cursor(last_id: UUID = None, size: int = 20):
    query = session.query(Post).order_by(Post.created_at.desc())
    if last_id:
        query = query.filter(Post.id > last_id)
    return query.limit(size).all()
```

## 🛡️ 数据安全最佳实践

### 1. 软删除模式

```python
class User(Base):
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        comment="账户是否激活（软删除标记）"
    )
    
    def deactivate(self) -> None:
        """软删除：停用账户而不是物理删除"""
        self.is_active = False
        
    @classmethod
    def active_users(cls):
        """只查询活跃用户的查询器"""
        return session.query(cls).filter(cls.is_active == True)
```

### 2. 敏感数据处理

```python
class User(Base):
    # ❌ 永远不存储明文密码
    # password = Column(String)
    
    # ✅ 只存储哈希值
    password_hash: Mapped[str] = mapped_column(
        String(255),
        comment="密码哈希值"
    )
    
    def set_password(self, password: str) -> None:
        """设置密码：自动进行哈希处理"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"])
        self.password_hash = pwd_context.hash(password)
    
    def verify_password(self, password: str) -> bool:
        """验证密码"""
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"])
        return pwd_context.verify(password, self.password_hash)
```

## 🧪 测试友好设计

### 1. 工厂方法模式

```python
class User(Base):
    # ... 字段定义
    
    @classmethod
    def create_test_user(
        cls,
        username: str = "test_user",
        email: str = "test@example.com",
        **kwargs
    ) -> "User":
        """创建测试用户的工厂方法"""
        return cls(
            username=username,
            email=email,
            nickname=kwargs.get('nickname', username),
            password_hash='test_hash',
            **kwargs
        )
```

### 2. 数据完整性检查

```python
from sqlalchemy import event

# 数据完整性检查
@event.listens_for(Post, 'before_insert')
@event.listens_for(Post, 'before_update')
def validate_post_data(mapper, connection, target):
    """保存前的数据验证"""
    # 确保已发布的文章有发布时间
    if target.status == PostStatus.PUBLISHED and not target.published_at:
        target.published_at = datetime.utcnow()
    
    # 确保 slug 唯一性
    if not target.slug:
        target.slug = target.generate_slug()
```

## 📋 开发工作流最佳实践

### 1. 模型演进策略

```python
# ✅ 向后兼容的字段添加
class User(Base):
    # 新字段设为可空，避免现有数据问题
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        default=None,
        comment="手机号码"
    )
    
    # 枚举扩展要考虑兼容性
    class UserRole(str, Enum):
        USER = "user"
        ADMIN = "admin"
        MODERATOR = "moderator"  # 新增角色
```

### 2. 代码组织结构

```
models/
├── __init__.py          # 导入所有模型
├── base.py             # 基础模型类
├── user.py             # 用户相关模型
├── post.py             # 文章相关模型
├── comment.py          # 评论相关模型
└── mixins.py           # 共用的 mixin 类

# 共用功能提取为 mixin
class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now()
    )

class User(Base, TimestampMixin):  # 继承 mixin
    # ... 用户特有字段
```

## 🎯 性能监控和调试

### 1. SQL 查询日志

```python
# 开发环境启用 SQL 日志
engine = create_engine(
    DATABASE_URL,
    echo=True,  # 打印所有 SQL
    echo_pool=True,  # 打印连接池信息
)

# 生产环境性能监控
import time
from sqlalchemy import event

@event.listens_for(Engine, "before_cursor_execute")
def receive_before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    context._query_start_time = time.time()

@event.listens_for(Engine, "after_cursor_execute")
def receive_after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.time() - context._query_start_time
    if total > 0.1:  # 慢查询警告
        logger.warning(f"Slow query: {total:.2f}s - {statement[:100]}")
```

### 2. 内存使用监控

```python
# 检查会话中的对象数量
def check_session_size(session):
    new_count = len(session.new)
    dirty_count = len(session.dirty)
    deleted_count = len(session.deleted)
    
    if new_count + dirty_count + deleted_count > 1000:
        logger.warning(f"Large session: new={new_count}, dirty={dirty_count}, deleted={deleted_count}")
```

## 📚 学习进阶路径

### 初级掌握
- ✅ 基础模型定义
- ✅ 字段类型和约束
- ✅ 简单关系映射

### 中级掌握
- ✅ 性能优化（N+1 问题）
- ✅ 复杂查询和关系
- ✅ 数据迁移策略

### 高级掌握
- 🎯 查询优化器理解
- 🎯 数据库分库分表
- 🎯 读写分离配置

---

## 🎯 核心要点总结

1. **性能第一**：时刻考虑查询性能，避免 N+1 问题
2. **类型安全**：使用现代语法，充分利用类型提示
3. **业务驱动**：从业务角度设计模型，不要被数据库表结构限制
4. **安全意识**：正确处理敏感数据，实施软删除策略
5. **测试友好**：设计易于测试的模型结构
6. **监控到位**：在开发和生产环境都要有性能监控

记住：好的 ORM 模型设计不仅要功能正确，更要性能优秀、安全可靠、易于维护。