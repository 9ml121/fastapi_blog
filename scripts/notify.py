#!/usr/bin/env python3
"""
终端通知脚本 - Python 版本
支持 macOS, Linux, Windows 跨平台通知

用法:
    python scripts/notify.py "消息内容"
    python scripts/notify.py "消息内容" "标题"
    python scripts/notify.py "消息内容" "标题" --sound
"""

import argparse
import platform
import subprocess
from pathlib import Path


def send_notification(
    message: str, title: str = "FastAPI Blog", with_sound: bool = False
):
    """发送系统通知"""
    system = platform.system().lower()

    # 终端输出（带颜色）
    print(f"\n\033[1;32m✓ {title}: {message}\033[0m\n")

    try:
        if system == "darwin":  # macOS
            # 系统通知
            subprocess.run(
                [
                    "osascript",
                    "-e",
                    f'display notification "{message}" with title "{title}"',
                ],
                check=False,
            )

            # 播放声音
            if with_sound:
                subprocess.run(
                    ["afplay", "/System/Library/Sounds/Glass.aiff"], check=False
                )

        elif system == "linux":
            # Linux 通知
            if (
                subprocess.run(["which", "notify-send"], capture_output=True).returncode
                == 0
            ):
                subprocess.run(["notify-send", title, message], check=False)

            # Linux 声音
            if with_sound:
                sound_files = [
                    "/usr/share/sounds/alsa/Front_Left.wav",
                    "/usr/share/sounds/sound-icons/bell.wav",
                    "/usr/share/sounds/ubuntu/notifications/Blip.ogg",
                ]
                for sound_file in sound_files:
                    if Path(sound_file).exists():
                        subprocess.run(["paplay", sound_file], check=False)
                        break

        elif system == "windows":
            # Windows 通知
            try:
                import win10toast

                toaster = win10toast.ToastNotifier()
                toaster.show_toast(title, message, duration=3)
            except ImportError:
                print("提示: 在 Windows 上需要安装 win10toast: pip install win10toast")

    except Exception as e:
        print(f"通知发送失败: {e}")


def main():
    parser = argparse.ArgumentParser(description="发送终端通知")
    parser.add_argument("message", help="通知消息内容")
    parser.add_argument("title", nargs="?", default="FastAPI Blog", help="通知标题")
    parser.add_argument("--sound", action="store_true", help="播放提示音")

    args = parser.parse_args()

    send_notification(args.message, args.title, args.sound)


if __name__ == "__main__":
    main()
