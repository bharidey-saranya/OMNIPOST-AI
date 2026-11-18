"""
Validation utilities for message length, CTA links, and URL integrity.
Directly aligned with python-post-message.md specifications.
"""

import re
from typing import Tuple, List, Optional
from urllib.parse import urlparse
import ipaddress
import socket

# Regex matching standard HTTP/HTTPS URLs
URL_REGEX = re.compile(
    r"(?:https?:\/\/)"                          # scheme
    r"(?:[a-zA-Z0-9_\-\.]+\.[a-zA-Z]{2,}|localhost|\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})"  # domain or ip
    r"(?::\d+)?"                                # optional port
    r"(?:\/[^\s]*)?",                           # optional path
    re.IGNORECASE
)


def extract_urls(text: str) -> List[str]:
    """Extract all valid URL candidates from message text."""
    if not text:
        return []
    # Match urls but clean trailing punctuation commonly placed at the end of sentences (.,!?)
    raw_matches = URL_REGEX.findall(text)
    cleaned = []
    for match in raw_matches:
        trimmed = match.rstrip(".,;!?)\"'")
        if trimmed:
            cleaned.append(trimmed)
    return cleaned


def is_valid_url(url: str) -> Tuple[bool, Optional[str]]:
    """
    Validate URL syntax, scheme, and basic host presence.
    Returns (is_valid, error_message).
    """
    try:
        parsed = urlparse(url)
        if parsed.scheme not in ("http", "https"):
            return False, f"URL scheme '{parsed.scheme}' is unsupported. Only 'http' and 'https' are allowed."
        if not parsed.netloc:
            return False, "URL host/domain is missing or invalid."

        # Hostname structure check
        host = parsed.hostname
        if not host:
            return False, "URL hostname could not be parsed."

        if host != "localhost" and "." not in host:
            return False, f"URL domain '{host}' is missing a valid top-level domain."

        return True, None
    except Exception as e:
        return False, f"Malformed URL: {str(e)}"


def validate_posting_message(message: str) -> Tuple[bool, Optional[str], Optional[str]]:
    """
    Validate posting request message:
    1. Must not be empty.
    2. Must not exceed 200 characters.
    3. Exactly one CTA link must be included in the message.
    4. The extracted CTA URL must be syntactically valid.

    Returns:
        (is_valid: bool, error_message: Optional[str], extracted_url: Optional[str])
    """
    if not message or not message.strip():
        return False, "Message cannot be empty.", None

    trimmed_message = message.strip()

    # Rule 1: Max 200 characters
    if len(trimmed_message) > 200:
        return (
            False,
            f"Message length ({len(trimmed_message)} chars) exceeds maximum allowed limit of 200 characters.",
            None,
        )

    # Rule 2: Exactly one CTA link
    found_urls = extract_urls(trimmed_message)
    if len(found_urls) == 0:
        return (
            False,
            "Message must include exactly one CTA link. Found 0 links.",
            None,
        )
    if len(found_urls) > 1:
        return (
            False,
            f"Message must include exactly one CTA link. Found {len(found_urls)} links: {', '.join(found_urls)}",
            None,
        )

    cta_url = found_urls[0]

    # Rule 3: Validate the URL
    url_ok, url_err = is_valid_url(cta_url)
    if not url_ok:
        return False, f"Invalid CTA link: {url_err}", None

    return True, None, cta_url
