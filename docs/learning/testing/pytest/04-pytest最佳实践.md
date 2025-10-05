# Pytest 最佳实践指南

## 🎯 测试设计原则

### 1. FIRST 原则

- **Fast (快速)**：测试应该快速运行
- **Independent (独立)**：测试之间不应相互依赖
- **Repeatable (可重复)**：测试应该在任何环境中都能重复运行
- **Self-Validating (自验证)**：测试应该有明确的通过/失败结果
- **Timely (及时)**：测试应该及时编写

### 2. 测试金字塔

```
    🔺 E2E 测试 (少量)
       - 端到端集成测试
       - UI/API 集成测试

  🔺🔺 集成测试 (适量)
     - 模块间集成
     - 数据库集成
     - 外部服务集成

🔺🔺🔺🔺 单元测试 (大量)
       - 函数测试
       - 类方法测试
       - 逻辑分支测试
```

## 📁 项目结构组织

### 推荐的目录结构

```
project/
├── app/
│   ├── models/
│   ├── api/
│   ├── core/
│   └── services/
├── tests/
│   ├── conftest.py              # 全局 fixtures
│   ├── test_models/
│   │   ├── conftest.py          # 模型测试专用 fixtures
│   │   ├── test_user.py
│   │   └── test_post.py
│   ├── test_api/
│   │   ├── conftest.py          # API 测试专用 fixtures
│   │   ├── test_auth.py
│   │   └── test_posts.py
│   ├── test_services/
│   │   └── test_email_service.py
│   ├── fixtures/
│   │   ├── __init__.py
│   │   ├── database.py          # 数据库相关 fixtures
│   │   ├── auth.py              # 认证相关 fixtures
│   │   └── data.py              # 测试数据 fixtures
│   └── utils/
│       ├── __init__.py
│       ├── factories.py         # 测试数据工厂
│       └── helpers.py           # 测试辅助函数
├── pytest.ini
└── pyproject.toml
```

### conftest.py 层级管理

```python
# tests/conftest.py - 全局配置
import pytest
from .fixtures.database import *
from .fixtures.auth import *
from .fixtures.data import *

# tests/test_models/conftest.py - 模型测试专用
import pytest
from app.models import User, Post

@pytest.fixture
def sample_user(db_session):
    """模型测试专用的用户对象"""
    user = User(username="model_test_user", email="model@test.com")
    db_session.add(user)
    db_session.commit()
    return user

# tests/test_api/conftest.py - API 测试专用
import pytest
from fastapi.testclient import TestClient
from app.main import app

@pytest.fixture
def api_client():
    """API 测试客户端"""
    return TestClient(app)
```

## 🏭 测试数据管理

### 1. 工厂模式 (推荐)

```python
# tests/utils/factories.py
import factory
import uuid
from datetime import datetime
from app.models import User, Post, UserRole, PostStatus

class UserFactory(factory.Factory):
    """用户数据工厂"""
    class Meta:
        model = User

    id = factory.LazyFunction(lambda: uuid.uuid4())
    username = factory.Sequence(lambda n: f"user_{n}")
    email = factory.LazyAttribute(lambda obj: f"{obj.username}@example.com")
    password_hash = "hashed_password"
    nickname = factory.LazyAttribute(lambda obj: f"用户_{obj.username}")
    role = UserRole.USER
    is_active = True
    is_verified = False
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

class PostFactory(factory.Factory):
    """文章数据工厂"""
    class Meta:
        model = Post

    id = factory.LazyFunction(lambda: uuid.uuid4())
    title = factory.Sequence(lambda n: f"测试文章_{n}")
    content = factory.LazyAttribute(lambda obj: f"这是{obj.title}的内容")
    slug = factory.LazyAttribute(lambda obj: obj.title.lower().replace(" ", "-"))
    status = PostStatus.PUBLISHED
    author = factory.SubFactory(UserFactory)
    created_at = factory.LazyFunction(datetime.utcnow)
    updated_at = factory.LazyFunction(datetime.utcnow)

# 使用工厂
def test_user_creation():
    user = UserFactory()
    assert user.username.startswith("user_")

def test_post_with_author():
    post = PostFactory()
    assert post.author.username.startswith("user_")
    assert post.content.startswith("这是测试文章")
```

