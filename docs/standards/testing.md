# 测试开发规范

## 🎯 测试要求

### 覆盖率标准
- **最低要求**：85% 测试覆盖率
- **推荐目标**：90%+ 测试覆盖率
- **核心模块**：95%+ 测试覆盖率（如 User 模型）

### 必须测试的内容
每个模块都必须包含以下测试：

#### 数据模型测试
- ✅ **基础 CRUD 操作**：创建、查询、更新、删除
- ✅ **数据库约束**：唯一性、非空、长度限制等
- ✅ **模型关系**：一对多、多对多关系加载
- ✅ **业务方法**：自定义方法和属性
- ✅ **边界情况**：异常处理、极值测试
- ✅ **字符串表示**：`__str__`、`__repr__` 方法

#### API 测试
- ✅ **端点功能**：正常请求和响应
- ✅ **认证授权**：权限控制测试
- ✅ **参数验证**：输入验证和错误处理
- ✅ **状态码**：各种响应状态码
- ✅ **数据格式**：JSON 序列化和反序列化

## 🎓 高覆盖率测试实践

### 测试数据四象限

每个功能都应该用 4 类数据进行测试：

| 类型 | 说明 | 示例 |
|-----|------|-----|
| **正常数据** | 常见的有效输入 | `"Hello World"` |
| **边界数据** | 极限但有效的值 | 空字符串 `""`、None、最大长度 |
| **异常数据** | 预期会失败的输入 | 重复的唯一字段、违反外键约束 |
| **极端数据** | 压力测试场景 | 超长字符串、大量数据 |

### 逻辑分支全覆盖

**原则**：每个 if-else 分支都必须有测试用例

```python
# 被测试代码
def process(value):
    if value > 50:
        # 分支 A
        return "high"
    elif value > 10:
        # 分支 B
        return "medium"
    else:
        # 分支 C
        return "low"

# 测试用例必须覆盖所有分支
def test_process_high_value():
    assert process(100) == "high"  # 分支 A

def test_process_medium_value():
    assert process(30) == "medium"  # 分支 B

def test_process_low_value():
    assert process(5) == "low"  # 分支 C

def test_process_boundary_values():
    assert process(51) == "high"   # 边界：刚好进入分支 A
    assert process(50) == "medium" # 边界：刚好不进入分支 A
    assert process(11) == "medium" # 边界：刚好进入分支 B
    assert process(10) == "low"    # 边界：刚好不进入分支 B
```


### 边界情况识别清单

✅ **字符串类型**：
- `""` 空字符串
- `None`
- `"   "` 只有空格
- 超长字符串（超过字段长度限制）
- 特殊字符：`"@#$%^&*()"`
- Unicode 字符：中文、emoji

✅ **数字类型**：
- `0`
- `-1` 负数
- 最大值/最小值
- 浮点数边界

✅ **集合类型**：
- 空列表 `[]`
- 单元素列表
- 重复元素

✅ **布尔逻辑**：
- Truthy vs Falsy 值
- `None` 的特殊处理

### 测试注释规范

每个测试场景**必须有注释**说明：

```python
def test_slug_generation(self):
    """✅ 正常数据：测试 slug 生成的各种场景"""

    # 1. 正常中文标题
    slug = generate_slug("我的文章")
    assert slug == "我的文章"

    # 2. 空字符串 - 应返回时间戳格式
    slug = generate_slug("")
    assert slug.startswith("文章-")

    # 3. 超长标题（有连字符）- 应在连字符处智能截断
    long_title = "部分1-部分2-部分3-" * 10
    slug = generate_slug(long_title)
    assert len(slug) <= 50
    assert not slug.endswith("...")  # 不应有省略号

    # 4. 超长标题（无连字符）- 应直接截断并加省略号
    long_title = "没有连字符的超长文本" * 10
    slug = generate_slug(long_title)
    assert len(slug) <= 50
    assert slug.endswith("...")  # 应有省略号
```

### 覆盖率检查流程

1. **运行覆盖率报告**：
   ```bash
   uv run pytest --cov=app --cov-report=term-missing
   ```

2. **分析未覆盖行**：
   - 查看 `term-missing` 输出，找到未覆盖的行号
   - 识别这些行属于哪个逻辑分支

3. **补充测试用例**：
   - 为每个未覆盖分支添加测试
   - 确认边界情况都已测试

