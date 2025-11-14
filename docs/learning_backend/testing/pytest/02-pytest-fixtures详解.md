# Pytest Fixtures 详解

## 🎯 什么是 Fixture

Fixture 是 pytest 最强大的功能之一，它提供了一种优雅的方式来管理测试资源、设置测试环境和共享测试数据。

### 核心概念

- **依赖注入**：测试函数通过参数名自动获取 fixture
- **生命周期管理**：自动处理资源的创建和清理
- **作用域控制**：控制 fixture 的创建频率和共享范围
- **组合能力**：fixture 可以依赖其他 fixture

## 🔧 基础 Fixture 语法

### 1. 简单 Fixture

```python
import pytest

@pytest.fixture
def sample_data():
    """提供测试数据"""
    return {"name": "张三", "age": 25}

@pytest.fixture
def sample_list():
    """提供列表数据"""
    return [1, 2, 3, 4, 5]

# 使用 fixture
def test_data_access(sample_data):
    assert sample_data["name"] == "张三"
    assert sample_data["age"] == 25

def test_list_operations(sample_list):
    assert len(sample_list) == 5
    assert 3 in sample_list
```

### 2. Fixture 的自动发现

```python
# 参数名必须与 fixture 名称完全一致
@pytest.fixture
def user_data():
    return {"username": "test_user"}

def test_user_creation(user_data):  # ✅ 自动注入
    user = User(**user_data)
    assert user.username == "test_user"

def test_wrong_parameter(wrong_name):  # ❌ 找不到名为 wrong_name 的 fixture
    pass
```

## 🔄 Fixture 作用域 (Scope)

### 作用域层级

```python
# Function（默认）：每个测试函数创建一次
@pytest.fixture  # scope="function"
@pytest.fixture(scope="function")

# Class：每个测试类创建一次
@pytest.fixture(scope="class")

# Module：每个测试模块创建一次
@pytest.fixture(scope="module")

# Package：每个测试包创建一次
@pytest.fixture(scope="package")

# Session：整个测试会话创建一次
@pytest.fixture(scope="session")
```

### 实际应用示例

```python
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Session 级别：全局配置，整个测试会话只创建一次
@pytest.fixture(scope="session")
def database_url():
    return "sqlite:///:memory:"

# Module 级别：数据库引擎，每个测试文件创建一次
@pytest.fixture(scope="module")
def engine(database_url):
    print("🚀 创建数据库引擎")
    engine = create_engine(database_url)
    Base.metadata.create_all(engine)
    yield engine
    print("🗑️ 清理数据库引擎")

# Class 级别：适用于一组相关测试
@pytest.fixture(scope="class")
def session_factory(engine):
    print("🏭 创建会话工厂")
    return sessionmaker(bind=engine)

# Function 级别：每个测试独立的会话
@pytest.fixture
def db_session(session_factory):
    print("🔗 创建数据库会话")
    session = session_factory()
    yield session
    print("🧹 清理数据库会话")
    session.rollback()
    session.close()

# Function 级别：每个测试独立的数据
@pytest.fixture
def sample_user():
    import uuid
    unique_id = str(uuid.uuid4())[:8]
    return {
        "username": f"user_{unique_id}",
        "email": f"user_{unique_id}@example.com"
    }
```

### 执行流程演示

```python
class TestUser:
    def test_create_user(self, db_session, sample_user):
        # 执行顺序：
        # 1. database_url (session)
        # 2. engine (module) - 🚀 创建数据库引擎
        # 3. session_factory (class) - 🏭 创建会话工厂
        # 4. sample_user (function)
        # 5. db_session (function) - 🔗 创建数据库会话

        user = User(**sample_user)
        db_session.add(user)
        db_session.commit()
        assert user.id is not None

        # 清理顺序（与创建相反）：
        # 6. db_session teardown - 🧹 清理数据库会话

    def test_user_query(self, db_session, sample_user):
        # session_factory 被复用，不重新创建
        # db_session 重新创建 - 🔗 创建数据库会话

        user = User(**sample_user)
        db_session.add(user)
        db_session.commit()

        found_user = db_session.query(User).filter_by(
            username=sample_user["username"]
        ).first()
        assert found_user is not None

        # 🧹 清理数据库会话
```

## 💫 Yield Fixtures（推荐方式）

### Setup & Teardown 模式

