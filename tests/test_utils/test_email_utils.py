import asyncio

from app.core.config import settings
from app.core.email_utils import EmailUtils


async def main():
    print("准备发送邮件...")
    print(f"服务器: {settings.MAIL_SERVER}:{settings.MAIL_PORT}")
    print(f"发件人: {settings.MAIL_FROM}")

    # 收件人设为发件人自己，方便测试
    recipient = settings.MAIL_USERNAME

    try:
        await EmailUtils.send_email(
            email_to=recipient,
            subject="FastAPI Blog 邮件测试",
            template_name="email_template.html",
            template_data={
                "project_name": "FastAPI Blog",
                "username": "开发者",
                "verification_code": "888888",
                "valid_minutes": 10,
            },
        )
        print("\n✅ 邮件发送成功！请检查你的收件箱。")
    except Exception as e:
        print(f"\n❌ 邮件发送失败: {str(e)}")
        # 打印更详细的错误堆栈，如果有的话
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    if not settings.MAIL_PASSWORD.get_secret_value():
        print("❌ 错误: .env 中未配置 MAIL_PASSWORD")
    else:
        asyncio.run(main())
