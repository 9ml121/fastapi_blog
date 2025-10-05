# Pytest 基础概念

## 🎯 什么是 Pytest

Pytest 是 Python 生态系统中最流行的测试框架，以其简洁、强大和易用而著称。

### 核心特点

- **简洁的语法**：使用简单的 `assert` 语句
- **自动发现**：自动发现和运行测试
- **丰富的插件生态**：支持大量第三方插件
- **强大的 fixture 系统**：优雅的测试资源管理
- **详细的错误报告**：清晰的失败信息

## 📚 基本概念

### 1. 测试文件和函数命名

```python
# 测试文件命名：test_*.py 或 *_test.py
# test_user.py
# test_models.py
# user_test.py

# 测试函数命名：test_*
def test_user_creation():
    """测试用户创建"""
    pass

def test_user_login():
    """测试用户登录"""
    pass

# 测试类命名：Test*
class TestUser:
    def test_create_user(self):
        pass

    def test_update_user(self):
        pass
```

### 2. 断言（Assertions）

```python
def test_basic_assertions():
    # 基本断言
    assert True
    assert 1 == 1
    assert "hello" in "hello world"
    assert len([1, 2, 3]) == 3

    # 比较断言
    assert 5 > 3
    assert 10 >= 10
    assert "abc" != "def"

    # 类型断言
    assert isinstance([], list)
    assert isinstance("hello", str)

    # None 检查
    value = None
    assert value is None
    assert value is not True

def test_exception_assertions():
    """测试异常"""
    import pytest

    # 期望抛出特定异常
    with pytest.raises(ValueError):
        int("not_a_number")

    # 检查异常消息
    with pytest.raises(ValueError, match="invalid literal"):
        int("not_a_number")
```

### 3. 测试类 vs 测试函数

```python
# 函数式测试：简单、直接
def test_simple_calculation():
    result = 2 + 2
    assert result == 4

# 类式测试：组织相关测试，共享 fixtures
class TestCalculator:
    def test_addition(self):
        result = 2 + 2
        assert result == 4

    def test_subtraction(self):
        result = 5 - 3
        assert result == 2
```

## 🔧 运行测试

### 基本运行命令

```bash
# 运行所有测试
pytest

# 运行特定文件
pytest tests/test_user.py

# 运行特定测试函数
pytest tests/test_user.py::test_user_creation

# 运行特定测试类
pytest tests/test_user.py::TestUser

# 运行特定类的特定方法
pytest tests/test_user.py::TestUser::test_create_user
```

### 常用参数

```bash
# 显示详细输出
pytest -v

# 显示测试覆盖率
pytest --cov=app

# 只运行失败的测试
pytest --lf

# 遇到第一个失败就停止
pytest -x

# 并行运行测试
pytest -n auto  # 需要 pytest-xdist

# 显示最慢的 10 个测试
pytest --durations=10
```

## 📊 测试发现机制

Pytest 会自动发现测试，遵循以下规则：

### 文件发现
- 当前目录及子目录中的 `test_*.py` 或 `*_test.py` 文件

### 测试发现
- 文件中以 `test_` 开头的函数
- 文件中以 `Test` 开头的类
- 类中以 `test_` 开头的方法

### 目录结构示例

```
project/
├── app/
│   ├── models/
│   │   └── user.py
│   └── main.py
├── tests/
│   ├── __init__.py
│   ├── test_models/
│   │   ├── __init__.py
│   │   ├── test_user.py      ✅ 会被发现
│   │   └── test_post.py      ✅ 会被发现
│   ├── test_api.py           ✅ 会被发现
│   └── utils_test.py         ✅ 会被发现
└── pytest.ini
```

## ⚙️ 配置文件

### pytest.ini

```ini
[tool:pytest]
# 测试路径
testpaths = tests

# 测试文件模式
python_files = test_*.py

# 测试函数模式
python_functions = test_*

# Python 路径
pythonpath = .

# 运行选项
addopts =
    -v
    --tb=short
    --cov=app
    --cov-report=term-missing

# 最小版本
minversion = 6.0

# 测试标记
markers =
    unit: 单元测试
    integration: 集成测试
    slow: 慢速测试
```

