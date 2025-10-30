# FastAPI 博客项目测试开发规范

## 🎯 测试目标与标准

### 覆盖率要求
- **最低要求**：85% 测试覆盖率
- **推荐目标**：90%+ 测试覆盖率
- **核心业务模块**：95%+ 测试覆盖率

### 测试四象限分类
每个功能模块必须用以下4类数据进行测试：

| 类型 | 说明 | 示例 | 测试意图 |
|-----|------|-----|---------|
| **正常数据** ✅ | 常见有效输入，验证基本功能 | `"Hello World"`, 有效用户数据 | 验证正常业务流程 |
| **边界数据** ⚠️ | 极限但有效的值 | `""`, `None`, 最大长度 | 验证边界条件处理 |
| **异常数据** ❌ | 预期失败的输入 | 重复唯一字段、违反约束 | 验证错误处理机制 |
| **极端数据** 🚀 | 压力测试场景 | 超长字符串、大量数据 | 验证系统稳定性 |

## 📝 测试注释规范（核心要求）

### 测试意图必须清晰

每个测试方法都必须包含详细的测试意图说明：

```python
def test_follow_user_success(
    self,
    client: TestClient,
    auth_headers: dict,
    sample_users: list[User],
):
    """✅ 正常数据：成功关注用户

    测试意图:
    1. 验证用户可以成功关注其他用户
    2. 验证返回的关注关系数据正确性
    3. 测试互相关注场景 (因为 sample_users[1] 已经关注了 sample_users[0])

    测试数据:
    - follower: sample_users[0] (原始用户，使用 auth_headers 登录)
    - target: sample_users[1] (zhangsan，已经关注了原始用户)

    业务规则验证:
    - 关注关系成功创建 (HTTP 201)
    - 返回数据包含 follower_id, followed_id, created_at
    """
```

### 数据来源必须明确

**规则**: 不允许有"魔法数据"或模糊的测试数据说明

```python
# ❌ 错误：模糊的数据说明
"""sample_users中 3 个用户都关注了 sample_user"""

# ✅ 正确：明确的数据来源说明
"""测试数据来源:
- 使用 conftest.py 中 sample_users fixture 的预设数据
- sample_users[0] (原始用户) 有3个预设的粉丝:
  * sample_users[1] (zhangsan)
  * sample_users[2] (lisi)
  * sample_users[3] (wangwu)

数据构建说明:
- 这3个关注关系在 conftest.py 第454-458行建立
- 不在测试中动态创建，使用现有的预设数据
- 确保分页测试基于真实的关注关系数据
"""
```

### 业务流程验证

对于复杂的业务场景，必须明确标注验证步骤：

```python
"""✅ 正常数据：完整的关注-取消关注工作流程

业务流程验证 (8个步骤):
1. 初始状态: 未关注 (is_following = False)
2. 执行关注: 成功创建关注关系 (HTTP 201)
3. 关注状态: 已关注 (is_following = True)
4. 粉丝统计: 目标用户粉丝数增加 (>= 1)
5. 粉丝列表: 目标用户出现在粉丝列表中
6. 关注列表: 关注关系出现在关注列表中
7. 取消关注: 成功删除关注关系 (HTTP 204)
8. 最终状态: 未关注 (is_following = False)

数据一致性检查:
- 关注状态查询与实际关系保持一致
- 粉丝数统计与实际粉丝列表保持一致
- 关注列表与粉丝列表的对称关系正确
"""
```

## 🏗️ 测试数据构建规范

### 优先使用 fixture 构建测试数据

**原则**: 复杂场景必须在 `conftest.py` 中构建 fixture，而不是在测试中动态创建

#### 1. 简单场景：在测试中动态创建
```python
def test_simple_case(self, client: TestClient):
    """✅ 正常数据：简单场景，可在测试中创建数据"""
    # 适合：单个对象、简单关系
    user = User(username="test", email="test@example.com")
```

#### 2. 复杂场景：在 conftest.py 中构建 fixture
```python
# conftest.py
@pytest.fixture
def sample_users(session: Session, sample_user: User) -> list[User]:
    """创建多个测试用户，包含 sample_user

    创建 3 个额外的测试用户，用于：
    - 测试用户 API 端点
    - 作为文章和评论的作者
    - 测试关注功能：3 个用户都关注 sample_user

    数据结构:
    - sample_users[0]: 原始用户 (被3个用户关注)
    - sample_users[1]: zhangsan (关注了原始用户)
    - sample_users[2]: lisi (关注了原始用户)
    - sample_users[3]: wangwu (关注了原始用户)
    """
    # 复杂的关联关系构建
    for template in user_templates:
        user = create_user(session, user_in=user_data)
        users.append(user)
        # 建立预设的关联关系
        follow_crud.follow_user(
            db=session,
            follower_id=user.id,
            followed_id=sample_user.id,
        )
    return users
```

