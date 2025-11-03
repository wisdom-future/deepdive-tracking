"""FastAPI application entry point for DeepDive Tracking."""

import asyncio
import json
import logging
import subprocess
from datetime import datetime
from pathlib import Path

from fastapi import FastAPI, Response
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

    @app.post("/init-db")
    async def init_database() -> dict:
        """Initialize database tables (runs alembic migrations).

        This endpoint runs alembic upgrade head to create all required tables.
        Safe to call multiple times - alembic tracks applied migrations.

        Returns:
            dict: Migration status.
        """
        logger = logging.getLogger(__name__)
        logger.info("Database initialization request received")

        try:
            # Import alembic tools
            from alembic.config import Config
            from alembic import command

            project_root = Path(__file__).parent.parent
            alembic_cfg = Config(str(project_root / "alembic.ini"))

            # Get database URL from settings
            settings = get_settings()
            alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)

            logger.info(f"Running migrations with database: {settings.database_url[:50]}...")

            # Run migrations
            command.upgrade(alembic_cfg, "head")

            logger.info("Database initialization completed successfully")
            return {
                "status": "success",
                "message": "Database tables initialized successfully",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Database initialization failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": f"Database initialization failed: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }

    @app.post("/trigger-workflow")
    @app.post("/")
    async def trigger_workflow() -> dict:
        """Trigger daily workflow via Cloud Scheduler.

        Executes: collect → score → email → github

        Returns:
            dict: Workflow execution status.
        """
        logger = logging.getLogger(__name__)
        logger.info("Workflow trigger received")

        try:
            # Get project root
            project_root = Path(__file__).parent.parent
            workflow_script = project_root / "scripts" / "publish" / "daily_complete_workflow.py"

            if not workflow_script.exists():
                logger.error(f"Workflow script not found: {workflow_script}")
                return {
                    "status": "error",
                    "message": f"Workflow script not found: {workflow_script}",
                    "timestamp": datetime.now().isoformat()
                }

            logger.info(f"Executing workflow: {workflow_script}")

            # Run the workflow script
            result = subprocess.run(
                ["python", str(workflow_script)],
                capture_output=True,
                text=True,
                timeout=900,  # 15 minutes
                cwd=str(project_root)
            )

            logger.info(f"Workflow exit code: {result.returncode}")

            # Check if there's a results JSON file
            logs_dir = project_root / "logs"
            if logs_dir.exists():
                # Find the most recent workflow log
                log_files = sorted(logs_dir.glob("workflow_*.json"), reverse=True)
                if log_files:
                    try:
                        with open(log_files[0], 'r', encoding='utf-8') as f:
                            workflow_result = json.load(f)
                        logger.info(f"Workflow completed with status: {workflow_result.get('status')}")
                        return {
                            "status": "completed",
                            "workflow_status": workflow_result.get("status"),
                            "details": workflow_result,
                            "timestamp": datetime.now().isoformat()
                        }
                    except Exception as e:
                        logger.error(f"Failed to read workflow result: {e}")

            return {
                "status": "success" if result.returncode == 0 else "failed",
                "exit_code": result.returncode,
                "stdout": result.stdout[-500:] if result.stdout else "",  # Last 500 chars
                "stderr": result.stderr[-500:] if result.stderr else "",
                "timestamp": datetime.now().isoformat()
            }

        except subprocess.TimeoutExpired:
            logger.error("Workflow execution timeout")
            return {
                "status": "error",
                "message": "Workflow execution timeout (15 minutes)",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            logger.error(f"Workflow execution error: {e}")
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }

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
