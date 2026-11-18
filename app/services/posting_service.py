"""
Posting Service orchestrating concurrent, fault-tolerant broadcasting across all 5 platforms.
"""

import asyncio
import logging
from typing import List, Dict, Any

from app.schemas import PlatformResult
from app.platforms.base import BasePlatform
from app.platforms.telegram import TelegramPlatform
from app.platforms.discord import DiscordPlatform
from app.platforms.slack import SlackPlatform
from app.platforms.mastodon import MastodonPlatform
from app.platforms.reddit import RedditPlatform

logger = logging.getLogger("posting-service")


class PostingService:
    """Manages the lifecycle and concurrent execution of all third-party platform integrations."""

    def __init__(self, platforms: List[BasePlatform] = None):
        self.platforms: List[BasePlatform] = platforms or [
            TelegramPlatform(),
            DiscordPlatform(),
            SlackPlatform(),
            MastodonPlatform(),
            RedditPlatform(),
        ]

    async def publish_to_all(self, message: str, cta_url: str) -> List[PlatformResult]:
        """
        Broadcast the message across all 5 platforms concurrently.
        Guarantees that a failure or timeout on one platform will not interrupt
        or cancel execution on the remaining platforms.
        """
        logger.info("Initiating multi-platform broadcast across %d platforms", len(self.platforms))

        tasks = [platform.post(message=message, cta_url=cta_url) for platform in self.platforms]
        raw_results = await asyncio.gather(*tasks, return_exceptions=True)

        final_results: List[PlatformResult] = []
        for platform, res in zip(self.platforms, raw_results):
            if isinstance(res, Exception):
                logger.error("Platform '%s' encountered unexpected exception: %s", platform.name, str(res))
                final_results.append(platform.make_failed(f"Unexpected execution error: {str(res)}"))
            elif isinstance(res, PlatformResult):
                final_results.append(res)
            else:
                final_results.append(platform.make_failed("Invalid result returned from platform driver"))

        return final_results

    def get_platforms_overview(self) -> List[Dict[str, Any]]:
        """Return metadata for all registered platforms."""
        return [
            {
                "platform": p.name,
                "public_access": p.is_public,
                "driver": p.__class__.__name__,
            }
            for p in self.platforms
        ]
