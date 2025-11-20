# Alembic 数据库迁移详解

## 🎯 三种数据库变更方案对比

### 方案1：Base.metadata.create_all()

**适用场景：** 开发初期快速原型

```python
from app.db.database import Base, engine
Base.metadata.create_all(bind=engine)
```

**优点：**
✅ 简单直接，一行代码搞定
✅ 适合学习和快速测试

**缺点：**
❌ 无法处理表结构变更
❌ 无版本控制，无法追溯历史
❌ 团队协作困难
❌ 生产环境不可用（会丢数据）

---

### 方案2：手动编写 SQL

**适用场景：** 复杂的遗留系统

```sql
-- migration_001.sql
ALTER TABLE users ADD COLUMN email VARCHAR(100);
ALTER TABLE users ADD COLUMN is_verified BOOLEAN DEFAULT FALSE;
```

**优点：**
✅ 完全控制，精确执行
✅ 可以执行复杂的数据迁移逻辑

**缺点：**
❌ 容易出错，难以维护
❌ 需要手动追踪执行状态
❌ 回滚复杂，需要手写反向 SQL
❌ 团队协作需要额外协调

---

### 方案3：Alembic 迁移工具 ⭐ 推荐

**适用场景：** 现代项目的标准实践

```bash
# 自动生成迁移脚本
alembic revision --autogenerate -m "Add email field"

# 应用迁移
alembic upgrade head

# 回滚
alembic downgrade -1
```

**优点：**
✅ 自动化 + 版本控制
✅ 与 SQLAlchemy 完美集成
✅ 支持安全回滚
✅ 迁移脚本可纳入 Git
✅ 团队协作一致性保证
✅ 生产环境安全

**缺点：**
⚠️ 学习曲线（但值得投资）
⚠️ 复杂迁移需要手动调整脚本

---
## 📚 核心概念

### 什么是数据库迁移？

**数据库迁移（Database Migration）** 是一种管理数据库模式（schema）变更的方法，就像 Git 管理代码变更一样。

### 1️⃣ 为什么需要数据库迁移工具？

  问题场景：

  **开发流程：**
  Day 1: 创建 users 表（username, email, password_hash）
  Day 5: 需要添加 deleted_at 字段
  Day 10: 需要添加索引优化查询
  Day 20: 需要修改字段类型（String(50) → String(100)）

  **传统做法的问题：**
  ❌ 手动写 SQL（ALTER TABLE ...）→ 容易出错，不可重现
  ❌ 开发/测试/生产环境不一致 → 难以同步
  ❌ 无法回滚 → 改错了无法恢复
  ❌ 团队协作困难 → 每个人的数据库结构可能不同

  **Alembic 的解决方案：**
  ✅ 版本控制：每次修改都是一个版本（像 Git commit）
  ✅ 可重现：在任何环境执行相同的迁移脚本
  ✅ 可回滚：支持 upgrade（前进）和 downgrade（后退）
  ✅ 团队协作：迁移脚本提交到代码仓库，团队共享

  ---
### 2️⃣ Alembic 核心概念

#### 概念一：版本（Revision）

每次数据库结构修改都会生成一个唯一的版本标识：

  ```plaintext
alembic/versions/
├── 001_create_users_table.py        # 版本 1: 创建用户表
├── 002_add_deleted_at_field.py      # 版本 2: 添加 deleted_at
└── 003_add_email_index.py           # 版本 3: 添加索引
  ```
 
每个版本文件包含：
  - Revision ID：唯一标识（如 "a1b2c3d4e5f6"）
  - Down Revision：父版本 ID（从哪个版本演进来的）
  - upgrade()：升级逻辑（如何从旧版本升级到新版本）
  - downgrade()：降级逻辑（如何从新版本回退到旧版本）

#### 概念二：版本链（Migration Chain）

```plaintext
数据库版本演进链：
None → 001 → 002 → 003 → 004(head)
(空)   创建表  加字段  加索引  改类型

当前版本head记录在：
数据库的 alembic_version 表中（自动创建）
```


#### 概念三：自动检测（Auto-generation）

```plaintext
Alembic 对比两个状态，自动生成迁移代码：

状态 A：数据库当前结构（从 alembic_version 表读取）
状态 B：SQLAlchemy 模型定义（从 app/models/*.py 读取）

对比结果 → 生成迁移脚本：
	- 添加了字段？生成 op.add_column()
	- 删除了字段？生成 op.drop_column()
	- 修改了类型？生成 op.alter_column()
```

  ---

### 3️⃣ Alembic 工作流程图

#### 场景 1：第一次迁移 SQLAlchemy 模型

