# Phase 5 - 用户资料管理

> **文档用途**：用户资料管理功能的设计与实现
> **创建时间**：2025-10-11
> **更新策略**：根据项目实际需求更新用户资料管理功能

---

## 📚 目录

1. [API 设计](#1-api-设计)
2. [数据模型设计](#2-数据模型设计)
3. [CRUD 层设计](#3-crud-层设计)
4. [API 端点实现](#4-api-端点实现)
5. [测试设计](#5-测试设计)
6. [安全考虑](#6-安全考虑)
7. [最佳实践](#7-最佳实践)

---

## 1. API 设计

### 1.1 查看用户资料

**端点**：`GET /api/v1/users/me`

**认证**：需要 JWT Token

**响应示例**：

```json
{
    "id": 1,
    "username": "johndoe",
    "email": "john@example.com",
    "nickname": "John Doe",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2025-01-10T10:00:00Z"
}
```

**状态码**：

-   `200 OK` - 成功
-   `401 Unauthorized` - 未登录

### 1.2 更新用户资料

**端点**：`PATCH /api/v1/users/me`

**认证**：需要 JWT Token

**请求体**：

```json
{
    "nickname": "John Smith", // 可选
    "email": "john.new@example.com" // 可选
}
```

**响应示例**：

```json
{
    "id": 1,
    "username": "johndoe",
    "email": "john.new@example.com",
    "nickname": "John Smith",
    "is_active": true,
    "is_superuser": false,
    "created_at": "2025-01-10T10:00:00Z"
}
```

**状态码**：

-   `200 OK` - 成功
-   `400 Bad Request` - 请求数据格式错误
-   `401 Unauthorized` - 未登录
-   `409 Conflict` - 邮箱已被占用

**业务逻辑**：

1. 验证用户已登录（JWT Token）
2. 如果更新邮箱，检查新邮箱是否已存在（排除自己）
3. 只更新传入的字段（PATCH 语义）
4. 返回更新后的完整用户信息

### 1.3 修改密码

**端点**：`PUT /api/v1/users/me/password`

**认证**：需要 JWT Token

**请求体**：

```json
{
    "old_password": "OldPassword123!",
    "new_password": "NewPassword456!"
}
```

**响应示例**：

```json
{
    "message": "Password updated successfully"
}
```

**状态码**：

-   `200 OK` - 成功
-   `400 Bad Request` - 旧密码错误或新密码不符合要求
-   `401 Unauthorized` - 未登录

**业务逻辑**：

1. 验证用户已登录（JWT Token）
2. 验证旧密码是否正确
3. 验证新密码强度（可选，如果有密码策略）
4. 更新密码（使用 bcrypt 哈希）
5. 返回成功消息

**安全考虑**：

-   ✅ 必须验证旧密码（防止会话劫持）
-   ✅ 新密码不能与旧密码相同（可选）
-   ✅ 密码哈希使用 bcrypt（已在 Phase 3 实现）

---

## 2. 数据模型设计

### 2.1 UserProfileUpdate Schema（新增）

**文件**：`app/schemas/user.py`

**功能**：用户自主更新个人资料请求模型

**字段设计**：

```python
class UserProfileUpdate(BaseModel):
    """用户自主更新个人资料（PATCH /users/me）"""
    nickname: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(default=None)
```

**设计要点**：

-   所有字段都是可选的（支持 PATCH 部分更新）
-   使用 `EmailStr` 自动验证邮箱格式
-   ❌ 不包含 `username`（用户名通常不可更改）
-   ❌ 不包含 `is_active`（需要管理员权限，Phase 6 实现）
-   ❌ 不包含 `password`（使用单独的 `PasswordChange` 和端点）

**与 `UserUpdate` 的区别**：

| Schema              | 用途           | 端点                     | 权限     | 字段                                 |
| ------------------- | -------------- | ------------------------ | -------- | ------------------------------------ |
| `UserProfileUpdate` | 用户自主更新   | `PATCH /users/me`        | 普通用户 | nickname, email                      |
| `UserUpdate`        | 管理员更新用户 | `PATCH /users/{user_id}` | 管理员   | nickname, email, username, is_active |

**安全考虑**：

-   ✅ 普通用户无法修改 `is_active`（防止权限越界）
-   ✅ 类型即文档（API 文档自动反映真实限制）

### 2.2 PasswordChange Schema

**文件**：`app/schemas/user.py`

**功能**：密码修改请求模型

**字段设计**：

```python
class PasswordChange(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """验证新密码强度（可选）"""
        # 可以在这里添加密码强度校验逻辑
        # 例如：必须包含大小写字母、数字、特殊字符
        return v
```

**设计要点**：

-   `old_password` 必填且非空
-   `new_password` 必填且至少 8 位
-   可扩展：添加密码强度验证器

---

## 3. CRUD 层设计

### 3.1 update_profile() 方法

**文件**：`app/crud/user.py`

**函数签名**：

```python
def update_profile(
    db: Session,
    *,
    user: User,
    profile_update: UserProfileUpdate
) -> User:
    """更新用户资料"""
```

**实现逻辑**：

1. 检查邮箱去重（如果更新邮箱）
    ```python
    if profile_update.email and profile_update.email != user.email:
        existing_user = db.query(User).filter(User.email == profile_update.email).first()
        if existing_user:
            raise ValueError("Email already registered")
    ```
2. 只更新非 None 的字段
    ```python
    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    ```
3. 提交并刷新
    ```python
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
    ```

**为什么用 `exclude_unset=True`？**

-   只获取实际传入的字段（不包括默认 None 值）
-   实现真正的 PATCH 语义

### 3.2 update_password() 方法

**文件**：`app/crud/user.py`

**函数签名**：

```python
def update_password(
    db: Session,
    *,
    user: User,
    old_password: str,
    new_password: str
) -> User:
    """更新用户密码"""
```

**实现逻辑**：

1. 验证旧密码
    ```python
    if not verify_password(old_password, user.hashed_password):
        raise ValueError("Incorrect password")
    ```
2. 哈希新密码并更新
    ```python
    user.hashed_password = get_password_hash(new_password)
    db.add(user)
    db.commit()
    db.refresh(user)
    return user
    ```

**为什么要单独的方法而不是复用 update？**

-   密码修改是特殊的安全操作，逻辑独立
-   需要验证旧密码，不同于普通字段更新

---

## 4. API 端点实现

### 4.1 文件结构

**文件**：`app/api/v1/endpoints/users.py`（新建）

**路由前缀**：`/api/v1/users`

**依赖注入**：

-   `current_user: User = Depends(get_current_active_user)` - 获取当前用户
-   `db: Session = Depends(get_db)` - 数据库会话

### 4.2 GET /users/me 实现框架

```python
@router.get("/me", response_model=UserResponse)
def get_current_user_profile(
    current_user: User = Depends(get_current_active_user)
) -> User:
    """获取当前用户资料"""
    return current_user
```

**设计亮点**：

-   极简实现：依赖注入已提供 `current_user`，直接返回即可
-   `response_model=UserResponse` 自动过滤敏感字段（如 `hashed_password`）

### 4.3 PATCH /users/me 实现框架

```python
@router.patch("/me", response_model=UserResponse)
def update_current_user_profile(
    *,
    db: Session = Depends(get_db),
    profile_update: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user)
) -> User:
    """更新当前用户资料"""
    try:
        updated_user = crud_user.update_profile(
            db=db, user=current_user, profile_update=profile_update
        )
        return updated_user
    except ValueError as e:
        raise HTTPException(status_code=409, detail=str(e))
```

**异常处理**：

-   `ValueError("Email already registered")` → `409 Conflict`
-   其他异常 → 全局异常处理器捕获

### 4.4 PUT /users/me/password 实现框架

```python
@router.put("/me/password")
def change_password(
    *,
    db: Session = Depends(get_db),
    password_change: PasswordChange,
    current_user: User = Depends(get_current_active_user)
) -> dict[str, str]:
    """修改当前用户密码"""
    try:
        crud_user.update_password(
            db=db,
            user=current_user,
            old_password=password_change.old_password,
            new_password=password_change.new_password
        )
        return {"message": "Password updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
```

**为什么返回 dict 而不是 User？**

-   密码修改不需要返回用户完整信息
-   只返回成功消息，减少响应体积

---

## 5. 测试设计

### 5.1 测试数据四象限

| 数据类型     | 测试场景                                   |
| ------------ | ------------------------------------------ |
| **正常数据** | 更新昵称成功、更新邮箱成功、修改密码成功   |
| **边界数据** | 昵称为空字符串、邮箱格式边界、密码长度边界 |
| **异常数据** | 邮箱已存在、旧密码错误、未登录访问         |
| **极端数据** | 超长昵称、特殊字符、并发更新               |

### 5.2 核心测试用例（至少 10 个）

**查看资料**：

1. ✅ 已登录用户查看资料成功

**更新资料**： 2. ✅ 更新昵称成功 3. ✅ 更新邮箱成功 4. ✅ 同时更新昵称和邮箱成功 5. ✅ 更新邮箱到已存在的邮箱（409 Conflict） 6. ✅ 更新邮箱到自己当前邮箱（200 OK，无变化）

**修改密码**： 7. ✅ 提供正确旧密码，修改成功 8. ✅ 提供错误旧密码，修改失败（400 Bad Request） 9. ✅ 新密码过短，修改失败（422 Validation Error）

**权限控制**： 10. ✅ 未登录访问任何端点（401 Unauthorized）

### 5.3 测试文件结构

```
tests/
├── test_api/
│   └── test_users.py          # API 集成测试
└── test_crud/
    └── test_user.py           # CRUD 单元测试（扩展已有文件）
```


---

## 6. 安全考虑

### 6.1 权限控制

#### 用户自主更新 vs 管理员更新

```python
# 用户自主更新：只能修改自己的资料
@router.patch("/me", response_model=UserResponse)
def update_current_user_profile(
    current_user: User = Depends(get_current_active_user),
    profile_update: UserProfileUpdate,
    db: Session = Depends(get_db)
):
    # 只能更新自己的资料
    return crud_user.update_profile(db, user=current_user, profile_update=profile_update)

# 管理员更新：可以修改任何用户的资料（Phase 6 实现）
@router.patch("/{user_id}", response_model=UserResponse)
def update_user_by_admin(
    user_id: UUID,
    user_update: UserUpdate,
    current_user: User = Depends(get_current_admin_user),  # 需要管理员权限
    db: Session = Depends(get_db)
):
    # 可以更新任何用户的资料
    return crud_user.update(db, user_id=user_id, user_update=user_update)
```

### 6.2 数据验证

#### 邮箱唯一性检查

```python
def update_profile(db: Session, *, user: User, profile_update: UserProfileUpdate) -> User:
    # 如果更新邮箱，检查新邮箱是否已被占用（排除自己）
    if profile_update.email and profile_update.email != user.email:
        existing_user = get_user_by_email(db, email=profile_update.email)
        if existing_user and existing_user.id != user.id:
            raise ValueError("Email already registered")

    # 更新字段
    update_data = profile_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)

    db.add(user)
    db.commit()
    db.refresh(user)
    return user
```

### 6.3 密码安全

#### 密码强度验证

```python
class PasswordChange(BaseModel):
    old_password: str = Field(..., min_length=1)
    new_password: str = Field(..., min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """验证新密码强度"""
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")

        # 检查是否包含大小写字母、数字
        if not re.search(r"[A-Z]", v):
            raise ValueError("Password must contain uppercase letter")
        if not re.search(r"[a-z]", v):
            raise ValueError("Password must contain lowercase letter")
        if not re.search(r"\d", v):
            raise ValueError("Password must contain digit")

        return v

    @field_validator("new_password")
    @classmethod
    def validate_password_different(cls, v, info):
        """验证新密码与旧密码不同"""
        if "old_password" in info.data and v == info.data["old_password"]:
            raise ValueError("New password must be different from old password")
        return v
```

---

## 7. 最佳实践

### 7.1 API 设计原则

#### RESTful 资源设计

```python
# ✅ 好的设计：使用 /users/me 表示当前用户资源
GET    /api/v1/users/me           # 获取当前用户资料
PATCH  /api/v1/users/me           # 更新当前用户资料
PUT    /api/v1/users/me/password  # 修改当前用户密码

# ❌ 不好的设计：使用 /profile 等非资源命名
GET    /api/v1/profile            # 不符合 REST 规范
POST   /api/v1/update-profile     # 使用 POST 更新资源
```

#### HTTP 方法语义

```python
# ✅ 正确使用 HTTP 方法
PATCH /api/v1/users/me           # 部分更新用户资料
PUT   /api/v1/users/me/password  # 完整替换密码

# ❌ 错误使用 HTTP 方法
POST /api/v1/users/me           # 不应该用 POST 更新资源
GET  /api/v1/users/me/password  # 不应该用 GET 修改密码
```

### 7.2 数据模型设计

#### Schema 分离原则

```python
# ✅ 好的设计：不同用途使用不同的 Schema
class UserProfileUpdate(BaseModel):    # 用户自主更新
    nickname: str | None = None
    email: EmailStr | None = None

class UserUpdate(BaseModel):           # 管理员更新
    username: str | None = None
    nickname: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None

class PasswordChange(BaseModel):       # 密码修改
    old_password: str
    new_password: str

# ❌ 不好的设计：所有更新使用同一个 Schema
class UserUpdate(BaseModel):
    username: str | None = None      # 用户不应该能修改用户名
    nickname: str | None = None
    email: EmailStr | None = None
    is_active: bool | None = None    # 用户不应该能修改激活状态
    password: str | None = None      # 密码修改应该单独处理
```

### 7.3 错误处理

#### 统一异常处理

```python
# ✅ 好的设计：使用自定义异常
from app.core.exceptions import EmailAlreadyExistsError

def update_profile(db: Session, *, user: User, profile_update: UserProfileUpdate) -> User:
    if profile_update.email and profile_update.email != user.email:
        existing_user = get_user_by_email(db, email=profile_update.email)
        if existing_user and existing_user.id != user.id:
            raise EmailAlreadyExistsError(email=profile_update.email)

    # 更新逻辑...

# ❌ 不好的设计：直接抛出 HTTPException
def update_profile(db: Session, *, user: User, profile_update: UserProfileUpdate) -> User:
    if profile_update.email and profile_update.email != user.email:
        existing_user = get_user_by_email(db, email=profile_update.email)
        if existing_user and existing_user.id != user.id:
            raise HTTPException(status_code=409, detail="Email already registered")
```

### 7.4 测试策略

#### 测试覆盖原则

```python
# ✅ 好的测试：覆盖所有业务场景
def test_update_profile_success(self):
    """正常数据：更新成功"""

def test_update_profile_email_conflict(self):
    """异常数据：邮箱冲突"""

def test_update_profile_unauthorized(self):
    """权限控制：未登录访问"""

def test_update_profile_invalid_data(self):
    """边界数据：无效输入"""

# ❌ 不好的测试：只测试正常情况
def test_update_profile(self):
    """更新用户资料"""
    # 只测试了正常情况，没有测试异常情况
```

---

## 参考资源

-   [FastAPI 用户认证](https://fastapi.tiangolo.com/tutorial/security/)
-   [RESTful API 设计原则](https://restfulapi.net/)
-   [Pydantic 数据验证](https://docs.pydantic.dev/latest/)
-   [密码安全最佳实践](https://owasp.org/www-project-top-ten/)