4. **验证提升**：
   - 再次运行覆盖率报告
   - 确认覆盖率达到 85%+ 目标

## 🔧 测试技术规范

### 框架和工具
- **测试框架**：pytest
- **覆盖率工具**：pytest-cov
- **异步测试**：pytest-asyncio
- **Mock 工具**：pytest-mock

### 文件组织
```
tests/
├── conftest.py              # 全局 fixtures
├── test_database.py         # 数据库连接测试
│
├── test_models/
│   ├── __init__.py          # ⚠️ 必须添加（避免模块名冲突）
│   ├── conftest.py          # 模型测试专用 fixtures（可选）
│   ├── test_user.py         # User 模型测试
│   └── test_post.py         # Post 模型测试
│
├── test_schemas/            # Schema 测试
│   ├── __init__.py          # ⚠️ 必须添加
│   └── test_user.py         # User Schema 测试
│
├── test_crud/               # CRUD 测试
│   └── __init__.py          # ⚠️ 必须添加
│
├── test_core/               # 核心功能测试
│   └── __init__.py          # ⚠️ 必须添加
│
└── test_api/                # API 端点测试
    └── __init__.py          # ⚠️ 必须添加
```

### ⚠️ 避免模块名冲突（重要！）

#### 问题：同名测试文件冲突

当不同子目录中存在同名测试文件时（如 `test_models/test_user.py` 和 `test_schemas/test_user.py`），会导致 pytest 和 IDE 测试发现失败：

```bash
# ❌ 错误示例
tests/
├── test_models/
│   └── test_user.py         # 模块名：test_user
└── test_schemas/
    └── test_user.py         # 模块名：test_user（冲突！）

# 错误信息：
# ImportError: import file mismatch:
# imported module 'test_user' has this __file__ attribute:
#   /path/to/test_models/test_user.py
# which is not the same as the test file we want to collect:
#   /path/to/test_schemas/test_user.py
```

#### 解决方案：在测试子目录中添加 `__init__.py`

**规则**：每个测试子目录（`test_*/`）都必须包含 `__init__.py` 文件（可以是空文件）。

```bash
# ✅ 正确示例
tests/
├── test_models/
│   ├── __init__.py          # 创建独立命名空间
│   └── test_user.py         # 模块名：test_models.test_user
└── test_schemas/
    ├── __init__.py          # 创建独立命名空间
    └── test_user.py         # 模块名：test_schemas.test_user（不冲突）
```

**效果**：
- 有 `__init__.py`：两个文件分别是 `test_models.test_user` 和 `test_schemas.test_user`，**命名空间隔离** ✅
- 没有 `__init__.py`：两个文件都叫 `test_user`，**模块名冲突** ❌

#### 清理缓存

如果遇到模块冲突错误，需要清理缓存：

```bash
# 清理 pytest 缓存
rm -rf .pytest_cache
find tests -type d -name __pycache__ -exec rm -rf {} +
find tests -name "*.pyc" -delete

# VSCode 用户：刷新测试发现
# Cmd+Shift+P → "Python: Discover Tests"
# 或 Cmd+Shift+P → "Developer: Reload Window"
```

#### 最佳实践

1. **创建测试子目录时立即添加 `__init__.py`**
   ```bash
   mkdir tests/test_new_module
   touch tests/test_new_module/__init__.py
   ```

2. **使用独特的测试文件名**（可选，但推荐）
   ```
   test_models/test_user_model.py        # 明确是模型测试
   test_schemas/test_user_schema.py      # 明确是 Schema 测试
   test_api/test_user_endpoints.py       # 明确是 API 测试
   ```

3. **定期清理缓存**
   - 重组测试目录后
   - 遇到模块导入错误时
   - IDE 测试发现异常时

### 命名约定
- **测试文件**：`test_*.py`
- **测试类**：`TestModelName`、`TestAPIEndpoint`
- **测试方法**：`test_[scenario]_[expected_behavior]`
- **Fixture**：描述性名称，避免缩写

### 类型注解规范

**⚠️ 重要**：测试代码同样需要完整的类型注解，这不仅能提供 IDE 智能提示，还能让代码更易读、更易维护。

#### Fixture 类型注解

**规则 1：使用 `Generator` 类型标注 yield fixture**

