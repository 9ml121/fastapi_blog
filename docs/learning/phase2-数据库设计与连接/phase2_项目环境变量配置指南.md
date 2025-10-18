# Phase 2 - 项目环境变量配置指南

> **目标**：建立安全、灵活的环境变量配置管理系统
> **更新**：2025-10-13 | Phase 5.2 环境配置完善
> **版本**：2025-10-13

---

## 目录大纲

1. [配置重要性](#配置重要性)
2. [环境变量分类](#环境变量分类)
3. [配置加载机制](#配置加载机制)
4. [安全最佳实践](#安全最佳实践)
5. [部署配置](#部署配置)

---

## 配置重要性

### 为什么需要环境变量管理

**目标**：实现配置与代码分离，提高应用的可移植性和安全性
- 开发环境、测试环境、生产环境的配置隔离
- 敏感信息（数据库密码、API密钥）的安全管理
- 容器化部署和云平台兼容性

**技术选型**：采用 Pydantic Settings + python-dotenv
- 支持类型验证和默认值
- 自动从 .env 文件加载，Git 忽略敏感文件
- 提供 IDE 智能提示和配置验证

### 技术实现：Pydantic Settings

```python
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    DATABASE_URL: str = "default_value"  # 提供fallback值

    model_config = {
        "env_file": ".env",           # 指定.env文件
        "env_file_encoding": "utf-8",
        "case_sensitive": False,      # 不区分大小写
        "extra": "ignore"             # 忽略额外字段
    }
```

**核心优势**：
1. **类型安全**：自动类型转换，支持 str、int、bool 等
2. **优先级明确**：环境变量 > .env 文件 > 默认值
3. **IDE 支持**：完整的代码补全和类型检查
4. **测试友好**：易于 mock 配置进行单元测试

---

## 环境变量分类

### 1. 数据库配置

| 变量名                 | 类型  | 默认值                     | 说明     | 使用位置          |
| ------------------- | --- | ----------------------- | ------ | ------------- |
| `DATABASE_URL`      | str | `postgres://.../dbname` | 连接字符串  | `database.py` |
| `DATABASE_HOST`     | str | `localhost`             | 主机地址   | 拆分配置用         |
| `DATABASE_PORT`     | int | `5432`                  | 端口     | 拆分配置用         |
| `DATABASE_USER`     | str | `user`                  | 用户名    | 拆分配置用         |
| `DATABASE_PASSWORD` | str | `change-this-password`  | 密码（敏感） | 拆分配置用         |
| `DATABASE_NAME`     | str | `dbname`                | 数据库名   | 拆分配置用         |

**说明**：
- 优先使用完整的 `DATABASE_URL` 配置
- 拆分配置（HOST、PORT等）便于云平台动态配置
- 云平台通常会自动设置 `DATABASE_URL` 环境变量

**配置示例**：
```env
# 开发环境
DATABASE_URL=postgresql://root:Password123@pg@localhost:5432/blogdb

# 生产环境
DATABASE_URL=postgresql://prod_user:secure_pass@prod-db.example.com:5432/blog_prod
```

### 2. 应用配置

| 变量名 | 类型 | 默认值 | 说明 | 使用位置 |
|--------|------|--------|------|----------|
| `APP_NAME` | `str` | `FastAPI 博客系统` | 应用名称 | API 文档标题 |
| `APP_VERSION` | `str` | `1.0.0` | 应用版本号 | API 版本信息 |
| `DEBUG` | `bool` | `True` | 调试模式开关 | 影响日志级别和SQL调试 |

**说明**：
- `DEBUG=True`：开启详细日志和SQL查询输出
- `DEBUG=False`：生产环境关闭调试信息

**配置示例**：
```env
# 开发环境
APP_NAME=FastAPI 博客系统
APP_VERSION=1.0.0
DEBUG=True

# 生产环境
APP_NAME=FastAPI Blog System
APP_VERSION=1.0.0
DEBUG=False
```

### 3. 安全配置

| 变量名 | 类型 | 默认值 | 说明 | 使用位置 |
|--------|------|--------|------|----------|
| `SECRET_KEY` | `str` | `dev-secret-key-change-in-production` | JWT 签名密钥（敏感） | `app/core/security.py` |
| `ALGORITHM` | `str` | `HS256` | JWT 算法 | `app/core/security.py` |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `int` | `30` | Token 过期时间（分钟） | `app/core/security.py` |

**说明**：
- `SECRET_KEY` 必须**在生产环境中更改为安全的随机字符串**，建议32位以上
- `ALGORITHM` 通常使用 `HS256`，高安全场景可用 `RS256`
- Token 过期时间建议：开发环境30分钟，生产环境60分钟

**生产环境 SECRET_KEY 生成**：
```bash
# 方法1：使用 openssl
openssl rand -hex 32

# 方法2：使用 Python
python -c "import secrets; print(secrets.token_urlsafe(32))"

# 示例输出：
# your-very-secure-secret-key-with-random-chars-32plus
```

**配置示例**：
```env
# 开发环境（仅限本地）
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 生产环境
SECRET_KEY=qL8kN2vR9wX5tY7uZ3aE6bD4cF1gH0jK9mP8oQ7iL6sU5vW4xY3zA2bC1dE0fG9h
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=60
```

### 4. CORS 配置和其他设置

> **注意**：CORS origins 配置在 `app/main.py` 中处理
> **扩展**：Phase 6 可能会添加更多配置项

| 变量名 | 类型 | 默认值 | 说明 |
|--------|------|--------|------|
| `CORS_ORIGINS` | `str` | `http://localhost:3000,http://localhost:5173` | 允许的跨域来源 |

**实现方式**：
```python
# app/core/config.py
class Settings(BaseSettings):
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def get_cors_origins(self) -> list[str]:
        """将字符串转换为列表"""
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",")]

# app/main.py
from app.core.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.get_cors_origins,  # 动态配置
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 配置加载机制

Pydantic Settings 配置加载遵循以下优先级：

```
1. 系统环境变量（最高优先级）
   临时设置，用于部署
2. .env 文件
   项目配置，不提交到Git
3. config.py 默认值（最低优先级）
   代码中的fallback值
```

### 加载示例

首先看默认值：

```python
# config.py
class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:pass@localhost/db"  # 默认值
```

然后 .env 文件覆盖：

```env
# .env 文件
DATABASE_URL=postgresql://dev_user:dev_pass@localhost/dev_db
```

最后环境变量覆盖：

```bash
# 环境变量
export DATABASE_URL=postgresql://prod_user:prod_pass@prod_host/prod_db
```

**结果**：
- 开发环境使用 `.env` 文件配置
- 生产环境通过环境变量覆盖
- 如果都没有，使用 `config.py` 的默认值

### 配置验证技巧

```bash
# 方法1：Python 一行命令
uv run python -c "from app.core.config import settings; print(f'DATABASE_URL: {settings.DATABASE_URL}')"

# 方法2：交互式 Shell
uv run python
>>> from app.core.config import settings
>>> print(settings.DATABASE_URL)
>>> print(settings.SECRET_KEY)
>>> print(settings.DEBUG)
```

---

## 安全最佳实践

### 1. `.env` 文件管理

**文件结构**：
```
.env              # 本地开发环境配置，不提交到Git
.env.example      # 配置模板，提交到Git供参考
.env.test         # 测试环境配置
.env.production   # 生产环境配置模板，不提交到Git
```

**`.gitignore` 配置**：
```gitignore
# 环境变量文件
.env
.env.local
.env.*.local
.env.production

# 保留模板文件
!.env.example
```

**`.env.example` 模板**：
```env
# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# 安全配置（生产环境请更换为安全的SECRET_KEY）
SECRET_KEY=your-secret-key-here
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 应用配置
APP_NAME=FastAPI 博客系统
APP_VERSION=1.0.0
DEBUG=True
```

### 2. 配置验证

使用 Pydantic 的验证器确保配置安全：

```python
from pydantic import field_validator
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str

    @field_validator("SECRET_KEY")
    @classmethod
    def validate_secret_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("SECRET_KEY 必须至少32位字符")
        if v.startswith("dev-") or v.startswith("change-"):
            import os
            if os.getenv("ENVIRONMENT") == "production":
                raise ValueError("生产环境不能使用开发用SECRET_KEY")
        return v
```

### 3. 生产环境配置管理

**开发环境**：
```bash
# 本地 .env 文件
cat .env
DATABASE_URL=postgresql://root:Password123@pg@localhost:5432/blogdb
```

**生产环境**：
```bash
# 方法1：云平台配置管理
# AWS: Systems Manager Parameter Store / Secrets Manager
# Azure: Key Vault
# Vercel/Netlify: Environment Variables 配置界面

# 方法2：容器环境变量
docker run -e DATABASE_URL=xxx -e SECRET_KEY=xxx your-app

# 方法3：Kubernetes Secrets
kubectl create secret generic app-secrets \
  --from-literal=DATABASE_URL=xxx \
  --from-literal=SECRET_KEY=xxx
```

### 4. 环境检测

```python
# app/core/config.py
class Settings(BaseSettings):
    ENVIRONMENT: str = "development"  # development | testing | production

    @property
    def is_production(self) -> bool:
        return self.ENVIRONMENT == "production"

    @property
    def is_development(self) -> bool:
        return self.ENVIRONMENT == "development"

# 使用示例
from app.core.config import settings

if settings.is_production:
    # 生产环境配置
    logger.setLevel(logging.WARNING)
else:
    # 开发环境配置
    logger.setLevel(logging.DEBUG)
```

---

## 部署配置

### 本地开发

```bash
# 1. 复制配置模板
cp .env.example .env

# 2. 编辑 .env 文件配置
nano .env

# 3. 启动开发服务器
uv run uvicorn app.main:app --reload
```

### Docker 部署

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

# 安装依赖
RUN pip install uv
RUN uv sync --no-dev

# 启动应用（注意：Docker中通常通过环境变量传递配置）
CMD ["uv", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

```bash
# 运行容器时传递环境变量
docker run -d \
  -e DATABASE_URL=postgresql://user:pass@host/db \
  -e SECRET_KEY=your-secret-key \
  -e DEBUG=False \
  -p 8000:8000 \
  your-app-image
```

### 云平台部署

**Vercel / Railway / Render**：
1. 在平台设置 Environment Variables 配置
2. 主要配置项：
   - `DATABASE_URL` = `postgresql://...`
   - `SECRET_KEY` = `your-secret-key`
   - `DEBUG` = `False`

**Heroku**：
```bash
heroku config:set DATABASE_URL=postgresql://...
heroku config:set SECRET_KEY=your-secret-key
heroku config:set DEBUG=False
```

**AWS / Azure / GCP**：
使用各平台的 Secrets Manager 或 Key Vault 服务

---

## 完整配置代码示例

### `app/core/config.py` 完整实现

```python
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    应用配置类
    使用 Pydantic Settings 进行类型验证和环境变量管理
    """

    # 数据库配置 - 建议优先使用 DATABASE_URL，其他字段用于拆分配置
    DATABASE_URL: str = "postgresql://user:password@localhost:5432/dbname"
    DATABASE_HOST: str = "localhost"
    DATABASE_PORT: int = 5432
    DATABASE_USER: str = "user"
    DATABASE_PASSWORD: str = "change-this-password"
    DATABASE_NAME: str = "dbname"

    # 应用配置
    APP_NAME: str = "FastAPI 博客系统"
    APP_VERSION: str = "1.0.0"
    DEBUG: bool = True

    # 安全配置 - 生产环境必须更改为安全的密钥
    SECRET_KEY: str = "dev-secret-key-change-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = {
        "env_file": ".env",
        "env_file_encoding": "utf-8",
        "case_sensitive": False,
    }


# 全局配置实例
settings = Settings()


def get_settings() -> Settings:
    """
    获取配置单例
    便于依赖注入和测试时替换配置
    """
    return settings
```

### `.env.example` 模板文件（提交到Git）

```env
# ============================================
# FastAPI 博客系统 - 配置模板
# 使用方法：复制为 .env 文件并填写实际配置
# ============================================

# 数据库配置
DATABASE_URL=postgresql://user:password@localhost:5432/dbname

# 安全配置（生产环境请更换为安全的SECRET_KEY）
SECRET_KEY=dev-secret-key-change-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# 应用配置
APP_NAME=FastAPI 博客系统
APP_VERSION=1.0.0
DEBUG=True
```

### `.env` 本地开发文件（不提交到Git）

```env
# 数据库配置
DATABASE_URL=postgresql://root:Password123@pg@localhost:5432/blogdb
DATABASE_HOST=localhost
DATABASE_PORT=5432
DATABASE_USER=root
DATABASE_PASSWORD=Password123@pg
DATABASE_NAME=blogdb

# 安全配置
SECRET_KEY=your-secret-key-change-this-in-production
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

---

## 相关参考资料

- [Pydantic Settings 官方文档](https://docs.pydantic.dev/latest/concepts/pydantic_settings/)
- [12-Factor App: Config](https://12factor.net/config)
- [FastAPI 环境变量配置](https://fastapi.tiangolo.com/advanced/settings/)

---

## 版本历史

| 日期 | 版本 | 更新内容 | 作者 |
|------|------|----------|--------|
| 2025-10-13 | v1.0 | 初始完成 Phase 2-5 环境变量配置 | Claude |
| - | - | 待补充CORS_ORIGINS 完整配置 | - |