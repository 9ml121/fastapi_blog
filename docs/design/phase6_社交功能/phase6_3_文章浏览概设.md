# Phase 6.3 文章浏览统计 - MVP概设

## 📋 功能概述

**目标**：为作者提供基础的文章浏览统计功能，展示文章的阅读情况和用户互动数据。

**MVP原则**：聚焦核心价值，快速验证需求，为后续功能扩展奠定基础。

---

## 🎯 MVP核心功能

### 1. 核心用户故事
- 作为作者，我希望看到文章的总浏览次数
- 作为作者，我希望记录用户的浏览行为
- 作为管理员，我希望查看热门文章的浏览数据

### 2. MVP功能范围
```
✅ 必须功能（MVP核心）：
- 浏览记录创建（支持匿名用户）
- 文章浏览计数更新
- 基础浏览统计查询

❌ 暂不包含（后续迭代）：
- 复杂的防刷机制
- 浏览行为深度分析
- 实时统计面板
- 地理分布分析
- 设备统计
```

---

## 🏗️ 技术架构设计

### 数据模型层

#### 1. PostView 模型（已存在）
```python
class PostView(Base):
    """文章浏览记录模型"""

    # 核心字段
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    post_id: Mapped[UUID] = mapped_column(ForeignKey("posts.id", ondelete="CASCADE"))
    user_id: Mapped[UUID | None] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"))

    # 访问信息
    ip_address: Mapped[str | None] = mapped_column(String(45))  # IPv6兼容
    user_agent: Mapped[str | None] = mapped_column(String(500))
    viewed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    # 关系
    post: Mapped["Post"] = relationship("Post", back_populates="post_views")
    user: Mapped[Optional["User"]] = relationship("User", back_populates="post_views")
```

#### 2. Post 模型扩展（已存在）
```python
class Post(Base):
    # 已有字段...
    view_count: Mapped[int] = mapped_column(Integer, default=0, comment="浏览次数统计")
```

### Schema 设计层

#### 1. 请求 Schema
```python
# app/schemas/post_view.py

class PostViewCreate(BaseModel):
    """创建浏览记录请求"""
    ip_address: str | None = Field(default=None, max_length=45)
    user_agent: str | None = Field(default=None, max_length=500)

    model_config = ConfigDict(extra="forbid")

class PostViewStatsQuery(BaseModel):
    """浏览统计查询参数"""
    days: int = Field(default=30, ge=1, le=365, description="统计天数")
    include_anonymous: bool = Field(default=True, description="包含匿名用户")

    model_config = ConfigDict(extra="forbid")
```

#### 2. 响应 Schema
```python
class PostViewStatusResponse(BaseModel):
    """浏览状态响应"""
    post_id: UUID
    view_count: int
    is_viewed: bool = Field(description="当前用户是否已浏览")
    last_viewed_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)

class PostViewStatsResponse(BaseModel):
    """浏览统计响应"""
    post_id: UUID
    total_views: int = Field(description="总浏览次数")
    unique_visitors: int = Field(description="独立访客数")
    logged_in_views: int = Field(description="登录用户浏览次数")
    anonymous_views: int = Field(description="匿名用户浏览次数")
    days_analyzed: int
    analysis_date: datetime

    model_config = ConfigDict(from_attributes=True)
```

### CRUD 层设计

#### 1. 核心函数
```python
# app/crud/post_view.py

def record_post_view(
    db: Session,
    *,
    post_id: UUID,
    user_id: UUID | None = None,
    ip_address: str | None = None,
    user_agent: str | None = None
) -> PostView:
    """记录文章浏览

    MVP简化版本：允许重复记录，不做复杂防刷

    Args:
        db: 数据库会话
        post_id: 文章ID
        user_id: 用户ID（可选，支持匿名）
        ip_address: IP地址
        user_agent: 用户代理

    Returns:
        PostView: 新创建的浏览记录

    Raises:
        ResourceNotFoundError: 文章不存在
        PermissionDeniedError: 无权限浏览（草稿文章）
    """

def get_post_view_stats(
    db: Session,
    *,
    post_id: UUID,
    days: int = 30,
    include_anonymous: bool = True
) -> dict:
    """获取文章浏览统计

    Args:
        db: 数据库会话
        post_id: 文章ID
        days: 统计天数
        include_anonymous: 是否包含匿名用户

    Returns:
        dict: 浏览统计数据
    """

def update_post_view_count(db: Session, post_id: UUID) -> int:
    """更新文章浏览计数

    Args:
        db: 数据库会话
        post_id: 文章ID

    Returns:
        int: 更新后的浏览计数
    """
```

### API 层设计

#### 1. 端点设计
```python
# app/api/v1/endpoints/post_views.py

@router.post("/{post_id}/view", response_model=PostViewStatusResponse)
async def record_view(
    post_id: UUID,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
    request: Request = None
):
    """记录文章浏览

    功能：
    - 支持登录用户和匿名用户
    - 自动获取IP和User-Agent
    - 更新文章浏览计数
    - 返回浏览状态
    """

@router.get("/{post_id}/view-stats", response_model=PostViewStatsResponse)
async def get_view_stats(
    post_id: UUID,
    query: PostViewStatsQuery = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """获取文章浏览统计

    功能：
    - 提供基础浏览统计
    - 支持时间范围过滤
    - 支持匿名用户过滤
    - 权限：只有文章作者和管理员可查看
    """
```

