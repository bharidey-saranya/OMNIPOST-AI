"""
Pydantic schemas for the Automated Multi-Platform Posting System.
Matches exact fields defined in python-post-message.md Section 3.B.
"""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field


class PostingRequest(BaseModel):
    """Incoming request payload for POST /posting."""
    message: str = Field(
        ...,
        description="The short marketing message containing exactly one CTA link (max 200 characters).",
        examples=["Check out our latest business platform and grow your online visibility. https://example.com"],
    )


class PlatformResult(BaseModel):
    """Individual posting result per third-party platform."""
    platform: str = Field(..., description="Platform name (e.g. Telegram, Discord, Slack, Mastodon, Reddit)")
    status: Literal["success", "failed"] = Field(..., description="Posting outcome: 'success' or 'failed'")
    posted_url: Optional[str] = Field(None, description="Published content URL, or null if failed")
    public_access: bool = Field(..., description="Whether content is publicly accessible")
    date: Optional[str] = Field(None, description="Posting date in YYYY-MM-DD format")
    time: Optional[str] = Field(None, description="Posting time in HH:MM:SS format")
    error: Optional[str] = Field(None, description="Error details if status is 'failed', else null")


class PostingResponse(BaseModel):
    """Aggregate response returned by POST /posting."""
    success: bool = Field(True, description="True if at least one platform succeeded or all finished")
    results: List[PlatformResult] = Field(..., description="List of individual posting results across all 5 platforms")


class ErrorResponse(BaseModel):
    """Standardized validation or server error response."""
    success: bool = Field(False, description="Always false for error responses")
    error: str = Field(..., description="Error summary title")
    detail: Optional[str] = Field(None, description="Detailed explanation of the validation error")
