"""Main entry point for the AarthSaathi Financial Orchestrator API."""

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from api.routes import router as api_router
from config.settings import get_settings
from config.logging_config import configure_logging
from config.paths import server_log_path
import os
from pathlib import Path


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    settings = get_settings()

    # Configure logging
    log_path = Path(os.getenv("LOG_FILE", server_log_path()))
    configure_logging(log_path, verbose_third_party=False)

    app = FastAPI(
        title="AarthSaathi Financial Orchestrator API",
        description="API for financial advice orchestration with scoped authentication",
        version="1.0.0",
    )

    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Configure appropriately for production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include API routes
    app.include_router(api_router, prefix="/api/v1")

    @app.get("/")
    async def root():
        return {
            "message": "AarthSaathi Financial Orchestrator API",
            "docs": "/docs",
            "version": "1.0.0"
        }

    return app


app = create_app()


if __name__ == "__main__":
    settings = get_settings()
    uvicorn.run(
        app,
        host=settings.host,
        port=settings.port,
        log_level="info",
    )