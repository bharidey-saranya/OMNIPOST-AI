"""
In-memory store for published and simulated announcements.
Enables instant real-time live previewing at /view/{platform}/{post_id}.
"""

from typing import Dict, Any, Optional
from datetime import datetime, timezone

POST_CACHE: Dict[str, Dict[str, Any]] = {}


def save_post(platform: str, post_id: str, message: str, cta_url: str):
    """Save an announcement for live viewing."""
    key = f"{platform.lower()}_{post_id}"
    now = datetime.now(timezone.utc)
    POST_CACHE[key] = {
        "platform": platform,
        "post_id": post_id,
        "message": message,
        "cta_url": cta_url,
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S UTC"),
    }


def get_post(platform: str, post_id: str) -> Optional[Dict[str, Any]]:
    """Retrieve an announcement, or return a sensible fallback."""
    key = f"{platform.lower()}_{post_id}"
    if key in POST_CACHE:
        return POST_CACHE[key]
    
    # Sensible fallback if server restarted
    now = datetime.now(timezone.utc)
    return {
        "platform": platform.capitalize(),
        "post_id": post_id,
        "message": "Check out our latest business platform and grow your online visibility. https://example.com",
        "cta_url": "https://example.com",
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S UTC"),
    }
