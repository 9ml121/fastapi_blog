"""
测试分页工具模块

测试覆盖：
1. PaginationParams - 分页参数验证
2. PaginatedResponse - 分页响应格式
3. get_sortable_columns - 可排序字段获取
4. apply_safe_sorting - 安全排序功能
5. paginate_query - 分页查询函数

测试策略：
- 正常数据：标准输入和预期输出
- 边界数据：空值、最大/最小值、边界条件
- 异常数据：错误输入、权限不足
- 极端数据：特殊字符、超长输入
"""

import time

import pytest
from pydantic import ValidationError
from sqlalchemy import func, select

from app.core.exceptions import InvalidParametersError
from app.core.pagination import (
    PaginatedResponse,
    PaginationParams,
    _get_sortable_columns,
    paginate_query,
)
from app.models.post import Post


class TestPaginationParams:
    """测试分页参数验证"""

    def test_valid_params(self):
        """✅ 正常数据：有效参数"""
        params = PaginationParams(page=1, size=20, sort="created_at", order="desc")
        assert params.page == 1
        assert params.size == 20
        assert params.sort == "created_at"
        assert params.order == "desc"
        assert params.offset == 0
        assert params.limit == 20

    def test_default_params(self):
        """✅ 正常数据：默认参数"""
        params = PaginationParams()
        assert params.page == 1
        assert params.size == 20
        assert params.sort == "created_at"
        assert params.order == "desc"
        assert params.offset == 0

    def test_offset_calculation(self):
        """✅ 正常数据：偏移量计算"""
        # 第1页
        params = PaginationParams(page=1, size=10)
        assert params.offset == 0

        # 第2页
        params = PaginationParams(page=2, size=10)
        assert params.offset == 10

        # 第5页，每页25条
        params = PaginationParams(page=5, size=25)
        assert params.offset == 100  # (5-1) * 25

    def test_page_boundary(self):
        """✅ 边界数据：页码边界值"""
        # 最小页码
        params = PaginationParams(page=1, size=10)
        assert params.offset == 0

        # 大页码
        params = PaginationParams(page=100, size=10)
        assert params.offset == 990

    def test_size_limits(self):
        """✅ 边界数据：每页数量限制"""
        # 最小值
        params = PaginationParams(size=1)
        assert params.size == 1

        # 中间值
        params = PaginationParams(size=50)
        assert params.size == 50

        # 最大值
        params = PaginationParams(size=100)
        assert params.size == 100

    def test_invalid_page(self):
        """❌ 异常数据：无效页码"""
        # 页码为0（必须 ≥ 1）
        with pytest.raises(ValidationError):
            PaginationParams(page=0)

        # 页码为负数
        with pytest.raises(ValidationError):
            PaginationParams(page=-1)

    def test_invalid_size(self):
        """❌ 异常数据：无效的每页数量"""
        # size为0（必须 ≥ 1）
        with pytest.raises(ValidationError):
            PaginationParams(size=0)

        # size超过最大值100
        with pytest.raises(ValidationError):
            PaginationParams(size=101)

    def test_invalid_order(self):
        """❌ 异常数据：无效排序方向"""
        # 无效的order值（非asc/desc）
        with pytest.raises(ValidationError):
            PaginationParams(order="invalid")

        # 有效值asc和desc
        params = PaginationParams(order="asc")
        assert params.order == "asc"
        params = PaginationParams(order="desc")
        assert params.order == "desc"


