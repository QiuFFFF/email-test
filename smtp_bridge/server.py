"""
SMTP → Zeabur Email REST API 桥接服务

你的应用通过标准 SMTP 协议连接本服务，本服务将邮件转发到 Zeabur Email API。

SMTP 配置（填到你的应用里）:
  Host: 本服务部署地址（本地测试用 localhost）
  Port: 2525（或环境变量 SMTP_PORT）
  Username: 任意值（如 "zeabur"）
  Password: 你的 Zeabur API Key（zs_xxx）
  TLS: 不需要（服务间内网通信）
"""

import os
import asyncio
import email
import base64
import logging
from email import policy
from email.utils import parseaddr, getaddresses

import aiosmtpd.controller
from aiosmtpd.smtp import AuthResult, LoginPassword
import httpx

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger("smtp-bridge")

ZEABUR_API_URL = os.environ.get(
    "ZEABUR_API_URL", "https://api.zeabur.com/api/v1/zsend"
)
SMTP_PORT = int(os.environ.get("SMTP_PORT", "2525"))
SMTP_HOST = os.environ.get("SMTP_HOST", "0.0.0.0")

# 可选：固定 API Key（不通过 SMTP 密码传入时使用）
ZEABUR_API_KEY = os.environ.get("ZEABUR_API_KEY", "")


class ZeaburAuthenticator:
    def __call__(self, server, session, envelope, mechanism, auth_data):
        if mechanism not in ("LOGIN", "PLAIN"):
            return AuthResult(success=False, handled=False)

        if isinstance(auth_data, LoginPassword):
            session.api_key = auth_data.password.decode()
            log.info(f"认证成功: {auth_data.login.decode()}")
            return AuthResult(success=True)

        return AuthResult(success=False, handled=False)


class ZeaburSMTPHandler:
    async def handle_RCPT(self, server, session, envelope, address, rcpt_options):
        envelope.rcpt_tos.append(address)
        return "250 OK"

    async def handle_DATA(self, server, session, envelope):
        api_key = getattr(session, "api_key", None) or ZEABUR_API_KEY
        if not api_key:
            log.error("无 API Key：SMTP 密码和环境变量都未提供")
            return "535 Authentication required"

        try:
            msg = email.message_from_bytes(envelope.content, policy=policy.default)
            payload = self._build_payload(envelope, msg)
            result = await self._send_via_zeabur(api_key, payload)
            log.info(f"发送成功: {payload['from']} -> {payload['to']} | {result}")
            return "250 OK"
        except Exception as e:
            log.error(f"发送失败: {e}")
            return f"554 Transaction failed: {e}"

    def _build_payload(self, envelope, msg):
        _, from_addr = parseaddr(msg["From"] or envelope.mail_from)
        to_list = [addr for _, addr in getaddresses(msg.get_all("To", []))]
        cc_list = [addr for _, addr in getaddresses(msg.get_all("Cc", []))]

        if not to_list:
            to_list = list(envelope.rcpt_tos)

        payload = {
            "from": from_addr,
            "to": to_list,
            "subject": msg["Subject"] or "(无主题)",
        }

        if cc_list:
            payload["cc"] = cc_list

        reply_to = msg["Reply-To"]
        if reply_to:
            _, reply_addr = parseaddr(reply_to)
            if reply_addr:
                payload["reply_to"] = reply_addr

        text_part = None
        html_part = None
        attachments = []

        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                disposition = str(part.get("Content-Disposition", ""))

                if "attachment" in disposition:
                    att_data = part.get_payload(decode=True)
                    if att_data:
                        attachments.append({
                            "filename": part.get_filename() or "attachment",
                            "content": base64.b64encode(att_data).decode("ascii"),
                            "content_type": content_type,
                        })
                elif content_type == "text/plain" and text_part is None:
                    text_part = part.get_content()
                elif content_type == "text/html" and html_part is None:
                    html_part = part.get_content()
        else:
            content_type = msg.get_content_type()
            if content_type == "text/html":
                html_part = msg.get_content()
            else:
                text_part = msg.get_content()

        if html_part:
            payload["html"] = html_part
        if text_part:
            payload["text"] = text_part
        if not html_part and not text_part:
            payload["text"] = "(空邮件)"
        if attachments:
            payload["attachments"] = attachments

        return payload

    async def _send_via_zeabur(self, api_key, payload):
        async with httpx.AsyncClient(timeout=30) as client:
            resp = await client.post(
                f"{ZEABUR_API_URL}/emails",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json=payload,
            )

            if resp.status_code not in (200, 201, 202):
                raise RuntimeError(f"Zeabur API {resp.status_code}: {resp.text}")

            return resp.json()


def main():
    handler = ZeaburSMTPHandler()
    authenticator = ZeaburAuthenticator()

    controller = aiosmtpd.controller.Controller(
        handler,
        hostname=SMTP_HOST,
        port=SMTP_PORT,
        authenticator=authenticator,
        auth_required=not bool(ZEABUR_API_KEY),
        auth_require_tls=False,
    )

    controller.start()
    log.info(f"SMTP 桥接服务已启动: {SMTP_HOST}:{SMTP_PORT}")
    log.info(f"Zeabur API: {ZEABUR_API_URL}")
    log.info(f"认证模式: {'固定Key' if ZEABUR_API_KEY else 'SMTP密码传入Key'}")
    log.info("将以下配置填入你的应用:")
    log.info(f"  SMTP Host: <本服务地址>")
    log.info(f"  SMTP Port: {SMTP_PORT}")
    if not ZEABUR_API_KEY:
        log.info(f"  SMTP Username: zeabur")
        log.info(f"  SMTP Password: <你的 Zeabur API Key>")
    log.info("按 Ctrl+C 停止...")

    try:
        asyncio.get_event_loop().run_forever()
    except KeyboardInterrupt:
        log.info("正在停止...")
    finally:
        controller.stop()


if __name__ == "__main__":
    main()