```python
from collections.abc import Generator
from sqlalchemy import Engine
from sqlalchemy.orm import Session

# ✅ 正确：使用 Generator 类型
@pytest.fixture
def engine() -> Generator[Engine, None, None]:
    """创建测试数据库引擎"""
    engine = create_engine("sqlite:///:memory:")
    yield engine  # yield 表示这是生成器
    engine.dispose()

# ✅ 正确：Session fixture 也用 Generator
@pytest.fixture
def session(engine: Engine) -> Generator[Session, None, None]:
    """创建测试数据库会话"""
    session = Session()
    yield session
    session.rollback()
    session.close()

# ❌ 错误：使用 yield 但标注为普通返回值
@pytest.fixture
def engine() -> Engine:  # 类型不匹配！
    engine = create_engine(...)
    yield engine  # 这会创建 Generator，不是直接返回 Engine
```

**Generator 类型参数说明**：
```python
Generator[YieldType, SendType, ReturnType]
         ↓          ↓         ↓
         yield值   send()值  return值

# 对于 pytest fixture：
# - YieldType: fixture 产出的值（如 Engine、Session）
# - SendType: 通常是 None（fixture 不接收 send）
# - ReturnType: 通常是 None（fixture 不返回值）
```

**规则 2：直接 return 的 fixture 使用普通类型**

```python
# ✅ 正确：直接 return 不需要 Generator
@pytest.fixture
def sample_user(session: Session) -> User:
    """创建测试用户"""
    user = User(...)
    session.add(user)
    session.commit()
    return user  # 直接返回，不是 yield

# ✅ 正确：返回字典也要标注类型
@pytest.fixture
def sample_user_data() -> dict[str, str]:
    """生成用户测试数据"""
    return {
        "username": "testuser",
        "email": "test@example.com"
    }
```

#### 测试方法类型注解

**⚠️ 关键**：即使 `conftest.py` 中的 fixture 有类型注解，测试方法的参数**也必须添加类型注解**，IDE 才能提供智能提示。

```python
from sqlalchemy.orm import Session
from app.models.user import User
from app.models.post import Post

# ✅ 正确：所有参数都有类型注解
def test_create_comment(
    self,
    session: Session,      # ← 必须标注！
    sample_user: User,     # ← 必须标注！
    sample_post: Post      # ← 必须标注！
):
    """测试创建评论"""
    session.add(...)       # IDE 有智能提示 ✅
    sample_user.username   # IDE 有智能提示 ✅
    sample_post.title      # IDE 有智能提示 ✅

# ❌ 错误：缺少类型注解
def test_create_comment(self, session, sample_user, sample_post):
    session.add(...)       # IDE 没有智能提示 ❌
    sample_user.username   # IDE 没有智能提示 ❌
```

**完整示例**：

```python
# conftest.py
from collections.abc import Generator
from sqlalchemy.orm import Session
from app.models.user import User

@pytest.fixture
def session(engine: Engine) -> Generator[Session, None, None]:
    """数据库会话 fixture"""
    session = Session()
    yield session
    session.close()

@pytest.fixture
def sample_user(session: Session) -> User:
    """测试用户 fixture"""
    user = User(username="test", email="test@example.com")
    session.add(user)
    session.commit()
    return user

# test_user.py
from sqlalchemy.orm import Session
from app.models.user import User

class TestUserModel:
    def test_user_creation(
        self,
        session: Session,    # ← 参数类型注解
        sample_user: User    # ← 参数类型注解
    ):
        """测试用户创建"""
        # 现在 IDE 能正确识别类型，提供智能提示
        assert sample_user.username == "test"
        session.query(User).count()  # 自动完成 query 方法
```

#### 类型注解的好处

1. **IDE 智能提示**
   - 输入 `session.` 自动提示 `add()`, `commit()`, `query()` 等方法
   - 输入 `sample_user.` 自动提示 `username`, `email`, `id` 等属性

2. **类型检查**
   - 使用 `mypy` 或 `pyright` 可以提前发现类型错误
   - 避免运行时才发现参数类型不匹配

3. **代码可读性**
   - 一眼就能看出参数和返回值是什么类型
   - 降低理解测试代码的成本

4. **重构安全**
   - 修改模型字段时，IDE 会提示哪些测试受影响
   - 减少重构时的遗漏

