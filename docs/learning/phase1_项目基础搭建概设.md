
## 后端项目搭建
```bash
# 创建项目目录
mkdir fastapi_blog
cd fastapi_blog

# 使用 uv 初始化项目
uv init --python 3.11

# 添加核心依赖
uv add fastapi uvicorn python-multipart

# 添加数据库相关依赖
uv add sqlalchemy psycopg2-binary alembic

# 添加认证和工具依赖
uv add "python-jose[cryptography]" "passlib[bcrypt]" python-dotenv

# 创建基本目录结构
mkdir app
mkdir app/api
mkdir app/core
mkdir app/models
mkdir app/schemas
mkdir app/crud
mkdir app/db

# 创建配置文件
touch .env
```

###  技术栈配置
```plaintext
 技术栈配置：
  - 框架: FastAPI (>=0.117.1)
  - 数据库: PostgreSQL (psycopg2-binary)
  - ORM: SQLAlchemy (>=2.0.43)
  - 数据库迁移: Alembic (>=1.16.5)
  - 服务器: Uvicorn (>=0.37.0)
  - 认证: python-jose + passlib[bcrypt]
  - 文件上传: python-multipart
  - 环境变量: python-dotenv
```


### 项目结构
```plaintext
项目结构：
  fastapi_blog/
  ├── app/                    # 主应用目录
  │   ├── api/               # API路由 (空)
  │   ├── core/              # 核心配置 (空)
  │   ├── crud/              # CRUD操作 (空)
  │   ├── db/                # 数据库配置 (空)
  │   ├── models/            # SQLAlchemy模型 (空)
  │   └── schemas/           # Pydantic模式 (空)
  ├── main.py                # 入口文件 (仅包含hello函数)
  ├── pyproject.toml         # 项目配置和依赖
  ├── uv.lock               # 依赖锁定文件
  ├── .gitignore            # Git忽略文件
  ├── .python-version       # Python版本
  └── README.md             # 项目说明 (空)

```


## 后端程序入口
`touch app/main.py`
```python
from fastapi import FastAPI

app = FastAPI(
    title="个人博客系统 API",
    description="基于 FastAPI 构建的博客系统后端",
    version="1.0.0"
)

@app.get("/")
async def root():
    return {"message": "欢迎访问博客系统 API"}

@app.get("/health")
async def health_check():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

# 也可以直接使用 uv 运行：
# uv run uvicorn app.main:app --reload
```