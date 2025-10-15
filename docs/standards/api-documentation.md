# API 文档注释标准规范

## 📋 **概述**

本文档定义了 FastAPI 项目中 API 端点文档注释的统一标准，确保文档的一致性、可读性和专业性。

## 🎯 **核心原则**

1. **一致性**: 所有 API 端点使用相同的文档结构和格式
2. **简洁性**: 重点描述业务逻辑，避免实现细节
3. **实用性**: 提供清晰的参数说明和实际示例
4. **专业性**: 符合 OpenAPI 3.0 规范和行业最佳实践

## 📝 **标准格式**

### **基础模板**

```python
@router.method("/path", response_model=ResponseModel)
async def endpoint_name(
    param1: Type,
    param2: Type = Depends(),
) -> ResponseModel:
    """端点功能描述

    **权限**: 权限描述

    **路径参数**:
    - param1: 参数描述

    **查询参数**:
    - param2: 参数描述

    **请求体**:
    - RequestModel: 请求数据描述

    **返回**:
    - 200: 成功响应描述
    - 400: 错误响应描述

    **示例**:
        METHOD /api/v1/path
        {
            "key": "value"
        }
    """
```

## 📚 **章节规范**

### **1. 权限 (Permission)**

**格式**: `**权限**: 描述`

**示例**:

-   `**权限**: 公开访问，无需登录`
-   `**权限**: 需要登录且账户活跃`
-   `**权限**: 需要登录且是资源所有者`

### **2. 路径参数 (Path Parameters)**

**格式**: `**路径参数**:`

**示例**:

```python
**路径参数**:
- user_id: 用户的 UUID
- post_id: 文章的 UUID
```

### **3. 查询参数 (Query Parameters)**

**格式**: `**查询参数**:`

**示例**:

```python
**查询参数**:
- page: 页码（从1开始，默认1）
- size: 每页数量（1-100，默认20）
- sort: 排序字段（默认created_at）
- order: 排序方向（asc/desc，默认desc）
```

### **4. 请求体 (Request Body)**

**格式**: `**请求体**:`

**示例**:

```python
**请求体**:
- UserCreate: 用户创建数据（用户名、邮箱、密码等）
- PostUpdate: 文章更新数据（所有字段可选）
```

### **5. 返回 (Response)**

**格式**: `**返回**:`

**示例**:

```python
**返回**:
- 200: 操作成功
- 201: 资源创建成功
- 400: 请求数据无效
- 401: 未授权访问
- 403: 权限不足
- 404: 资源不存在
- 409: 资源冲突
- 422: 参数验证失败
```

### **6. 示例 (Examples)**

**格式**: `**示例**:`

**示例**:

```python
**示例**:
    GET /api/v1/users/123e4567-e89b-12d3-a456-426614174000
    POST /api/v1/posts/
    {
        "title": "文章标题",
        "content": "文章内容"
    }
```

## 🔧 **具体端点模板**

### **列表查询端点**

```python
@router.get("/", response_model=PaginatedResponse[ItemResponse])
async def get_items(
    params: PaginationParams = Depends(),
    filters: ItemFilters = Depends(),
    db: Session = Depends(get_db),
) -> PaginatedResponse[ItemResponse]:
    """获取{资源名称}列表（支持分页、排序、过滤）

    **权限**: {权限描述}

    **查询参数**:
    - page: 页码（从1开始，默认1）
    - size: 每页数量（1-100，默认20）
    - sort: 排序字段（默认created_at）
    - order: 排序方向（asc/desc，默认desc）
    {其他查询参数}

    **返回**:
    - 200: 分页的{资源名称}列表
    - 422: 参数验证失败

    **示例**:
        GET /api/v1/{resource}/?page=1&size=10
        GET /api/v1/{resource}/?filter_param=value
    """
```

### **详情查询端点**

```python
@router.get("/{item_id}", response_model=ItemResponse)
async def get_item(
    item_id: UUID,
    db: Session = Depends(get_db),
) -> ItemResponse:
    """获取{资源名称}详情

    **权限**: {权限描述}

    **路径参数**:
    - item_id: {资源名称}的 UUID

    **返回**:
    - 200: {资源名称}详情
    - 404: {资源名称}不存在

    **示例**:
        GET /api/v1/{resource}/123e4567-e89b-12d3-a456-426614174000
    """
```

### **创建端点**

```python
@router.post("/", response_model=ItemResponse, status_code=status.HTTP_201_CREATED)
async def create_item(
    item_in: ItemCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ItemResponse:
    """创建新{资源名称}

    **权限**: 需要登录且账户活跃

    **请求体**:
    - ItemCreate: {资源名称}创建数据

    **返回**:
    - 201: {资源名称}创建成功
    - 400: 请求数据无效
    - 409: {资源名称}已存在（如适用）

    **示例**:
        POST /api/v1/{resource}/
        {
            "name": "示例{资源名称}",
            "description": "描述"
        }
    """
```

### **更新端点**

```python
@router.patch("/{item_id}", response_model=ItemResponse)
async def update_item(
    item_id: UUID,
    item_in: ItemUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> ItemResponse:
    """更新{资源名称}（部分更新）

    **权限**: 需要登录且是{资源名称}所有者

    **路径参数**:
    - item_id: {资源名称}的 UUID

    **请求体**:
    - ItemUpdate: {资源名称}更新数据（所有字段可选）

    **返回**:
    - 200: 更新后的{资源名称}详情
    - 404: {资源名称}不存在
    - 403: 无权限修改此{资源名称}

    **示例**:
        PATCH /api/v1/{resource}/123e4567-e89b-12d3-a456-426614174000
        {
            "name": "更新后的名称"
        }
    """
```

### **删除端点**

```python
@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_item(
    item_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """删除{资源名称}

    **权限**: 需要登录且是{资源名称}所有者

    **路径参数**:
    - item_id: {资源名称}的 UUID

    **返回**:
    - 204: 删除成功（无响应体）
    - 404: {资源名称}不存在
    - 403: 无权限删除此{资源名称}

    **示例**:
        DELETE /api/v1/{resource}/123e4567-e89b-12d3-a456-426614174000
    """
```

## ✅ **检查清单**

在编写或审查 API 文档注释时，请确保：

-   [ ] 使用统一的章节格式（**权限**、**路径参数**等）
-   [ ] 权限描述简洁明确
-   [ ] 参数说明包含类型和默认值
-   [ ] 返回状态码覆盖主要场景
-   [ ] 示例代码真实可用
-   [ ] 避免实现细节，专注业务逻辑
-   [ ] 使用中文描述，保持一致性

## 🔗 **参考资源**

-   [FastAPI 官方文档](https://fastapi.tiangolo.com/)
-   [OpenAPI 3.0 规范](https://swagger.io/specification/)
-   [Django REST Framework 文档风格](https://www.django-rest-framework.org/)
-   [Spring Boot API 文档最佳实践](https://spring.io/guides/gs/rest-service/)

---

**最后更新**: 2025-01-09  
**版本**: 1.0  
**维护者**: FastAPI Blog 项目团队
