# FastAPI 博客系统

基于 FastAPI 构建的现代博客系统后端，用于学习 FastAPI 和现代 Web 开发技术栈。

## 技术栈

- **框架**: FastAPI (异步Web框架)
- **数据库**: PostgreSQL + SQLAlchemy 2.0+ ORM
- **迁移**: Alembic 数据库迁移工具
- **认证**: python-jose + passlib[bcrypt]
- **服务器**: Uvicorn ASGI 服务器
- **包管理**: uv (现代 Python 包管理器)
- **测试**: pytest + pytest-cov

## 开发环境启动

### 1. 环境准备

确保你的系统已安装：

- Python 3.11+
- uv 包管理器
- Docker (用于 PostgreSQL 和 Redis)

### 2. 启动数据库 和 redis

使用 Docker Compose 启动 PostgreSQL 数据库 和 redis：

```bash
# 启动数据库容器
docker-compose up -d

# 检查容器状态
docker ps

# 查看数据库日志
docker-compose logs postgres
```

数据库配置信息：

- 主机: localhost:5432
- 数据库: blogdb
- 用户名: root
- 密码: Password123@pg

Redis 配置信息：

- 主机: localhost:6379
- 无密码认证（开发环境）

### 3. 安装项目依赖

```bash
# 安装所有依赖
uv sync

# 激活虚拟环境（如果需要）
source .venv/bin/activate  # Linux/macOS
# 或
.venv\Scripts\activate     # Windows
```

### 4. 环境变量配置

项目根目录的 `.env` 文件已包含必要的环境变量配置，无需额外设置。

### 5. 启动开发服务器

```bash
# 启动开发服务器（自动重载）
uv run uvicorn app.main:app --reload

# 在指定主机/端口启动
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000

# 直接运行 Python 脚本
uv run python app/main.py
```

### 6. 访问应用

启动成功后，你可以访问：

- **API 文档**: <http://localhost:8000/docs> (Swagger UI)
- **API 文档**: <http://localhost:8000/redoc> (ReDoc)
- **健康检查**: <http://localhost:8000/health>
- **欢迎页面**: <http://localhost:8000/>

## 开发工具

### 代码质量检查

```bash
# 代码格式化和检查
uv run ruff check app/
uv run ruff format app/
```

### 运行测试

```bash
# 运行所有测试
uv run pytest

# 运行测试并显示覆盖率
uv run pytest --cov=app

# 运行特定标记的测试
uv run pytest -m unit        # 单元测试
uv run pytest -m integration # 集成测试
uv run pytest -m db          # 数据库测试
uv run pytest -m api         # API测试
```

### 数据库迁移

```bash
# 生成迁移文件
uv run alembic revision --autogenerate -m "描述信息"

# 应用迁移
uv run alembic upgrade head

# 查看迁移历史
uv run alembic history
```

## 项目结构

```text
fastapi_blog/
├── app/                    # 主应用目录
│   ├── api/               # API 路由处理器
│   ├── core/              # 核心配置、安全和工具类
│   ├── crud/              # 数据库 CRUD 操作
│   ├── db/                # 数据库连接和会话管理
│   ├── models/            # SQLAlchemy 数据库模型
│   ├── schemas/           # Pydantic 请求/响应验证模式
│   └── main.py            # FastAPI 应用入口点
├── tests/                 # 测试文件
├── docs/                  # 文档
├── docker-compose.yml     # Docker 配置
├── pyproject.toml         # 项目配置和依赖
├── pytest.ini            # 测试配置
├── .env                   # 环境变量
└── README.md              # 项目说明
```

## 常见问题

### 数据库连接问题

如果遇到数据库连接错误：

1. 确认 Docker 容器正在运行：`docker ps`
2. 检查数据库连接配置：`.env` 文件
3. 查看数据库日志：`docker-compose logs postgres`

### 依赖安装问题

如果遇到依赖安装错误：

1. 确认 uv 版本：`uv --version`
2. 清理缓存：`uv cache clean`
3. 重新安装：`uv sync --reinstall`

## 贡献指南

1. Fork 项目
2. 创建功能分支
3. 提交代码前运行测试和代码检查
4. 提交 Pull Request

## 许可证

MIT License
