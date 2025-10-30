# GET users/me/notifications：分页查询，支持 is_read 过滤，返回聚合后的通知列表。

from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_current_active_user
from app.core.pagination import PaginatedResponse, PaginationParams
from app.crud import notification as notification_crud
from app.db.database import get_db
from app.models.user import User
from app.schemas.notification import (
    NotificationResponse,
)

router = APIRouter()


# ============================= 查询当前用户通知列表 ===========================
@router.get("/me/notifications", response_model=PaginatedResponse[NotificationResponse])
def get_current_user_notifications(
    pagination_params: PaginationParams = Depends(),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    *,
    is_read: bool | None = None,
) -> PaginatedResponse[NotificationResponse]:
    """获取我的通知列表（分页、过滤已读/未读）

    **权限**: 需要登录

    **查询参数**:
    - pagination_params: 分页参数
    - is_read: 是否已读（可选）

    **返回**:
    - PaginatedResponse[NotificationResponse]: 通知列表

    **示例**:
        GET /api/v1/users/me/notifications?is_read=false&page=1&size=20

    """
    items, total = notification_crud.get_notifications(
        db,
        user_id=current_user.id,
        pagination_params=pagination_params,
        is_read=is_read,
    )

    response = PaginatedResponse.create(
        items=items, total=total, params=pagination_params
    )

    return response


# ============================= 获取未读通知数量 ===========================
@router.get("/me/notifications/unread-count", response_model=int)
def get_unread_count(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> int:
    """获取未读通知数量

    **权限**: 需要登录
    """
    return notification_crud.get_unread_count(db, current_user.id)


# ============================= 标记全部通知为已读 ===========================
@router.patch("/me/notifications/mark-all-read")
def mark_all_as_read(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> int:
    """标记全部通知为已读

    **权限**: 需要登录

    **返回**:
    - int: 标记的通知数量

    **示例**:
        PATCH /api/v1/users/me/notifications/mark-all-read
    """
    return notification_crud.mark_all_as_read(db, current_user.id)


# ============================= 标记单条通知为已读 ===========================
@router.patch(
    "/me/notifications/{notification_id:uuid}", response_model=NotificationResponse
)
def mark_as_read(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> NotificationResponse:
    """标记单条通知为已读

    **权限**: 需要登录

    **路径参数**:
    - notification_id: 通知ID，
    - ⚠️ {notification_id:uuid} 可以在请求到达你的业务逻辑之前，
    就完成对路径参数的格式验证和类型转换

    **返回**:
    - NotificationResponse: 通知响应

    **示例**:
        PATCH /api/v1/users/me/notifications/{{notification_id}}
    """
    notification = notification_crud.mark_as_read(db, notification_id, current_user.id)

    return notification  # type: ignore


# ============================= 删除单条通知 ===========================
@router.delete(
    "/me/notifications/{notification_id}",
    status_code=status.HTTP_204_NO_CONTENT,
)
def delete_notification(
    notification_id: UUID,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
) -> None:
    """删除单条通知（通常用于“清理通知”场景）

    **权限**: 需要登录

    **路径参数**:
    - notification_id: 通知ID

    **返回**:
    - 204: 删除成功（无响应体）

    **示例**:
        DELETE /api/v1/users/me/notifications/{{notification_id}}
    """
    notification_crud.delete_notification(db, notification_id, current_user.id)

    return None
