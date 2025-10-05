# Python 编码规范

基于现代 Python 3.11+ 的行业最佳实践

---

## 🎯 类型注解（Type Hints）

### 基本原则
- **所有公共 API** 必须有完整类型注解
- **函数签名** 必须标注参数类型和返回值
- **复杂类型** 使用 typing 模块明确声明

### 示例
```python
from typing import Optional, List, Dict, Union
from uuid import UUID

# ✅ 完整的类型注解
def get_post_by_id(post_id: UUID) -> Optional[Post]:
    """根据 ID 获取文章"""
    return session.query(Post).filter(Post.id == post_id).first()

def create_posts(data: List[Dict[str, str]]) -> List[Post]:
    """批量创建文章"""
    return [Post(**item) for item in data]

# ✅ 使用现代语法（Python 3.10+）
def process_title(title: str | None = None) -> str:
    """处理标题（使用 | 替代 Optional）"""
    return title or "默认标题"
```

### 常用类型
```python
# 基础类型
str, int, float, bool, bytes

# 容器类型（Python 3.9+ 可直接用内置类型）
list[str], dict[str, int], set[int], tuple[str, int]

# 可选类型
str | None  # Python 3.10+（推荐）
Optional[str]  # Python 3.9 及以下（兼容写法）

# 联合类型
int | str | None  # Python 3.10+（推荐）

# 自定义类型
from typing import TypeAlias
PostID: TypeAlias = UUID
```

### typing 模块使用说明

**✅ Python 3.9+ 可以用内置类型替代的：**
```python
# 容器泛型 - 直接用内置类型
list[str]           # ✅ 不需要 typing.List
dict[str, int]      # ✅ 不需要 typing.Dict
set[int]            # ✅ 不需要 typing.Set
tuple[str, int]     # ✅ 不需要 typing.Tuple
```

**✅ Python 3.10+ 可以用 | 替代的：**
```python
# 联合类型 - 使用 | 操作符
str | None          # ✅ 不需要 typing.Optional
int | str           # ✅ 不需要 typing.Union
int | str | None    # ✅ 不需要 typing.Union
```

**❌ 仍然需要从 typing 导入的（高级类型）：**
```python
from typing import (
    Any,           # 任意类型
    Callable,      # 可调用对象 Callable[[str], int]
    Literal,       # 字面量类型 Literal["draft", "published"]
    TypeAlias,     # 类型别名
    Protocol,      # 协议（结构化类型）
    TypeVar,       # 类型变量（泛型）T = TypeVar('T')
    Generic,       # 泛型基类 class Container(Generic[T])
    TypedDict,     # 类型字典
    Final,         # 最终值（常量）
    ClassVar,      # 类变量
    cast,          # 类型转换
    overload,      # 函数重载
    TYPE_CHECKING, # 类型检查标志（避免循环导入）
)

# 示例：高级类型注解
def process_callback(func: Callable[[str], int]) -> Any:
    """Callable 必须从 typing 导入"""
    return func("test")

Status: TypeAlias = Literal["draft", "published", "archived"]
"""Literal 和 TypeAlias 必须从 typing 导入"""

T = TypeVar('T')
class Container(Generic[T]):
    """泛型类必须使用 TypeVar 和 Generic"""
    def __init__(self, value: T):
        self.value = value
```

**💡 推荐：只导入需要的高级类型**
```python
# ✅ 最佳实践
from typing import Any, Callable, Literal, TypeAlias
from uuid import UUID

def get_posts(
    tags: list[str],           # ✅ 内置类型
    filters: dict[str, Any]    # ✅ 内置 + Any
) -> list[dict[str, str]]:
    ...

def find_user(id: int | str) -> User | None:  # ✅ 使用 |
    ...

Status: TypeAlias = Literal["active", "inactive"]  # ✅ 高级类型
```

---

## 📐 代码风格（PEP 8）

### 行长度
- **最大行长**: 100 字符（现代屏幕标准）
- **文档字符串**: 80 字符

### 缩进和空格
```python
# ✅ 4 个空格缩进
def my_function(
    param1: str,
    param2: int,
    param3: bool = False
) -> dict[str, Any]:
    """函数参数较多时，每行一个参数"""
    return {"result": param1}

# ✅ 运算符周围有空格
result = (a + b) * c
items = [1, 2, 3, 4]
data = {"key": "value"}

# ❌ 避免行尾空格
```

### 空行规范
```python
# 2 个空行分隔顶层定义
class MyClass:
    """类定义"""
    pass


def my_function():
    """函数定义"""
    pass


# 1 个空行分隔类中的方法
class User:
    def __init__(self):
        pass

    def save(self):
        pass
```

---

## 📦 导入规范

### 导入顺序
```python
# 1. 标准库
import os
import sys
from datetime import datetime
from typing import Optional

# 2. 第三方库
from sqlalchemy import String
from fastapi import APIRouter
import pytest

# 3. 本地应用
from app.models.user import User
from app.core.config import settings
```

### 导入风格
```python
# ✅ 推荐：显式导入
from app.models.user import User, Post
from app.core.config import settings

# ✅ 类型检查导入
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from app.models.post import Post  # 避免循环导入

# ❌ 避免：通配符导入
from app.models import *  # 不推荐
```

---

## 🏷️ 命名规范

### 基本规则
```python
# 变量、函数、方法：snake_case
user_name = "Alice"
def get_user_by_id(user_id: int): ...

# 类名：PascalCase
class UserProfile: ...
class HTTPClient: ...

# 常量：UPPER_SNAKE_CASE
MAX_CONNECTIONS = 100
DATABASE_URL = "postgresql://..."

# 私有成员：前缀下划线
class MyClass:
    def __init__(self):
        self._private_var = 10

    def _private_method(self): ...

# 受保护的名称：双下划线前后缀（魔术方法）
def __init__(self): ...
def __str__(self): ...
```

