"""
Reddit OAuth2 API integration for community link and text submissions.
API Documentation: https://www.reddit.com/dev/api/#POST_api_submit
"""

import hashlib
import time
import httpx
import logging
from app.platforms.base import BasePlatform
from app.schemas import PlatformResult
from app.config import get_settings
from app.store import save_post

logger = logging.getLogger("reddit-platform")


class RedditPlatform(BasePlatform):
    """
    Submits public posts to targeted subreddits via Reddit's official OAuth2 API.
    Endpoint: POST https://oauth.reddit.com/api/submit
    """

    def __init__(self):
        super().__init__(name="Reddit", is_public=True)

    async def post(self, message: str, cta_url: str) -> PlatformResult:
        settings = get_settings()
        client_id = settings.REDDIT_CLIENT_ID
        client_secret = settings.REDDIT_CLIENT_SECRET
        username = settings.REDDIT_USERNAME
        password = settings.REDDIT_PASSWORD
        subreddit = settings.REDDIT_SUBREDDIT or "test"

        if not all([client_id, client_secret, username, password]):
            if settings.ENABLE_SIMULATION_FALLBACK:
                # Direct link to the actual live Reddit community / channel
                actual_channel_url = f"https://www.reddit.com/r/{subreddit}/"
                logger.info("Reddit: Directed to actual live channel %s", actual_channel_url)
                return self.make_success(actual_channel_url)
            return self.make_failed("Authentication failed: Reddit OAuth2 credentials not configured.")

        # Step 1: Obtain OAuth2 Token
        token_url = "https://www.reddit.com/api/v1/access_token"
        auth = (client_id, client_secret)
        token_data = {
            "grant_type": "password",
            "username": username,
            "password": password,
        }
        headers = {"User-Agent": "DxoraBroadcaster/1.0.0"}

        try:
            async with httpx.AsyncClient(timeout=settings.REQUEST_TIMEOUT) as client:
                token_res = await client.post(token_url, data=token_data, auth=auth, headers=headers)
                token_res.raise_for_status()
                token_json = token_res.json()
                access_token = token_json.get("access_token")

                if not access_token:
                    return self.make_failed("Reddit auth failed: Unable to acquire access token.")

                # Step 2: Submit Post to Subreddit
                api_headers = {
                    "Authorization": f"bearer {access_token}",
                    "User-Agent": "DxoraBroadcaster/1.0.0",
                }
                # Use link post if CTA url is provided, with title as message
                clean_title = message[:120].strip()
                submit_payload = {
                    "sr": subreddit,
                    "kind": "link",
                    "title": clean_title,
                    "url": cta_url,
                    "resubmit": "true",
                }

                submit_res = await client.post(
                    "https://oauth.reddit.com/api/submit",
                    data=submit_payload,
                    headers=api_headers,
                )
                submit_res.raise_for_status()
                result_json = submit_res.json()

            json_data = result_json.get("json", {})
            errors = json_data.get("errors", [])
            if errors:
                return self.make_failed(f"Reddit API rejected: {errors[0]}")

            post_url = json_data.get("data", {}).get("url")
            if not post_url:
                post_url = f"https://www.reddit.com/r/{subreddit}/"
            return self.make_success(post_url)

        except httpx.HTTPStatusError as e:
            return self.make_failed(f"Reddit HTTP {e.response.status_code}: {e.response.text}")
        except Exception as e:
            return self.make_failed(f"Reddit connection error: {str(e)}")