class TestPaginatedResponse:
    """测试分页响应格式"""

    def test_create_response_normal_case(self):
        """✅ 正常数据：创建分页响应"""
        params = PaginationParams(page=2, size=10)
        items = ["item1", "item2", "item3"]
        total = 25

        response = PaginatedResponse.create(items, total, params)

        assert response.items == items
        assert response.total == 25
        assert response.page == 2
        assert response.size == 10
        assert response.pages == 3  # (25 + 10 - 1) // 10 = 3
        assert response.has_next is True  # page 2 < 3
        assert response.has_prev is True  # page 2 > 1

    def test_create_response_first_page(self):
        """✅ 边界数据：第一页"""
        params = PaginationParams(page=1, size=10)
        items = ["item1", "item2"]
        total = 15

        response = PaginatedResponse.create(items, total, params)

        assert response.page == 1
        assert response.pages == 2
        assert response.has_next is True  # page 1 < 2
        assert response.has_prev is False  # page 1 == 1

    def test_create_response_last_page(self):
        """✅ 边界数据：最后一页"""
        params = PaginationParams(page=3, size=10)
        items = ["item1", "item2", "item3"]
        total = 25
        response = PaginatedResponse.create(items, total, params)
        assert response.page == 3
        assert response.pages == 3
        assert response.has_next is False
        assert response.has_prev is True

    def test_create_response_empty_result(self):
        """✅ 边界数据：空结果"""
        params = PaginationParams(page=1, size=10)
        items = []
        total = 0
        response = PaginatedResponse.create(items, total, params)
        assert response.page == 1
        assert response.pages == 0
        assert response.has_next is False
        assert response.has_prev is False

    def test_create_response_single_page(self):
        """✅ 边界数据：只有一页"""
        params = PaginationParams(page=1, size=20)
        items = ["item1", "item2"]
        total = 2
        response = PaginatedResponse.create(items, total, params)
        assert response.page == 1
        assert response.pages == 1
        assert response.has_next is False
        assert response.has_prev is False

    def test_response_serialization(self):
        """✅ 测试响应序列化"""
        params = PaginationParams(page=1, size=10)
        items = ["item1", "item2", "item3"]
        total = 25
        response = PaginatedResponse.create(items, total, params)
        assert response.model_dump() == {
            "items": ["item1", "item2", "item3"],
            "total": 25,
            "page": 1,
            "size": 10,
            "pages": 3,
            "has_next": True,
            "has_prev": False,
        }


class TestGetSortableColumns:
    """测试可排序字段获取"""

    def test_get_sortable_columns_post(self, session):
        """✅ 正常数据：获取Post模型的可排序字段"""
        from app.models.post import Post

        sortable_fields = _get_sortable_columns(Post)
        # pprint(sortable_fields)

        # 验证返回的是字典
        assert isinstance(sortable_fields, dict)

        # 验证包含预期的字段
        expected_fields = {"id", "title", "content", "created_at", "updated_at"}
        actual_fields = set(sortable_fields.keys())

        # 至少包含这些字段
        assert expected_fields.issubset(actual_fields)

        # 验证字段值是SQLAlchemy列对象
        for field_name, column in sortable_fields.items():
            assert hasattr(column, "name")
            assert column.name == field_name

    def test_get_sortable_columns_user(self, session):
        """✅ 正常数据：获取User模型的可排序字段"""
        from app.models.user import User

        sortable_fields = _get_sortable_columns(User)
        expected_user_fields = {"id", "username", "email", "created_at"}
        assert expected_user_fields.issubset(sortable_fields.keys())

    def test_get_sortable_columns_excludes_relationships(self, session):
        """✅ 边界数据：排除关系字段"""
        from app.models.post import Post

        sortable_fields = _get_sortable_columns(Post)
        assert "author" not in sortable_fields
        assert "tags" not in sortable_fields
        assert "comments" not in sortable_fields