```
┌─────────────────┐
│  SQLAlchemy     │  定义：Python 模型类
│    Models       │  (app/models/*.py)
└────────┬────────┘
         │
         │ alembic revision --autogenerate
         ↓
┌─────────────────┐
│    Alembic      │  对比：模型 vs 数据库
│   Migration     │  生成：迁移脚本
│    Scripts      │  (alembic/versions/*.py)
└────────┬────────┘
         │
         │ alembic upgrade head
         ↓
┌─────────────────┐
│    Database     │  执行：SQL DDL 语句
│   (PostgreSQL)  │  记录：版本号
└─────────────────┘
```

#### 场景2：后续修改 SQLAlchemy 模型
```
 ┌─────────────────────────────────────────────────────┐
  │  1. 修改 SQLAlchemy 模型（app/models/user.py）      │
  │     添加字段：deleted_at: Mapped[datetime | None]   │
  └─────────────────┬───────────────────────────────────┘
                    │
                    ▼
  ┌─────────────────────────────────────────────────────┐
  │  2. 生成迁移脚本（自动检测差异）                     │
  │     $ alembic revision --autogenerate -m "add..."   │
  │     生成：alembic/versions/xxx_add_deleted_at.py    │
  └─────────────────┬───────────────────────────────────┘
                    │
                    ▼
  ┌─────────────────────────────────────────────────────┐
  │  3. 检查迁移脚本（确认自动生成的代码正确）           │
  │     def upgrade():                                  │
  │         op.add_column('users',                      │
  │             sa.Column('deleted_at', ...))           │
  └─────────────────┬───────────────────────────────────┘
                    │
                    ▼
  ┌─────────────────────────────────────────────────────┐
  │  4. 执行迁移（应用到数据库）                         │
  │     $ alembic upgrade head                          │
  │     数据库更新：ALTER TABLE users ADD COLUMN...     │
  └─────────────────┬───────────────────────────────────┘
                    │
                    ▼
  ┌─────────────────────────────────────────────────────┐
  │  5. 版本记录更新（alembic_version 表）              │
  │     current_version: xxx_add_deleted_at             │
  └─────────────────────────────────────────────────────┘

```
### 4️⃣ 版本追踪机制

**`alembic_version` 表：**

| version_num |
|-------------|
| ae1027a6acf |

- 记录当前数据库的迁移版本号
- Alembic 根据此表决定执行哪些迁移
- 防止重复执行同一迁移

### 5️⃣ 迁移脚本结构

```python
# alembic/versions/xxxx_initial_migration.py

"""add deleted_at field to users

  Revision ID: a1b2c3d4e5f6
  Revises: previous_version_id  # 父版本
  Create Date: 2025-10-05 10:00:00
  """
  from alembic import op
  import sqlalchemy as sa

  # 版本标识（关键！）
  revision = 'a1b2c3d4e5f6'      # 当前版本 ID
  down_revision = 'previous_id'  # 从哪个版本演进
  branch_labels = None
  depends_on = None

  def upgrade():
      """升级逻辑：如何从旧版本变成新版本"""
      op.add_column('users',
          sa.Column('deleted_at', sa.DateTime(timezone=True),
                    nullable=True, comment='软删除时间')
      )

  def downgrade():
      """降级逻辑：如何从新版本回退到旧版本"""
      op.drop_column('users', 'deleted_at')


```

**关键字段：**
- `revision` - 当前版本唯一标识（哈希值）
- `down_revision` - 父版本（构成迁移链）
- `upgrade()` - 应用此迁移的操作
- `downgrade()` - 回滚此迁移的操作



---

## 📋 Alembic 核心命令

### 初始化和配置

```bash
# 1. 初始化 Alembic（生成配置文件和目录结构）
alembic init alembic

# 2. 编辑配置文件 alembic.ini
# 设置数据库连接字符串
sqlalchemy.url = postgresql://user:password@localhost/dbname
```

### 迁移管理

```bash
# 创建迁移脚本（手动）
alembic revision -m "create users table"

# 创建迁移脚本（自动检测）
alembic revision --autogenerate -m "add email field"

# 查看迁移历史
alembic history

# 查看当前版本
alembic current
```

### 升级和降级

```bash
# 升级到最新版本
alembic upgrade head

# 升级到指定版本
alembic upgrade ae1027a6acf

# 升级 N 个版本
alembic upgrade +2

# 降级一个版本
alembic downgrade -1

# 降级到指定版本
alembic downgrade ae1027a6acf

# 降级到初始状态
alembic downgrade base
```

### 查看将要执行的SQL(不实际执行)
```shell
alembic upgrade head --sql
```

---

## 🔍 迁移脚本深入解析

### 自动生成的迁移脚本示例