### pyproject.toml（现代方式）

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py"]
python_functions = ["test_*"]
addopts = [
    "-v",
    "--cov=app",
    "--cov-report=term-missing"
]
markers = [
    "unit: 单元测试",
    "integration: 集成测试"
]
```

## 🏷️ 测试标记（Markers）

```python
import pytest

# 跳过测试
@pytest.mark.skip(reason="功能未实现")
def test_future_feature():
    pass

# 条件跳过
@pytest.mark.skipif(sys.version_info < (3, 8), reason="需要 Python 3.8+")
def test_new_feature():
    pass

# 期望失败
@pytest.mark.xfail(reason="已知 bug")
def test_buggy_feature():
    assert False

# 自定义标记
@pytest.mark.slow
def test_heavy_computation():
    # 耗时测试
    pass

@pytest.mark.unit
def test_simple_function():
    # 单元测试
    pass
```

### 运行特定标记的测试

```bash
# 只运行单元测试
pytest -m unit

# 只运行非慢速测试
pytest -m "not slow"

# 运行单元测试或集成测试
pytest -m "unit or integration"
```

## 🔄 测试生命周期

```python
class TestLifecycle:
    def setup_method(self):
        """每个测试方法前执行"""
        print("🔧 设置测试")

    def teardown_method(self):
        """每个测试方法后执行"""
        print("🧹 清理测试")

    @classmethod
    def setup_class(cls):
        """整个测试类开始前执行一次"""
        print("🚀 设置测试类")

    @classmethod
    def teardown_class(cls):
        """整个测试类结束后执行一次"""
        print("🏁 清理测试类")

    def test_example_1(self):
        print("📝 执行测试 1")
        assert True

    def test_example_2(self):
        print("📝 执行测试 2")
        assert True
```

执行顺序：
```
🚀 设置测试类
🔧 设置测试        # test_example_1
📝 执行测试 1
🧹 清理测试
🔧 设置测试        # test_example_2
📝 执行测试 2
🧹 清理测试
🏁 清理测试类
```

## 💡 最佳实践

### 1. 测试命名
```python
# ✅ 好的命名：描述行为和预期
def test_user_creation_with_valid_data_should_succeed():
    pass

def test_user_login_with_invalid_password_should_fail():
    pass

# ❌ 不好的命名：不够描述性
def test_user():
    pass

def test_login():
    pass
```

### 2. 测试独立性
```python
# ✅ 每个测试独立
def test_user_creation():
    user = User(username="test")
    assert user.username == "test"

def test_user_update():
    user = User(username="original")
    user.username = "updated"
    assert user.username == "updated"

# ❌ 测试间有依赖
global_user = None

def test_create_user():
    global global_user
    global_user = User(username="test")

def test_update_user():  # 依赖上个测试
    global_user.username = "updated"
    assert global_user.username == "updated"
```

### 3. 单一职责
```python
# ✅ 每个测试只验证一个行为
def test_user_creation():
    user = User(username="test", email="test@example.com")
    assert user.username == "test"

def test_user_email_validation():
    user = User(username="test", email="test@example.com")
    assert user.email == "test@example.com"

# ❌ 一个测试验证多个行为
def test_user_everything():
    user = User(username="test", email="test@example.com")
    assert user.username == "test"
    assert user.email == "test@example.com"
    user.activate()
    assert user.is_active
    # 太多验证在一个测试中
```

## 🎯 小结

Pytest 的核心理念：
1. **简洁性**：用最简单的方式写测试
2. **自动化**：自动发现和运行测试
3. **可扩展性**：丰富的插件和配置选项
4. **清晰性**：清楚的错误报告和测试输出

下一步学习：[Pytest Fixtures 深入指南](./02-pytest-fixtures详解.md)