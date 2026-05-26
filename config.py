# ═══════════════════════════════════════════
#  Zeabur Email 配置
# ═══════════════════════════════════════════

ZEABUR_CONFIG = {
    "api_key": "YOUR_API_KEY",                        # Zeabur API 密钥（只显示一次，注意保存）
    "api_url": "https://api.zeabur.com/api/v1/zsend",  # API 基地址
    "from": "test@yourdomain.com",                    # 发件人（必须是已验证的域名）
}

# 测试收件人
RECIPIENT = "recipient@example.com"


# ═══════════════════════════════════════════
#  传统 SMTP 配置（如果你同时有自建 SMTP 服务器）
# ═══════════════════════════════════════════

SMTP_CONFIG = {
    "host": "mail.example.com",
    "port": 587,
    "use_tls": True,
    "use_ssl": False,
    "username": "test@example.com",
    "password": "your_password",
}

SENDER = "test@example.com"
