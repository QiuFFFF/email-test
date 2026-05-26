"""
SMTP 服务器诊断工具
检查常见端口、DNS 解析、TLS 证书等
"""

import socket
import ssl
import smtplib
import time


def diagnose(host):
    print(f"诊断目标: {host}\n")

    # 1. DNS 解析
    print("[1/5] DNS 解析")
    try:
        ips = socket.getaddrinfo(host, None, socket.AF_UNSPEC, socket.SOCK_STREAM)
        seen = set()
        for family, _, _, _, addr in ips:
            ip = addr[0]
            if ip not in seen:
                seen.add(ip)
                family_name = "IPv4" if family == socket.AF_INET else "IPv6"
                print(f"  {family_name}: {ip}")
    except socket.gaierror as e:
        print(f"  ✗ DNS 解析失败: {e}")
        return

    # 2. MX 记录（通过 nslookup）
    print("\n[2/5] MX 记录")
    try:
        import subprocess
        result = subprocess.run(
            ["nslookup", "-type=mx", host],
            capture_output=True, text=True, timeout=10
        )
        lines = result.stdout.strip().split("\n")
        mx_found = False
        for line in lines:
            if "mail exchanger" in line.lower() or "mx preference" in line.lower():
                print(f"  {line.strip()}")
                mx_found = True
        if not mx_found:
            print("  未找到 MX 记录（自建服务器可能直接使用 A 记录）")
    except Exception as e:
        print(f"  查询失败: {e}")

    # 3. 端口扫描
    print("\n[3/5] SMTP 端口扫描")
    ports = [
        (25,  "SMTP（明文/STARTTLS）"),
        (465, "SMTPS（隐式 SSL）"),
        (587, "Submission（STARTTLS）"),
    ]
    open_ports = []
    for port, desc in ports:
        try:
            sock = socket.create_connection((host, port), timeout=5)
            banner = sock.recv(1024).decode("utf-8", errors="replace").strip()
            sock.close()
            print(f"  ✓ 端口 {port} ({desc}) - 开放")
            print(f"    响应: {banner}")
            open_ports.append(port)
        except (socket.timeout, ConnectionRefusedError, OSError):
            print(f"  ✗ 端口 {port} ({desc}) - 关闭/不可达")

    if not open_ports:
        print("\n  警告: 没有任何 SMTP 端口可达！请检查防火墙设置。")
        return

    # 4. TLS 证书检查
    print("\n[4/5] TLS 证书检查")
    tls_port = 465 if 465 in open_ports else (587 if 587 in open_ports else None)
    if tls_port:
        try:
            ctx = ssl.create_default_context()
            if tls_port == 465:
                with ctx.wrap_socket(socket.create_connection((host, tls_port), timeout=5), server_hostname=host) as ssock:
                    cert = ssock.getpeercert()
            else:
                server = smtplib.SMTP(host, tls_port, timeout=5)
                server.starttls(context=ctx)
                cert = server.sock.getpeercert()
                server.quit()

            subject = dict(x[0] for x in cert.get("subject", []))
            issuer = dict(x[0] for x in cert.get("issuer", []))
            print(f"  主题: {subject.get('commonName', 'N/A')}")
            print(f"  颁发者: {issuer.get('organizationName', 'N/A')}")
            print(f"  有效期至: {cert.get('notAfter', 'N/A')}")

            san = cert.get("subjectAltName", [])
            if san:
                names = [v for _, v in san]
                print(f"  SAN: {', '.join(names[:5])}")
        except ssl.SSLCertVerificationError as e:
            print(f"  ✗ 证书验证失败: {e}")
            print(f"    提示: 自签名证书需要在客户端信任或跳过验证")
        except Exception as e:
            print(f"  ✗ TLS 检查失败: {e}")
    else:
        print("  跳过: 没有支持 TLS 的端口开放")

    # 5. EHLO 能力检测
    print("\n[5/5] 服务器能力检测")
    test_port = open_ports[0]
    try:
        server = smtplib.SMTP(host, test_port, timeout=10)
        code, response = server.ehlo()
        if code == 250:
            features = response.decode("utf-8", errors="replace").split("\n")
            print(f"  服务器标识: {features[0]}")
            print(f"  支持的功能:")
            for feat in features[1:]:
                print(f"    - {feat.strip()}")
        server.quit()
    except Exception as e:
        print(f"  ✗ EHLO 失败: {e}")


if __name__ == "__main__":
    import sys
    host = sys.argv[1] if len(sys.argv) > 1 else input("请输入邮件服务器地址: ")
    diagnose(host)
