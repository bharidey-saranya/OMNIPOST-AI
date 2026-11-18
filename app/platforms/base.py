"""
Abstract Base Platform interface for automated social and messaging dispatch.
"""

from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Tuple, Optional
import logging

from app.schemas import PlatformResult

logger = logging.getLogger("posting-platform")


class BasePlatform(ABC):
    """Abstract base class for all third-party publishing platforms."""

    def __init__(self, name: str, is_public: bool = True):
        self.name = name
        self.is_public = is_public

    @staticmethod
    def get_current_timestamp() -> Tuple[str, str]:
        """Return (YYYY-MM-DD, HH:MM:SS) in UTC."""
        now = datetime.now(timezone.utc)
        return now.strftime("%Y-%m-%d"), now.strftime("%H:%M:%S")

    @abstractmethod
    async def post(self, message: str, cta_url: str) -> PlatformResult:
        """
        Publish the message to the third-party platform.
        Must catch internal errors and return a PlatformResult with status='failed'
        rather than raising unhandled exceptions, ensuring fault-tolerant concurrency.
        """
        pass

    def make_success(self, posted_url: str) -> PlatformResult:
        """Helper to construct a standardized successful PlatformResult."""
        d, t = self.get_current_timestamp()
        return PlatformResult(
            platform=self.name,
            status="success",
            posted_url=posted_url,
            public_access=self.is_public,
            date=d,
            time=t,
            error=None,
        )

    def make_failed(self, error_message: str) -> PlatformResult:
        """Helper to construct a standardized failed PlatformResult."""
        return PlatformResult(
            platform=self.name,
            status="failed",
            posted_url=None,
            public_access=False,
            date=None,
            time=None,
            error=error_message,
        )
