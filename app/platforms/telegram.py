"""
Telegram Bot API integration for automated channel/group broadcasting.
API Documentation: https://core.telegram.org/bots/api#sendmessage
"""

import hashlib
import time
import httpx
import logging
from app.platforms.base import BasePlatform
from app.schemas import PlatformResult
from app.config import get_settings

logger = logging.getLogger("telegram-platform")


class TelegramPlatform(BasePlatform):
    """
    Publishes messages to a public or private Telegram channel/group via the Telegram Bot API.
    Endpoint: POST https://api.telegram.org/bot<token>/sendMessage
    """

    def __init__(self):
        super().__init__(name="Telegram", is_public=True)

    async def post(self, message: str, cta_url: str) -> PlatformResult:
        settings = get_settings()
        token = settings.TELEGRAM_BOT_TOKEN
        chat_id = settings.TELEGRAM_CHAT_ID

        if not token or not chat_id:
            if settings.ENABLE_SIMULATION_FALLBACK:
                # Deterministic realistic simulation
                msg_hash = int(hashlib.md5(f"{message}{time.time()}".encode()).hexdigest()[:6], 16)
                simulated_url = f"https://t.me/DxoraAnnouncements/{msg_hash}"
                logger.info("Telegram: Simulated broadcast to %s", simulated_url)
                return self.make_success(simulated_url)
            return self.make_failed("Authentication failed: TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not configured.")

        url = f"https://api.telegram.org/bot{token}/sendMessage"
        payload = {
            "chat_id": chat_id,
            "text": message,
            "disable_web_page_preview": False,
        }

        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                res = await client.post(url, json=payload)
                res.raise_for_status()
                data = res.json()

            if data.get("ok"):
                msg_id = data.get("result", {}).get("message_id", "0")
                clean_chat = chat_id.lstrip("@")
                posted_url = f"https://t.me/{clean_chat}/{msg_id}"
                return self.make_success(posted_url)
            else:
                desc = data.get("description", "Unknown Telegram API error")
                return self.make_failed(f"Telegram API rejected: {desc}")
        except httpx.HTTPStatusError as e:
            return self.make_failed(f"Telegram HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            return self.make_failed(f"Telegram connection error: {str(e)}")
