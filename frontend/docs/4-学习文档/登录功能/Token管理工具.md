# Token 管理工具

> **用途**：统一管理 JWT Token 的读写和清除操作

---

## 1. 为什么需要 Token 管理工具？

JWT Token 是登录后后端返回的**凭证**，前端需要在多个场景中操作它：

| 场景 | 操作 |
|------|------|
| 登录成功 | 保存 Token |
| 发起请求 | 读取 Token 添加到 Header |
| 页面刷新 | 恢复登录状态 |
| 退出登录 | 清除 Token |

如果没有统一工具，代码会分散在各处，难以维护。

---

## 2. 存储位置选择

| 存储方式 | 优点 | 缺点 |
|----------|------|------|
| **localStorage** | 持久化、简单 | 不够安全（XSS 可访问） |
| **sessionStorage** | 会话级、简单 | 关闭浏览器就丢失 |
| **Cookie** | 可设 httpOnly | 需要后端配合 |
| **内存** | 最安全 | 刷新就丢失 |

**推荐**：教学项目用 localStorage，生产环境建议 httpOnly Cookie。

---

## 3. 接口设计

```typescript
// utils/token.ts

const TOKEN_KEY = 'auth_token'

/** 获取 Token */
export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY)
}

/** 保存 Token */
export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token)
}

/** 清除 Token */
export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY)
}
```

---

## 4. 使用场景

### 场景 1：登录成功后保存

```typescript
// auth.store.ts
async function login(email: string, password: string) {
  const response = await api.post('/auth/login', { email, password })
  setToken(response.data.access_token)  // ← 保存
}
```

### 场景 2：API 请求时添加 Header

```typescript
// api.ts
api.interceptors.request.use((config) => {
  const token = getToken()  // ← 读取
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})
```

### 场景 3：页面刷新恢复状态

```typescript
// auth.store.ts
function checkAuth() {
  const token = getToken()  // ← 读取
  if (token) {
    this.token = token
  }
}
```

### 场景 4：退出登录

```typescript
// auth.store.ts
function logout() {
  removeToken()  // ← 清除
  this.token = null
}
```

---

## 5. 为什么要封装？

| 好处 | 说明 |
|------|------|
| **统一 Key 名** | 避免硬编码 `'auth_token'` |
| **类型安全** | TypeScript 返回类型明确 |
| **易于替换** | 以后换 Cookie 只改一个文件 |
| **可加逻辑** | 比如加密、过期检查等 |

---

## 6. 扩展：Token 过期检查（可选）

```typescript
export function isTokenExpired(): boolean {
  const token = getToken()
  if (!token) return true
  
  try {
    const payload = JSON.parse(atob(token.split('.')[1]))
    return Date.now() > payload.exp * 1000
  } catch {
    return true
  }
}
```
