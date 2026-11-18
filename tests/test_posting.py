"""
Unit and integration test suite for Automated Multi-Platform Posting System.
Covers input validation (character count, single CTA URL, invalid URLs),
concurrent multi-platform dispatch, fault-tolerant failure isolation, and API responses.
"""

import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app
from app.utils.validators import validate_posting_message, extract_urls, is_valid_url
from app.platforms.base import BasePlatform
from app.services.posting_service import PostingService
from app.schemas import PlatformResult


@pytest.fixture
def anyio_backend():
    return "asyncio"


# -------------------------------------------------------------
# Unit Tests: Validators
# -------------------------------------------------------------

def test_extract_urls():
    text = "Visit our site at https://example.com for more info. Or check http://test.org/path?q=1."
    urls = extract_urls(text)
    assert len(urls) == 2
    assert urls[0] == "https://example.com"
    assert urls[1] == "http://test.org/path?q=1"


def test_url_syntax_validation():
    valid_ok, _ = is_valid_url("https://example.com")
    assert valid_ok is True

    valid_http, _ = is_valid_url("http://sub.domain.co.uk/docs")
    assert valid_http is True

    invalid_scheme, err = is_valid_url("ftp://files.example.com")
    assert invalid_scheme is False
    assert "scheme 'ftp' is unsupported" in err

    invalid_domain, err = is_valid_url("https://nodomain")
    assert invalid_domain is False


def test_validator_rejects_empty():
    ok, err, cta = validate_posting_message("")
    assert ok is False
    assert "empty" in err.lower()


def test_validator_rejects_over_200_chars():
    long_msg = "A" * 190 + " https://example.com"
    assert len(long_msg) > 200
    ok, err, cta = validate_posting_message(long_msg)
    assert ok is False
    assert "exceeds maximum allowed limit of 200 characters" in err


def test_validator_rejects_zero_urls():
    msg = "Check out our new business announcement with no link."
    ok, err, cta = validate_posting_message(msg)
    assert ok is False
    assert "Found 0 links" in err


def test_validator_rejects_multiple_urls():
    msg = "Visit https://link1.com and also https://link2.com for details."
    ok, err, cta = validate_posting_message(msg)
    assert ok is False
    assert "Found 2 links" in err


def test_validator_accepts_valid_message():
    msg = "Check out our latest business platform and grow your online visibility. https://example.com"
    ok, err, cta = validate_posting_message(msg)
    assert ok is True
    assert err is None
    assert cta == "https://example.com"


# -------------------------------------------------------------
# Integration Tests: FastAPI Endpoints
# -------------------------------------------------------------

@pytest.mark.asyncio
async def test_root_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/", headers={"Accept": "application/json"})
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert "Telegram" in data["platforms_supported"]
    assert "Discord" in data["platforms_supported"]


@pytest.mark.asyncio
async def test_health_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert "configured_platforms" in data


@pytest.mark.asyncio
async def test_platforms_endpoint():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        response = await ac.get("/platforms")
    assert response.status_code == 200
    data = response.json()
    platforms = [p["platform"] for p in data["platforms"]]
    assert set(platforms) == {"Telegram", "Discord", "Slack", "Mastodon", "Reddit"}


@pytest.mark.asyncio
async def test_posting_rejects_missing_cta_link():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {"message": "Hello world without any links!"}
        response = await ac.post("/posting", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "Found 0 links" in data["detail"]


@pytest.mark.asyncio
async def test_posting_rejects_message_exceeding_200_chars():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        long_text = "Grow your business online with our innovative software suite that provides all tools needed. " * 3 + "https://example.com"
        assert len(long_text) > 200
        response = await ac.post("/posting", json={"message": long_text})
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "exceeds maximum allowed limit of 200 characters" in data["detail"]


@pytest.mark.asyncio
async def test_posting_rejects_multiple_links():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {"message": "Check https://site1.com and https://site2.com for offers"}
        response = await ac.post("/posting", json=payload)
    assert response.status_code == 422
    data = response.json()
    assert data["success"] is False
    assert "Found 2 links" in data["detail"]


@pytest.mark.asyncio
async def test_successful_multi_platform_posting():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        payload = {
            "message": "Check out our latest business platform and grow your online visibility. https://example.com"
        }
        response = await ac.post("/posting", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    results = data["results"]
    assert len(results) == 5

    platforms_returned = {r["platform"]: r for r in results}
    expected_platforms = {"Telegram", "Discord", "Slack", "Mastodon", "Reddit"}
    assert set(platforms_returned.keys()) == expected_platforms

    for name, r in platforms_returned.items():
        assert r["status"] == "success"
        assert r["posted_url"] is not None
        assert r["date"] is not None
        assert r["time"] is not None
        assert r["error"] is None

    # Slack is workspace protected
    assert platforms_returned["Slack"]["public_access"] is False
    # Others are public
    assert platforms_returned["Telegram"]["public_access"] is True
    assert platforms_returned["Discord"]["public_access"] is True
    assert platforms_returned["Mastodon"]["public_access"] is True
    assert platforms_returned["Reddit"]["public_access"] is True


# -------------------------------------------------------------
# Fault-Tolerance & Platform Isolation Test
# -------------------------------------------------------------

class FailingPlatform(BasePlatform):
    def __init__(self, name: str):
        super().__init__(name=name, is_public=True)

    async def post(self, message: str, cta_url: str) -> PlatformResult:
        # Simulate network or authentication error
        return self.make_failed("Simulated OAuth token expired")


class CrashPlatform(BasePlatform):
    def __init__(self, name: str):
        super().__init__(name=name, is_public=True)

    async def post(self, message: str, cta_url: str) -> PlatformResult:
        raise ConnectionResetError("Socket abruptly closed by peer")


@pytest.mark.asyncio
async def test_fault_tolerant_isolation_keeps_posting():
    """Verify that when one platform fails or crashes, others still succeed."""
    from app.platforms.telegram import TelegramPlatform
    from app.platforms.discord import DiscordPlatform

    custom_service = PostingService(platforms=[
        TelegramPlatform(),
        FailingPlatform("FailingSocial"),
        CrashPlatform("CrashingPlatform"),
        DiscordPlatform(),
    ])

    results = await custom_service.publish_to_all(
        message="Test announcement https://example.com",
        cta_url="https://example.com"
    )

    assert len(results) == 4
    by_name = {r.platform: r for r in results}

    assert by_name["Telegram"].status == "success"
    assert by_name["Discord"].status == "success"
    assert by_name["FailingSocial"].status == "failed"
    assert "Simulated OAuth token expired" in by_name["FailingSocial"].error
    assert by_name["CrashingPlatform"].status == "failed"
    assert "Socket abruptly closed" in by_name["CrashingPlatform"].error
