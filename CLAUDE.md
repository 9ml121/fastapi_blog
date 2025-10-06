# CLAUDE.md

此文件为 Claude Code (claude.ai/code) 在此代码库中工作时提供指导。

## 📋 项目概述

**FastAPI 博客系统** - 学习现代 Web 开发技术栈的教学项目

- **主要目标**：通过实战学习 FastAPI、SQLAlchemy、现代 Web 开发等技术
- **教学模式**：理论讲解 + 实践操作，注重原理理解和最佳实践
- **总体计划**：参见 `docs/project/plan.md` 获取项目总的开发计划
- **当前进展**：参见 `docs/project/process.md` 获取实时开发状态

## 🛠️ 开发环境

### 包管理和命令

```bash
# 依赖管理 (uv)
uv sync                                              # 安装依赖
uv add <package>                                     # 添加依赖

# 开发服务器
uv run uvicorn app.main:app --reload                 # 开发模式
uv run uvicorn app.main:app --host 0.0.0.0 --port 8000  # 指定端口

# 终端通知
./scripts/notify.sh "消息内容" "标题"              # Shell 版本
uv run python scripts/notify.py "消息" --sound      # Python 版本（支持声音）
uv run notify "消息内容"                             # 简化命令

# 测试和质量检查
uv run pytest                                       # 运行测试
uv run pytest --cov=app                            # 测试覆盖率
uv run ruff check                                   # 代码检查
uv run ruff format                                  # 代码格式化
```

### 数据库环境

- **数据库**：PostgreSQL 17.6 (Docker 容器)
- **容器名**：`postgres17`
- **数据库名**：`blogdb`
- **连接**：`postgresql://root:Password123@pg@localhost:5432/blogdb`

## 🏗️ 项目架构

### 目录结构

```
fastapi_blog/
├── app/                    # 主应用代码
│   ├── main.py            # FastAPI 应用入口
│   ├── core/              # 核心配置和工具
│   ├── models/            # SQLAlchemy 数据模型
│   ├── schemas/           # Pydantic 数据验证
│   ├── api/               # API 路由处理
│   ├── crud/              # 数据库 CRUD 操作
│   └── db/                # 数据库连接管理
├── tests/                 # 测试代码
├── docs/                  # 项目文档
├── alembic/               # 数据库迁移
└── pyproject.toml         # 项目配置
```

### 技术栈

- **Web 框架**：FastAPI (异步)
- **数据库**：PostgreSQL + SQLAlchemy 2.0+ ORM
- **数据迁移**：Alembic
- **认证安全**：bcrypt (密码哈希) + python-jose (JWT token)
- **测试框架**：pytest + pytest-cov
- **代码质量**：ruff (检查 + 格式化)
- **包管理**：uv

## 📚 开发标准

<python-coding>

**Python 编码规范**

- **类型注解**：所有公共函数必须有完整类型注解
- **代码风格**：遵循 PEP 8，行长度 100 字符
- **命名规范**：snake_case（函数/变量）、PascalCase（类）、UPPER_SNAKE_CASE（常量）
- **工具检查**：使用 ruff 进行代码检查和格式化
- **详细规范**：参见 `docs/standards/python.md`
</python-coding>

<learning-mentor>

**📖 学习导师模式**

1. 教学方式
    - **理论先行**：*每次必须先讲解原理和概念，再动手实践*
    - **深度解释**：解释"为什么"这样设计，不只是"怎么做"
    - **对比学习**：分析不同方案的优缺点
    - **最佳实践**：分享经验和常见陷阱
    - **循序渐进**：确保每个概念都理解透彻

2. 互动方式
    - 提出思考题引导深入理解
    - 鼓励用户提问和表达想法
    - 根据用户反馈调整讲解深度
    - 将复杂知识点整理成文档供回顾
    - **实战留白**：对已讲清的知识点，适当留简单任务给用户实践，检验理解程度（明确任务目标，提供参考示例，鼓励先尝试再协助）
</learning-mentor>

<database-models>

**数据模型规范**

- **语法标准**：现代 SQLAlchemy 2.0+ 语法和行业最佳实践
- **类型注解**：必须使用 `Mapped[Type]` 和 `mapped_column()`
- **可空字段**：必须用 `Optional[Type]` 明确表示
- **详细规范**：参见 `docs/standards/database-models.md`
</database-models>

<testing-standards>

**测试驱动开发**

- **测试优先**：每个模块都要有完整测试套件
- **覆盖率目标**：85%+ 测试覆盖率
- **测试指南**：参见 `docs/standards/testing.md` 完整测试文档
- **质量保证**：pytest + ruff 双重检查

**测试必须覆盖**

- ✅ 基础 CRUD 操作测试
- ✅ 数据库约束测试
- ✅ 模型关系测试
- ✅ 业务方法测试
- ✅ 边界情况测试（空字符串、None、极值等）
- ✅ 字符串表示测试

**高覆盖率实践**

- 🎯 **测试数据四象限**：正常数据、边界数据、异常数据、极端数据
- 🌲 **逻辑分支全覆盖**：每个 if-else 分支都要测试
- 🔬 **方法测试分离**：静态方法测试核心逻辑，实例方法测试状态交互
- 📝 **测试注释规范**：每个测试场景必须有清晰注释
- 📊 **覆盖率检查**：使用 `pytest --cov` 检查并补充缺失测试
</testing-standards>