### 2. Builder 模式

```python
# tests/utils/builders.py
class UserBuilder:
    """用户构建器"""

    def __init__(self):
        self.reset()

    def reset(self):
        self._user_data = {
            "username": f"user_{uuid.uuid4().hex[:8]}",
            "email": None,
            "password_hash": "default_hash",
            "nickname": "默认昵称",
            "role": UserRole.USER,
            "is_active": True,
            "is_verified": False
        }
        return self

    def with_username(self, username):
        self._user_data["username"] = username
        return self

    def with_email(self, email):
        self._user_data["email"] = email
        return self

    def as_admin(self):
        self._user_data["role"] = UserRole.ADMIN
        return self

    def inactive(self):
        self._user_data["is_active"] = False
        return self

    def verified(self):
        self._user_data["is_verified"] = True
        return self

    def build(self):
        if self._user_data["email"] is None:
            self._user_data["email"] = f"{self._user_data['username']}@example.com"
        return User(**self._user_data)

# 使用构建器
def test_admin_user():
    user = UserBuilder().with_username("admin").as_admin().verified().build()
    assert user.username == "admin"
    assert user.role == UserRole.ADMIN
    assert user.is_verified is True
```

## 🎯 测试命名约定

### 函数命名模式

```python
# 模式1: test_[unit_of_work]_[scenario]_[expected_behavior]
def test_user_creation_with_valid_data_should_succeed():
    pass

def test_user_login_with_invalid_password_should_fail():
    pass

def test_post_publication_with_draft_status_should_update_published_at():
    pass

# 模式2: test_[scenario]_[expected_behavior]
def test_duplicate_username_raises_integrity_error():
    pass

def test_admin_user_can_delete_any_post():
    pass

def test_inactive_user_cannot_login():
    pass

# 模式3: describe-it 风格 (使用类)
class DescribeUserAuthentication:
    class DescribeWithValidCredentials:
        def it_should_return_access_token(self):
            pass

        def it_should_update_last_login_time(self):
            pass

    class DescribeWithInvalidCredentials:
        def it_should_raise_authentication_error(self):
            pass

        def it_should_not_update_last_login_time(self):
            pass
```

### 测试文档字符串

```python
def test_user_password_hashing():
    """
    测试用户密码哈希功能

    Given: 一个明文密码
    When: 创建用户时
    Then: 密码应该被正确哈希存储
    And: 原始密码不应该以明文形式存在
    """
    password = "my_secure_password"
    user = User(username="test", email="test@example.com", password=password)

    assert user.password_hash != password
    assert user.verify_password(password) is True
    assert user.verify_password("wrong_password") is False
```

## 🔧 Fixture 设计模式

### 1. 分层 Fixture 架构

```python
# 基础资源层 (Session/Module scope)
@pytest.fixture(scope="session")
def database_url():
    return "sqlite:///:memory:"

@pytest.fixture(scope="module")
def engine(database_url):
    return create_engine(database_url)

# 服务层 (Class scope)
@pytest.fixture(scope="class")
def user_service(db_session):
    return UserService(db_session)

# 数据层 (Function scope)
@pytest.fixture
def sample_user(db_session):
    return UserFactory.create(db_session)

# 场景层 (组合多个 fixture)
@pytest.fixture
def authenticated_user(api_client, sample_user):
    """已认证的用户场景"""
    # 登录用户
    response = api_client.post("/auth/login", json={
        "username": sample_user.username,
        "password": "password"
    })
    token = response.json()["access_token"]

    # 返回用户和令牌
    return {
        "user": sample_user,
        "token": token,
        "headers": {"Authorization": f"Bearer {token}"}
    }
```

