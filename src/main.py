"""FastAPI application entry point for DeepDive Tracking."""

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src import __version__
from src.config import get_settings
from src.api.v1.endpoints import news, processed_news, statistics


def create_app() -> FastAPI:
    """Create and configure FastAPI application.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        description="AI-powered news tracking platform for technology decision makers",
        version=__version__,
        debug=settings.debug,
    )

    # Configure CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Configure logging
    logging.basicConfig(level=settings.log_level)

    # Health check endpoint
    @app.get("/health")
    async def health_check() -> dict[str, str]:
        """Health check endpoint.

        Returns:
            dict: Health status.
        """
        return {"status": "ok", "version": __version__}

    @app.get("/")
    async def root() -> dict[str, str]:
        """Root endpoint.

        Returns:
            dict: Welcome message.
        """
        return {"message": "Welcome to DeepDive Tracking API"}

    # Include API routers
    app.include_router(news.router, prefix="/api/v1")
    app.include_router(processed_news.router, prefix="/api/v1")
    app.include_router(statistics.router, prefix="/api/v1")

    return app


# Create application instance
app = create_app()


if __name__ == "__main__":
    import uvicorn

    settings = get_settings()
    uvicorn.run(
        "src.main:app",
        host=settings.server_host,
        port=settings.server_port,
        reload=settings.debug,
    )
