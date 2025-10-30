# Alembic 数据库迁移最佳实践

## 📚 核心原则

本项目遵循以下 Alembic 最佳实践，确保数据库迁移的安全性、可维护性和团队协作效率。

---

## ✅ 我们已实施的最佳实践

### 1. **安全的配置管理** ✅

**问题：** 数据库密码等敏感信息不应硬编码或提交到 Git

**解决方案：**

-   ✅ 使用 `.env` 文件存储敏感配置
-   ✅ `.env` 已加入 `.gitignore`
-   ✅ 提供 `.env.example` 作为配置模板
-   ✅ `config.py` 中使用占位符作为默认值

```python
# app/core/config.py
class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/dbname"  # 占位符

    model_config = {
        "env_file": ".env",  # 从 .env 读取实际配置
    }
```

---

### 2. **正确的模型导入** ✅

**问题：** Alembic autogenerate 需要 import 所有模型才能检测

**解决方案：**

```python
# alembic/env.py
from app.db.database import Base
from app.models import Comment, Post, PostView, Tag, User

target_metadata = Base.metadata  # 包含所有表定义
```

**关键点：**

-   必须显式导入所有模型类
-   如果模型很多，考虑在 `app/models/__init__.py` 中统一导出

---

### 3. **高级比较选项** ✅

**问题：** 默认 autogenerate 可能错过列类型或默认值的变化

**解决方案：**

```python
# alembic/env.py - context.configure()
compare_type=True,              # 检测列类型变化
compare_server_default=True,    # 检测服务端默认值变化
```

**作用：**

-   检测 `VARCHAR(50)` → `VARCHAR(100)` 的变化
-   检测 `server_default=func.now()` 的变化

---

### 4. **事务模式配置** ✅

**问题：** 迁移失败时如何回滚？

**解决方案：**

```python
# alembic/env.py - context.configure()
transaction_per_migration=True  # 每个迁移一个事务
```

**PostgreSQL 优势：**

-   ✅ 支持 DDL 事务（CREATE TABLE 等可以回滚）
-   ✅ 迁移失败自动回滚，数据库保持一致状态

**注意：** MySQL 不支持 DDL 事务，迁移失败可能导致不一致

---

### 5. **连接池管理** ✅

**问题：** 迁移时使用连接池可能导致连接泄漏

**解决方案：**

```python
# alembic/env.py
connectable = engine_from_config(
    configuration,
    poolclass=pool.NullPool,  # 不使用连接池
)
```

**原因：**

-   迁移脚本是一次性执行，不需要连接池
-   NullPool 确保连接用完立即关闭

---

### 6. **语义化文件名** ✅

**问题：** 默认文件名 `ae1027a6acf_add_email.py` 难以识别时间顺序

**解决方案：**

```ini
# alembic.ini
file_template = %%(year)d%%(month).2d%%(day).2d_%%(hour).2d%%(minute).2d_%%(rev)s_%%(slug)s
```

**效果：**

```
默认：ae1027a6acf_add_email_field.py
改进：20251004_1430_ae1027a6acf_add_email_field.py
```

**优势：**

-   按时间排序
-   便于识别创建时间
-   便于查找特定时期的迁移

---

## ⚠️ 推荐但未实施的最佳实践（可选）

### 1. **排除特定表** （可选）

如果有不需要 Alembic 管理的表（如第三方库的表）：

```python
# alembic/env.py
def include_object(object, name, type_, reflected, compare_to):
    """排除不需要迁移的表"""
    if type_ == "table" and name in ["spatial_ref_sys", "alembic_version"]:
        return False
    return True

context.configure(
    ...,
    include_object=include_object,
)
```

---

### 2. **自定义类型比较** （高级）

如果使用自定义类型（如 PostGIS 的 GEOMETRY），需要自定义比较逻辑：

```python
# alembic/env.py
def compare_type(context, inspected_column, metadata_column, inspected_type, metadata_type):
    # 自定义类型比较逻辑
    return False  # 不生成 ALTER TYPE 语句
```

---

### 3. **多数据库环境** （可选）

如果需要支持 PostgreSQL / MySQL / SQLite：

```python
# alembic/env.py
def run_migrations_online() -> None:
    # 根据数据库类型动态配置
    dialect_name = connectable.dialect.name

    render_as_batch = dialect_name == "sqlite"  # SQLite 需要 batch 模式

    context.configure(
        ...,
        render_as_batch=render_as_batch,
    )
```

---

## 📋 生产环境部署检查清单

### 部署前

-   [ ] 在开发环境测试迁移脚本
-   [ ] 在测试环境运行完整迁移
-   [ ] 生成 SQL 审查：`alembic upgrade head --sql`
-   [ ] 检查 SQL 是否有风险操作（DROP、ALTER、大表操作）
-   [ ] 估算迁移执行时间（大表可能需要维护窗口）
-   [ ] 准备回滚计划：`alembic downgrade -1 --sql`

### 部署时

