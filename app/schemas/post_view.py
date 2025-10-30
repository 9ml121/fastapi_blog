"""
PostView相关的Pydantic模型

用于文章浏览统计功能的请求验证和响应序列化
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PostViewCreate(BaseModel):
    """创建浏览记录请求模型

    用于记录文章浏览时的数据验证
    """

    session_id: str | None = Field(
        default=None, max_length=32, description="会话标识符（用于防刷）"
    )
    ip_address: str | None = Field(
        default=None, max_length=45, description="访问者IP地址（IPv4或IPv6）"
    )
    user_agent: str | None = Field(
        default=None, max_length=500, description="浏览器User-Agent信息"
    )
    skip_duplicate_check: bool = Field(default=False, description="是否跳过防刷检查")

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {
            "example": {
                "session_id": "abc123def456789012345678901234",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "skip_duplicate_check": False,
            }
        },
    }


class PostViewStatsQuery(BaseModel):
    """浏览统计查询参数模型

    用于获取文章浏览统计时的参数验证
    """

    days: int = Field(default=30, ge=1, description="统计天数（正数，支持任意时间段）")
    include_anonymous: bool = Field(default=True, description="是否包含匿名用户数据")

    model_config = {
        "extra": "forbid",
        "json_schema_extra": {"example": {"days": 30, "include_anonymous": True}},
    }


class PostViewStatusResponse(BaseModel):
    """浏览状态响应模型

    返回用户对文章的浏览状态和统计信息
    """

    post_id: UUID = Field(description="文章ID")
    is_viewed: bool = Field(description="当前用户是否已浏览此文章")
    view_count: int = Field(description="文章总浏览次数")
    last_viewed_at: datetime | None = Field(default=None, description="最近浏览时间")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "post_id": "123e4567-e89b-12d3-a456-426614174000",
                "is_viewed": True,
                "view_count": 42,
                "last_viewed_at": "2025-01-15T10:30:00Z",
            }
        },
    }


class PostViewStatsResponse(BaseModel):
    """浏览统计响应模型

    返回文章的详细浏览统计数据
    """

    post_id: UUID = Field(description="文章ID")
    total_views: int = Field(description="总浏览次数 (PV)")
    unique_visitors: int = Field(description="独立访客数 (UV)")
    logged_in_views: int = Field(description="登录用户浏览次数")
    anonymous_views: int = Field(description="匿名用户浏览次数")
    unique_logged_in_users: int = Field(description="独立登录用户数")
    days_analyzed: int = Field(description="统计天数")
    analysis_date: datetime = Field(description="统计分析日期")
    start_date: datetime = Field(description="统计开始日期")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "post_id": "123e4567-e89b-12d3-a456-426614174000",
                "total_views": 150,
                "unique_visitors": 85,
                "logged_in_views": 120,
                "anonymous_views": 30,
                "unique_logged_in_users": 45,
                "days_analyzed": 30,
                "analysis_date": "2025-01-15T12:00:00Z",
                "start_date": "2024-12-16T12:00:00Z",
            }
        },
    }


class PostViewResponse(BaseModel):
    """浏览记录响应模型

    返回单个浏览记录的详细信息
    """

    id: UUID = Field(description="浏览记录ID")
    post_id: UUID = Field(description="文章ID")
    user_id: UUID | None = Field(default=None, description="用户ID")
    session_id: str | None = Field(default=None, description="会话ID")
    ip_address: str | None = Field(default=None, description="IP地址")
    user_agent: str | None = Field(default=None, description="User-Agent")
    viewed_at: datetime = Field(description="浏览时间")

    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "987e6543-e21b-45d6-b789-123456789abc",
                "post_id": "123e4567-e89b-12d3-a456-426614174000",
                "user_id": "456e7890-f12c-34d5-e678-901234567890",
                "session_id": "abc123def456789012345678901234",
                "ip_address": "192.168.1.100",
                "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
                "viewed_at": "2025-01-15T10:30:00Z",
            }
        },
    }