#### 3. 业务专用 fixture
为特定业务场景创建专门的 fixture：

```python
@pytest.fixture
def follow_relationships(session: Session, sample_users: list[User]) -> dict[str, list[User]]:
    """构建复杂的关注关系网络，用于测试关注功能

    测试数据设计:
    - sample_users[0] (zhangsan): 被3个用户关注，关注2个用户
    - sample_users[1] (lisi): 被2个用户关注，关注2个用户
    - sample_users[2] (wangwu): 被1个用户关注，关注1个用户
    - sample_users[3] (原始sample_user): 被3个用户关注，不关注任何人

    Returns:
        dict: 包含关注关系映射的字典
    """
    # 构建复杂的业务关系网络
    # ... 复杂的数据构建逻辑
```

### Fixture 复用性原则

1. **通用性**: fixture 应该能在多个测试中复用
2. **独立性**: fixture 不应依赖特定的测试上下文
3. **文档化**: fixture 必须有清晰的数据结构说明

```python
# ✅ 好的 fixture 设计
@pytest.fixture
def sample_users(session: Session) -> list[User]:
    """创建标准测试用户集合，可用于多种测试场景"""
    # 通用的用户数据，可以被各种测试复用

# ❌ 避免的 fixture 设计
@pytest.fixture
def users_for_follow_test(session: Session) -> list[User]:
    """专门用于关注测试的用户集合"""  # 太具体，不便于复用
```

## 🧪 业务场景覆盖要求

### API 端点测试必须覆盖

每个 API 端点必须测试以下场景：

```python
class TestFollowUser:
    """测试关注用户功能

    必须覆盖的场景:
    1. ✅ 正常数据：成功关注
    2. ❌ 异常数据：自我关注
    3. ❌ 边界数据：重复关注
    4. ❌ 异常数据：关注不存在用户
    5. ❌ 异常数据：未授权访问
    """
```

### 业务规则验证

每个业务规则都要有对应的测试：

```python
# 关注功能的业务规则
- 用户不能关注自己
- 不能重复关注同一用户
- 取消关注必须有关注关系存在
- 关注关系删除后相关统计数据要更新

# 每个规则都要有对应的测试用例
def test_cannot_follow_self() -> ...
def test_cannot_follow_twice() -> ...
def test_unfollow_nonexistent_relation() -> ...
```

### 数据一致性验证

复杂操作必须验证数据一致性：

```python
def test_follow_unfollow_complete_workflow(self):
    """验证完整业务流程的数据一致性"""

    # 操作前验证状态
    # 执行操作
    # 操作后验证状态变化
    # 验证多个相关端点的数据一致性
```

## 📊 代码质量要求

### 类型注解完整
```python
# ✅ 正确：完整的类型注解
def test_follow_user_success(
    self,
    client: TestClient,
    auth_headers: dict,
    sample_users: list[User],
):
    # 参数有类型注解，IDE有智能提示
```

### 测试分组合理
```python
# 按功能分组，每个类测试一个完整的功能模块
class TestFollowUser:      # 关注功能
class TestUnfollowUser:    # 取消关注功能
class TestGetFollowers:     # 获取粉丝列表
class TestGetFollowing:     # 获取关注列表
```

### 命名规范清晰
```python
# ✅ 清晰的命名
test_follow_user_success           # 测试意图明确
test_get_followers_pagination      # 包含测试场景
test_follow_user_self              # 包含业务规则

# ❌ 模糊的命名
test_follow_1                      # 不明确
test_api_endpoint                  # 太泛化
```

## ✅ 质量检查流程

### 1. 代码质量检查
```bash
uv run ruff check tests/            # 代码风格检查
uv run mypy tests/                 # 类型检查
```

### 2. 测试执行检查
```bash
uv run pytest tests/test_api/test_follows.py -v  # 运行特定测试
uv run pytest --cov=app --cov-report=term-missing  # 覆盖率检查
```

### 3. 测试审查清单
- [ ] 每个测试都有清晰的测试意图说明
- [ ] 测试数据来源明确，无"魔法数据"
- [ ] 四象限测试数据覆盖完整
- [ ] 业务规则验证充分
- [ ] 数据一致性检查到位
- [ ] 类型注解完整
- [ ] 命名规范合理

---

**💡 核心原则**: 好的测试不仅是验证功能正确，更是业务需求的详细说明书和维护变更的安全网。