```bash
# 1. 备份数据库（！！！非常重要！！！）
pg_dump -U user -d blogdb > backup_$(date +%Y%m%d_%H%M%S).sql

# 2. 检查当前版本
PYTHONPATH=. uv run alembic current

# 3. 查看待执行的迁移
PYTHONPATH=. uv run alembic history

# 4. 执行迁移
PYTHONPATH=. uv run alembic upgrade head

# 5. 验证结果
PYTHONPATH=. uv run alembic current

# 6. 检查表结构
psql -U user -d blogdb -c "\d tablename"
```

### 部署后

-   [ ] 验证应用启动正常
-   [ ] 验证关键功能正常
-   [ ] 监控数据库性能指标
-   [ ] 保留备份文件至少 7 天

---

完美！现在更新 TODO 列表，开始下一步：

[1 tool called]

完美！现在进入 **Step 2: 创建数据库迁移脚本**

---

##  📌 迁移步骤

### **背景知识**

项目使用 Alembic 进行数据库迁移。你需要：

1. 使用 `alembic revision --autogenerate` 自动生成迁移脚本
2. 检查生成的脚本是否正确
3. 执行迁移测试

### **具体步骤**

**Step 2.1：生成迁移脚本**

```bash
# 进入项目根目录
cd /Users/limq/00-app/fastapi_blog

# 使用 Alembic 自动生成迁移脚本
uv run alembic revision --autogenerate -m "add_post_like_and_favorite_tables"
```

这会在 `alembic/versions/` 目录下创建一个新的迁移文件。

**Step 2.2：检查迁移脚本**

生成的迁移脚本会自动检测你的模型变化，并生成相应的 SQL。你需要：

1. 打开生成的迁移文件（通常是最新的文件）
2. 检查 `upgrade()` 和 `downgrade()` 函数
3. 验证表结构、字段、约束是否正确

**预期内容**：

```python
def upgrade() -> None:
    # 添加新的计数字段到 posts 表
    op.add_column('posts', sa.Column('like_count', sa.Integer(), nullable=False, server_default='0'))
    op.add_column('posts', sa.Column('favorite_count', sa.Integer(), nullable=False, server_default='0'))

    # 创建 post_likes 表
    op.create_table('post_likes',
        sa.Column('id', sa.UUID(), nullable=False),
        sa.Column('user_id', sa.UUID(), nullable=True),
        sa.Column('post_id', sa.UUID(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['post_id'], ['posts.id'], ondelete='CASCADE'),
        sa.UniqueConstraint('user_id', 'post_id', name='uix_user_post')
    )

    # 创建索引
    op.create_index('ix_post_likes_user_id', 'post_likes', ['user_id'])
    op.create_index('ix_post_likes_post_id', 'post_likes', ['post_id'])

    # 创建 post_favorites 表（类似）
    op.create_table('post_favorites', ...)
```

**Step 2.3：执行迁移**

```bash
# 应用迁移
uv run alembic upgrade head

# 验证迁移是否成功（检查数据库表）
uv run alembic current  # 显示当前版本
```

**Step 2.4：验证迁移结果**

你可以用 SQL 查询验证表是否创建成功：

```bash
# 进入 PostgreSQL
psql -U root -d blogdb -h localhost

# 查看表结构
\d post_likes
\d post_favorites

# 查看 posts 表新增字段
\d posts
```

---

### 注意事项

**重要**：在执行迁移前，需要确保：

1. ✅ 所有模型文件已经保存并导入正确
2. ✅ PostgreSQL 数据库容器已启动
3. ✅ 数据库连接配置正确（见 `alembic/env.py`）

**如果出现问题**：

-   如果自动生成的迁移不完整，可以手动编辑迁移文件
-   如果需要回滚，使用 `uv run alembic downgrade -1` 回到上一个版本

---

## ⚠️ 常见陷阱与避免方法

### 1. **忘记导入新模型**

**问题：** 添加新模型但忘记在 `env.py` 中导入

**症状：** `alembic revision --autogenerate` 检测不到新表

**解决：**

-   在 `app/models/__init__.py` 中统一导出所有模型
-   在 `env.py` 中 `from app.models import *`

---

### 2. **直接修改已执行的迁移脚本**

**问题：** 修改已经 `upgrade` 的迁移脚本

**后果：**

-   团队成员的数据库状态不一致
-   可能导致迁移失败

**正确做法：**

-   创建新的迁移脚本修正错误
-   或者使用 `alembic downgrade` 回滚后重新生成

---

### 3. **忽略 autogenerate 的警告**

**问题：** autogenerate 生成的脚本可能不完美

**必须审查：**

-   列的 `nullable` 变化（需要先填充默认值）
-   列类型变化（可能需要数据转换）
-   索引和约束的变化

**示例：**

```python
# ❌ 错误：直接添加 NOT NULL 列
op.add_column('users', sa.Column('email', sa.String(100), nullable=False))

# ✅ 正确：分步处理
# 1. 添加为可空
op.add_column('users', sa.Column('email', sa.String(100), nullable=True))
# 2. 填充默认值
op.execute("UPDATE users SET email = username || '@example.com' WHERE email IS NULL")
# 3. 修改为 NOT NULL
op.alter_column('users', 'email', nullable=False)
```