```python
@pytest.fixture
def file_manager():
    # Setup 阶段
    import tempfile
    import os

    temp_dir = tempfile.mkdtemp()
    test_file = os.path.join(temp_dir, "test.txt")

    print(f"📁 创建临时目录: {temp_dir}")

    yield test_file  # 返回给测试使用

    # Teardown 阶段（测试完成后执行）
    import shutil
    shutil.rmtree(temp_dir)
    print(f"🗑️ 清理临时目录: {temp_dir}")

def test_file_operations(file_manager):
    # 使用临时文件
    with open(file_manager, 'w') as f:
        f.write("Hello, World!")

    with open(file_manager, 'r') as f:
        content = f.read()

    assert content == "Hello, World!"
    # 测试结束后，file_manager fixture 自动清理临时目录
```

### 数据库会话管理

```python
@pytest.fixture
def db_session(engine):
    """提供数据库会话，自动回滚"""
    # Setup
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        yield session  # 提供给测试使用
    finally:
        # Teardown：确保无论测试成功失败都会清理
        session.rollback()  # 回滚未提交的事务
        session.close()     # 关闭会话

def test_user_creation(db_session):
    user = User(username="test")
    db_session.add(user)
    db_session.commit()

    assert user.id is not None
    # 会话自动回滚和关闭

def test_user_rollback(db_session):
    user = User(username="test")
    db_session.add(user)
    # 故意不提交，测试回滚功能

    # 即使测试失败，会话也会被正确清理
```

## 🔗 Fixture 依赖链

### 简单依赖

```python
@pytest.fixture
def database():
    return "sqlite:///:memory:"

@pytest.fixture
def engine(database):  # 依赖 database fixture
    return create_engine(database)

@pytest.fixture
def session(engine):   # 依赖 engine fixture
    Session = sessionmaker(bind=engine)
    session = Session()
    yield session
    session.close()

def test_with_dependencies(session):
    # pytest 自动解析依赖链：database -> engine -> session
    assert session is not None
```

### 复杂依赖网络

```python
@pytest.fixture(scope="session")
def config():
    return {"debug": True, "database": "test.db"}

@pytest.fixture(scope="module")
def app(config):
    from myapp import create_app
    return create_app(config)

@pytest.fixture(scope="module")
def database(config):
    db_url = config["database"]
    engine = create_engine(f"sqlite:///{db_url}")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def client(app):
    return app.test_client()

@pytest.fixture
def db_session(database):
    Session = sessionmaker(bind=database)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def logged_in_user(client, db_session):
    # 创建用户并登录
    user = User(username="testuser", email="test@example.com")
    db_session.add(user)
    db_session.commit()

    # 模拟登录
    client.post('/login', json={
        'username': 'testuser',
        'password': 'password'
    })

    return user

def test_protected_endpoint(client, logged_in_user):
    # 依赖链：config -> app -> client
    #         config -> database -> db_session -> logged_in_user
    response = client.get('/protected')
    assert response.status_code == 200
```

## 🎯 Fixture 参数化

### 简单参数化

```python
@pytest.fixture(params=["sqlite", "postgresql", "mysql"])
def database_type(request):
    return request.param

def test_database_connection(database_type):
    # 这个测试会运行 3 次，每次使用不同的数据库类型
    assert database_type in ["sqlite", "postgresql", "mysql"]
```

### 复杂参数化

```python
@pytest.fixture(params=[
    {"driver": "sqlite", "url": ":memory:"},
    {"driver": "postgresql", "url": "localhost:5432"},
    {"driver": "mysql", "url": "localhost:3306"}
])
def database_config(request):
    return request.param

@pytest.fixture
def engine(database_config):
    if database_config["driver"] == "sqlite":
        return create_engine(f"sqlite://{database_config['url']}")
    elif database_config["driver"] == "postgresql":
        return create_engine(f"postgresql://user:pass@{database_config['url']}/test")
    # ... 其他数据库配置

def test_user_creation(engine):
    # 这个测试会在不同数据库上运行
    # 确保代码在各种数据库上都能正常工作
    pass
```

## 📂 Fixture 的放置位置

### 1. 同文件 Fixture

```python
# test_user.py
import pytest

@pytest.fixture
def user_data():
    """只在当前文件中可用"""
    return {"username": "local_user"}

def test_user_creation(user_data):
    assert user_data["username"] == "local_user"
```

