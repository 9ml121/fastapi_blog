# Phase 5 - CORS 跨域资源共享

> **文档用途**：CORS 跨域资源共享的理论与实践
> **创建时间**：2025-10-11
> **更新策略**：根据项目实际需求更新配置

---

## 📚 目录

1. [CORS 理论基础](#1-cors-理论基础)
2. [CORS 配置实践](#2-cors-配置实践)
3. [安全考虑](#3-安全考虑)
4. [环境配置](#4-环境配置)
5. [故障排查](#5-故障排查)

---

## 1. CORS 理论基础

### 1.1 什么是 CORS？

**CORS（Cross-Origin Resource Sharing，跨域资源共享）** 是浏览器的安全机制。

#### 同源策略（Same-Origin Policy）

浏览器默认禁止跨域请求，**同源**的定义：

| 组成部分         | 说明          | 示例                                      |
| ---------------- | ------------- | ----------------------------------------- |
| 协议（Protocol） | http vs https | `http://` 和 `https://` 不同源            |
| 域名（Domain）   | 完整域名      | `example.com` 和 `api.example.com` 不同源 |
| 端口（Port）     | 端口号        | `:3000` 和 `:8000` 不同源                 |

**判断示例**：

```javascript
// 前端运行在：http://localhost:3000

// ❌ 跨域（端口不同）
fetch("http://localhost:8000/api/users");

// ❌ 跨域（域名不同）
fetch("http://127.0.0.1:3000/api/users");

// ✅ 同源
fetch("http://localhost:3000/api/users");
```

#### 为什么需要同源策略？

**防止恶意网站窃取用户数据**：

```javascript
// 场景：用户登录了 https://yourbank.com
// 浏览器存储了银行网站的 Cookie（包含 session_id）

// 用户访问恶意网站 https://evil.com
// 恶意网站的 JavaScript 代码：
fetch("https://yourbank.com/api/transfer", {
    method: "POST",
    credentials: "include", // 自动带上银行的 Cookie！
    body: JSON.stringify({
        to: "hacker-account",
        amount: 1000000,
    }),
});

// 如果没有同源策略：
// → 请求会成功，钱被转走
// → 用户只是访问了 evil.com，什么都没做

// 有了同源策略：
// → 浏览器拦截请求：CORS policy blocked
// → 恶意网站无法发起请求
```

### 1.2 CORS 工作原理

#### 简单请求（GET、POST，不带自定义头）

```http
# 1. 浏览器发送请求，自动添加 Origin 头
GET /api/users HTTP/1.1
Host: localhost:8000
Origin: http://localhost:3000

# 2. 服务器检查 Origin，决定是否允许
HTTP/1.1 200 OK
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Credentials: true

# 3. 浏览器检查响应头：
#    - 如果有 Access-Control-Allow-Origin → 允许
#    - 如果没有 → 拦截并报错
```

#### 预检请求（PUT、DELETE、带 Authorization 头）

```http
# 1. 浏览器先发送 OPTIONS 预检请求
OPTIONS /api/users/me HTTP/1.1
Origin: http://localhost:3000
Access-Control-Request-Method: PATCH
Access-Control-Request-Headers: Authorization

# 2. 服务器返回允许的方法和头
HTTP/1.1 204 No Content
Access-Control-Allow-Origin: http://localhost:3000
Access-Control-Allow-Methods: GET, POST, PATCH, DELETE
Access-Control-Allow-Headers: Authorization, Content-Type
Access-Control-Max-Age: 86400

# 3. 浏览器检查通过后，才发送真正的请求
PATCH /api/users/me HTTP/1.1
Authorization: Bearer <token>
```

---

## 2. CORS 配置实践

### 2.1 FastAPI CORS 配置

#### 基础配置

```python
# app/main.py

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI()

# CORS 配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",      # 本地开发：React/Vue
        "http://localhost:5173",      # 本地开发：Vite
        "https://yourdomain.com",     # 生产环境域名
        "https://www.yourdomain.com", # 生产环境带 www
    ],
    allow_credentials=True,           # 允许携带 Cookie/Token
    allow_methods=["*"],              # 允许所有 HTTP 方法
    allow_headers=["*"],              # 允许所有请求头
)
```

#### 配置参数详解

| 参数                | 说明                                      | 推荐值                                                 | ⚠️ 安全注意                                 |
| ------------------- | ----------------------------------------- | ------------------------------------------------------ | ------------------------------------------- |
| `allow_origins`     | 允许的前端域名列表                        | 明确列举域名                                           | **生产环境禁止用 `["*"]`！**                |
| `allow_credentials` | 是否允许携带凭据（Cookie、Authorization） | `True`                                                 | 如果为 True，`allow_origins` 不能是 `["*"]` |
| `allow_methods`     | 允许的 HTTP 方法                          | `["*"]` 或 `["GET", "POST", "PUT", "DELETE", "PATCH"]` | 一般允许全部即可                            |
| `allow_headers`     | 允许的请求头                              | `["*"]` 或 `["Authorization", "Content-Type"]`         | 建议允许全部                                |
| `max_age`           | 预检请求缓存时间（秒）                    | `600`（10 分钟）                                       | 可选，减少预检请求次数                      |

### 2.2 环境配置最佳实践

#### 使用环境变量

```python
# app/core/config.py

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # CORS 配置
    CORS_ORIGINS: list[str] = ["http://localhost:3000"]  # 默认开发环境

    class Config:
        env_file = ".env"

settings = Settings()

# app/main.py

from app.core.config import settings

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,  # 从环境变量读取
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### 环境配置文件

```bash
# 开发环境 .env.development
CORS_ORIGINS=["http://localhost:3000","http://localhost:5173"]

# 生产环境 .env.production
CORS_ORIGINS=["https://yourdomain.com","https://www.yourdomain.com"]
```

### 2.3 动态 CORS 配置

#### 基于环境的动态配置

```python
# app/core/config.py

class Settings(BaseSettings):
    ENVIRONMENT: str = "development"
    CORS_ORIGINS_DEV: list[str] = [
        "http://localhost:3000",
        "http://localhost:5173",
        "http://127.0.0.1:3000",
    ]
    CORS_ORIGINS_PROD: list[str] = [
        "https://yourdomain.com",
        "https://www.yourdomain.com",
    ]

    @property
    def cors_origins(self) -> list[str]:
        """根据环境返回对应的 CORS 配置"""
        if self.ENVIRONMENT == "production":
            return self.CORS_ORIGINS_PROD
        return self.CORS_ORIGINS_DEV

# app/main.py

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

---

## 3. 安全考虑

### 3.1 安全风险警告

#### ❌ 危险配置（生产环境绝对禁止）

```python
# ❌ 危险配置（生产环境绝对禁止）
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],              # 允许任何网站访问！
    allow_credentials=True,           # 还允许携带凭据！
    allow_methods=["*"],
    allow_headers=["*"],
)

# 风险：
# → 任何恶意网站都能调用你的 API
# → 可能导致 CSRF 攻击
# → 用户数据泄露
```

#### ✅ 安全配置

```python
# ✅ 安全配置
allow_origins=[
    "https://yourdomain.com",      # 只允许自己的域名
    "https://www.yourdomain.com",  # 支持带 www 的域名
]
```

### 3.2 生产环境安全策略

#### 严格域名控制

```python
# 生产环境：只允许特定域名
CORS_ORIGINS_PROD = [
    "https://yourdomain.com",
    "https://www.yourdomain.com",
    "https://admin.yourdomain.com",  # 管理后台
]

# 开发环境：允许本地开发
CORS_ORIGINS_DEV = [
    "http://localhost:3000",
    "http://localhost:5173",
    "http://127.0.0.1:3000",
]
```

#### 凭据安全

```python
# 如果不需要携带凭据，可以设为 False
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=False,  # 不允许携带凭据
    allow_methods=["GET", "POST"],  # 只允许特定方法
    allow_headers=["Content-Type"],  # 只允许特定头
)
```

---

## 4. 环境配置

### 4.1 开发环境配置

#### 本地开发配置

```python
# 开发环境：宽松配置，便于调试
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",    # React 默认端口
        "http://localhost:5173",    # Vite 默认端口
        "http://localhost:8080",    # Vue CLI 默认端口
        "http://127.0.0.1:3000",   # 支持 IP 访问
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

#### Docker 开发环境

```python
# Docker 环境：可能需要额外的配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",
        "http://host.docker.internal:3000",  # Docker 内部访问
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
```

### 4.2 生产环境配置

#### 生产环境最佳实践

```python
# 生产环境：严格配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "https://yourdomain.com",
        "https://www.yourdomain.com",
    ],
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE"],
    allow_headers=[
        "Authorization",
        "Content-Type",
        "Accept",
        "Origin",
        "User-Agent",
    ],
    max_age=600,  # 预检请求缓存 10 分钟
)
```

---

## 5. 故障排查

### 5.1 常见 CORS 错误

#### 错误 1：Access-Control-Allow-Origin 缺失

```javascript
// 前端错误
Access to fetch at 'http://localhost:8000/api/users' from origin 'http://localhost:3000'
has been blocked by CORS policy: No 'Access-Control-Allow-Origin' header is present on the requested resource.

// 解决方案：检查服务器 CORS 配置
```

#### 错误 2：预检请求失败

```javascript
// 前端错误
Access to fetch at 'http://localhost:8000/api/users/me' from origin 'http://localhost:3000'
has been blocked by CORS policy: Response to preflight request doesn't pass access control check:
It does not have HTTP ok status.

// 解决方案：确保 OPTIONS 请求返回 200/204
```

#### 错误 3：凭据被拒绝

```javascript
// 前端错误
Access to fetch at 'http://localhost:8000/api/users/me' from origin 'http://localhost:3000'
has been blocked by CORS policy: The value of the 'Access-Control-Allow-Credentials' header
in the response is '' which must be 'true' when the request's credentials mode is 'include'.

// 解决方案：设置 allow_credentials=True
```

### 5.2 调试技巧

#### 检查 CORS 响应头

```bash
# 使用 curl 检查 CORS 响应头
curl -H "Origin: http://localhost:3000" \
     -H "Access-Control-Request-Method: GET" \
     -H "Access-Control-Request-Headers: Authorization" \
     -X OPTIONS \
     http://localhost:8000/api/users/me

# 期望的响应头：
# Access-Control-Allow-Origin: http://localhost:3000
# Access-Control-Allow-Methods: GET, POST, PUT, DELETE, PATCH
# Access-Control-Allow-Headers: Authorization, Content-Type
# Access-Control-Allow-Credentials: true
```

#### 浏览器开发者工具

```javascript
// 在浏览器控制台检查 CORS 错误
fetch("http://localhost:8000/api/users", {
    method: "GET",
    credentials: "include",
    headers: {
        Authorization: "Bearer your-token",
    },
})
    .then((response) => response.json())
    .catch((error) => console.error("CORS Error:", error));
```

### 5.3 测试 CORS 配置

#### 自动化测试

```python
# tests/test_cors.py

import pytest
from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)

def test_cors_headers():
    """测试 CORS 响应头"""
    response = client.options(
        "/api/users/me",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "Authorization",
        }
    )

    assert response.status_code == 200
    assert "Access-Control-Allow-Origin" in response.headers
    assert response.headers["Access-Control-Allow-Origin"] == "http://localhost:3000"
    assert "Access-Control-Allow-Methods" in response.headers
    assert "Access-Control-Allow-Headers" in response.headers

def test_cors_preflight():
    """测试预检请求"""
    response = client.options(
        "/api/users/me",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "PATCH",
            "Access-Control-Request-Headers": "Authorization,Content-Type",
        }
    )

    assert response.status_code == 200
    assert "Authorization" in response.headers["Access-Control-Allow-Headers"]
    assert "Content-Type" in response.headers["Access-Control-Allow-Headers"]
```

---

## 6. 最佳实践总结

### 6.1 配置原则

1. **最小权限原则**：只允许必要的域名、方法、头
2. **环境隔离**：开发和生产环境使用不同配置
3. **安全优先**：生产环境禁止使用 `["*"]`
4. **凭据控制**：只在必要时允许携带凭据

### 6.2 实施建议

1. **开发阶段**：使用宽松配置，便于调试
2. **测试阶段**：模拟生产环境配置
3. **生产阶段**：严格限制，只允许必要域名
4. **监控阶段**：记录 CORS 错误，及时调整

### 6.3 常见陷阱

1. **忘记设置 `allow_credentials=True`**：导致无法携带认证信息
2. **生产环境使用 `["*"]`**：安全风险极高
3. **忽略预检请求**：复杂请求被拦截
4. **域名配置错误**：前端无法访问 API

---

## 参考资源

-   [MDN CORS 文档](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS)
-   [FastAPI CORS 中间件](https://fastapi.tiangolo.com/tutorial/cors/)
-   [CORS 安全最佳实践](https://web.dev/cross-origin-resource-sharing/)
