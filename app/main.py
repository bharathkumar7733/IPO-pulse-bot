from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import settings
from app.core.logging import logger
from app.core.exceptions import register_exception_handlers
from app.core.middleware import RateLimitMiddleware
from app.api.router import api_router

def create_application() -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
        version=settings.VERSION,
        openapi_url=f"{settings.API_V1_STR}/openapi.json",
        docs_url="/docs",
        redoc_url="/redoc",
    )

    # Rate limiting middleware
    app.add_middleware(RateLimitMiddleware, requests_per_minute=120)

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register global exception handlers to prevent raw trace exposure
    register_exception_handlers(app)

    # Include API Router
    app.include_router(api_router)

    logger.info(f"Initialized {settings.PROJECT_NAME} (v{settings.VERSION})")
    return app

app = create_application()
