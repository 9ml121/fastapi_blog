# 🌿: 采用命名空间导出

from . import (
    comment,
    follow,
    notification,
    post,
    post_favorite,
    post_like,
    post_view,
    tag,
    user,
)

__all__ = [
    "user",
    "post",
    "comment",
    "tag",
    "notification",
    "follow",
    "post_like",
    "post_view",
    "post_favorite",
]