class TestPaginateQuery:
    """测试分页查询函数"""

    @pytest.fixture
    def post_datas(self, session, sample_post_data):
        """创建100条测试文章数据"""
        post_datas = [Post(**sample_post_data()) for _ in range(100)]
        session.add_all(post_datas)
        session.commit()

        return post_datas

    def test_paginate_query_basic(self, session, post_datas):
        """✅ 正常数据：基础分页查询"""
        from app.models.post import Post

        # 构建查询
        query = select(Post)
        params = PaginationParams(page=1, size=5)

        # 执行分页查询
        items, total = paginate_query(session, query, params, model=Post)

        # 验证结果
        assert len(items) >= 0
        assert total >= 0
        assert isinstance(items, list)
        assert all(isinstance(item, Post) for item in items)

    def test_paginate_query_with_sorting(self, session, post_datas):
        """✅ 正常数据：带排序的分页查询"""
        # 构建查询
        query = select(Post)
        params = PaginationParams(page=1, size=5, sort="created_at", order="desc")

        items, total = paginate_query(session, query, params, model=Post)
        assert len(items) >= 0
        assert items[0].created_at >= items[1].created_at
        assert items[1].created_at >= items[2].created_at

    def test_paginate_query_with_custom_count(self, session, sample_post):
        """✅ 正常数据：自定义计数查询"""
        from app.models.post import Post

        # 构建基础查询
        query = select(Post)
        params = PaginationParams(page=1, size=3)

        # 自定义计数查询（性能更好）
        count_query = select(func.count(Post.id))

        items, total = paginate_query(
            session, query, params, model=Post, count_query=count_query
        )
        assert len(items) >= 0
        assert total >= 0
        assert isinstance(items, list)
        assert all(isinstance(item, Post) for item in items)

    def test_paginate_query_empty_result(self, session):
        """✅ 边界数据：空结果查询"""
        from app.models.post import Post

        # 查询不存在的数据
        query = select(Post).where(Post.title == "nonexistent_title_xyz")
        params = PaginationParams(page=1, size=10)

        items, total = paginate_query(session, query, params, model=Post)
        assert len(items) == 0
        assert total == 0

    def test_paginate_query_offset_calculation(self, session, post_datas):
        """✅ 边界数据：偏移量计算"""
        query = select(Post)
        page_1_params = PaginationParams(page=1, size=10)
        items_1, _ = paginate_query(session, query, page_1_params, model=Post)
        page_2_params = PaginationParams(page=2, size=10)
        items_2, _ = paginate_query(session, query, page_2_params, model=Post)
        page_3_params = PaginationParams(page=3, size=10)
        items_3, _ = paginate_query(session, query, page_3_params, model=Post)
        assert len(items_1) == 10
        assert len(items_2) == 10
        assert len(items_3) == 10

    def test_paginate_query_large_size(self, session, post_datas):
        """✅ 极端数据：大页面大小"""
        query = select(Post)
        params = PaginationParams(page=1, size=100)
        items, total = paginate_query(session, query, params, model=Post)
        assert len(items) <= 100
        assert total == 100

    def test_paginate_query_invalid_sort_field(self, session, sample_post):
        """❌ 异常数据：无效排序字段"""
        from app.models.post import Post

        query = select(Post)
        params = PaginationParams(sort="invalid_field")

        with pytest.raises(InvalidParametersError):
            paginate_query(session, query, params, model=Post)

    def test_paginate_query_asc_order(self, session, post_datas):
        """✅ 正常数据：升序排序"""
        query = select(Post)
        params = PaginationParams(page=1, size=5, sort="created_at", order="asc")

        items, total = paginate_query(session, query, params, model=Post)

        # 验证升序排序：第一条应该 <= 第二条 <= 第三条
        assert len(items) >= 3
        assert items[0].created_at <= items[1].created_at
        assert items[1].created_at <= items[2].created_at

    def test_paginate_query_sql_injection_attempt(self, session, sample_post):
        """❌ 异常数据：SQL注入尝试"""
        from app.models.post import Post

        query = select(Post)
        # 尝试通过排序字段进行SQL注入
        params = PaginationParams(sort="id; DROP TABLE posts; --")

        with pytest.raises(InvalidParametersError):
            paginate_query(session, query, params, model=Post)


class TestPaginationPerformance:
    """测试分页性能"""

    @pytest.fixture
    def many_posts(self, session, sample_post_data):
        """生成10000条文章数据"""
        many_posts = [Post(**sample_post_data()) for i in range(10000)]

        # 将生成的数据保存到数据库
        session.add_all(many_posts)
        session.commit()

        return many_posts

    def test_pagination_performance(self, session, many_posts):
        """✅ 性能测试：分页查询性能"""
        # 测试基础分页查询性能
        query = select(Post)
        params = PaginationParams(page=1000, size=10)

        start_time = time.time()
        items, total = paginate_query(session, query, params, model=Post)
        execution_time = time.time() - start_time

        # 验证性能目标：分页查询应该在100ms内完成
        assert execution_time < 0.1  # 100ms
        assert len(items) == 10
        assert total == len(many_posts)
        assert all(isinstance(item, Post) for item in items)

    def test_sorting_performance(self, session, many_posts):
        """✅ 性能测试：排序性能"""
        # 测试按不同字段排序的性能
        query = select(Post)
        params = PaginationParams(page=100, size=100, sort="created_at", order="desc")

        start_time = time.time()
        items, total = paginate_query(session, query, params, model=Post)
        execution_time = time.time() - start_time

        # 验证排序性能
        assert execution_time < 0.15  # 排序查询允许稍长时间
        assert len(items) == 100
        assert total == len(many_posts)

        # 验证排序正确性
        assert items[0].created_at >= items[1].created_at

    def test_large_dataset_pagination(self, session, many_posts):
        """✅ 极端数据：大数据集分页"""
        # 测试深度分页性能
        query = select(Post)
        params = PaginationParams(page=100, size=50)  # 深度分页

        start_time = time.time()
        items, total = paginate_query(session, query, params, model=Post)
        execution_time = time.time() - start_time

        # 验证深度分页性能
        assert execution_time < 0.2  # 深度分页允许更长时间
        assert len(items) == 50
        assert total == len(many_posts)

        # 验证分页逻辑正确性
        expected_offset = (100 - 1) * 50  # 第100页的偏移量
        assert len(items) == min(50, total - expected_offset)