### 2. conftest.py 文件

```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

@pytest.fixture(scope="session")
def database_engine():
    """整个测试套件可用的全局 fixture"""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    return engine

@pytest.fixture
def db_session(database_engine):
    """所有测试文件都可以使用这个 fixture"""
    Session = sessionmaker(bind=database_engine)
    session = Session()
    yield session
    session.rollback()
    session.close()
```

### 3. conftest.py 层级结构

```
tests/
├── conftest.py              # 全局 fixtures
├── test_basic.py
├── models/
│   ├── conftest.py          # models 包专用 fixtures
│   ├── test_user.py
│   └── test_post.py
└── api/
    ├── conftest.py          # api 包专用 fixtures
    ├── test_auth.py
    └── test_posts.py
```

## 🛠️ 高级 Fixture 技巧

### 1. 自动使用的 Fixture

```python
@pytest.fixture(autouse=True)
def setup_logging():
    """每个测试自动应用，无需在参数中声明"""
    import logging
    logging.basicConfig(level=logging.DEBUG)
    yield
    # 清理日志配置

def test_something():
    # setup_logging 自动生效，无需声明参数
    import logging
    logging.info("测试日志")
```

### 2. 请求对象访问

```python
@pytest.fixture
def dynamic_data(request):
    """根据测试上下文提供不同数据"""
    if "slow" in request.keywords:
        return {"size": "large", "timeout": 60}
    else:
        return {"size": "small", "timeout": 5}

@pytest.mark.slow
def test_heavy_operation(dynamic_data):
    assert dynamic_data["size"] == "large"

def test_quick_operation(dynamic_data):
    assert dynamic_data["size"] == "small"
```

### 3. Fixture 工厂模式

```python
@pytest.fixture
def user_factory(db_session):
    """返回一个工厂函数，可以创建多个用户"""
    def _create_user(username=None, email=None):
        import uuid
        if username is None:
            username = f"user_{uuid.uuid4().hex[:8]}"
        if email is None:
            email = f"{username}@example.com"

        user = User(username=username, email=email)
        db_session.add(user)
        db_session.commit()
        return user

    return _create_user

def test_multiple_users(user_factory):
    # 使用工厂创建多个用户
    user1 = user_factory("alice")
    user2 = user_factory("bob")
    user3 = user_factory()  # 自动生成用户名

    assert user1.username == "alice"
    assert user2.username == "bob"
    assert user3.username.startswith("user_")
```

## ⚠️ 常见陷阱和最佳实践

### 1. 作用域陷阱

```python
# ❌ 错误：高作用域 fixture 依赖低作用域 fixture
@pytest.fixture(scope="class")
def bad_fixture(db_session):  # db_session 是 function scope
    # 这会导致错误！
    pass

# ✅ 正确：低作用域 fixture 依赖高作用域 fixture
@pytest.fixture
def good_fixture(database_engine):  # database_engine 是 class scope
    # 这是可以的
    pass
```

### 2. 状态共享陷阱

```python
# ❌ 错误：在高作用域 fixture 中使用可变对象
@pytest.fixture(scope="class")
def shared_list():
    return []  # 危险！所有测试共享同一个列表

# ✅ 正确：使用工厂模式
@pytest.fixture(scope="class")
def list_factory():
    def _create_list():
        return []
    return _create_list
```

### 3. 清理顺序

```python
@pytest.fixture
def proper_cleanup():
    resource = acquire_resource()
    try:
        yield resource
    finally:
        # 使用 finally 确保清理一定执行
        release_resource(resource)
```

## 💡 总结

Fixture 的核心价值：

1. **依赖注入**：自动管理测试依赖
2. **资源管理**：自动清理资源
3. **代码复用**：避免重复的设置代码
4. **作用域控制**：优化性能和隔离性的平衡
5. **组合能力**：构建复杂的测试环境

### 最佳实践清单

- ✅ 使用有意义的 fixture 名称
- ✅ 选择合适的作用域
- ✅ 使用 yield 进行资源清理
- ✅ 将通用 fixture 放在 conftest.py 中
- ✅ 避免在高作用域 fixture 中使用可变状态
- ✅ 使用工厂模式创建多个相似对象

下一步学习：[数据库测试实战](03-数据库测试实战.md)