"""
SMTP 邮件发送测试套件
测试项目：连接、认证、纯文本、HTML、附件、大邮件
"""

import smtplib
import ssl
import socket
import time
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from config import SMTP_CONFIG, SENDER, RECIPIENT


def get_smtp_connection():
    """建立 SMTP 连接并返回"""
    if SMTP_CONFIG["use_ssl"]:
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(
            SMTP_CONFIG["host"], SMTP_CONFIG["port"], context=context, timeout=10
        )
    else:
        server = smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"], timeout=10)
        if SMTP_CONFIG["use_tls"]:
            context = ssl.create_default_context()
            server.starttls(context=context)

    if SMTP_CONFIG["username"] and SMTP_CONFIG["password"]:
        server.login(SMTP_CONFIG["username"], SMTP_CONFIG["password"])

    return server


def run_test(name, func):
    """运行单个测试并打印结果"""
    print(f"\n{'='*60}")
    print(f"测试: {name}")
    print(f"{'='*60}")
    start = time.time()
    try:
        func()
        elapsed = time.time() - start
        print(f"✓ 通过 ({elapsed:.2f}s)")
        return True
    except Exception as e:
        elapsed = time.time() - start
        print(f"✗ 失败 ({elapsed:.2f}s)")
        print(f"  错误: {type(e).__name__}: {e}")
        return False


# ─── 测试 1: 端口连通性 ───

def test_port_connectivity():
    """测试 SMTP 端口是否可达"""
    host = SMTP_CONFIG["host"]
    port = SMTP_CONFIG["port"]
    print(f"  连接 {host}:{port} ...")
    sock = socket.create_connection((host, port), timeout=10)
    banner = sock.recv(1024).decode("utf-8", errors="replace").strip()
    print(f"  服务器响应: {banner}")
    sock.close()
    assert banner.startswith("220"), f"期望 220 响应，收到: {banner}"


# ─── 测试 2: EHLO 握手 ───

def test_ehlo():
    """测试 EHLO 握手，列出服务器支持的扩展"""
    server = smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"], timeout=10)
    code, msg = server.ehlo()
    print(f"  EHLO 响应码: {code}")
    extensions = msg.decode("utf-8", errors="replace").split("\n")
    print(f"  支持的扩展:")
    for ext in extensions[1:]:
        print(f"    - {ext.strip()}")
    server.quit()
    assert code == 250, f"EHLO 失败，响应码: {code}"


# ─── 测试 3: TLS/SSL 加密 ───

def test_tls():
    """测试 TLS 加密连接"""
    if SMTP_CONFIG["use_ssl"]:
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(
            SMTP_CONFIG["host"], SMTP_CONFIG["port"], context=context, timeout=10
        )
        cipher = server.sock.cipher()
        print(f"  SSL 连接成功")
    elif SMTP_CONFIG["use_tls"]:
        server = smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"], timeout=10)
        context = ssl.create_default_context()
        server.starttls(context=context)
        cipher = server.sock.cipher()
        print(f"  STARTTLS 升级成功")
    else:
        print(f"  跳过: 未启用 TLS/SSL")
        server = smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"], timeout=10)
        server.quit()
        return

    print(f"  加密协议: {cipher[1]}")
    print(f"  密码套件: {cipher[0]}")
    print(f"  密钥长度: {cipher[2]} bits")
    server.quit()


# ─── 测试 4: 用户认证 ───

def test_auth():
    """测试 SMTP 用户名密码认证"""
    if not SMTP_CONFIG["username"]:
        print("  跳过: 未配置用户名")
        return

    if SMTP_CONFIG["use_ssl"]:
        context = ssl.create_default_context()
        server = smtplib.SMTP_SSL(
            SMTP_CONFIG["host"], SMTP_CONFIG["port"], context=context, timeout=10
        )
    else:
        server = smtplib.SMTP(SMTP_CONFIG["host"], SMTP_CONFIG["port"], timeout=10)
        if SMTP_CONFIG["use_tls"]:
            context = ssl.create_default_context()
            server.starttls(context=context)

    server.login(SMTP_CONFIG["username"], SMTP_CONFIG["password"])
    print(f"  认证成功: {SMTP_CONFIG['username']}")
    server.quit()


# ─── 测试 5: 发送纯文本邮件 ───

def test_send_plaintext():
    """发送一封纯文本测试邮件"""
    msg = MIMEText("这是一封 SMTP 纯文本测试邮件。\n\n发送时间: " + time.strftime("%Y-%m-%d %H:%M:%S"), "plain", "utf-8")
    msg["Subject"] = "[测试] 纯文本邮件"
    msg["From"] = SENDER
    msg["To"] = RECIPIENT

    server = get_smtp_connection()
    server.sendmail(SENDER, [RECIPIENT], msg.as_string())
    server.quit()
    print(f"  已发送纯文本邮件 -> {RECIPIENT}")


# ─── 测试 6: 发送 HTML 邮件 ───

