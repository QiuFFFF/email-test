"""
测试 SMTP 桥接服务
先启动 server.py，再运行本脚本
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import time

# ─── 配置 ───
BRIDGE_HOST = "localhost"
BRIDGE_PORT = 2525
ZEABUR_API_KEY = "zs_your_api_key_here"  # 你的 Zeabur API Key
FROM_ADDR = "test@yourdomain.com"        # 已在 Zeabur 验证的域名
TO_ADDR = "recipient@example.com"


def test_plaintext():
    """测试纯文本邮件"""
    print("[1] 发送纯文本邮件...")
    msg = MIMEText(f"SMTP 桥接测试 - 纯文本\n时间: {time.strftime('%H:%M:%S')}", "plain", "utf-8")
    msg["Subject"] = "[桥接测试] 纯文本"
    msg["From"] = FROM_ADDR
    msg["To"] = TO_ADDR

    with smtplib.SMTP(BRIDGE_HOST, BRIDGE_PORT) as server:
        server.login("zeabur", ZEABUR_API_KEY)
        server.sendmail(FROM_ADDR, [TO_ADDR], msg.as_string())
    print("    ✓ 成功")


def test_html():
    """测试 HTML 邮件"""
    print("[2] 发送 HTML 邮件...")
    msg = MIMEMultipart("alternative")
    msg["Subject"] = "[桥接测试] HTML"
    msg["From"] = FROM_ADDR
    msg["To"] = TO_ADDR
    msg.attach(MIMEText("纯文本备用", "plain", "utf-8"))
    msg.attach(MIMEText("<h1>HTML 桥接测试</h1><p>通过 SMTP 桥接发送</p>", "html", "utf-8"))

    with smtplib.SMTP(BRIDGE_HOST, BRIDGE_PORT) as server:
        server.login("zeabur", ZEABUR_API_KEY)
        server.sendmail(FROM_ADDR, [TO_ADDR], msg.as_string())
    print("    ✓ 成功")


def test_no_auth():
    """测试无认证时是否正确拒绝"""
    print("[3] 测试无认证发送（应被拒绝）...")
    msg = MIMEText("不应该成功", "plain", "utf-8")
    msg["Subject"] = "no auth"
    msg["From"] = FROM_ADDR
    msg["To"] = TO_ADDR

    try:
        with smtplib.SMTP(BRIDGE_HOST, BRIDGE_PORT) as server:
            server.sendmail(FROM_ADDR, [TO_ADDR], msg.as_string())
        print("    ⚠ 未被拒绝（可能服务配置了固定 Key）")
    except smtplib.SMTPSenderRefused:
        print("    ✓ 正确拒绝")
    except Exception as e:
        print(f"    ✓ 已拒绝: {e}")


if __name__ == "__main__":
    print(f"测试 SMTP 桥接: {BRIDGE_HOST}:{BRIDGE_PORT}\n")
    test_plaintext()
    test_html()
    test_no_auth()
    print("\n全部完成!")
