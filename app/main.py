"""
FastAPI application entrypoint for Automated Multi-Platform Posting System.
Directly aligned with python-post-message.md specifications.
"""

import os
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.schemas import PostingRequest, PostingResponse, ErrorResponse
from app.utils.validators import validate_posting_message
from app.services.posting_service import PostingService

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)
logger = logging.getLogger("automated-posting-api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle startup and shutdown logs."""
    settings = get_settings()
    logger.info("Starting Automated Multi-Platform Posting System on %s:%s", settings.HOST, settings.PORT)
    logger.info("Simulation fallback enabled: %s", settings.ENABLE_SIMULATION_FALLBACK)
    yield
    logger.info("Shutting down Automated Multi-Platform Posting System")


app = FastAPI(
    title="Automated Multi-Platform Posting System API",
    description=(
        "Production-grade FastAPI service that automatically publishes short marketing announcements "
        "with exactly one CTA link across multiple third-party platforms (Telegram, Discord, Slack, "
        "Mastodon, Reddit) with independent failure isolation and unified reporting."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# CORS Middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount Static Files for Dashboard UI
STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")
STATIC_INDEX = os.path.join(STATIC_DIR, "index.html")

if os.path.exists(STATIC_DIR):
    app.mount("/static", StaticFiles(directory=STATIC_DIR), name="static")

# Shared posting service singleton
posting_service = PostingService()


@app.get("/", tags=["UI & System"])
async def root(request: Request):
    """Serve the Web Dashboard to browsers, or JSON metadata to API clients."""
    accept = request.headers.get("accept", "")
    if "text/html" in accept and os.path.exists(STATIC_INDEX):
        return FileResponse(STATIC_INDEX)
    settings = get_settings()
    return {
        "status": "online",
        "service": "Automated Multi-Platform Posting System",
        "version": "1.0.0",
        "docs": "/docs",
        "dashboard": "/dashboard",
        "endpoint": "POST /posting",
        "platforms_supported": [p["platform"] for p in posting_service.get_platforms_overview()],
    }


@app.get("/dashboard", tags=["UI & System"])
async def dashboard():
    """Direct route to access the interactive web dashboard."""
    if os.path.exists(STATIC_INDEX):
        return FileResponse(STATIC_INDEX)
    return JSONResponse(status_code=404, content={"error": "Dashboard UI not found"})


@app.get("/health", tags=["System"])
async def health_check():
    """System health check and credentials status."""
    settings = get_settings()
    return {
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
        "simulation_fallback_enabled": settings.ENABLE_SIMULATION_FALLBACK,
        "configured_platforms": {
            "telegram": bool(settings.TELEGRAM_BOT_TOKEN and settings.TELEGRAM_CHAT_ID),
            "discord": bool(settings.DISCORD_WEBHOOK_URL),
            "slack": bool(settings.SLACK_WEBHOOK_URL),
            "mastodon": bool(settings.MASTODON_ACCESS_TOKEN),
            "reddit": bool(settings.REDDIT_CLIENT_ID and settings.REDDIT_CLIENT_SECRET),
        },
    }


@app.get("/platforms", tags=["Platforms"])
async def list_platforms():
    """List registered platforms and their driver metadata."""
    return {"platforms": posting_service.get_platforms_overview()}


@app.post(
    "/posting",
    response_model=PostingResponse,
    responses={
        422: {"model": ErrorResponse, "description": "Validation error: Message length or CTA link invalid"},
        500: {"model": ErrorResponse, "description": "Internal dispatch error"},
    },
    summary="Publish short message with 1 CTA link across all 5 platforms",
    tags=["Posting"],
)
async def post_message(payload: PostingRequest):
    """
    Validate and automatically broadcast message across all integrated platforms:
    - Enforces <= 200 characters limit.
    - Requires exactly one valid CTA link.
    - Dispatches concurrently to Telegram, Discord, Slack, Mastodon, and Reddit.
    - Isolates failures: if one platform fails, all others complete independently.
    - Returns standardized status, posted URLs, public access, date, and time.
    """
    raw_message = payload.message.strip()
    logger.info("Received posting request: %s", raw_message[:60])

    # 1. Input Validation
    is_valid, error_msg, cta_url = validate_posting_message(raw_message)
    if not is_valid:
        logger.warning("Posting input validation failed: %s", error_msg)
        return JSONResponse(
            status_code=422,
            content=ErrorResponse(
                success=False,
                error="Input Validation Error",
                detail=error_msg,
            ).model_dump(),
        )

    # 2. Concurrently broadcast across all 5 platforms
    try:
        results = await posting_service.publish_to_all(message=raw_message, cta_url=cta_url)
        return PostingResponse(
            success=True,
            results=results,
        )
    except Exception as e:
        logger.error("Unexpected error during multi-platform broadcast: %s", str(e))
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=ErrorResponse(
                success=False,
                error="Internal Dispatch Error",
                detail=str(e),
            ).model_dump(),
        )


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
