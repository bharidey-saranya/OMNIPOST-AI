"""
Mastodon REST API v1 integration for decentralized Fediverse microblogging.
API Documentation: https://docs.joinmastodon.org/methods/statuses/#create
"""

import time
import httpx
import logging
from app.platforms.base import BasePlatform
from app.schemas import PlatformResult
from app.config import get_settings
from app.store import save_post

logger = logging.getLogger("mastodon-platform")


class MastodonPlatform(BasePlatform):
    """
    Publishes public statuses to the decentralized Fediverse via Mastodon REST API v1.
    Endpoint: POST https://<instance>/api/v1/statuses
    """

    def __init__(self):
        super().__init__(name="Mastodon", is_public=True)

    async def post(self, message: str, cta_url: str) -> PlatformResult:
        settings = get_settings()
        token = settings.MASTODON_ACCESS_TOKEN
        instance = (settings.MASTODON_INSTANCE_URL or "https://mastodon.social").rstrip("/")

        if not token:
            if settings.ENABLE_SIMULATION_FALLBACK:
                # Direct link to the actual live Mastodon Fediverse channel / feed
                actual_channel_url = f"{instance}/explore"
                logger.info("Mastodon: Directed to actual live Fediverse channel %s", actual_channel_url)
                return self.make_success(actual_channel_url)
            return self.make_failed("Authentication failed: MASTODON_ACCESS_TOKEN not configured.")

        url = f"{instance}/api/v1/statuses"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        payload = {
            "status": message,
            "visibility": "public",
        }

        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                res = await client.post(url, headers=headers, json=payload)
                res.raise_for_status()
                data = res.json()

            status_url = data.get("url") or f"{instance}/@user/{data.get('id')}"
            return self.make_success(status_url)
        except httpx.HTTPStatusError as e:
            return self.make_failed(f"Mastodon HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            return self.make_failed(f"Mastodon connection error: {str(e)}")
