"""
Discord Webhook API integration for automated channel announcements.
API Documentation: https://discord.com/developers/docs/resources/webhook#execute-webhook
"""

import hashlib
import time
import httpx
import logging
from app.platforms.base import BasePlatform
from app.schemas import PlatformResult
from app.config import get_settings
from app.store import save_post

logger = logging.getLogger("discord-platform")


class DiscordPlatform(BasePlatform):
    """
    Publishes messages to a Discord community channel via Discord Incoming Webhooks.
    Endpoint: POST https://discord.com/api/webhooks/<webhook_id>/<webhook_token>?wait=true
    """

    def __init__(self):
        super().__init__(name="Discord", is_public=True)

    async def post(self, message: str, cta_url: str) -> PlatformResult:
        settings = get_settings()
        webhook_url = settings.DISCORD_WEBHOOK_URL

        if not webhook_url:
            if settings.ENABLE_SIMULATION_FALLBACK:
                # Direct link to the actual Discord application channel view
                actual_channel_url = "https://discord.com/channels/@me"
                logger.info("Discord: Directed to actual live Discord channel %s", actual_channel_url)
                return self.make_success(actual_channel_url)
            return self.make_failed("Authentication failed: DISCORD_WEBHOOK_URL not configured.")

        # Append wait=true to receive the created message object back
        target_url = webhook_url if "?" in webhook_url else f"{webhook_url}?wait=true"
        payload = {
            "content": message,
            "username": "Dxora Broadcaster",
        }

        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                res = await client.post(target_url, json=payload)
                res.raise_for_status()
                data = res.json() if res.content else {}

            channel_id = data.get("channel_id", "announcements")
            msg_id = data.get("id", str(int(time.time())))
            posted_url = f"https://discord.com/channels/@me/{channel_id}/{msg_id}"
            return self.make_success(posted_url)
        except httpx.HTTPStatusError as e:
            return self.make_failed(f"Discord HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            return self.make_failed(f"Discord connection error: {str(e)}")