---

### 4. **大表迁移锁表时间过长**

**问题：** `ALTER TABLE` 大表可能锁表数分钟

**风险：** 生产环境服务不可用

**解决方案：**

-   使用 PostgreSQL 的 `CONCURRENTLY` 选项（索引）
-   分批处理数据迁移
-   在维护窗口执行

```python
# 创建索引时避免锁表
op.create_index(
    'idx_users_email',
    'users',
    ['email'],
    postgresql_concurrently=True,  # 不锁表
)
```

---

### 5. **不测试 downgrade**

**问题：** 只测试 `upgrade` 不测试 `downgrade`

**后果：** 回滚时发现 `downgrade` 脚本有错误

**最佳实践：**

```bash
# 完整测试流程
alembic upgrade head    # 升级
alembic downgrade -1    # 降级一步
alembic upgrade head    # 再次升级
```

---

### 6. **`default` 与 `server_default` 混淆**

**问题：** Alembic 无法正确检测 Python 层面的 `default` 参数

**症状：** 在已有数据的表上添加 NOT NULL 列时出现 `NotNullViolation` 错误

**错误示例：**

```python
# 模型定义
like_count: Mapped[int] = mapped_column(Integer, default=0, comment="点赞次数统计")

# Alembic 生成的迁移（错误）
op.add_column(
    "posts",
    sa.Column("like_count", sa.Integer(), nullable=False, comment="点赞次数统计"),
)
# 缺少 server_default，导致现有数据行无法满足 NOT NULL 约束
```

**原因分析：**

-   `default=0`：Python/ORM 层面的默认值，只在创建新实例时生效
-   `server_default=text('0')`：数据库层面的默认值，在数据库操作时生效
-   Alembic 的 `compare_server_default=True` **只检测 `server_default`，不检测 `default`**

**解决方案：**

**方案 A：在模型中同时使用两种默认值**

```python
like_count: Mapped[int] = mapped_column(
    Integer,
    default=0,                    # Python 层面默认值
    server_default=text('0'),     # 数据库层面默认值，必须明确指定为 SQL 文本，不能用 0
    comment="点赞次数统计"
)
```

**方案 B：手动修复迁移文件**

```python
op.add_column(
    "posts",
    sa.Column(
        "like_count",
        sa.Integer(),
        nullable=False,
        server_default=text('0'),  # 添加数据库默认值
        comment="点赞次数统计"
    ),
)
```

**最佳实践：**

-   对于需要在数据库层面有默认值的列，**必须同时使用 `server_default`**
-   这是 Alembic 的已知限制，不是配置问题
-   建议在模型定义时就同时设置两种默认值，避免后续问题

---

## 🎯 团队协作规范

### 1. **迁移脚本冲突**

**场景：** 两个开发者同时创建迁移脚本

**问题：** 两个分支都有 `down_revision=xxx` 指向同一版本

**解决：**

```bash
# 开发者 A 先合并
git checkout main
git pull

# 开发者 B 合并前：
git rebase main
alembic merge heads -m "Merge migrations"  # 合并迁移分支
```

---

### 2. **迁移脚本命名规范**

**规范：**

-   使用有意义的 slug：`add_email_verification` 而不是 `update`
-   英文命名，使用下划线分隔
-   简洁但清晰

**示例：**

```bash
# ✅ 好的命名
alembic revision --autogenerate -m "add_email_verification_to_users"
alembic revision --autogenerate -m "create_posts_table"
alembic revision --autogenerate -m "add_cascade_delete_to_comments"

# ❌ 不好的命名
alembic revision --autogenerate -m "update"
alembic revision --autogenerate -m "修改用户表"  # 不要用中文
alembic revision --autogenerate -m "fix_bug"  # 不够具体
```

---

## 📚 扩展阅读

-   [Alembic 官方文档](https://alembic.sqlalchemy.org/)
-   [SQLAlchemy 迁移最佳实践](https://docs.sqlalchemy.org/en/20/core/migration.html)
-   [PostgreSQL DDL 事务支持](https://www.postgresql.org/docs/current/ddl.html)
-   [[02-Alembic数据库迁移详解]] ⭐️

---

## 🔖 快速参考

```bash
# 创建迁移（自动检测）
PYTHONPATH=. uv run alembic revision --autogenerate -m "description"

# 创建迁移（手动）
PYTHONPATH=. uv run alembic revision -m "description"

# 应用迁移
PYTHONPATH=. uv run alembic upgrade head

# 回滚一步
PYTHONPATH=. uv run alembic downgrade -1

# 生成 SQL（不执行）
PYTHONPATH=. uv run alembic upgrade head --sql

# 查看历史
PYTHONPATH=. uv run alembic history

# 查看当前版本
PYTHONPATH=. uv run alembic current

# 合并迁移分支
PYTHONPATH=. uv run alembic merge heads -m "merge migrations"
```

---

**更新日期：** 2025-10-04
**当前版本：** b9cf7908383e (Initial migration)
