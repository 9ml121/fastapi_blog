# JWT 认证机制详解

> 本文档详细讲解 JWT（JSON Web Token）的工作原理、使用场景、安全机制和最佳实践，帮助你深入理解现代 Web 应用的认证体系。

## 目录

- [1. 为什么需要认证？](#1-为什么需要认证)
- [2. 认证方案对比](#2-认证方案对比)
- [3. JWT 深度剖析](#3-jwt-深度剖析)
- [4. JWT 工作流程](#4-jwt-工作流程)
- [5. JWT 安全机制](#5-jwt-安全机制)
- [6. 实践问题与方案](#6-实践问题与方案)
- [7. 最佳实践清单](#7-最佳实践清单)

---

## 1. 为什么需要认证？

### 1.1 HTTP 的无状态特性

**问题场景**：

```
用户 A 第一次访问：
GET /api/posts  → 服务器返回文章列表

用户 A 第二次访问：
GET /api/posts  → 服务器不知道这是同一个用户！
```

**HTTP 协议的特点**：

- ❌ **无状态**：每次请求都是独立的，服务器不记得上次是谁访问的
- ❌ **无记忆**：不知道用户是否登录过
- ❌ **不安全**：任何人都可以访问公开接口

**需要解决的问题**：

1. 如何识别用户身份？（Authentication - 认证）
2. 如何记住用户登录状态？（Session Management - 会话管理）
3. 如何保护敏感数据？（Authorization - 授权）

### 1.2 认证的本质

**认证（Authentication）的核心问题**：

```
问题：服务器如何知道"这个请求来自张三"？

解决方案：给用户一个"身份凭证"
- 用户登录时：验证身份 → 颁发凭证
- 后续请求时：携带凭证 → 服务器验证 → 识别身份
```

**类比现实世界**：

| 场景 | 身份验证 | 凭证 | 后续使用 |
|------|---------|------|----------|
| **进入小区** | 门卫验证身份证 | 发放门禁卡 | 刷卡进入 |
| **登机** | 验证身份证+机票 | 发放登机牌 | 凭登机牌登机 |
| **Web 认证** | 验证用户名+密码 | 发放 Token | 携带 Token 访问 |

---

## 2. 认证方案对比

### 2.1 方案一：Session-Cookie 认证（传统方案）

**工作流程**：

```
1. 登录验证
   用户 → POST /login (username + password) → 服务器

2. 创建会话
   服务器验证成功 → 创建 Session → 存储到服务器内存/数据库
   Session: {
     session_id: "abc123",
     user_id: 100,
     username: "zhangsan",
     expire_at: "2025-10-06 10:00:00"
   }

3. 返回凭证
   服务器 → Set-Cookie: session_id=abc123 → 浏览器保存 Cookie

4. 后续请求
   浏览器 → GET /api/posts (自动携带 Cookie: session_id=abc123) → 服务器
   服务器 → 查询 Session 存储 → 找到用户信息 → 返回数据
```

**优点**：

- ✅ 服务器完全控制（可随时撤销 session）
- ✅ 安全性好（session 数据在服务器端）
- ✅ 浏览器自动处理 Cookie

**缺点**：

- ❌ **服务器有状态**：需要存储 session（内存/Redis/数据库）
- ❌ **扩展性差**：多服务器需要共享 session（粘性会话/集中式存储）
- ❌ **跨域问题**：Cookie 不支持跨域
- ❌ **移动端不友好**：原生 APP 不支持 Cookie

### 2.2 方案二：JWT Token 认证（现代方案）

**工作流程**：

```
1. 登录验证
   用户 → POST /login (username + password) → 服务器

2. 生成 Token
   服务器验证成功 → 生成 JWT Token → 不需要存储！
   JWT = Header.Payload.Signature

   示例 Token:
   eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.
   eyJ1c2VyX2lkIjoxMDAsInVzZXJuYW1lIjoiemhhbmdzYW4iLCJleHAiOjE3Mjg5ODk2MDB9.
   SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c

3. 返回 Token
   服务器 → { "access_token": "eyJhbG..." } → 客户端保存（localStorage）

4. 后续请求
   客户端 → GET /api/posts (Header: Authorization: Bearer eyJhbG...) → 服务器
   服务器 → 验证签名 → 解码 Payload → 获取用户信息 → 返回数据
```

**优点**：

- ✅ **无状态**：服务器不需要存储 session
- ✅ **可扩展**：多服务器无需共享状态
- ✅ **跨域友好**：通过 HTTP Header 传递
- ✅ **移动端友好**：原生 APP 也可以使用
- ✅ **自包含**：Token 包含所有用户信息

**缺点**：

- ❌ **无法主动撤销**：Token 在有效期内始终有效
- ❌ **Token 较大**：比 session_id 占用更多带宽
- ❌ **安全依赖密钥**：密钥泄露所有 Token 失效

### 2.3 方案对比总结

| 特性 | Session-Cookie | JWT Token |
|------|---------------|-----------|
| **服务器状态** | 有状态（需存储） | 无状态（不存储） |
| **扩展性** | 差（需共享 session） | 好（无需共享） |
| **跨域支持** | 差（Cookie 限制） | 好（HTTP Header） |
| **移动端** | 不友好 | 友好 |
| **撤销能力** | 容易（删除 session） | 困难（需黑名单） |
| **性能** | 查询存储有开销 | 验证签名较快 |
| **安全性** | 高（数据在服务器） | 中（依赖密钥安全） |

**选择建议**：

- **传统 Web 应用**：Session-Cookie（单体应用、强管理需求）
- **现代 Web/移动应用**：JWT Token（微服务、跨域、APP）
- **混合方案**：短期 JWT + 长期 Refresh Token

---

## 3. JWT 深度剖析

### 3.1 JWT 结构详解

**完整的 JWT Token**：

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMDAsInVzZXJuYW1lIjoiemhhbmdzYW4iLCJleHAiOjE3Mjg5ODk2MDB9.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

**由三部分组成（用 `.` 分隔）**：

```
Header.Payload.Signature
```

---

#### **Part 1: Header（头部）**

```json
{
  "alg": "HS256",  // 签名算法（HMAC SHA256）
  "typ": "JWT"     // Token 类型
}
```

**Base64 编码后**：

```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9
```

**作用**：

- 声明 Token 类型（JWT）
- 声明签名算法（用于验证）

---

#### **Part 2: Payload（载荷/声明）**

```json
{
  "user_id": 100,               // 自定义字段：用户 ID
  "username": "zhangsan",       // 自定义字段：用户名
  "role": "admin",              // 自定义字段：角色
  "exp": 1728989600,            // 标准字段：过期时间（Unix 时间戳）
  "iat": 1728986000,            // 标准字段：签发时间
  "nbf": 1728986000             // 标准字段：生效时间
}
```

**Base64 编码后**：

```
eyJ1c2VyX2lkIjoxMDAsInVzZXJuYW1lIjoiemhhbmdzYW4iLCJleHAiOjE3Mjg5ODk2MDB9
```

**标准字段（Registered Claims）**：

| 字段    | 全称              | 含义              | 示例                |
| ----- | --------------- | --------------- | ----------------- |
| `iss` | Issuer          | 签发者             | "my-app"          |
| `sub` | Subject         | 主题（通常是 user_id） | "user_100"        |
| `aud` | Audience        | 接收者             | "api.example.com" |
| `exp` | Expiration Time | 过期时间            | 1728989600        |
| `nbf` | Not Before      | 生效时间            | 1728986000        |
| `iat` | Issued At       | 签发时间            | 1728986000        |
| `jti` | JWT ID          | Token 唯一标识      | "uuid-xxx"        |

**自定义字段（Private Claims）**：

- 可以添加任何业务数据（user_id、username、role 等）
- ⚠️ **注意**：Payload 是 Base64 编码，**不是加密**，任何人都可以解码查看！

---

#### **Part 3: Signature（签名）**

**生成过程**：

```javascript
// 1. 组合 Header 和 Payload（Base64 编码后）
const data = base64(header) + "." + base64(payload)

// 2. 使用密钥和算法生成签名
const signature = HMACSHA256(data, secret_key)

// 3. Base64 编码签名
const encodedSignature = base64(signature)
```

**示例**：

```python
import hmac
import hashlib
import base64

# 数据
data = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMDAsImV4cCI6MTcyODk4OTYwMH0"

# 密钥（保存在服务器环境变量中）
secret_key = "my-super-secret-key-keep-it-safe"

# 生成签名
signature = hmac.new(
    secret_key.encode(),
    data.encode(),
    hashlib.sha256
).digest()

# Base64 编码
encoded_signature = base64.urlsafe_b64encode(signature).decode()
print(encoded_signature)  # SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

**签名的作用**：

- ✅ **防篡改**：任何人修改 Header 或 Payload，签名就会失效
- ✅ **验证来源**：只有知道密钥的服务器才能生成有效签名
- ✅ **完整性**：确保 Token 没有被修改

---

### 3.2 JWT 验证流程

**服务器如何验证 Token**：

```python
def verify_jwt(token: str, secret_key: str) -> dict | None:
    """验证 JWT Token"""

    # 1. 分割 Token
    parts = token.split(".")
    if len(parts) != 3:
        return None

    header_b64, payload_b64, signature_b64 = parts

    # 2. 重新计算签名
    data = f"{header_b64}.{payload_b64}"
    expected_signature = hmac_sha256(data, secret_key)

    # 3. 比对签名
    if signature_b64 != expected_signature:
        return None  # 签名不匹配，Token 被篡改

    # 4. 解码 Payload
    payload = base64_decode(payload_b64)

    # 5. 检查过期时间
    if payload["exp"] < current_timestamp():
        return None  # Token 已过期

    # 6. 返回用户信息
    return payload
```

**验证步骤**：

1. ✅ **格式检查**：是否是 `Header.Payload.Signature` 格式
2. ✅ **签名验证**：重新计算签名并比对（防篡改）
3. ✅ **过期检查**：检查 `exp` 字段
4. ✅ **解码数据**：Base64 解码获取用户信息

---

## 4. JWT 工作流程

### 4.1 完整认证流程图

```
┌─────────────────────────────────────────────────────────────┐
│ 1. 用户登录                                                  │
└─────────────────────────────────────────────────────────────┘
    客户端                              服务器
       │                                   │
       │  POST /api/auth/login             │
       │  { "email": "...",                │
       │    "password": "..." }            │
       │──────────────────────────────────>│
       │                                   │
       │                                   ├─ 1. 验证用户名密码
       │                                   │  (查询数据库 + bcrypt 验证)
       │                                   │
       │                                   ├─ 2. 生成 JWT Token
       │                                   │  payload = {
       │                                   │    "user_id": 100,
       │                                   │    "username": "zhangsan",
       │                                   │    "exp": now + 1 hour
       │                                   │  }
       │                                   │  token = jwt.encode(payload, SECRET_KEY)
       │                                   │
       │  { "access_token": "eyJhbG..." }  │
       │<──────────────────────────────────│
       │                                   │
       ├─ 3. 保存 Token                   │
       │  localStorage.setItem(             │
       │    "token", "eyJhbG..."           │
       │  )                                │
       │                                   │

┌─────────────────────────────────────────────────────────────┐
│ 2. 访问受保护资源                                            │
└─────────────────────────────────────────────────────────────┘
    客户端                              服务器
       │                                   │
       │  GET /api/posts                   │
       │  Header:                          │
       │  Authorization: Bearer eyJhbG...  │
       │──────────────────────────────────>│
       │                                   │
       │                                   ├─ 1. 提取 Token
       │                                   │  token = request.headers["Authorization"]
       │                                   │         .replace("Bearer ", "")
       │                                   │
       │                                   ├─ 2. 验证签名
       │                                   │  payload = jwt.decode(token, SECRET_KEY)
       │                                   │
       │                                   ├─ 3. 检查过期
       │                                   │  if payload["exp"] < now:
       │                                   │    raise TokenExpired
       │                                   │
       │                                   ├─ 4. 获取用户信息
       │                                   │  user_id = payload["user_id"]
       │                                   │  user = db.get_user(user_id)
       │                                   │
       │                                   ├─ 5. 执行业务逻辑
       │                                   │  posts = get_user_posts(user_id)
       │                                   │
       │  { "posts": [...] }               │
       │<──────────────────────────────────│
       │                                   │

┌─────────────────────────────────────────────────────────────┐
│ 3. Token 过期处理                                            │
└─────────────────────────────────────────────────────────────┘
    客户端                              服务器
       │                                   │
       │  GET /api/posts                   │
       │  Authorization: Bearer expired... │
       │──────────────────────────────────>│
       │                                   │
       │                                   ├─ 检查过期时间
       │                                   │  if exp < now:
       │                                   │
       │  { "error": "Token expired" }     │
       │<──────────────────────────────────│
       │                                   │
       ├─ 处理过期                         │
       │  1. 删除本地 Token                │
       │  2. 跳转登录页                    │
       │                                   │
```

### 4.2 FastAPI 中的 JWT 依赖注入

**典型实现**：

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from jose import jwt, JWTError

# 1. 配置 Bearer Token 提取器
security = HTTPBearer()

# 2. 依赖函数：提取并验证 Token
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security)
) -> User:
    """从 Token 中获取当前用户"""

    # 提取 Token
    token = credentials.credentials

    try:
        # 解码并验证
        payload = jwt.decode(token, SECRET_KEY, algorithms=["HS256"])

        # 提取用户 ID
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")

        # 查询用户
        user = await get_user_by_id(user_id)
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")

        return user

    except JWTError:
        raise HTTPException(status_code=401, detail="Invalid token")

# 3. 在路由中使用
@app.get("/api/posts")
async def get_posts(current_user: User = Depends(get_current_user)):
    """获取当前用户的文章（需要登录）"""
    return {"posts": current_user.posts}
```

---

## 5. JWT 安全机制

### 5.1 常见安全威胁

#### **威胁 1：Token 泄露**

**场景**：

- XSS 攻击：恶意脚本窃取 localStorage 中的 Token
- 中间人攻击：HTTP 传输被截获
- 日志泄露：Token 被记录到日志文件

**防护措施**：

```javascript
// ❌ 错误：存储在 localStorage（易受 XSS 攻击）
localStorage.setItem("token", token)

// ✅ 正确：使用 HttpOnly Cookie（无法被 JS 访问）
document.cookie = `token=${token}; HttpOnly; Secure; SameSite=Strict`

// ✅ 正确：使用 HTTPS 传输（防中间人攻击）
// ✅ 正确：短过期时间（降低泄露影响）
// ✅ 正确：敏感操作二次验证（如修改密码）
```

#### **威胁 2：Token 篡改**

**场景**：

- 攻击者尝试修改 Payload 提升权限
- 修改过期时间延长有效期

**示例攻击**：

```javascript
// 原始 Token Payload
{
  "user_id": 100,
  "role": "user",      // 普通用户
  "exp": 1728989600
}

// 攻击者尝试篡改
{
  "user_id": 100,
  "role": "admin",     // 改成管理员！
  "exp": 1728989600
}
```

**防护措施**：

- ✅ **签名验证**：任何修改都会导致签名失效
- ✅ **密钥保密**：SECRET_KEY 绝对不能泄露
- ✅ **算法固定**：防止 `alg: "none"` 攻击

#### **威胁 3：重放攻击**

**场景**：

- 攻击者截获有效 Token
- 在过期前重复使用

**防护措施**：

```python
# ✅ 方案1：添加 jti（JWT ID）+ 黑名单
payload = {
    "user_id": 100,
    "jti": "uuid-xxx",  # 唯一 ID
    "exp": now + 3600
}

# 用户注销时，将 jti 加入黑名单
redis.set(f"blacklist:{jti}", "1", ex=3600)

# 验证时检查黑名单
if redis.exists(f"blacklist:{jti}"):
    raise HTTPException(401, "Token revoked")

# ✅ 方案2：短过期 + Refresh Token
access_token_expire = 15 分钟  # 短期
refresh_token_expire = 7 天    # 长期
```

### 5.2 密钥安全

**密钥强度要求**：

```python
# ❌ 弱密钥（容易被暴力破解）
SECRET_KEY = "123456"
SECRET_KEY = "my-app-secret"

# ✅ 强密钥（随机生成，足够长）
import secrets
SECRET_KEY = secrets.token_urlsafe(32)
# 输出：'KpNsD6h_8Yf2Tq3Jw9Lx5Rm7Vz4Bn1Ac6Fg8Hk0Mn2'
```

**密钥管理**：

```bash
# ✅ 使用环境变量（不要硬编码）
# .env 文件
SECRET_KEY=KpNsD6h_8Yf2Tq3Jw9Lx5Rm7Vz4Bn1Ac6Fg8Hk0Mn2
ALGORITHM=HS256
ACCESS_TOKEN_EXPIRE_MINUTES=30

# Python 代码
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str
    ALGORITHM: str = "HS256"

    class Config:
        env_file = ".env"

settings = Settings()  # 从环境变量加载
```

**密钥轮换**：

```python
# ✅ 支持多密钥验证（密钥轮换）
CURRENT_SECRET_KEY = "new-key"
OLD_SECRET_KEYS = ["old-key-1", "old-key-2"]

def verify_token(token):
    # 先用当前密钥验证
    try:
        return jwt.decode(token, CURRENT_SECRET_KEY)
    except JWTError:
        pass

    # 再用旧密钥验证（兼容性）
    for old_key in OLD_SECRET_KEYS:
        try:
            payload = jwt.decode(token, old_key)
            # 验证成功，但建议用户重新登录获取新 Token
            payload["_needs_refresh"] = True
            return payload
        except JWTError:
            continue

    raise HTTPException(401, "Invalid token")
```

---

## 6. 实践问题与方案

### 6.1 问题：如何撤销 Token？

**挑战**：JWT 是无状态的，服务器不存储 Token，无法主动撤销。

**解决方案**：

#### **方案 1：黑名单（Blacklist）**

```python
# 用户注销时
@app.post("/api/auth/logout")
async def logout(token: str = Depends(get_token)):
    payload = jwt.decode(token, SECRET_KEY)
    jti = payload["jti"]  # Token 唯一 ID
    exp = payload["exp"]  # 过期时间

    # 加入黑名单（Redis）
    ttl = exp - int(time.time())  # 剩余有效时间
    redis.setex(f"blacklist:{jti}", ttl, "1")

    return {"message": "Logged out"}

# 验证时检查
async def verify_token(token: str):
    payload = jwt.decode(token, SECRET_KEY)
    jti = payload["jti"]

    # 检查黑名单
    if redis.exists(f"blacklist:{jti}"):
        raise HTTPException(401, "Token revoked")

    return payload
```

**优缺点**：

- ✅ 可以立即撤销 Token
- ❌ 引入了状态（Redis），失去了无状态优势
- ❌ 需要额外的存储和查询

#### **方案 2：短期 Token + Refresh Token**

```python
# 登录时返回两个 Token
@app.post("/api/auth/login")
async def login(credentials: LoginCredentials):
    user = authenticate_user(credentials)

    # Access Token（短期，15 分钟）
    access_token = create_access_token({
        "user_id": user.id,
        "exp": now + timedelta(minutes=15)
    })

    # Refresh Token（长期，7 天，存储在数据库）
    refresh_token = create_refresh_token({
        "user_id": user.id,
        "exp": now + timedelta(days=7)
    })

    # 将 Refresh Token 存储到数据库（可撤销）
    db.save_refresh_token(user.id, refresh_token)

    return {
        "access_token": access_token,
        "refresh_token": refresh_token
    }

# 刷新 Access Token
@app.post("/api/auth/refresh")
async def refresh(refresh_token: str):
    # 验证 Refresh Token
    payload = jwt.decode(refresh_token, SECRET_KEY)

    # 检查数据库（是否被撤销）
    if not db.is_refresh_token_valid(refresh_token):
        raise HTTPException(401, "Refresh token revoked")

    # 签发新的 Access Token
    new_access_token = create_access_token({
        "user_id": payload["user_id"],
        "exp": now + timedelta(minutes=15)
    })

    return {"access_token": new_access_token}

# 注销时撤销 Refresh Token
@app.post("/api/auth/logout")
async def logout(refresh_token: str):
    db.revoke_refresh_token(refresh_token)
    return {"message": "Logged out"}
```

**流程**：

```
1. 用户登录 → 获得 Access Token (15分钟) + Refresh Token (7天)
2. 访问 API → 使用 Access Token
3. Access Token 过期 → 使用 Refresh Token 获取新的 Access Token
4. 注销 → 撤销 Refresh Token（Access Token 15 分钟后自动失效）
```

**优缺点**：

- ✅ 平衡了安全性和可用性
- ✅ Refresh Token 可撤销（存储在数据库）
- ✅ Access Token 短期，泄露影响小
- ❌ 实现复杂度较高

### 6.2 问题：Payload 可以被解码怎么办？

**事实**：JWT 的 Payload 只是 Base64 编码，**不是加密**！

```javascript
// 任何人都可以解码 Token
const token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMDAsInVzZXJuYW1lIjoiemhhbmdzYW4ifQ.xxx"

const payload = JSON.parse(atob(token.split('.')[1]))
console.log(payload)  // { user_id: 100, username: "zhangsan" }
```

**解决方案**：

```python
# ❌ 不要在 Payload 中放敏感信息
payload = {
    "user_id": 100,
    "password": "123456",        # ❌ 密码！
    "credit_card": "1234-5678",  # ❌ 信用卡号！
    "api_key": "secret-key"      # ❌ 密钥！
}

# ✅ 只放必要的非敏感信息
payload = {
    "sub": "user_100",     # 用户 ID（可公开）
    "username": "zhangsan", # 用户名（可公开）
    "role": "admin",        # 角色（可公开）
    "exp": 1728989600       # 过期时间
}

# ✅ 敏感信息需要时再查询数据库
@app.get("/api/user/profile")
async def get_profile(current_user: User = Depends(get_current_user)):
    # 从数据库获取完整用户信息（包括敏感数据）
    user = db.get_user_by_id(current_user.id)
    return {
        "username": user.username,
        "email": user.email,
        "phone": user.phone,  # 敏感信息，从数据库查询
        "address": user.address
    }
```

### 6.3 问题：如何实现"记住我"功能？

**方案：动态过期时间**

```python
@app.post("/api/auth/login")
async def login(credentials: LoginCredentials, remember_me: bool = False):
    user = authenticate_user(credentials)

    # 根据"记住我"设置不同的过期时间
    if remember_me:
        expires_delta = timedelta(days=30)  # 30 天
    else:
        expires_delta = timedelta(hours=1)  # 1 小时

    token = create_access_token({
        "user_id": user.id,
        "exp": datetime.utcnow() + expires_delta
    })

    return {"access_token": token}
```

---

## 7. 最佳实践清单

### 7.1 Token 设计

- ✅ **使用标准字段**：遵循 JWT 规范（exp、iat、sub 等）
- ✅ **最小化 Payload**：只放必要信息，减少 Token 大小
- ✅ **避免敏感数据**：密码、密钥、信用卡号等绝对不能放
- ✅ **添加 jti**：便于撤销和追踪

```python
# ✅ 推荐的 Payload 结构
payload = {
    "sub": "user_100",           # 标准字段：用户 ID
    "username": "zhangsan",      # 自定义字段：用户名
    "role": "admin",             # 自定义字段：角色
    "exp": 1728989600,           # 标准字段：过期时间
    "iat": 1728986000,           # 标准字段：签发时间
    "jti": "uuid-xxx"            # 标准字段：Token 唯一 ID
}
```

### 7.2 安全配置

- ✅ **强密钥**：至少 32 字节随机字符串
- ✅ **环境变量**：SECRET_KEY 绝对不能硬编码
- ✅ **HTTPS**：生产环境必须使用 HTTPS
- ✅ **短过期**：Access Token 不超过 1 小时
- ✅ **HttpOnly Cookie**：前端无法访问（防 XSS）

```python
# ✅ 安全配置示例
class Settings(BaseSettings):
    SECRET_KEY: str = secrets.token_urlsafe(32)  # 强密钥
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15        # 15 分钟
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7           # 7 天

    class Config:
        env_file = ".env"
```

### 7.3 错误处理

```python
# ✅ 统一错误响应
@app.exception_handler(JWTError)
async def jwt_exception_handler(request, exc):
    return JSONResponse(
        status_code=401,
        content={"detail": "Invalid or expired token"}
    )

# ✅ 区分错误类型（内部日志，用户看到统一消息）
try:
    payload = jwt.decode(token, SECRET_KEY)
except jwt.ExpiredSignatureError:
    logger.info(f"Expired token from user {user_id}")
    raise HTTPException(401, "Token expired")  # 用户看到的
except jwt.InvalidSignatureError:
    logger.warning(f"Invalid signature, possible attack!")
    raise HTTPException(401, "Invalid token")
except Exception as e:
    logger.error(f"JWT error: {e}")
    raise HTTPException(401, "Invalid token")
```

### 7.4 前端集成

```javascript
// ✅ 登录后保存 Token
const response = await fetch('/api/auth/login', {
    method: 'POST',
    body: JSON.stringify({ email, password })
})
const { access_token } = await response.json()
localStorage.setItem('token', access_token)

// ✅ 请求时携带 Token
const token = localStorage.getItem('token')
const response = await fetch('/api/posts', {
    headers: {
        'Authorization': `Bearer ${token}`
    }
})

// ✅ 过期处理
if (response.status === 401) {
    localStorage.removeItem('token')
    window.location.href = '/login'
}

// ✅ 自动刷新 Token（Refresh Token 方案）
async function refreshToken() {
    const refresh = localStorage.getItem('refresh_token')
    const res = await fetch('/api/auth/refresh', {
        method: 'POST',
        headers: { 'Authorization': `Bearer ${refresh}` }
    })
    const { access_token } = await res.json()
    localStorage.setItem('token', access_token)
}
```

---

## 8. 总结对比

### JWT vs Session

| 特性 | Session-Cookie | JWT Token | 推荐场景 |
|------|---------------|-----------|----------|
| **状态** | 有状态 | 无状态 | JWT 适合微服务 |
| **扩展性** | 差 | 好 | JWT 适合分布式 |
| **撤销** | 容易 | 困难 | Session 适合强管理 |
| **跨域** | 困难 | 容易 | JWT 适合跨域 API |
| **移动端** | 不友好 | 友好 | JWT 适合 APP |
| **安全性** | 高 | 中 | 看具体实现 |

### 何时使用 JWT？

**✅ 适合 JWT 的场景**：

- 微服务架构（多服务器无状态）
- 跨域 API（前后端分离）
- 移动应用（原生 APP）
- 单页应用（SPA）
- 短期 Token（几分钟到几小时）

**❌ 不适合 JWT 的场景**：

- 需要频繁撤销 Token
- 长期会话（几天到几周）
- 高敏感操作（支付、修改密码）
- 实时性要求高（即时撤销）

**推荐方案**：

- **短期 JWT (15分钟) + Refresh Token (7天)**：平衡安全和体验
- **敏感操作二次验证**：如修改密码需要再次输入旧密码

---

## 下一步学习

1. **实践环节**：
   - 实现 JWT Token 生成函数
   - 实现 JWT Token 验证函数
   - 创建 FastAPI 依赖注入
   - 编写完整测试

2. **进阶主题**：
   - OAuth 2.0 协议
   - 单点登录（SSO）
   - 多因素认证（MFA）
   - API 权限控制（RBAC）

3. **参考资料**：
   - [JWT 官网](https://jwt.io/)
   - [RFC 7519 - JWT 标准](https://tools.ietf.org/html/rfc7519)
   - [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)

---

**记住核心要点**：

- JWT = Header.Payload.Signature
- Payload 不加密，不放敏感数据
- 签名防篡改，密钥要保密
- 短期 Token，配合 Refresh Token
- HTTPS 必须，HttpOnly Cookie 更安全

### 配置 JWT 相关的环境变量和设置

  在应用中添加 JWT 所需的配置项，包括：

  1. SECRET_KEY - 用于签名 JWT 的密钥
  2. ALGORITHM - 加密算法（HS256）
  3. ACCESS_TOKEN_EXPIRE_MINUTES - Token 过期时间

  ---
  💡 为什么需要这些配置？

  让我先讲解一下这些配置的作用：

#### 1. SECRET_KEY（密钥）

- 作用：JWT 签名的核心，防止 token 被篡改
- 原理：使用 HMAC-SHA256 算法时，需要一个密钥来生成签名
  signature = HMAC-SHA256(
      secret_key,
      base64UrlEncode(header) + "." + base64UrlEncode(payload)
  )
- 安全要求：
  - 足够长（建议 32+ 字符）
  - 足够随机（使用加密安全的随机数生成器）
  - 绝对保密（不能泄露，不能提交到 Git）

#### 2. ALGORITHM（算法）

- 作用：指定 JWT 使用的加密算法
- 常见选择：
  - HS256（HMAC-SHA256）- 对称加密，需要密钥
  - RS256（RSA-SHA256）- 非对称加密，需要公钥/私钥对
- 我们的选择：HS256（简单、高效、适合单体应用）

#### 3. ACCESS_TOKEN_EXPIRE_MINUTES（过期时间）

- 作用：控制 token 的有效期
- 平衡考虑：
  - 太短：用户频繁需要重新登录，体验差
  - 太长：token 被盗后危害时间长，安全性差
- 业界实践：
  - 短期 token：15-60 分钟（需要刷新机制）
  - 长期 token：7-30 天（"记住我"功能）
  - 我们先用 30 分钟（适合学习和开发）

  ---
  📝 实施步骤

  我需要修改两个文件：

  1. app/core/config.py - 添加 JWT 配置类
  2. .env.example - 添加环境变量示例

#### 配置安全的三个层次

  1. 开发环境：可以用简单的默认值（如当前配置），方便本地调试
  2. 测试环境：使用独立的密钥，与生产隔离
  3. 生产环境：必须使用加密安全的随机密钥

  为什么 SECRET_KEY 这么重要？

- 如果密钥泄露 → 攻击者可以伪造任何用户的 token
- 如果密钥太弱 → 可以通过暴力破解获得
- 如果多环境共用 → 测试环境的 token 可以在生产环境使用

  实用技巧：在 .env.example 中提供生成命令（我们已经做到了✅）
  生成随机密钥：`python -c "import secrets; print(secrets.token_urlsafe(32))"`
  `SECRET_KEY=your-secret-key-change-this-in-production`