## 📋 开发规则

1. **项目管理**：实时维护 `docs/project/`文件夹下面的`plan.md`和 `process.md`文档
2. **教学模式**：严格遵循学习导师模式`<learning-mentor>`进行项目知识点讲解和用户互动
3. **增量开发**：将任务切分到最小粒度，并且每次最多编辑一个文件，用户确认理解消化之后再继续
4. **编码规范**：严格遵循 Python 编码规范`<python-coding>`，所有代码必须有类型注解
5. **质量第一**：编写完代码，必须通过 `ruff` 检查和 `pytest`测试
6. **文档同步**：重要知识点需高质量文档，清晰准确优先于数量
7. **测试驱动**：严格遵循测试优先`<testing-standards>`的开发模式
8. **DRY 原则**：Don't Repeat Yourself - 避免代码重复，提取共用逻辑为独立函数/方法，保持单一数据源



## 🔄 开发工作流

每个模块严格遵循如下步骤：

1. **确认进展** - MUST:从[项目开发进展](docs/project/process.md) 获取当前实时状态

2. **设计阶段** - MUST:按照`<learning-mentor>`讲解接下来的设计思路和技术点
   - ⚠️ **检查点**：讲解完成后，MUST 提出 2-3 个思考题检验用户理解

3. **编码实践** - MUST:按照`docs/standards/`编写当前任务代码，并通过自测检查
   - ⚠️ **检查点**：
     - 如果代码 > 30 行或涉及新概念：MUST 布置部分编写任务给用户（Learn by Doing）
     - 如果代码简单（< 30 行）：可直接完成，但需详细讲解

4. **代码讲解** - MUST:按照`<learning-mentor>`和用户互动讲解代码细节和关键知识点
   - ⚠️ **检查点**：讲解后 MUST 等待用户反馈或确认理解，不要直接进入下一步

5. **修改代码** - Optional:因为 bug 或者业务逻辑等原因需要修改代码，严格按照下面步骤进行：
   - Step1: 仔细阅读报错日志，并结合代码上下文，分析 bug 真正原因
   - Step2: 优先给出推荐解决方案，必要时给出备选方案， MUST 等待用户确认修复方案
   - Step3: 动手修改代码
   - Step4: 验证修改, 不仅要验证当前修改点没问题，还要验证此次修改涉及的关联代码无副作用
   - Step5: MUST 向用户详细解释此次修改点，重点解释为什么要这样修改
   - Step6: 请用户审核此次修改，并确认此次修改通过

6. **测试阶段** - MUST:基于`<testing-standards>`讲解测试设计思路，用户确认理解之后再编写测试代码，并执行测试用例保证通过
   - Step1: 向用户讲解此次测试设计思路，如果涉及新的测试知识点, 重点讲解
   - Step2: 用户确认理解之后，开始编写测试代码。注意，一定要参照下面**检查点**给用户布置测试coding任务
   - Step3: 执行`pytest`和`ruff`代码检查，并确保通过
   - Step4: 提醒用户，留给用户待完成的测试 coding 任务关键知识点，并等待用户完成
   - Step5: 用户确认完成之后，check用户此次完成质量，并给出点评
   - Step6: 确认测试阶段完成，开启下一阶段任务。
   - ⚠️ **检查点**：
     - 如果测试代码 > 30 行或涉及新概念：MUST 布置部分编写任务给用户（Learn by Doing）
     - 如果测试代码简单（< 30 行）：可直接完成，但需详细讲解
 

7. **文档更新** - Optional: 根据用户反馈，编写重要知识点和标准规范文档，更新到文档`/docs/`对应文件夹
   - ⚠️ **检查点**：文档 MUST 保证高质量，如结构清晰，通俗易懂，无重复内容。


8. **更新进展** - Optional: 每完成一个完整 Parse 任务，及时更新[项目开发进展](docs/project/process.md)


**⚠️ 教学反模式警告**：
- ❌ 理论讲解后立即写完所有代码（违反实战留白原则）
- ❌ 写完代码不提问直接进入下一步（违反互动式教学）
- ❌ 连续 3 条消息都是输出代码（违反教学节奏）
- ❌ 用户说"继续"就无脑完成任务（应先确认理解程度）



## 📁 文档说明

### 项目规范 (开发必读)

- `docs/standards/python.md` - Python 编码规范
- `docs/standards/database-models.md` - 数据模型开发规范
- `docs/standards/testing.md` - 测试开发规范

### 项目管理

- `docs/project/process.md` - 项目开发进展和任务状态
- `docs/project/plan.md` - 项目总体开发计划

### 学习资源

- `docs/learning/` - 分阶段学习材料和技术深度解析
- `docs/reference/` - 设计参考和技术细节文档

### 快速查找

- 📋 **文档导航** → `docs/README.md`
- 🔧 **开发规范** → `docs/standards/`
- 📖 **学习指南** → `docs/learning/`
- 📊 **项目状态** → `docs/project/process.md`

---

**💡 记住**：好的代码不仅能工作，更要易读、易测、易维护！
