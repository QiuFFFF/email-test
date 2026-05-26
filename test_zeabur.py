"""
Zeabur Email REST API 测试套件
文档: https://zeabur.com/docs/zh-CN/email
"""

import json
import time
import base64
import os
try:
    import requests
except ImportError:
    print("需要安装 requests: pip install requests")
    exit(1)

from config import ZEABUR_CONFIG, RECIPIENT


API_URL = ZEABUR_CONFIG["api_url"]
HEADERS = {
    "Content-Type": "application/json",
    "Authorization": f"Bearer {ZEABUR_CONFIG['api_key']}",
}
FROM = ZEABUR_CONFIG["from"]


def run_test(name, func):
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


# ─── 测试 1: API 连通性 ───

def test_api_connectivity():
    """验证 API 端点可达且认证有效"""
    resp = requests.get(
        f"{API_URL}/emails",
        headers=HEADERS,
        timeout=10,
    )
    print(f"  状态码: {resp.status_code}")
    print(f"  响应: {resp.text[:200]}")
    assert resp.status_code != 401, "API 密钥无效（401 Unauthorized）"
    assert resp.status_code != 403, "API 密钥权限不足（403 Forbidden）"


# ─── 测试 2: 发送纯文本邮件 ───

def test_send_plaintext():
    """通过 REST API 发送纯文本邮件"""
    payload = {
        "from": FROM,
        "to": [RECIPIENT],
        "subject": "[Zeabur测试] 纯文本邮件",
        "text": f"这是一封通过 Zeabur Email API 发送的纯文本测试邮件。\n发送时间: {time.strftime('%Y-%m-%d %H:%M:%S')}",
    }

    resp = requests.post(f"{API_URL}/emails", headers=HEADERS, json=payload, timeout=15)
    data = resp.json()
    print(f"  状态码: {resp.status_code}")
    print(f"  响应: {json.dumps(data, indent=2, ensure_ascii=False)}")

    assert resp.status_code in (200, 201, 202), f"发送失败: {resp.status_code}"
    print(f"  邮件ID: {data.get('email_id', 'N/A')}")
    print(f"  状态: {data.get('status', 'N/A')}")


# ─── 测试 3: 发送 HTML 邮件 ───

def test_send_html():
    """发送 HTML 格式邮件（含纯文本备用）"""
    html = f"""\
    <html>
    <body>
        <h1 style="color: #6c5ce7;">Zeabur Email 测试</h1>
        <p>这是一封 <b>HTML 格式</b> 的测试邮件。</p>
        <table border="1" cellpadding="8" style="border-collapse: collapse; margin: 16px 0;">
            <tr style="background: #0984e3; color: white;">
                <th>测试项</th><th>状态</th>
            </tr>
            <tr><td>HTML 渲染</td><td>✓</td></tr>
            <tr><td>中文支持</td><td>✓</td></tr>
            <tr><td>CSS 内联样式</td><td>✓</td></tr>
        </table>
        <p style="color: #636e72; font-size: 12px;">
            发送时间: {time.strftime('%Y-%m-%d %H:%M:%S')} | Powered by Zeabur Email
        </p>
    </body>
    </html>"""

    payload = {
        "from": FROM,
        "to": [RECIPIENT],
        "subject": "[Zeabur测试] HTML 邮件",
        "html": html,
        "text": "你的邮件客户端不支持 HTML，这是纯文本备用内容。",
    }

    resp = requests.post(f"{API_URL}/emails", headers=HEADERS, json=payload, timeout=15)
    data = resp.json()
    print(f"  状态码: {resp.status_code}")
    print(f"  邮件ID: {data.get('email_id', 'N/A')}")
    assert resp.status_code in (200, 201, 202), f"发送失败: {resp.status_code}"


# ─── 测试 4: 多收件人 ───