### 2. 参数化 Fixture

```python
@pytest.fixture(params=[
    {"role": UserRole.USER, "expected_status": 403},
    {"role": UserRole.ADMIN, "expected_status": 200},
    {"role": UserRole.MODERATOR, "expected_status": 200}
])
def user_with_role(request, db_session):
    """参数化用户角色测试"""
    user_data = {
        "username": f"user_{uuid.uuid4().hex[:8]}",
        "email": "test@example.com",
        "role": request.param["role"]
    }
    user = UserFactory.create(db_session, **user_data)
    return user, request.param["expected_status"]

def test_admin_endpoint_access(api_client, user_with_role):
    """测试不同角色用户访问管理员接口"""
    user, expected_status = user_with_role

    # 登录并访问管理员接口
    response = login_and_get(api_client, user, "/admin/users")
    assert response.status_code == expected_status
```

## 🧪 测试分类和标记

### 标记系统

```python
import pytest

# 按测试类型分类
@pytest.mark.unit
def test_password_hashing():
    """单元测试标记"""
    pass

@pytest.mark.integration
def test_user_post_relationship():
    """集成测试标记"""
    pass

@pytest.mark.e2e
def test_complete_user_workflow():
    """端到端测试标记"""
    pass

# 按速度分类
@pytest.mark.fast
def test_simple_calculation():
    """快速测试"""
    pass

@pytest.mark.slow
def test_heavy_database_operation():
    """慢速测试"""
    pass

# 按功能模块分类
@pytest.mark.auth
def test_user_login():
    """认证相关测试"""
    pass

@pytest.mark.posts
def test_post_creation():
    """文章相关测试"""
    pass

# 按环境分类
@pytest.mark.requires_db
def test_database_operation():
    """需要数据库的测试"""
    pass

@pytest.mark.requires_redis
def test_cache_operation():
    """需要 Redis 的测试"""
    pass
```

### 运行特定测试

```bash
# 只运行单元测试
pytest -m unit

# 运行非慢速测试
pytest -m "not slow"

# 运行认证和文章相关测试
pytest -m "auth or posts"

# 运行需要数据库但不慢的测试
pytest -m "requires_db and not slow"

# 运行特定功能的集成测试
pytest -m "integration and auth"
```

## 📊 测试覆盖率策略

### 配置覆盖率

```ini
# pytest.ini
[tool:pytest]
addopts =
    --cov=app
    --cov-report=term-missing
    --cov-report=html:htmlcov
    --cov-report=xml:coverage.xml
    --cov-fail-under=85
    --cov-branch

# 排除不需要测试的文件
omit =
    */migrations/*
    */venv/*
    */tests/*
    */conftest.py
    */setup.py
```

### 覆盖率目标

```python
# 不同类型代码的覆盖率目标
"""
- 核心业务逻辑: 95%+
- 模型和数据层: 90%+
- API 接口: 85%+
- 工具函数: 80%+
- 配置和初始化: 70%+
"""

# 关键路径必须覆盖
def test_all_user_model_methods():
    """确保用户模型所有方法都被测试"""
    user = UserFactory()

    # 测试所有公共方法
    assert hasattr(user, 'verify_password')
    assert hasattr(user, 'activate')
    assert hasattr(user, 'deactivate')
    assert hasattr(user, 'promote_to_admin')

    # 实际调用以确保覆盖
    user.verify_password("password")
    user.activate()
    user.deactivate()
    user.promote_to_admin()
```

## 🚀 性能测试最佳实践

### 性能基准测试