### 特殊命名
```python
# 避免单字母变量（除了循环）
# ❌ 不好
def f(x, y): ...

# ✅ 清晰
def calculate_distance(x_coord: float, y_coord: float) -> float: ...

# ✅ 循环中的单字母变量可以接受
for i in range(10): ...
for x, y in coordinates: ...
```

---

## 📖 文档字符串（Docstrings）

### 函数文档
```python
def generate_slug(title: str, max_length: int = 50) -> str:
    """
    从标题生成 URL 友好的 slug

    将标题转换为适合 URL 使用的格式，包括：
    - 移除特殊字符
    - 转换空格为连字符
    - 限制长度

    Args:
        title: 要转换的标题
        max_length: slug 最大长度，默认 50

    Returns:
        生成的 slug 字符串

    Examples:
        >>> generate_slug("Hello World")
        "hello-world"

        >>> generate_slug("Python 教程", max_length=10)
        "python-教程"
    """
    # 实现代码...
```

### 类文档
```python
class Post(Base):
    """
    文章模型

    管理博客文章的数据模型，包含标题、内容、状态等信息。

    Attributes:
        id: 文章唯一标识（UUID）
        title: 文章标题
        content: 文章正文内容（Markdown 格式）
        status: 文章状态（草稿/已发布/已归档）
        author_id: 作者 ID（外键）

    Examples:
        >>> post = Post(title="我的文章", content="内容...")
        >>> post.publish()
        >>> print(post.status)
        PostStatus.PUBLISHED
    """
    __tablename__ = "posts"
```

### 模块文档
```python
"""
用户模型模块

定义用户相关的数据模型和业务逻辑，包括：
- User: 用户基本信息
- UserProfile: 用户详细资料
- UserRole: 用户角色枚举
"""
```

---

## ⚠️ 错误处理

### 异常处理原则
```python
# ✅ 捕获具体异常
try:
    user = get_user(user_id)
except UserNotFoundError:
    logger.warning(f"用户不存在: {user_id}")
    raise
except DatabaseError as e:
    logger.error(f"数据库错误: {e}")
    raise

# ❌ 避免捕获所有异常
try:
    process_data()
except Exception:  # 太宽泛
    pass

# ✅ 自定义异常
class PostNotFoundError(Exception):
    """文章不存在异常"""
    def __init__(self, post_id: UUID):
        self.post_id = post_id
        super().__init__(f"Post not found: {post_id}")
```

### 上下文管理器
```python
# ✅ 使用 with 管理资源
with open("file.txt") as f:
    data = f.read()

# ✅ 数据库会话
with SessionLocal() as session:
    user = session.query(User).first()
    session.commit()
```

---

## 🚀 现代 Python 特性（3.10+）

### 模式匹配（Match-Case）
```python
def process_status(status: PostStatus) -> str:
    match status:
        case PostStatus.DRAFT:
            return "草稿状态"
        case PostStatus.PUBLISHED:
            return "已发布"
        case PostStatus.ARCHIVED:
            return "已归档"
        case _:
            return "未知状态"
```

### 联合类型
```python
# Python 3.10+ 推荐写法
def get_value(key: str) -> int | str | None:
    return data.get(key)

# 旧写法（兼容性）
from typing import Union, Optional
def get_value(key: str) -> Optional[Union[int, str]]:
    return data.get(key)
```

### 数据类（Dataclass）
```python
from dataclasses import dataclass
from datetime import datetime

@dataclass
class PostCreate:
    """创建文章的数据传输对象"""
    title: str
    content: str
    author_id: UUID
    status: PostStatus = PostStatus.DRAFT
    created_at: datetime = datetime.now()
```

### 结构化模式匹配
```python
def handle_response(response: dict) -> str:
    match response:
        case {"status": "success", "data": data}:
            return f"成功: {data}"
        case {"status": "error", "message": msg}:
            return f"错误: {msg}"
        case _:
            return "未知响应"
```

---

## 🛠️ 工具配置

### Ruff（代码检查和格式化）
```toml
[tool.ruff]
line-length = 100
target-version = "py311"

[tool.ruff.lint]
select = [
    "E",   # pycodestyle errors
    "W",   # pycodestyle warnings
    "F",   # pyflakes
    "I",   # isort
    "N",   # pep8-naming
    "UP",  # pyupgrade
]
```

### Mypy（类型检查）
```toml
[tool.mypy]
python_version = "3.11"
strict = true
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
```

### 运行检查
```bash
# 代码检查
uv run ruff check .

# 代码格式化
uv run ruff format .

# 类型检查
uv run mypy app/
```

---

## 📋 检查清单

在提交代码前，确保：

- [ ] 所有公共函数有类型注解
- [ ] 函数有清晰的文档字符串
- [ ] 通过 `ruff check` 检查
- [ ] 通过 `ruff format` 格式化
- [ ] 通过 `mypy` 类型检查
- [ ] 没有未使用的导入
- [ ] 变量命名清晰有意义
- [ ] 适当的错误处理

---

## 🔗 参考资源

- [PEP 8 - Python 代码风格指南](https://peps.python.org/pep-0008/)
- [PEP 484 - 类型注解](https://peps.python.org/pep-0484/)
- [Google Python Style Guide](https://google.github.io/styleguide/pyguide.html)
- [Ruff 文档](https://docs.astral.sh/ruff/)
- [Mypy 文档](https://mypy.readthedocs.io/)

---

**💡 记住**：好的代码是给人读的，只是顺便让计算机执行！
