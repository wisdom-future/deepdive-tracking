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
from src.api.v1.endpoints import news, processed_news, statistics, workflows, migrations, database_fix


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

            # Step 3: Initialize data sources
            logger.info("Initializing data sources...")
            from src.services.setup.data_source_manager import initialize_data_sources

            try:
                stats = initialize_data_sources()
                logger.info(f"Data sources initialized: {stats}")
            except Exception as sources_e:
                logger.warning(f"Data source initialization had an issue: {sources_e}")

            return {
                "status": "success",
                "message": "Database tables initialized, migrations applied, and data sources initialized",
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

    @app.get("/data/news")
    async def get_news_data(limit: int = 100, offset: int = 0, table: str = "processed") -> dict:
        """Get news data from database.

        Args:
            limit: Number of records to return (max 100)
            offset: Record offset for pagination
            table: Which table to query ("raw", "processed")

        Returns:
            dict: News data with pagination info.
        """
        logger = logging.getLogger(__name__)
        logger.info(f"News data request: table={table}, limit={limit}, offset={offset}")

        try:
            from src.database.connection import get_session
            from src.models import RawNews, ProcessedNews

            session = get_session()
            limit = min(limit, 100)  # Max 100 records

            if table == "raw":
                total = session.query(RawNews).count()
                records = session.query(RawNews).offset(offset).limit(limit).all()
                data = [{
                    "id": str(r.id),
                    "title": r.title,
                    "url": r.url,
                    "source_name": r.source_name,
                    "author": r.author,
                    "published_at": r.published_at.isoformat() if r.published_at else None,
                    "status": r.status,
                    "is_duplicate": r.is_duplicate
                } for r in records]
            else:  # processed
                total = session.query(ProcessedNews).count()
                records = session.query(ProcessedNews).offset(offset).limit(limit).all()
                data = [{
                    "id": str(p.id),
                    "raw_news_id": str(p.raw_news_id),
                    "title": str(p.raw_news.title) if (p.raw_news and p.raw_news.title) else "Unknown",
                    "score": float(p.score) if p.score is not None else 0.0,
                    "category": str(p.category) if p.category else "unknown",
                    "summary_zh": str(p.summary_pro or p.summary_sci or "No summary available"),
                    "summary_en": str((p.summary_pro_en or p.summary_sci_en) or "No English summary available"),
                    "confidence": float(p.confidence) if p.confidence is not None else 0.0,
                    "created_at": p.created_at.isoformat() if p.created_at else None
                } for p in records]

            session.close()

            return {
                "status": "success",
                "table": table,
                "total_records": total,
                "returned_records": len(data),
                "limit": limit,
                "offset": offset,
                "data": data,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"News data query failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }

    @app.post("/clean-database")
    async def clean_database() -> dict:
        """清空数据库所有数据（仅保留data_sources）

        用于端到端测试前的完全重置

        Returns:
            dict: 清空结果
        """
        logger = logging.getLogger(__name__)
        logger.info("Database clean request received")

        try:
            from src.database.connection import get_session
            from src.models import RawNews, ProcessedNews, PublishedContent, CostLog

            session = get_session()

            # 统计
            raw_before = session.query(RawNews).count()
            processed_before = session.query(ProcessedNews).count()

            logger.info(f"Before clean: raw_news={raw_before}, processed_news={processed_before}")

            # 按依赖顺序删除 (cost_log必须在processed_news之前删除，因为有外键约束)
            deleted_published = session.query(PublishedContent).delete()
            deleted_cost = session.query(CostLog).delete()
            deleted_processed = session.query(ProcessedNews).delete()
            deleted_raw = session.query(RawNews).delete()

            session.commit()

            # 验证
            raw_after = session.query(RawNews).count()
            processed_after = session.query(ProcessedNews).count()

            session.close()

            logger.info(f"After clean: raw_news={raw_after}, processed_news={processed_after}")

            return {
                "status": "success",
                "deleted": {
                    "raw_news": deleted_raw,
                    "processed_news": deleted_processed,
                    "published_content": deleted_published,
                    "cost_log": deleted_cost
                },
                "verification": {
                    "raw_news_count": raw_after,
                    "processed_news_count": processed_after,
                    "is_clean": raw_after == 0 and processed_after == 0
                },
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Database clean failed: {e}", exc_info=True)
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

    @app.post("/publish/email")
    async def publish_email() -> dict:
        """Publish news via email channel.

        Returns:
            dict: Email publishing status.
        """
        logger = logging.getLogger(__name__)
        logger.info("Email publishing request received")

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
            logger.error(f"Email publishing failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }

    @app.post("/diagnose/score-sample")
    async def diagnose_score_sample(count: int = 5) -> dict:
        """Score a small sample of news for testing.

        Args:
            count: Number of news to score (default 5)

        Returns:
            dict: Scoring results
        """
        logger = logging.getLogger(__name__)
        logger.info(f"Scoring sample diagnostic: {count} items")

        try:
            from src.database.connection import get_session
            from src.models import RawNews, ProcessedNews
            from src.services.ai import ScoringService
            from src.config import get_settings

            session = get_session()
            settings = get_settings()

            # Get unscored news
            unscored = session.query(RawNews).filter(
                ~RawNews.id.in_(session.query(ProcessedNews.raw_news_id))
            ).limit(count).all()

            if not unscored:
                return {
                    "status": "success",
                    "message": "No unscored news found",
                    "timestamp": datetime.now().isoformat()
                }

            logger.info(f"Found {len(unscored)} unscored news")

            # Initialize scoring service
            service = ScoringService(settings, session)
            logger.info(f"Using {settings.ai_provider} with model {service.model}")

            # Score each item
            results = []
            for news in unscored:
                try:
                    logger.info(f"Scoring: {news.title[:50]}")
                    result = await service.score_news(news)
                    await service.save_to_database(news, result)

                    results.append({
                        "title": news.title[:60],
                        "score": result.scoring.score,
                        "summary_pro": result.summaries.summary_pro[:50] if result.summaries.summary_pro else None,
                        "cost": result.metadata.cost
                    })
                except Exception as e:
                    logger.error(f"Failed to score {news.id}: {e}")
                    results.append({
                        "title": news.title[:60],
                        "error": str(e)[:100]
                    })

            session.commit()

            return {
                "status": "success",
                "scored_count": len([r for r in results if 'score' in r]),
                "failed_count": len([r for r in results if 'error' in r]),
                "results": results,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Score sample diagnostic failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }

    @app.post("/fix-simhash-column")
    async def fix_simhash_column() -> dict:
        """Fix content_simhash column type from bigint to numeric.

        Returns:
            dict: Fix result
        """
        logger = logging.getLogger(__name__)
        logger.info("Fixing content_simhash column type")

        try:
            from src.database.connection import get_session
            from sqlalchemy import text

            session = get_session()

            # Alter column type to VARCHAR to support unsigned 64-bit integers as strings
            session.execute(text(
                "ALTER TABLE raw_news ALTER COLUMN content_simhash TYPE VARCHAR(20) USING content_simhash::VARCHAR"
            ))
            session.commit()

            logger.info("Successfully changed content_simhash to VARCHAR(20)")

            return {
                "status": "success",
                "message": "content_simhash column type changed to VARCHAR(20)",
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to fix simhash column: {e}", exc_info=True)
            session.rollback()
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }

    @app.post("/diagnose/collect-all")
    async def diagnose_collect_all() -> dict:
        """Run full collection and return detailed statistics.

        Returns:
            dict: Detailed collection results
        """
        logger = logging.getLogger(__name__)
        logger.info("Full collection diagnostic request")

        try:
            from src.database.connection import get_session
            from src.services.collection import CollectionManager

            session = get_session()
            manager = CollectionManager(session)

            logger.info("Starting collection...")
            stats = await manager.collect_all()
            logger.info(f"Collection completed: {stats}")

            # Get current database counts
            from src.models import RawNews
            raw_count = session.query(RawNews).count()

            return {
                "status": "success",
                "collection_stats": stats,
                "database_count": raw_count,
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Collection diagnostic failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "error_type": type(e).__name__,
                "timestamp": datetime.now().isoformat()
            }

    @app.get("/diagnose/sources")
    async def diagnose_sources() -> dict:
        """List all data sources in database.

        Returns:
            dict: All data sources with details
        """
        logger = logging.getLogger(__name__)
        logger.info("Data sources diagnostic request")

        try:
            from src.database.connection import get_session
            from src.models import DataSource

            session = get_session()

            sources = session.query(DataSource).order_by(DataSource.priority.desc()).all()

            return {
                "status": "success",
                "total_sources": len(sources),
                "sources": [
                    {
                        "id": s.id,
                        "name": s.name,
                        "type": s.type,
                        "url": s.url,
                        "priority": s.priority,
                        "is_enabled": s.is_enabled,
                        "max_items_per_run": s.max_items_per_run
                    }
                    for s in sources
                ],
                "timestamp": datetime.now().isoformat()
            }

        except Exception as e:
            logger.error(f"Sources diagnostic failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }

    @app.post("/diagnose/rss-source")
    async def diagnose_rss_source(source_name: str = "OpenAI News") -> dict:
        """Diagnose RSS collection for a specific source.

        Args:
            source_name: Name of the data source to test

        Returns:
            dict: Detailed diagnostic information
        """
        logger = logging.getLogger(__name__)
        logger.info(f"RSS diagnostic request for source: {source_name}")

        try:
            from src.database.connection import get_session
            from src.models import DataSource
            from src.services.collection.rss_collector import RSSCollector

            session = get_session()

            # Find the source
            source = session.query(DataSource).filter(
                DataSource.name == source_name
            ).first()

            if not source:
                return {
                    "status": "error",
                    "message": f"Source '{source_name}' not found",
                    "timestamp": datetime.now().isoformat()
                }

            # Test RSS collection
            logger.info(f"Testing RSS collection for: {source.url}")
            collector = RSSCollector(source)

            try:
                articles = await collector.collect()

                return {
                    "status": "success",
                    "source": {
                        "name": source.name,
                        "url": source.url,
                        "enabled": source.is_enabled,
                        "priority": source.priority
                    },
                    "result": {
                        "articles_collected": len(articles),
                        "sample_articles": [
                            {
                                "title": a["title"][:60],
                                "url": a["url"],
                                "content_length": len(a.get("content", "")),
                                "published_at": a.get("published_at")
                            }
                            for a in articles[:3]
                        ]
                    },
                    "timestamp": datetime.now().isoformat()
                }
            except Exception as collect_error:
                logger.error(f"Collection failed: {collect_error}", exc_info=True)
                return {
                    "status": "error",
                    "source": {
                        "name": source.name,
                        "url": source.url
                    },
                    "error": str(collect_error),
                    "error_type": type(collect_error).__name__,
                    "timestamp": datetime.now().isoformat()
                }

        except Exception as e:
            logger.error(f"Diagnostic failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }

    @app.post("/publish/github")
    async def publish_github() -> dict:
        """Publish news via GitHub channel.

        Returns:
            dict: GitHub publishing status.
        """
        logger = logging.getLogger(__name__)
        logger.info("GitHub publishing request received")

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
            logger.error(f"GitHub publishing failed: {e}", exc_info=True)
            return {
                "status": "error",
                "message": str(e),
                "timestamp": datetime.now().isoformat()
            }

    # Include API routers
    app.include_router(news.router, prefix="/api/v1")
    app.include_router(processed_news.router, prefix="/api/v1")
    app.include_router(statistics.router, prefix="/api/v1")
    app.include_router(workflows.router, prefix="/api/v1")
    app.include_router(migrations.router, prefix="/api/v1")
    app.include_router(database_fix.router, prefix="/api/v1")

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
