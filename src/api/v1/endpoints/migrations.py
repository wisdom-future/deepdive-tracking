"""Database migration API endpoints."""

import logging
from pathlib import Path
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status
from alembic.config import Config
from alembic import command

from src.database import get_engine

router = APIRouter(prefix="/migrations", tags=["migrations"])

logger = logging.getLogger(__name__)


@router.post(
    "/upgrade",
    summary="Run database migrations",
    description="Execute all pending Alembic migrations to upgrade database schema",
    response_model=Dict[str, Any]
)
async def upgrade_database() -> Dict[str, Any]:
    """Run all pending database migrations.

    This endpoint executes Alembic migrations to upgrade the database schema
    to the latest version. Use this after deploying new code that includes
    database schema changes.

    Returns:
        Dict with migration execution status
    """
    try:
        logger.info("Starting database migration...")

        # Get project root (migrations.py is in src/api/v1/endpoints/)
        project_root = Path(__file__).parent.parent.parent.parent.parent

        # Set up Alembic config
        alembic_cfg = Config(str(project_root / "alembic.ini"))
        alembic_cfg.set_main_option("script_location", str(project_root / "alembic"))

        # Get database engine
        engine = get_engine()

        # Run migrations
        with engine.connect() as connection:
            alembic_cfg.attributes["connection"] = connection

            logger.info("Running migrations...")
            command.upgrade(alembic_cfg, "head")
            logger.info("Migrations completed successfully")

        return {
            "status": "success",
            "message": "Database migrations completed successfully"
        }

    except Exception as e:
        logger.error(f"Migration failed: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Migration failed: {str(e)}"
        )


@router.get(
    "/current",
    summary="Get current migration version",
    description="Check the current database schema version",
    response_model=Dict[str, Any]
)
async def get_current_version() -> Dict[str, Any]:
    """Get the current database migration version.

    Returns:
        Dict with current migration version
    """
    try:
        from alembic.runtime.migration import MigrationContext

        engine = get_engine()

        with engine.connect() as connection:
            context = MigrationContext.configure(connection)
            current_rev = context.get_current_revision()

        return {
            "status": "success",
            "current_version": current_rev or "no migrations applied"
        }

    except Exception as e:
        logger.error(f"Failed to get current version: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get current version: {str(e)}"
        )