---

## 🧠 MVP实现策略

### 开发优先级

#### Phase 1: 核心功能（2-3天）
```
Day 1:
1. 完善PostView模型（如需要）
2. 实现record_post_view CRUD函数
3. 实现基础的POST /posts/{id}/view端点

Day 2:
4. 实现get_post_view_stats统计函数
5. 实现GET /posts/{id}/view-stats端点
6. 基础权限控制

Day 3:
7. 编写核心测试用例
8. 基础错误处理
9. 文档更新
```

#### Phase 2: 优化增强（后续迭代）
```
- 防刷机制
- 高级统计分析
- 性能优化
- 实时统计
```

### 技术决策

#### 1. 简化设计原则
```
✅ MVP简化点：
- 允许重复浏览记录
- 基础IP防刷（简单时间窗口）
- 基础统计维度（总浏览、独立访客）
- 简单的权限控制

❌ 暂不实现：
- 复杂的指纹识别
- 高级防刷算法
- 实时数据流
- 复杂的用户行为分析
```

#### 2. 数据一致性策略
```
浏览计数更新策略：
1. 同步更新：创建PostView记录时同步更新Post.view_count
2. 简单原子操作：使用数据库层面原子更新
3. 后续优化：异步更新、批量更新等
```

#### 3. 扩展性考虑
```
预留扩展点：
- Schema字段预留（session_id, referrer等）
- 函数参数预留（防刷参数、高级统计参数）
- 数据库索引预留（复合索引优化）
- API端点预留（查询参数扩展）
```

---

## 🧪 测试策略

### MVP测试覆盖

#### 1. 核心功能测试
```python
def test_record_view_logged_in_user():
    """测试登录用户浏览记录"""

def test_record_view_anonymous_user():
    """测试匿名用户浏览记录"""

def test_record_view_draft_post_permission():
    """测试草稿文章权限控制"""

def test_get_view_stats_basic():
    """测试基础浏览统计"""

def test_view_count_increment():
    """测试浏览计数递增"""
```

#### 2. 边界条件测试
```python
def test_nonexistent_post():
    """测试不存在文章"""

def test_empty_stats():
    """测试空统计数据"""

def test_permission_denied():
    """测试权限拒绝"""
```

#### 3. 数据一致性测试
```python
def test_view_count_accuracy():
    """测试浏览计数准确性"""

def test_concurrent_views():
    """测试并发浏览处理"""
```

### 测试数据策略
```python
# 测试数据四象限
正常数据：标准用户浏览文章
边界数据：空数据、最大数据量
异常数据：无效ID、权限错误
极端数据：大量并发访问
```

---

## 📈 性能考虑

### MVP性能策略

#### 1. 数据库优化
```sql
-- 基础索引
CREATE INDEX idx_post_view_post_id ON post_views(post_id);
CREATE INDEX idx_post_view_user_id ON post_views(user_id);
CREATE INDEX idx_post_view_viewed_at ON post_views(viewed_at);

-- 复合索引（后续优化）
CREATE INDEX idx_post_view_post_time ON post_views(post_id, viewed_at);
```

#### 2. 查询优化
```python
# 使用聚合函数
total_views = db.query(func.count(PostView.id)).filter(...).scalar()

# 使用DISTINCT去重
unique_visitors = db.query(func.count(func.distinct(PostView.user_id))).filter(...).scalar()
```

#### 3. 缓存策略（预留）
```python
# 预留缓存接口
@lru_cache(maxsize=100)
def get_cached_view_count(post_id: UUID) -> int:
    pass
```

---

## 🔄 迭代计划

### MVP验证指标
```
技术指标：
- API响应时间 < 200ms
- 数据库查询优化
- 测试覆盖率 > 85%

业务指标：
- 浏览记录创建成功率 > 99%
- 统计数据准确性
- 用户使用反馈
```

### 后续迭代方向
```
Phase 2: 防刷优化
- IP限制
- 用户行为分析
- 异常检测

Phase 3: 高级统计
- 实时数据
- 趋势分析
- 用户画像

Phase 4: 性能优化
- 缓存系统
- 异步处理
- 数据预聚合
```

---

## 📝 总结

**MVP核心价值**：
- 快速提供基础的浏览统计功能
- 验证用户对统计数据的需求
- 为后续功能迭代奠定基础

**技术亮点**：
- 支持匿名用户的灵活设计
- 简洁高效的统计实现
- 良好的扩展性架构

**风险控制**：
- 简化功能降低开发复杂度
- 基础防刷避免数据污染
- 完善测试保证质量

这个MVP设计聚焦核心价值，能够在短时间内交付可用功能，同时为后续扩展预留充分空间。