#### 常见类型导入

```python
from collections.abc import Generator
from sqlalchemy import Engine
from sqlalchemy.orm import Session

# 项目模型
from app.models.user import User
from app.models.post import Post
from app.models.comment import Comment
```

## 📊 Fixture 设计规范

### 作用域使用
```python
# Session 级别：全局配置、数据库 URL
@pytest.fixture(scope="session")
def database_url(): ...

# Module 级别：数据库引擎、重量级资源
@pytest.fixture(scope="module")
def engine(): ...

# Class 级别：测试类共享资源
@pytest.fixture(scope="class")
def user_service(): ...

# Function 级别：测试数据、数据库会话
@pytest.fixture
def db_session(): ...
@pytest.fixture
def sample_user(): ...
```

### 数据管理规范
- **使用工厂模式**：生成测试数据
- **确保唯一性**：UUID 避免数据冲突
- **自动清理**：yield fixtures 处理资源释放
- **隔离原则**：每个测试独立，不相互影响

## 🧪 测试数据规范

### 工厂模式示例
```python
@pytest.fixture
def sample_user_data():
    """生成唯一的用户测试数据"""
    unique_id = str(uuid.uuid4())[:8]
    return {
        "username": f"testuser_{unique_id}",
        "email": f"test_{unique_id}@example.com",
        "password_hash": "hashed_password_123",
        "nickname": f"测试用户_{unique_id}"
    }

def test_user_creation(db_session, sample_user_data):
    """测试用户创建功能"""
    user = User(**sample_user_data)
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    assert user.username == sample_user_data["username"]
```

### 数据隔离策略
```python
@pytest.fixture
def db_session(engine):
    """提供隔离的数据库会话"""
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        yield session
    finally:
        session.rollback()  # 回滚所有变更
        session.close()     # 关闭会话
```

## ✅ 测试质量检查

### 运行命令
```bash
# 运行所有测试
uv run pytest

# 检查完整覆盖率
uv run pytest --cov=app --cov-report=term-missing

# 只运行特定测试
uv run pytest tests/test_models/test_user.py

# 检查特定模块覆盖率
uv run pytest tests/test_models/test_user.py --cov=app.models.user --cov-report=term-missing

# HTML 详细报告
uv run pytest --cov=app --cov-report=html && open htmlcov/index.html
```

### 质量标准
- **覆盖率报告**：必须显示具体的未覆盖行
- **测试命名**：测试名称要能清楚表达测试意图
- **断言清晰**：每个测试的断言要有明确含义
- **错误处理**：异常情况必须有对应测试

## 🔍 查看测试变量

### 最佳实践：自定义断言消息
```python
def test_slug_generation(self):
    title = "超长标题-部分1-部分2-部分3"
    slug = generate_slug(title)

    # ✅ 失败时自动显示所有变量
    assert len(slug) <= 20, (
        f"slug 长度超限\n"
        f"  原标题: {title}\n"
        f"  生成slug: {slug}\n"
        f"  实际长度: {len(slug)}"
    )
```

### 调试方法
```bash
# 详细模式：显示更多测试细节
uv run pytest -vv

# 调试模式：失败时进入交互式调试器
uv run pytest --pdb

# 日志模式：显示 logger.debug() 输出
uv run pytest --log-cli-level=DEBUG
```

## 🚫 测试反模式

### 避免的做法
```python
# ❌ 硬编码测试数据
def test_user_creation():
    user = User(username="test", email="test@example.com")  # 可能冲突

# ❌ 测试间有依赖
global_user = None
def test_create_user():
    global global_user
    global_user = create_user()  # 后续测试依赖这个

# ❌ 一个测试验证多个功能
def test_user_everything():
    # 测试创建、更新、删除... 太多功能
```

### 推荐的做法
```python
# ✅ 使用 fixture 生成数据
def test_user_creation(sample_user_data):
    user = User(**sample_user_data)  # 数据隔离

# ✅ 测试独立
def test_user_creation(db_session, sample_user_data):
    # 完全独立的测试

# ✅ 单一职责
def test_user_creation_should_set_default_role():
    # 只测试一个具体行为
```

## 🎨 Schema 测试最佳实践

### 测试风格选择

**原则**：根据测试复杂度选择合适的组织方式

