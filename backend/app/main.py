"""
EchoEmotion – FastAPI Application Entry Point
=========================================
Production-ready Speech Emotion Recognition API
"""
import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from app.api.v1.router import router as v1_router
from app.core.config import get_settings
from app.core.logging import setup_logging

settings = get_settings()
setup_logging(debug=settings.DEBUG)
logger = logging.getLogger(__name__)

# ── Rate limiter ──────────────────────────────────────────────────────────────
limiter = Limiter(key_func=get_remote_address, default_limits=["30/minute"])


# ── Lifespan ──────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("🚀 %s v%s starting up …", settings.APP_NAME, settings.APP_VERSION)
    # Pre-load predictor (warm-up)
    from app.api.v1.router import get_predictor
    predictor = get_predictor()
    if predictor.is_loaded():
        logger.info("✅ Model loaded at startup.")
    else:
        logger.warning("⚠️  No trained model found. POST /api/v1/train to train.")
    yield
    logger.info("👋 Shutting down …")


# ── App factory ───────────────────────────────────────────────────────────────
def create_app() -> FastAPI:
    app = FastAPI(
        
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "## Speech Emotion Recognition API\n\n"
            "Detect emotions (calm, happy, fearful, disgust) from audio files "
            "using a multi-model ML pipeline trained on RAVDESS dataset.\n\n"
            "**GitHub**: https://github.com/your-username/echoemotion"
        ),
        openapi_url="/api/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
        lifespan=lifespan,
    )
    @app.middleware("http")
    async def log_requests(request, call_next):
        logger.info("Incoming request: %s %s",
                    request.method,
                    request.url.path)

        response = await call_next(request)

        logger.info("Response status: %s",
                    response.status_code)

        return response

    # ── Middleware ─────────────────────────────────────────────────────────────
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ── Rate limiting ──────────────────────────────────────────────────────────
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

    # ── Request timing middleware ──────────────────────────────────────────────
    @app.middleware("http")
    async def add_process_time(request: Request, call_next):
        t0 = time.perf_counter()
        response = await call_next(request)
        elapsed_ms = round((time.perf_counter() - t0) * 1000, 1)
        response.headers["X-Process-Time-Ms"] = str(elapsed_ms)
        return response

    # ── Global exception handler ───────────────────────────────────────────────
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled exception: %s", exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error.", "type": type(exc).__name__},
        )

    # ── Routes ─────────────────────────────────────────────────────────────────
    app.include_router(v1_router, prefix="/api/v1")

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
        log_level="debug" if settings.DEBUG else "info",
    )