```python
"""Add email and verification to users

Revision ID: 3d8f2a9c1e6b
Revises: ae1027a6acf
Create Date: 2025-10-03 14:30:22.456789
"""

from alembic import op
import sqlalchemy as sa

# 版本标识
revision = '3d8f2a9c1e6b'
down_revision = 'ae1027a6acf'  # 指向前一个版本
branch_labels = None
depends_on = None

def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('users', sa.Column('email', sa.String(length=100), nullable=True))
    op.add_column('users', sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'))
    op.create_unique_constraint('uq_users_email', 'users', ['email'])
    op.create_index('idx_users_email', 'users', ['email'])
    # ### end Alembic commands ###

def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index('idx_users_email', table_name='users')
    op.drop_constraint('uq_users_email', 'users', type_='unique')
    op.drop_column('users', 'is_verified')
    op.drop_column('users', 'email')
    # ### end Alembic commands ###
```

### 常用迁移操作（op 对象 API）

| 操作类型 | 函数 | 示例 |
|---------|------|------|
| **表操作** | `op.create_table()` | `op.create_table('posts', sa.Column('id', sa.UUID(), primary_key=True))` |
| | `op.drop_table()` | `op.drop_table('posts')` |
| | `op.rename_table()` | `op.rename_table('old_posts', 'posts')` |
| **列操作** | `op.add_column()` | `op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))` |
| | `op.drop_column()` | `op.drop_column('users', 'bio')` |
| | `op.alter_column()` | `op.alter_column('users', 'username', type_=sa.String(100))` |
| **索引** | `op.create_index()` | `op.create_index('idx_users_email', 'users', ['email'])` |
| | `op.drop_index()` | `op.drop_index('idx_users_email')` |
| **约束** | `op.create_unique_constraint()` | `op.create_unique_constraint('uq_users_email', 'users', ['email'])` |
| | `op.create_foreign_key()` | `op.create_foreign_key('fk_posts_author', 'posts', 'users', ['author_id'], ['id'])` |
| | `op.drop_constraint()` | `op.drop_constraint('uq_users_email', 'users', type_='unique')` |
| **数据迁移** | `op.execute()` | `op.execute("UPDATE users SET is_verified = TRUE WHERE ...")` |

**完整示例：**

```python
from alembic import op
import sqlalchemy as sa

def upgrade() -> None:
    # 1. 创建表
    op.create_table(
        'posts',
        sa.Column('id', sa.UUID(), primary_key=True),
        sa.Column('title', sa.String(200), nullable=False),
        sa.Column('author_id', sa.UUID(), sa.ForeignKey('users.id')),
    )
    
    # 2. 添加列
    op.add_column('users', sa.Column('bio', sa.Text(), nullable=True))
    
    # 3. 创建索引
    op.create_index('idx_users_email', 'users', ['email'])
    
    # 4. 执行数据迁移（填充默认值）
    op.execute("""
        UPDATE users 
        SET bio = '这是一个新用户' 
        WHERE bio IS NULL
    """)
```

---

## 🏗️ Alembic 配置详解

### 1. alembic.ini 配置文件

```ini
[alembic]
# 迁移脚本存储路径
script_location = alembic

# 数据库连接字符串（可配置在环境变量中）
# sqlalchemy.url = driver://user:pass@localhost/dbname
sqlalchemy.url = postgresql://root:password@localhost:5432/blogdb

# 迁移脚本文件名格式
# file_template = %%(rev)s_%%(slug)s
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s

# 日志配置
[loggers]
keys = root,sqlalchemy,alembic

[handlers]
keys = console

[formatters]
keys = generic
```

### 2. env.py 配置（核心）

```python
# alembic/env.py

from logging.config import fileConfig
from sqlalchemy import engine_from_config, pool
from alembic import context

# 导入项目配置
from app.core.config import settings
from app.db.database import Base

# 导入所有模型（必须！）
from app.models import User, Post, Comment, Tag, PostView

# Alembic Config 对象
config = context.config

# 设置数据库 URL（从项目配置读取）
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)

# 配置日志
fileConfig(config.config_file_name)

# 目标元数据（包含所有表定义）
target_metadata = Base.metadata

def run_migrations_offline() -> None:
    """离线模式：生成 SQL 脚本，不连接数据库"""
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online() -> None:
    """在线模式：连接数据库执行迁移"""
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()

# 根据运行模式选择
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
```


---
## ⚠️ 常见陷阱

  ❌ 错误：删除字段后立即添加同名字段（会丢失数据）
`op.drop_column('users', 'email')`
`op.add_column('users', sa.Column('email', sa.String(200)))`

  ✅ 正确：分两个迁移，中间有数据迁移逻辑
  Migration 1: 添加新字段 email_new
  Migration 2: 复制数据 email → email_new
  Migration 3: 删除旧字段 email，重命名 email_new → email

  ❌ 错误：修改已执行的迁移脚本
  如果团队成员已经执行了迁移，修改会导致版本不一致

  ✅ 正确：创建新的迁移来修正错误


