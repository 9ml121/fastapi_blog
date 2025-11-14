# 数据库 DDL 文档

本目录包含数据库结构的 SQL DDL 语句，用于文档、审查和备份。

---

## 📄 文件说明

### `initial_schema.sql`

**描述：** 初始数据库结构的完整 SQL DDL 语句（由 Alembic 自动生成）

**生成命令：**
```bash
PYTHONPATH=. uv run alembic upgrade head --sql > docs/database/initial_schema.sql
```

**包含内容：**
- 所有表的 CREATE TABLE 语句（7 个表）
- 所有索引的 CREATE INDEX 语句
- 所有枚举类型的 CREATE TYPE 语句（UserRole, PostStatus）
- 所有列的 COMMENT ON 注释（中文描述）
- 外键约束和级联删除策略
- Alembic 版本追踪表

**用途：**
1. **文档参考** - 查看完整的数据库结构
2. **代码审查** - 在 Pull Request 中审查表结构变更
3. **手动部署** - 在不能使用 Alembic 的环境中手动执行
4. **数据库对比** - 使用工具对比实际数据库与预期结构

---

## 🔄 Alembic 迁移 vs SQL DDL

### **Alembic 迁移脚本（推荐）**

**位置：** `alembic/versions/*.py`

**优点：**
- ✅ 版本控制友好（Python 代码）
- ✅ 跨数据库兼容（PostgreSQL/MySQL/SQLite）
- ✅ 支持复杂逻辑（条件判断、数据迁移）
- ✅ 自动追踪版本状态
- ✅ 支持回滚（downgrade）

**使用场景：**
- 开发环境：直接使用 `alembic upgrade head`
- 生产环境：执行前先 `alembic upgrade head --sql` 审查

---

### **SQL DDL 文件（辅助）**

**位置：** `docs/database/*.sql`

**优点：**
- ✅ 可读性强（标准 SQL）
- ✅ 可以用 SQL 工具直接执行
- ✅ 便于非 Python 环境使用

**使用场景：**
- 文档和审查
- 手动部署或回滚
- 数据库结构对比

---

## 📋 常用命令

### 生成当前版本的 SQL DDL

```bash
# 生成从初始状态到最新版本的 SQL
PYTHONPATH=. uv run alembic upgrade head --sql > docs/database/full_migration.sql

# 生成特定版本的 SQL
PYTHONPATH=. uv run alembic upgrade <revision_id> --sql > migration.sql

# 生成回滚 SQL
PYTHONPATH=. uv run alembic downgrade -1 --sql > rollback.sql
```

### 查看数据库当前结构

```bash
# 使用 psql 查看表结构
psql -U root -d blogdb -c "\dt"  # 列出所有表
psql -U root -d blogdb -c "\d users"  # 查看 users 表结构

# 使用 Python 查看
uv run python -c "
from sqlalchemy import inspect, create_engine
from app.core.config import settings
inspector = inspect(create_engine(settings.DATABASE_URL))
print(inspector.get_table_names())
"
```

---

## ⚠️ 注意事项

### **1. SQL 文件不是迁移的唯一源**

- Alembic 迁移脚本才是权威源（`alembic/versions/`）
- SQL 文件仅供参考和审查
- 不要直接修改 SQL 文件来修改数据库

### **2. 生产环境部署流程**

```bash
# 步骤1：生成 SQL 审查
PYTHONPATH=. uv run alembic upgrade head --sql > migration_review.sql

# 步骤2：审查 SQL（检查是否有风险操作）
less migration_review.sql

# 步骤3：备份数据库
pg_dump -U user -d blogdb > backup_$(date +%Y%m%d).sql

# 步骤4：执行迁移
PYTHONPATH=. uv run alembic upgrade head

# 步骤5：验证结果
PYTHONPATH=. uv run alembic current
```

### **3. 何时保存 SQL 文件**

**需要保存：**
- ✅ 重大版本发布前（作为文档）
- ✅ 生产环境部署前（审查和备份）
- ✅ 数据库结构初始化时

**不需要保存：**
- ❌ 每次开发调试的迁移
- ❌ 临时的实验性变更

---

## 🔗 相关文档

- [数据库设计参考](../reference/database-schema.md)
- [数据模型开发规范](database-models.md)
- [Alembic 迁移详解](02-Alembic数据库迁移详解.md)

---

**更新日期：** 2025-10-04
**当前版本：** b9cf7908383e (Initial migration)
