#!/bin/bash

# 终端通知脚本
# 用法: ./scripts/notify.sh "消息内容" [标题]

MESSAGE="${1:-任务完成}"
TITLE="${2:-FastAPI Blog}"

# 检测操作系统并使用相应的通知方式
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS - 使用 osascript
    osascript -e "display notification \"$MESSAGE\" with title \"$TITLE\""
    # 同时在终端输出，带颜色和声音
    echo -e "\n\033[1;32m✓ $TITLE: $MESSAGE\033[0m\n"
    # 播放系统提示音
    afplay /System/Library/Sounds/Glass.aiff 2>/dev/null || true
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux - 使用 notify-send（需要安装 libnotify-bin）
    if command -v notify-send &> /dev/null; then
        notify-send "$TITLE" "$MESSAGE"
    fi
    echo -e "\n\033[1;32m✓ $TITLE: $MESSAGE\033[0m\n"
    # Linux 提示音
    paplay /usr/share/sounds/alsa/Front_Left.wav 2>/dev/null || true
else
    # 其他系统 - 只显示文本通知
    echo -e "\n\033[1;32m✓ $TITLE: $MESSAGE\033[0m\n"
fi