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

        Uses Cloud SQL Connector in Cloud Run for secure database access.

        Returns:
            dict: Migration status.
        """
        logger = logging.getLogger(__name__)
        logger.info("Database initialization request received")

        try:
            # Ensure the database connection is initialized (uses Cloud SQL Connector in Cloud Run)
            from src.database.connection import _init_db, _engine
            _init_db()
            logger.info("Database connection initialized via Cloud SQL Connector")

            # Use SQLAlchemy to create tables directly instead of Alembic
            # This works with Cloud SQL Connector since we already have an initialized engine
            from src.models import Base

            logger.info("Creating database tables using SQLAlchemy...")

            # Create all tables defined in the ORM models
            Base.metadata.create_all(bind=_engine)

            logger.info("Database tables created successfully")

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

    @app.get("/diagnose/database")
    async def diagnose_database() -> dict:
        """Diagnostic endpoint to check database status and data.

        Returns:
            dict: Database diagnostics including record counts and table status.
        """
        logger = logging.getLogger(__name__)
        logger.info("Database diagnostic request received")

        try:
            from src.database.connection import get_session
            from src.models import RawNews, ProcessedNews

            session = get_session()

            # Count records in each table
            raw_count = session.query(RawNews).count()
            processed_count = session.query(ProcessedNews).count()

            session.close()

            issues = []
            if raw_count == 0:
                issues.append("No raw news data in database")
            if processed_count == 0:
                issues.append("No processed news data in database")

            return {
                "status": "success",
                "raw_news_count": raw_count,
                "processed_news_count": processed_count,
                "has_data": raw_count > 0 and processed_count > 0,
                "issues": issues,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Database diagnostic failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }

    @app.post("/test-email")
    async def test_email() -> dict:
        """Test email sending functionality.

        Returns:
            dict: Email test status.
        """
        logger = logging.getLogger(__name__)
        logger.info("Email test request received")

        try:
            # Run the email sending script
            project_root = Path(__file__).parent.parent
            email_script = project_root / "scripts" / "publish" / "send_top_news_email.py"

            logger.info(f"Executing email script: {email_script}")

            result = subprocess.run(
                ["python", str(email_script)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(project_root)
            )

            logger.info(f"Email script exit code: {result.returncode}")

            return {
                "status": "success" if result.returncode == 0 else "failed",
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Email test failed: {e}", exc_info=True)
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