def test_send_html():
    """发送一封 HTML 格式的测试邮件"""
    html_content = """\
    <html>
    <body>
        <h1 style="color: #2c3e50;">SMTP HTML 邮件测试</h1>
        <p>这是一封 <b>HTML 格式</b> 的测试邮件。</p>
        <table border="1" cellpadding="8" style="border-collapse: collapse;">
            <tr style="background: #3498db; color: white;">
                <th>测试项</th><th>状态</th>
            </tr>
            <tr><td>HTML 渲染</td><td>正常</td></tr>
            <tr><td>中文支持</td><td>正常</td></tr>
            <tr><td>CSS 样式</td><td>正常</td></tr>
        </table>
        <p style="color: #7f8c8d; font-size: 12px;">
            发送时间: {time}
        </p>
    </body>
    </html>
    """.format(time=time.strftime("%Y-%m-%d %H:%M:%S"))

    msg = MIMEMultipart("alternative")
    msg["Subject"] = "[测试] HTML 邮件"
    msg["From"] = SENDER
    msg["To"] = RECIPIENT
    msg.attach(MIMEText("你的邮件客户端不支持 HTML，这是纯文本备用内容。", "plain", "utf-8"))
    msg.attach(MIMEText(html_content, "html", "utf-8"))

    server = get_smtp_connection()
    server.sendmail(SENDER, [RECIPIENT], msg.as_string())
    server.quit()
    print(f"  已发送 HTML 邮件 -> {RECIPIENT}")


# ─── 测试 7: 发送带附件的邮件 ───

def test_send_attachment():
    """发送一封带附件的测试邮件"""
    # 创建临时测试附件
    attachment_path = os.path.join(os.path.dirname(__file__), "test_attachment.txt")
    with open(attachment_path, "w", encoding="utf-8") as f:
        f.write("这是一个测试附件文件。\n")
        f.write(f"生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("用于验证 SMTP 附件发送功能。\n")

    msg = MIMEMultipart()
    msg["Subject"] = "[测试] 带附件的邮件"
    msg["From"] = SENDER
    msg["To"] = RECIPIENT
    msg.attach(MIMEText("请查看附件。", "plain", "utf-8"))

    with open(attachment_path, "rb") as f:
        part = MIMEBase("application", "octet-stream")
        part.set_payload(f.read())
    encoders.encode_base64(part)
    part.add_header("Content-Disposition", f"attachment; filename=test_attachment.txt")
    msg.attach(part)

    server = get_smtp_connection()
    server.sendmail(SENDER, [RECIPIENT], msg.as_string())
    server.quit()
    print(f"  已发送带附件邮件 -> {RECIPIENT}")

    os.remove(attachment_path)


# ─── 测试 8: 多收件人 ───

def test_send_multiple_recipients():
    """测试发送给多个收件人（使用同一收件人模拟）"""
    recipients = [RECIPIENT]

    msg = MIMEText("这是一封多收件人测试邮件。", "plain", "utf-8")
    msg["Subject"] = "[测试] 多收件人"
    msg["From"] = SENDER
    msg["To"] = ", ".join(recipients)

    server = get_smtp_connection()
    server.sendmail(SENDER, recipients, msg.as_string())
    server.quit()
    print(f"  已发送给 {len(recipients)} 个收件人")


# ─── 测试 9: 错误处理 - 无效收件人 ───

def test_invalid_recipient():
    """测试发送给无效地址时服务器的响应"""
    invalid = "nonexistent_user_12345@invalid-domain-test.local"

    msg = MIMEText("测试无效收件人", "plain", "utf-8")
    msg["Subject"] = "[测试] 无效收件人"
    msg["From"] = SENDER
    msg["To"] = invalid

    server = get_smtp_connection()
    try:
        server.sendmail(SENDER, [invalid], msg.as_string())
        print(f"  警告: 服务器接受了无效地址（可能会延迟退信）")
    except smtplib.SMTPRecipientsRefused:
        print(f"  服务器正确拒绝了无效收件人 ✓")
    finally:
        server.quit()


# ─── 主函数 ───

def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║              SMTP 邮件服务测试套件                      ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"  服务器: {SMTP_CONFIG['host']}:{SMTP_CONFIG['port']}")
    print(f"  发件人: {SENDER}")
    print(f"  收件人: {RECIPIENT}")
    print(f"  加密:   {'SSL' if SMTP_CONFIG['use_ssl'] else 'STARTTLS' if SMTP_CONFIG['use_tls'] else '无'}")

    tests = [
        ("端口连通性", test_port_connectivity),
        ("EHLO 握手", test_ehlo),
        ("TLS/SSL 加密", test_tls),
        ("用户认证", test_auth),
        ("发送纯文本邮件", test_send_plaintext),
        ("发送 HTML 邮件", test_send_html),
        ("发送带附件邮件", test_send_attachment),
        ("多收件人发送", test_send_multiple_recipients),
        ("无效收件人处理", test_invalid_recipient),
    ]

    results = []
    for name, func in tests:
        results.append((name, run_test(name, func)))

    print(f"\n{'='*60}")
    print("测试结果汇总")
    print(f"{'='*60}")
    passed = sum(1 for _, ok in results if ok)
    for name, ok in results:
        status = "✓ 通过" if ok else "✗ 失败"
        print(f"  {status}  {name}")
    print(f"\n  总计: {passed}/{len(results)} 通过")


if __name__ == "__main__":
    main()
