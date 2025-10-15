# Phase 3 - Pydantic 模型设计

> **设计目标**：基于 FastAPI 博客项目实践，总结 Pydantic Schema 设计的最佳实践和安全配置策略

## 📚 目录

1. [博客系统 Schema 设计回顾](#1-博客系统-schema-设计回顾)
2. [配置策略总结](#2-配置策略总结)
3. [安全收益](#3-安全收益)
4. [实际测试案例](#4-实际测试案例)

---

## 1. 博客系统 Schema 设计回顾

基于我们的 FastAPI 博客项目，以下是完整的 Schema 设计实践：

### 1.1 用户管理 Schema

```python
# app/schemas/user.py

# ============ 基础模型 ============
class UserBase(BaseModel):
    """用户基础字段（复用）"""
    username: str = Field(min_length=3, max_length=50, pattern=r"^[a-zA-Z0-9_]+$")
    email: EmailStr
    nickname: str = Field(min_length=1, max_length=50)

# ============ 输入模型（严格验证）============
class UserCreate(UserBase):
    """用户注册 - 用户输入"""
    password: str = Field(min_length=8)

    @field_validator("password")
    @classmethod
    def password_complexity(cls, v: str) -> str:
        """自定义密码复杂度验证"""
        return validate_password_complexity(v)

    model_config = ConfigDict(
        extra="forbid",  # ✅ 禁止额外字段，确保类型安全
        json_schema_extra={
            "examples": [
                {
                    "username": "johndoe",
                    "email": "john@example.com",
                    "nickname": "张三",
                    "password": "SecurePass123",
                }
            ]
        }
    )

class UserProfileUpdate(BaseModel):
    """用户自主更新个人资料"""
    nickname: str | None = Field(default=None, min_length=1, max_length=50)
    email: EmailStr | None = Field(default=None)

    model_config = ConfigDict(
        extra="forbid",  # ✅ 禁止额外字段，确保类型安全
        json_schema_extra={
            "examples": [
                {
                    "nickname": "张三 Updated",
                    "email": "zhangsan@example.com",
                }
            ]
        }
    )

class UserUpdate(BaseModel):
    """管理员更新用户信息"""
    username: str | None = Field(default=None, min_length=3, max_length=50)
    email: EmailStr | None = Field(default=None)
    nickname: str | None = Field(default=None, min_length=1, max_length=50)
    is_active: bool | None = Field(default=None)

    model_config = ConfigDict(
        extra="forbid",  # ✅ 禁止额外字段，确保类型安全
        json_schema_extra={
            "examples": [
                {
                    "nickname": "John Doe Updated",
                    "is_active": True,
                }
            ]
        }
    )

class PasswordChange(BaseModel):
    """密码修改请求模型"""
    old_password: str = Field(min_length=8)
    new_password: str = Field(min_length=8)

    @field_validator("new_password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        """验证新密码强度"""
        return validate_password_complexity(v)

    model_config = ConfigDict(
        extra="forbid",  # ✅ 禁止额外字段，确保类型安全
        json_schema_extra={
            "examples": [
                {
                    "old_password": "OldPassword123!",
                    "new_password": "NewPassword456!",
                }
            ]
        }
    )

# ============ 响应模型（灵活序列化）============
class UserResponse(UserBase):
    """返回给客户端的用户数据"""
    id: UUID
    is_active: bool
    role: str
    avatar: str | None
    is_verified: bool
    last_login: datetime | None
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(
        from_attributes=True,  # ✅ 允许从 ORM 对象创建
        # 注意：没有设置 extra="forbid"，允许灵活序列化
        json_schema_extra={
            "examples": [
                {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "username": "johndoe",
                    "email": "john@example.com",
                    "nickname": "张三",
                    "is_active": True,
                    "role": "user",
                    "avatar": None,
                    "is_verified": False,
                    "last_login": None,
                    "created_at": "2024-01-01T00:00:00Z",
                    "updated_at": "2024-01-01T00:00:00Z",
                }
            ]
        }
    )

class UserInDB(UserResponse):
    """内部使用，包含所有数据库字段"""
    password_hash: str
    deleted_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)
```

### 1.2 文章管理 Schema

```python
# app/schemas/post.py

class PostBase(BaseModel):
    """文章基础字段"""
    title: str = Field(min_length=1, max_length=200)
    content: str = Field(min_length=1)
    summary: str | None = Field(default=None, max_length=500)
    slug: str = Field(max_length=200)

class PostCreate(PostBase):
    """创建文章 - 用户输入"""
    tags: list[str] | None = Field(default=None, description="与文章关联的标签名称列表")

    model_config = ConfigDict(
        extra="forbid",  # ✅ 禁止额外字段，确保类型安全
        json_schema_extra={
            "example": {
                "title": "如何用 FastAPI 构建现代 API",
                "content": "FastAPI 是一个基于 Starlette 和 Pydantic 的现代、高性能 Web 框架...",
                "summary": "本文将带你入门 FastAPI。",
                "slug": "how-to-build-api-with-fastapi",
                "tags": ["python", "fastapi", "webdev"],
            }
        }
    )

class PostUpdate(BaseModel):
    """更新文章 - 用户输入"""
    title: str | None = Field(default=None, min_length=1, max_length=200)
    content: str | None = Field(default=None, min_length=1)
    summary: str | None = Field(default=None, max_length=500)
    slug: str | None = Field(default=None, max_length=200)
    tags: list[str] | None = Field(default=None, description="文章的全新标签列表，将覆盖旧的标签")

    model_config = ConfigDict(
        extra="forbid",  # ✅ 禁止额外字段，确保类型安全
        json_schema_extra={
            "example": {
                "title": "如何用 FastAPI 构建现代 API (已更新)",
                "content": "在原文基础上，增加关于依赖注入的章节。",
                "tags": ["python", "fastapi", "di"],
            }
        }
    )

class PostFilters(BaseModel):
    """文章过滤条件 - 查询参数"""
    author_id: UUID | None = Field(default=None, description="按作者ID过滤文章")
    tag_name: str | None = Field(default=None, description="按标签名称过滤文章")
    is_published: bool | None = Field(default=None, description="按发布状态过滤文章")
    title_contains: str | None = Field(default=None, description="按标题关键词过滤文章（模糊匹配）")
    published_at_from: datetime | None = Field(default=None, description="按发布时间范围过滤（起始时间）")
    published_at_to: datetime | None = Field(default=None, description="按发布时间范围过滤（结束时间）")

    model_config = ConfigDict(
        extra="forbid",  # ✅ 禁止额外字段，确保类型安全
        json_schema_extra={
            "example": {
                "author_id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                "tag_name": "Python",
                "is_published": True,
                "title_contains": "FastAPI",
                "published_at_from": "2024-06-01T00:00:00Z",
                "published_at_to": "2024-06-30T23:59:59Z",
            }
        }
    )

class PostResponse(PostBase):
    """文章响应 - 从数据库读取"""
    id: UUID
    author: UserResponse
    tags: list[TagResponse]
    created_at: datetime
    updated_at: datetime
    published_at: datetime | None
    view_count: int
    is_featured: bool

    model_config = ConfigDict(
        from_attributes=True,  # ✅ 允许从 ORM 对象创建
        # 注意：没有设置 extra="forbid"，允许灵活序列化
        json_schema_extra={
            "examples": [
                {
                    "id": "a1b2c3d4-e5f6-7890-1234-567890abcdef",
                    "title": "探索 FastAPI 的强大功能",
                    "content": "FastAPI 是一个现代、快速的 Web 框架...",
                    "summary": "本文介绍了 FastAPI 的核心特性...",
                    "slug": "explore-fastapi-features",
                    "author": {
                        "id": "f0e9d8c7-b6a5-4321-fedc-ba9876543210",
                        "username": "main_user",
                        "email": "main_user@example.com",
                        "nickname": "主用户",
                        "is_active": True,
                        "role": "user",
                        "avatar": None,
                        "is_verified": False,
                        "last_login": None,
                        "created_at": "2025-10-08T10:00:00Z",
                        "updated_at": "2025-10-08T10:00:00Z",
                    },
                    "tags": [
                        {
                            "id": "a0eebc99-9c0b-4ef8-bb6d-6bb9bd380a11",
                            "name": "Python",
                            "description": "关于 Python 编程语言的所有文章。",
                            "slug": "python",
                            "created_at": "2024-10-01T10:00:00Z",
                            "updated_at": "2024-10-01T10:00:00Z",
                            "post_count": 42,
                        }
                    ],
                    "created_at": "2025-10-08T10:00:00Z",
                    "updated_at": "2025-10-08T10:00:00Z",
                    "published_at": "2025-10-08T10:00:00Z",
                    "view_count": 0,
                    "is_featured": False,
                }
            ]
        }
    )
```

---

## 2. 配置策略总结

基于项目实践，我们总结出以下配置策略：

| Schema 类型  | `extra` 配置            | `from_attributes`      | 原因                         |
| ------------ | ----------------------- | ---------------------- | ---------------------------- |
| **Create**   | `extra="forbid"`        | 不设置                 | 用户输入，需要严格验证       |
| **Update**   | `extra="forbid"`        | 不设置                 | 用户输入，需要严格验证       |
| **Filters**  | `extra="forbid"`        | 不设置                 | 查询参数，需要严格验证       |
| **Response** | 不设置（默认 `ignore`） | `from_attributes=True` | 从数据库读取，需要灵活序列化 |
| **InDB**     | 不设置（默认 `ignore`） | `from_attributes=True` | 内部使用，包含所有字段       |
| **Base**     | 不设置                  | 不设置                 | 基础类，由继承的模型决定     |

### 2.1 配置决策原则

**输入模型（Input Models）**：

-   ✅ **Create**：`extra="forbid"` - 防止用户传递不允许的字段
-   ✅ **Update**：`extra="forbid"` - 防止用户传递不允许的字段
-   ✅ **Filters**：`extra="forbid"` - 查询参数需要严格验证

**响应模型（Response Models）**：

-   ✅ **Response**：不设置 `extra`（默认 `ignore`）- 从数据库读取，需要灵活序列化
-   ✅ **InDB**：不设置 `extra`（默认 `ignore`）- 内部使用，包含所有字段

**基础模型（Base Models）**：

-   ✅ **Base**：不设置配置 - 基础类，由继承的模型决定

---

## 3. 安全收益

通过正确配置 `extra="forbid"`，我们获得了以下安全收益：

### 3.1 防止字段注入

用户无法通过传递额外字段来修改不允许的字段，例如：

-   用户无法通过 `UserProfileUpdate` 修改 `username` 或 `is_superuser`
-   用户无法通过 `PostCreate` 传递 `id` 或 `created_at` 等系统字段

### 3.2 明确的错误信息

用户知道哪些字段不被支持，提供清晰的 422 验证错误：

```json
{
    "detail": [
        {
            "type": "extra_forbidden",
            "loc": ["username"],
            "msg": "Extra inputs are not permitted",
            "input": "hacker"
        }
    ]
}
```

### 3.3 API 契约稳定

确保 API 接口的向后兼容性，防止意外字段导致的静默错误。

### 3.4 类型安全

编译时和运行时都有类型检查，提高代码质量和开发体验。

---

## 4. 实际测试案例

### 4.1 正常请求测试

```python
# ✅ 正常请求
normal_request = {
    "nickname": "新昵称",
    "email": "new@example.com"
}
schema = UserProfileUpdate(**normal_request)  # ✅ 成功
print(schema.model_dump())  # {"nickname": "新昵称", "email": "new@example.com"}
```

### 4.2 恶意请求拦截测试

```python
# ❌ 恶意请求
malicious_request = {
    "nickname": "新昵称",
    "username": "hacker",  # 尝试修改用户名
    "is_superuser": True,  # 尝试提升权限
    "email": "new@example.com"
}

try:
    schema = UserProfileUpdate(**malicious_request)
except ValidationError as e:
    print("✅ 成功拦截恶意字段")
    print(e.errors())
    # [
    #   {
    #     "type": "extra_forbidden",
    #     "loc": ("username",),
    #     "msg": "Extra inputs are not permitted",
    #     "input": "hacker"
    #   },
    #   {
    #     "type": "extra_forbidden",
    #     "loc": ("is_superuser",),
    #     "msg": "Extra inputs are not permitted",
    #     "input": True
    #   }
    # ]
```

### 4.3 API 端点测试

```python
# 测试 API 端点的字段验证
import requests

# ✅ 正常请求
response = requests.patch(
    "/api/v1/users/me",
    json={
        "nickname": "新昵称",
        "email": "new@example.com"
    }
)
assert response.status_code == 200

# ❌ 恶意请求
response = requests.patch(
    "/api/v1/users/me",
    json={
        "nickname": "新昵称",
        "username": "hacker",  # 尝试修改用户名
        "is_superuser": True,  # 尝试提升权限
        "email": "new@example.com"
    }
)
assert response.status_code == 422  # 验证错误
```

---

## 5. 设计原则总结

### 5.1 核心原则

1. **职责分离**：

    - Pydantic Schema = 数据验证 + 序列化（外部接口）
    - SQLAlchemy Model = 数据持久化（内部存储）

2. **安全优先**：

    - 所有用户输入模型必须设置 `extra="forbid"`
    - 响应模型允许灵活序列化，不设置 `extra`

3. **类型安全**：
    - 使用完整的类型注解
    - 利用 `from_attributes=True` 支持 ORM 对象转换

### 5.2 最佳实践

1. **Schema 分类**：

    - **Create**：创建资源的输入
    - **Update**：更新资源的输入（字段可选）
    - **Response**：返回给客户端的输出
    - **InDB**：内部使用，包含敏感字段
    - **Filters**：查询参数过滤

2. **配置策略**：

    - 输入模型：`extra="forbid"` + 验证规则
    - 响应模型：`from_attributes=True` + 示例数据
    - 基础模型：最小配置，由继承决定

3. **安全考虑**：
    - 防止字段注入攻击
    - 提供明确的错误信息
    - 确保 API 契约稳定

---

## 参考资源

-   [Pydantic 官方文档](https://docs.pydantic.dev/)
-   [FastAPI 数据验证教程](https://fastapi.tiangolo.com/tutorial/body/)
-   [Pydantic V2 迁移指南](https://docs.pydantic.dev/latest/migration/)
