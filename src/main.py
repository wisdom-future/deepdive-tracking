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
        """Initialize database tables and apply pending migrations.

        This endpoint:
        1. Creates all base tables using SQLAlchemy metadata
        2. Applies column additions from Alembic migrations using raw SQL

        Safe to call multiple times - checks existing columns before adding.

        Uses Cloud SQL Connector in Cloud Run for secure database access.

        Returns:
            dict: Migration status.
        """
        logger = logging.getLogger(__name__)
        logger.info("Database initialization request received")

        try:
            # Ensure the database connection is initialized (uses Cloud SQL Connector in Cloud Run)
            from src.database.connection import _init_db, _engine
            from src.models import Base

            _init_db()
            logger.info("Database connection initialized via Cloud SQL Connector")

            if _engine is None:
                logger.error("Failed to initialize database engine")
                return {
                    "status": "error",
                    "message": "Failed to initialize database engine",
                    "timestamp": datetime.now().isoformat()
                }

            logger.info("Creating base database tables using SQLAlchemy...")

            # Step 1: Create all tables defined in models
            Base.metadata.create_all(bind=_engine)
            logger.info("Base tables created successfully")

            # Step 2: Apply migration 002 - add English summary fields
            # Check if columns already exist before adding them
            logger.info("Checking for English summary columns...")

            from sqlalchemy import text

            with _engine.begin() as connection:
                # For PostgreSQL, check information_schema
                try:
                    result = connection.execute(
                        text("SELECT column_name FROM information_schema.columns "
                             "WHERE table_name='processed_news' AND column_name='summary_pro_en'")
                    )
                    has_summary_pro_en = result.fetchone() is not None
                except Exception as check_e:
                    logger.warning(f"Could not check for summary_pro_en: {check_e}")
                    has_summary_pro_en = False

                # Add summary_pro_en column if it doesn't exist
                if not has_summary_pro_en:
                    logger.info("Adding summary_pro_en column...")
                    try:
                        connection.execute(
                            text("ALTER TABLE processed_news ADD COLUMN summary_pro_en TEXT NULL")
                        )
                        logger.info("summary_pro_en column added successfully")
                    except Exception as add_e:
                        logger.warning(f"Could not add summary_pro_en: {add_e}")

                # Add summary_sci_en column if it doesn't exist
                try:
                    result = connection.execute(
                        text("SELECT column_name FROM information_schema.columns "
                             "WHERE table_name='processed_news' AND column_name='summary_sci_en'")
                    )
                    has_summary_sci_en = result.fetchone() is not None
                except Exception as check_e:
                    logger.warning(f"Could not check for summary_sci_en: {check_e}")
                    has_summary_sci_en = False

                if not has_summary_sci_en:
                    logger.info("Adding summary_sci_en column...")
                    try:
                        connection.execute(
                            text("ALTER TABLE processed_news ADD COLUMN summary_sci_en TEXT NULL")
                        )
                        logger.info("summary_sci_en column added successfully")
                    except Exception as add_e:
                        logger.warning(f"Could not add summary_sci_en: {add_e}")

            logger.info("Database initialization completed successfully")

            return {
                "status": "success",
                "message": "Database tables initialized and migrations applied successfully",
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

            # Get sample of raw news to check for errors
            samples = session.query(RawNews).limit(1).all()
            sample_data = None
            if samples:
                news = samples[0]
                sample_data = {
                    "id": str(news.id),
                    "title": news.title[:100] if news.title else None,
                    "status": news.status,
                    "is_duplicate": news.is_duplicate,
                    "published_at": news.published_at.isoformat() if news.published_at else None
                }

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
                "sample_raw_news": sample_data,
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

    @app.post("/seed-test-data")
    async def seed_test_data() -> dict:
        """Seed the database with test processed news data for email/publishing testing.

        This creates processed news records from collected raw news so the email
        and publishing functions can be tested without waiting for AI scoring.

        Also updates existing records to fill in missing English summaries.

        Returns:
            dict: Number of processed news records created or updated.
        """
        logger = logging.getLogger(__name__)
        logger.info("Test data seeding request received")

        try:
            from src.database.connection import get_session
            from src.models import RawNews, ProcessedNews

            session = get_session()

            # First, update existing records that have NULL English summaries
            logger.info("Updating existing records with NULL English summaries...")
            existing_null = session.query(ProcessedNews).filter(
                ProcessedNews.summary_pro_en.is_(None) | ProcessedNews.summary_sci_en.is_(None)
            ).all()

            updated_count = 0
            for processed in existing_null:
                title = processed.raw_news.title if processed.raw_news else "AI News Article"

                # Update with realistic English summaries
                if processed.summary_pro_en is None:
                    processed.summary_pro_en = (
                        f"This article discusses recent important advances in the AI field. "
                        f"The title mentions '{title[:30]}...', covering the latest technological breakthroughs and industry trends. "
                        f"This news reflects the continuous progress of AI technology and provides valuable reference for technology practitioners."
                    )

                if processed.summary_sci_en is None:
                    processed.summary_sci_en = (
                        f"This is a news report related to AI. "
                        f"The article titled '{title[:30]}...' introduces readers to the latest developments in the AI field. "
                        f"In an accessible way, it explains the practical significance and application prospects of this development."
                    )

                session.merge(processed)
                updated_count += 1

            if updated_count > 0:
                session.commit()
                logger.info(f"Updated {updated_count} existing records with English summaries")

            # Then, get raw news articles that don't have processed records yet
            unprocessed = session.query(RawNews).filter(
                ~RawNews.id.in_(
                    session.query(ProcessedNews.raw_news_id)
                )
            ).limit(5).all()

            created_count = 0
            if unprocessed:
                for raw_news in unprocessed:
                    # Generate realistic test summaries
                    title = raw_news.title if raw_news.title else "AI News Article"

                    # Professional summary (Chinese)
                    summary_pro = (
                        f"这篇文章讨论了近期AI领域的重要进展。"
                        f"标题为《{title[:30]}...》，内容涉及最新的技术突破和行业动向。"
                        f"该新闻反映了AI技术在持续进步，为相关从业者和技术决策者提供了有价值的参考信息。"
                    )

                    # Scientific summary (Chinese)
                    summary_sci = (
                        f"这是关于AI相关的新闻报道。"
                        f"文章标题《{title[:30]}...》向读者介绍了AI领域的最新发展。"
                        f"通过通俗易懂的方式，文章阐述了这一进展的现实意义和应用前景。"
                    )

                    # Professional summary (English)
                    summary_pro_en = (
                        f"This article discusses recent important advances in the AI field. "
                        f"The title mentions '{title[:30]}...', covering the latest technological breakthroughs and industry trends. "
                        f"This news reflects the continuous progress of AI technology and provides valuable reference for technology practitioners."
                    )

                    # Scientific summary (English)
                    summary_sci_en = (
                        f"This is a news report related to AI. "
                        f"The article titled '{title[:30]}...' introduces readers to the latest developments in the AI field. "
                        f"In an accessible way, it explains the practical significance and application prospects of this development."
                    )

                    processed = ProcessedNews(
                        raw_news_id=raw_news.id,
                        score=75,  # Test score
                        category="tech_breakthrough",
                        summary_pro=summary_pro,
                        summary_sci=summary_sci,
                        summary_pro_en=summary_pro_en,
                        summary_sci_en=summary_sci_en,
                        keywords=["AI", "technology", "advancement"],
                        confidence=0.85
                    )
                    session.add(processed)
                    created_count += 1

                session.commit()
                logger.info(f"Created {created_count} new processed news records")

            session.close()

            return {
                "status": "success",
                "created_count": created_count,
                "updated_count": updated_count,
                "message": f"Created {created_count} new records and updated {updated_count} existing records with English summaries",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Test data seeding failed: {e}", exc_info=True)
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

    @app.post("/test-github-publisher")
    async def test_github_publisher() -> dict:
        """Test GitHub publisher functionality.

        Returns:
            dict: GitHub publisher test status.
        """
        logger = logging.getLogger(__name__)
        logger.info("GitHub publisher test request received")

        try:
            # Run the GitHub publisher script
            project_root = Path(__file__).parent.parent
            github_script = project_root / "scripts" / "publish" / "github-publisher.py"

            logger.info(f"Executing GitHub publisher script: {github_script}")

            result = subprocess.run(
                ["python", str(github_script)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(project_root)
            )

            logger.info(f"GitHub publisher script exit code: {result.returncode}")

            return {
                "status": "success" if result.returncode == 0 else "failed",
                "exit_code": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"GitHub publisher test failed: {e}", exc_info=True)
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