| 场景 | 推荐风格 | 理由 |
|------|---------|------|
| **简单数据验证**（Schema） | 独立函数 + parametrize | 无状态管理，简洁直观 |
| **数据库集成测试**（Model） | 测试类 + fixture | 需要共享资源（session） |
| **API 端点测试** | 测试类 + fixture | 需要认证、数据准备等 |

```python
# ✅ Schema 测试：独立函数（推荐）
@pytest.mark.parametrize(...)
def test_user_create_validation(...):
    user = UserCreate(**data)
    assert user.username == expected

# ✅ Model 测试：测试类（推荐）
class TestUserModel:
    @pytest.fixture
    def session(self): ...

    def test_user_creation(self, session):
        user = User(...)
        session.add(user)
```

### 参数化测试规范

**规则 1：充分使用 `pytest.mark.parametrize`**

避免为每个测试场景写重复的测试函数，使用参数化测试一次定义多个场景。

```python
# ❌ 错误：重复代码
def test_invalid_password_too_short():
    data = VALID_USER_DATA.copy()
    data["password"] = "short"
    with pytest.raises(ValidationError):
        UserCreate(**data)

def test_invalid_password_no_digits():
    data = VALID_USER_DATA.copy()
    data["password"] = "onlyletters"
    with pytest.raises(ValidationError):
        UserCreate(**data)

# ✅ 正确：参数化测试
@pytest.mark.parametrize(
    ("invalid_password", "expected_error_msg"),
    [
        pytest.param("short", "String should have at least 8 characters", id="password_too_short"),
        pytest.param("onlyletters", "密码必须包含至少一个数字", id="password_no_digits"),
        pytest.param("12345678", "密码必须包含至少一个字母", id="password_no_letters"),
    ],
)
def test_user_create_invalid_password(invalid_password: str, expected_error_msg: str):
    """测试：使用无效的密码创建 UserCreate 实例应该失败"""
    data = VALID_USER_DATA.copy()
    data["password"] = invalid_password

    with pytest.raises(ValidationError) as excinfo:
        UserCreate(**data)

    assert any(expected_error_msg in str(e) for e in excinfo.value.errors())
```

**规则 2：使用 `pytest.param` 添加测试用例 ID**

测试用例 ID 让测试结果更易读，失败时能快速定位问题。

```python
# ❌ 没有 ID：测试输出不清晰
@pytest.mark.parametrize(
    ("invalid_password", "expected_error_msg"),
    [
        ("short", "String should have at least 8 characters"),  # 输出：[short-String should...]
    ],
)

# ✅ 有 ID：测试输出清晰
@pytest.mark.parametrize(
    ("invalid_password", "expected_error_msg"),
    [
        pytest.param(
            "short",
            "String should have at least 8 characters",
            id="password_too_short"  # 输出：test_xxx[password_too_short]
        ),
    ],
)
```

### 避免不必要的异常处理

**规则：不要为正常验证添加 try-except**

Pydantic 验证失败会自动抛出异常，pytest 会捕获并报告，无需手动处理。

```python
# ❌ 错误：多余的 try-except
def test_user_create_valid_data():
    """测试：使用完全有效的数据创建 UserCreate 实例应该成功"""
    try:
        user = UserCreate(**VALID_USER_DATA)
        assert user.username == VALID_USER_DATA["username"]
    except ValidationError as e:
        pytest.fail(f"UserCreate with valid data failed validation: {e}")

# ✅ 正确：直接断言
def test_user_create_valid_data():
    """测试：使用完全有效的数据创建 UserCreate 实例应该成功"""
    user = UserCreate(**VALID_USER_DATA)
    assert user.username == VALID_USER_DATA["username"]
    assert user.email == VALID_USER_DATA["email"]
    # 如果验证失败，pytest 会自动显示详细错误信息
```

**原因**：
- pytest 会自动捕获所有异常并显示详细堆栈
- `pytest.fail()` 会隐藏真实的错误信息
- 手动 try-except 增加了不必要的代码复杂度

**例外情况**：只在需要验证特定异常时使用 `pytest.raises`

```python
# ✅ 正确使用场景：验证异常
with pytest.raises(ValidationError) as excinfo:
    UserCreate(password="invalid")

# 验证异常详情
assert "密码必须包含至少一个数字" in str(excinfo.value)
```

### 精确的异常断言