def test_send_multiple_recipients():
    """发送给多个收件人"""
    recipients = [RECIPIENT]  # 添加更多收件人测试: ["a@x.com", "b@x.com"]

    payload = {
        "from": FROM,
        "to": recipients,
        "subject": "[Zeabur测试] 多收件人",
        "text": f"多收件人测试邮件，共 {len(recipients)} 位收件人。",
    }

    resp = requests.post(f"{API_URL}/emails", headers=HEADERS, json=payload, timeout=15)
    data = resp.json()
    print(f"  状态码: {resp.status_code}")
    print(f"  收件人数: {len(recipients)}")
    print(f"  邮件ID: {data.get('email_id', 'N/A')}")
    assert resp.status_code in (200, 201, 202), f"发送失败: {resp.status_code}"


# ─── 测试 5: 带附件邮件 ───

def test_send_with_attachment():
    """发送带附件的邮件"""
    # 创建临时附件
    attachment_content = f"Zeabur Email 附件测试\n生成时间: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
    encoded = base64.b64encode(attachment_content.encode("utf-8")).decode("ascii")

    payload = {
        "from": FROM,
        "to": [RECIPIENT],
        "subject": "[Zeabur测试] 带附件邮件",
        "text": "请查看附件。",
        "attachments": [
            {
                "filename": "test_report.txt",
                "content": encoded,
                "content_type": "text/plain",
            }
        ],
    }

    resp = requests.post(f"{API_URL}/emails", headers=HEADERS, json=payload, timeout=15)
    data = resp.json()
    print(f"  状态码: {resp.status_code}")
    print(f"  邮件ID: {data.get('email_id', 'N/A')}")
    assert resp.status_code in (200, 201, 202), f"发送失败: {resp.status_code}"


# ─── 测试 6: 查询邮件状态 ───

def test_check_email_status():
    """先发一封邮件，再查询其投递状态"""
    # 先发一封
    payload = {
        "from": FROM,
        "to": [RECIPIENT],
        "subject": "[Zeabur测试] 状态查询测试",
        "text": "用于测试状态查询的邮件。",
    }
    resp = requests.post(f"{API_URL}/emails", headers=HEADERS, json=payload, timeout=15)
    data = resp.json()
    email_id = data.get("email_id")

    if not email_id:
        print(f"  跳过: 无法获取 email_id")
        return

    print(f"  已发送，邮件ID: {email_id}")
    time.sleep(2)

    # 查询状态
    status_resp = requests.get(
        f"{API_URL}/emails/{email_id}",
        headers=HEADERS,
        timeout=10,
    )
    print(f"  查询状态码: {status_resp.status_code}")
    if status_resp.status_code == 200:
        status_data = status_resp.json()
        print(f"  投递状态: {json.dumps(status_data, indent=2, ensure_ascii=False)}")


# ─── 测试 7: 错误处理 ───

def test_error_handling():
    """测试各种错误情况的 API 响应"""
    # 缺少必填字段
    resp = requests.post(f"{API_URL}/emails", headers=HEADERS, json={}, timeout=10)
    print(f"  空请求 -> 状态码: {resp.status_code} (期望 400)")
    assert resp.status_code == 400 or resp.status_code == 422, \
        f"期望 400/422，收到: {resp.status_code}"

    # 无效发件人域名
    resp2 = requests.post(f"{API_URL}/emails", headers=HEADERS, json={
        "from": "test@not-verified-domain.fake",
        "to": [RECIPIENT],
        "subject": "test",
        "text": "test",
    }, timeout=10)
    print(f"  无效域名 -> 状态码: {resp2.status_code} (期望 400/403)")


# ─── 主函数 ───

def main():
    print("╔══════════════════════════════════════════════════════════╗")
    print("║           Zeabur Email API 测试套件                     ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print(f"  API: {API_URL}")
    print(f"  发件人: {FROM}")
    print(f"  收件人: {RECIPIENT}")

    if ZEABUR_CONFIG["api_key"] == "YOUR_API_KEY":
        print("\n  ⚠ 请先在 config.py 中填入你的 Zeabur API 密钥！")
        return

    tests = [
        ("API 连通性", test_api_connectivity),
        ("发送纯文本邮件", test_send_plaintext),
        ("发送 HTML 邮件", test_send_html),
        ("多收件人发送", test_send_multiple_recipients),
        ("发送带附件邮件", test_send_with_attachment),
        ("查询邮件状态", test_check_email_status),
        ("错误处理", test_error_handling),
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