```python
import time
import pytest

class TestPerformance:
    """性能测试套件"""

    @pytest.mark.slow
    @pytest.mark.performance
    def test_bulk_user_creation_performance(self, db_session):
        """测试批量用户创建性能"""
        start_time = time.time()

        # 批量创建 1000 个用户
        users = []
        for i in range(1000):
            user = UserFactory.build()
            users.append(user)

        db_session.add_all(users)
        db_session.commit()

        elapsed = time.time() - start_time

        # 性能断言
        assert elapsed < 2.0, f"批量创建耗时过长: {elapsed:.2f}s"
        assert db_session.query(User).count() == 1000

    @pytest.mark.performance
    def test_complex_query_performance(self, db_session):
        """测试复杂查询性能"""
        # 准备测试数据
        users = [UserFactory.create(db_session) for _ in range(100)]
        for user in users:
            PostFactory.create_batch(10, author=user)

        start_time = time.time()

        # 执行复杂查询
        result = db_session.query(User).join(Post).group_by(User.id).all()

        elapsed = time.time() - start_time

        assert len(result) == 100
        assert elapsed < 0.5, f"查询耗时过长: {elapsed:.2f}s"
```

## 🔍 调试测试

### 调试技巧

```python
import pytest
import logging

# 1. 使用 pytest 调试选项
"""
pytest --pdb                 # 失败时进入调试器
pytest --pdb-trace          # 立即进入调试器
pytest -s                   # 显示 print 输出
pytest -v                   # 详细输出
pytest --tb=long            # 详细的错误回溯
"""

# 2. 在测试中使用调试
def test_with_debug():
    user = UserFactory()

    # 添加调试断点
    import pdb; pdb.set_trace()

    # 或使用 breakpoint() (Python 3.7+)
    breakpoint()

    assert user.username is not None

# 3. 日志调试
@pytest.fixture(autouse=True)
def configure_logging():
    """自动配置日志用于调试"""
    logging.basicConfig(level=logging.DEBUG)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

def test_with_logging():
    logging.info("开始测试用户创建")
    user = UserFactory()
    logging.debug(f"创建用户: {user.username}")
    assert user.username is not None

# 4. 参数化调试
@pytest.mark.parametrize("username,expected", [
    ("valid_user", True),
    ("", False),
    ("a" * 100, False),  # 过长用户名
])
def test_username_validation(username, expected):
    """参数化测试便于定位问题"""
    result = validate_username(username)
    assert result == expected
```

## 📋 测试检查清单

### 编写测试前

- [ ] 明确测试目标和范围
- [ ] 选择合适的测试类型（单元/集成/E2E）
- [ ] 设计测试数据和场景
- [ ] 确定断言和期望结果

### 编写测试时

- [ ] 使用描述性的测试名称
- [ ] 保持测试独立性
- [ ] 一个测试只验证一个行为
- [ ] 使用合适的 fixture 作用域
- [ ] 添加必要的清理操作

### 测试完成后

- [ ] 检查测试覆盖率
- [ ] 验证测试的可读性
- [ ] 确认测试的稳定性（多次运行）
- [ ] 检查测试执行速度
- [ ] 添加适当的测试标记

### 持续改进

- [ ] 定期重构测试代码
- [ ] 删除重复或过时的测试
- [ ] 优化慢速测试
- [ ] 更新测试文档
- [ ] 分享测试经验和模式

## 💡 总结

### 核心原则

1. **可读性优先**：测试是活文档，要让人容易理解
2. **独立性**：测试间不应相互依赖
3. **快速反馈**：大部分测试应该快速运行
4. **真实性**：测试应该反映真实使用场景
5. **可维护性**：测试代码也需要良好的设计

### 推荐工具链

- **pytest**: 测试框架
- **pytest-cov**: 覆盖率报告
- **pytest-xdist**: 并行测试
- **pytest-mock**: Mock 对象
- **factory-boy**: 测试数据工厂
- **faker**: 生成假数据
- **pytest-benchmark**: 性能测试

### 学习资源

- [Pytest 官方文档](https://docs.pytest.org/)
- [测试驱动开发 (TDD)](https://zh.wikipedia.org/wiki/测试驱动开发)
- [行为驱动开发 (BDD)](https://zh.wikipedia.org/wiki/行为驱动开发)

记住：好的测试不仅能发现 bug，更是代码设计的指南和重构的安全网！