**规则：验证异常时要检查具体字段和错误信息**

```python
# 🟡 一般：只检查错误信息存在（可能误匹配）
with pytest.raises(ValidationError) as excinfo:
    UserCreate(**invalid_data)

assert any(expected_msg in str(e) for e in excinfo.value.errors())

# ✅ 更好：检查错误字段和信息（精确匹配）
with pytest.raises(ValidationError) as excinfo:
    UserCreate(**invalid_data)

errors = excinfo.value.errors()
assert len(errors) == 1  # 确保只有一个错误
assert errors[0]["loc"] == ("password",)  # 检查错误字段
assert expected_msg in errors[0]["msg"]  # 检查错误信息
```

### 测试数据管理

**Schema 测试 vs Model 测试**：

```python
# ✅ Schema 测试：全局常量（无状态，可共享）
VALID_USER_DATA = {
    "username": "testuser",
    "email": "test@example.com",
    "password": "ValidPass123",
}

def test_user_create_valid():
    user = UserCreate(**VALID_USER_DATA)
    assert user.username == "testuser"

def test_user_create_invalid():
    data = VALID_USER_DATA.copy()  # 手动复制避免污染
    data["password"] = "invalid"
    # ...

# ✅ Model 测试：fixture 生成唯一数据（避免数据库冲突）
@pytest.fixture
def sample_user_data():
    unique_id = str(uuid.uuid4())[:8]
    return {
        "username": f"testuser_{unique_id}",
        "email": f"test_{unique_id}@example.com",
    }

def test_user_creation(session, sample_user_data):
    user = User(**sample_user_data)
    session.add(user)
    # ...
```

### 类型注解要求

**规则：测试函数参数必须添加类型注解**

```python
# ✅ 正确：完整类型注解
@pytest.mark.parametrize(
    ("invalid_password", "expected_error_msg"),
    [...],
)
def test_user_create_invalid_password(
    invalid_password: str,           # ← 类型注解
    expected_error_msg: str          # ← 类型注解
):
    """测试：使用无效的密码创建 UserCreate 实例应该失败"""
    # IDE 有智能提示 ✅

# ❌ 错误：缺少类型注解
def test_user_create_invalid_password(invalid_password, expected_error_msg):
    # IDE 没有智能提示 ❌
```

### 完整示例

```python
"""
Test User Schemas - Pydantic 数据验证测试

测试目标：
- 验证 UserCreate schema 的数据验证逻辑是否按预期工作
- 覆盖有效数据、无效数据和边界条件
"""

import pytest
from pydantic import ValidationError

from app.schemas.user import UserCreate

# 全局测试数据（Schema 测试无需唯一性）
VALID_USER_DATA = {
    "username": "testuser",
    "email": "test@example.com",
    "full_name": "Test User",
    "password": "ValidPass123",
}


def test_user_create_valid_data():
    """测试：使用完全有效的数据创建 UserCreate 实例应该成功"""
    user = UserCreate(**VALID_USER_DATA)
    assert user.username == VALID_USER_DATA["username"]
    assert user.email == VALID_USER_DATA["email"]
    assert user.password == VALID_USER_DATA["password"]


@pytest.mark.parametrize(
    ("invalid_password", "expected_error_msg"),
    [
        pytest.param("short", "String should have at least 8 characters", id="password_too_short"),
        pytest.param("onlyletters", "密码必须包含至少一个数字", id="password_no_digits"),
        pytest.param("12345678", "密码必须包含至少一个字母", id="password_no_letters"),
    ],
)
def test_user_create_invalid_password(invalid_password: str, expected_error_msg: str):
    """测试：使用无效的密码创建 UserCreate 实例应该失败"""
    data = VALID_USER_DATA.copy()
    data["password"] = invalid_password

    with pytest.raises(ValidationError) as excinfo:
        UserCreate(**data)

    assert any(expected_error_msg in str(e) for e in excinfo.value.errors())
```

## 📈 持续改进

### 定期检查
- **每周**：检查测试覆盖率变化
- **每月**：重构重复的测试代码
- **每季度**：更新测试策略和工具

### 性能优化
- 使用内存数据库加速测试
- 合理使用 fixture 作用域
- 并行运行独立测试

---

**💡 记住**：好的测试不仅能发现 bug，更是代码设计的指南和重构的安全网！