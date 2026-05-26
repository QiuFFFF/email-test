"""
快速发送单封测试邮件
用法:
  python quick_send.py                          # 使用默认配置
  python quick_send.py recipient@x.com          # 指定收件人
  python quick_send.py recipient@x.com "主题"   # 指定收件人和主题
"""

import sys
import time

try:
    import requests
except ImportError:
    print("需要安装 requests: pip install requests")
    exit(1)

from config import ZEABUR_CONFIG, RECIPIENT


def send(to=None, subject=None, body=None):
    to = to or RECIPIENT
    subject = subject or "Zeabur Email 快速测试"
    body = body or f"这是一封快速测试邮件。\n发送时间: {time.strftime('%Y-%m-%d %H:%M:%S')}"

    if ZEABUR_CONFIG["api_key"] == "YOUR_API_KEY":
        print("请先在 config.py 中填入你的 Zeabur API 密钥！")
        return

    resp = requests.post(
        f"{ZEABUR_CONFIG['api_url']}/emails",
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {ZEABUR_CONFIG['api_key']}",
        },
        json={
            "from": ZEABUR_CONFIG["from"],
            "to": [to],
            "subject": subject,
            "text": body,
        },
        timeout=15,
    )

    if resp.status_code in (200, 201, 202):
        data = resp.json()
        print(f"✓ 发送成功!")
        print(f"  {ZEABUR_CONFIG['from']} -> {to}")
        print(f"  邮件ID: {data.get('email_id', 'N/A')}")
        print(f"  状态: {data.get('status', 'N/A')}")
    else:
        print(f"✗ 发送失败! 状态码: {resp.status_code}")
        print(f"  响应: {resp.text}")


if __name__ == "__main__":
    args = sys.argv[1:]
    send(
        to=args[0] if len(args) > 0 else None,
        subject=args[1] if len(args) > 1 else None,
        body=args[2] if len(args) > 2 else None,
    )