## 最佳实践

### 1. 必须导入所有模型

```python
# ❌ 错误：Alembic 检测不到模型
# alembic/env.py
from app.db.database import Base
target_metadata = Base.metadata

# ✅ 正确：导入所有模型
from app.models import User, Post, Comment, Tag, PostView
target_metadata = Base.metadata
```

**原因：** Alembic 通过 `Base.metadata` 获取表定义，但必须先导入模型类才能注册到 metadata。

---

### 2. 自动生成后需手动审查

```python
# Alembic 自动生成的脚本可能不完美
def upgrade() -> None:
    # ⚠️ 检查：是否需要数据迁移？
    op.add_column('users', sa.Column('email', sa.String(100), nullable=False))

    # ✅ 修正：先添加为可空，填充数据后再改为 NOT NULL
    # op.add_column('users', sa.Column('email', sa.String(100), nullable=True))
    # op.execute("UPDATE users SET email = username || '@example.com'")
    # op.alter_column('users', 'email', nullable=False)
```

**最佳实践：**
1. 自动生成脚本后，务必审查代码
2. 复杂迁移需手动调整（数据填充、条件判断等）
3. 在开发环境充分测试后再应用到生产

---

### 3. 迁移脚本需纳入版本控制

```bash
# Git 提交迁移脚本
git add alembic/versions/20251003_1430_ae1027a6acf_add_email_field.py
git commit -m "Add email field to users table"
```

**团队协作流程：**
1. 开发者 A 创建迁移脚本并提交
2. 开发者 B 拉取代码后执行 `alembic upgrade head`
3. 生产环境部署时执行相同命令

---

### 4. 数据库连接字符串安全

```python
# ❌ 错误：硬编码在 alembic.ini
sqlalchemy.url = postgresql://root:Password123@localhost/blogdb

# ✅ 正确：从环境变量或配置文件读取
# alembic/env.py
from app.core.config import settings
config.set_main_option('sqlalchemy.url', settings.DATABASE_URL)
```



### 5. 生产环境迁移策略

```bash
# 1. 备份数据库！！！
pg_dump -U user -d blogdb > backup_$(date +%Y%m%d).sql

# 2. 检查待执行的迁移
alembic current
alembic history

# 3. 在只读副本上测试
alembic upgrade head --sql > migration.sql  # 生成 SQL
# 在副本上执行 SQL 验证

# 4. 维护窗口执行（或使用零停机迁移策略）
alembic upgrade head

# 5. 验证表结构和数据完整性
```


 > [!NOTE]
  Alembic 的三个核心价值：
  >1. 版本化：每次修改都有明确的版本记录，像 Git 管理代码一样管理数据库
  >2. 可回滚：任何修改都可以撤销，增加安全性
  >3. 团队协作：迁移脚本纳入代码库，确保所有环境一致

---

## 🎓 学习路径

### 第一阶段：基础操作（今天完成）

1. ✅ 理解迁移工具的必要性
2. ✅ 掌握 Alembic 工作原理
3. ⏳ 初始化 Alembic 配置
4. ⏳ 创建第一个迁移脚本
5. ⏳ 执行迁移并验证

### 第二阶段：进阶技巧（实践中学习）

- 处理复杂数据迁移（数据转换、填充默认值）
- 多分支开发的迁移合并
- 离线模式生成 SQL 脚本
- 自定义迁移模板

### 第三阶段：生产实战（项目后期）

- 零停机迁移策略
- 回滚预案和测试
- 监控迁移执行时间
- 大表迁移优化（分批处理）

---

## 📚 扩展阅读

- [Alembic 官方文档](https://alembic.sqlalchemy.org/)
- [SQLAlchemy 数据库迁移实战](https://docs.sqlalchemy.org/en/20/orm/extensions/asyncio.html)
- [生产环境数据库迁移最佳实践](https://www.postgresql.org/docs/current/ddl-alter.html)

---

## 🔖 快速参考卡片

```bash
# 初始化
alembic init alembic

# 创建迁移
alembic revision --autogenerate -m "message"

# 应用迁移
alembic upgrade head

# 回滚一步
alembic downgrade -1

# 查看历史
alembic history

# 查看当前版本
alembic current

# 生成 SQL（不执行）
alembic upgrade head --sql
```

---

**下一步实践任务：**
1. 初始化 Alembic 配置
2. 配置 env.py 导入所有模型
3. 创建第一个迁移脚本
4. 执行迁移，创建数据库表
5. 验证表结构

准备好了就继续实践吧！🚀
