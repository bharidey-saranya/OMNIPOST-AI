"""
Slack Incoming Webhook integration for internal and partner messaging.
API Documentation: https://api.slack.com/messaging/webhooks
"""

import time
import httpx
import logging
from app.platforms.base import BasePlatform
from app.schemas import PlatformResult
from app.config import get_settings

logger = logging.getLogger("slack-platform")


class SlackPlatform(BasePlatform):
    """
    Publishes announcements to a Slack channel via Incoming Webhook.
    Note: Slack content requires workspace authentication, so public_access is False.
    """

    def __init__(self):
        super().__init__(name="Slack", is_public=False)

    async def post(self, message: str, cta_url: str) -> PlatformResult:
        settings = get_settings()
        webhook_url = settings.SLACK_WEBHOOK_URL

        if not webhook_url:
            if settings.ENABLE_SIMULATION_FALLBACK:
                ts = int(time.time() * 1000000)
                simulated_url = f"https://dxora-workspace.slack.com/archives/C06TECHNEWS/p{ts}"
                logger.info("Slack: Simulated broadcast to %s", simulated_url)
                return self.make_success(simulated_url)
            return self.make_failed("Authentication failed: SLACK_WEBHOOK_URL not configured.")

        payload = {
            "text": message,
            "unfurl_links": True,
            "unfurl_media": True,
        }

        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                res = await client.post(webhook_url, json=payload)
                res.raise_for_status()

            # Slack responds with plain text 'ok'
            if res.text.strip().lower() == "ok":
                ts = int(time.time() * 1000000)
                posted_url = f"https://app.slack.com/client/workspace/broadcast/p{ts}"
                return self.make_success(posted_url)
            else:
                return self.make_failed(f"Slack rejected payload: {res.text}")
        except httpx.HTTPStatusError as e:
            return self.make_failed(f"Slack HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            return self.make_failed(f"Slack connection error: {str(e)}")
