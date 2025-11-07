"""Database fix API endpoints for quick schema updates."""

import logging
from typing import Dict, Any

from fastapi import APIRouter, HTTPException, status
from sqlalchemy import text

from src.database import engine as db_engine

router = APIRouter(prefix="/database-fix", tags=["database-fix"])

logger = logging.getLogger(__name__)


@router.post(
    "/add-content-simhash",
    summary="Add content_simhash column to raw_news table",
    description="Manually add the content_simhash column and index to raw_news table if missing",
    response_model=Dict[str, Any]
)
async def add_content_simhash() -> Dict[str, Any]:
    """Add content_simhash column to raw_news table.

    This endpoint manually adds the content_simhash column and its index
    to the raw_news table if they don't already exist.

    Returns:
        Dict with operation status
    """
    try:
        logger.info("Checking for content_simhash column...")

        with db_engine.connect() as connection:
            # Check if column exists
            result = connection.execute(
                text(
                    "SELECT column_name FROM information_schema.columns "
                    "WHERE table_name='raw_news' AND column_name='content_simhash'"
                )
            )
            has_column = result.fetchone() is not None

            if has_column:
                logger.info("content_simhash column already exists")
                return {
                    "status": "success",
                    "message": "content_simhash column already exists",
                    "added": False
                }

            # Add column
            logger.info("Adding content_simhash column...")
            connection.execute(
                text(
                    "ALTER TABLE raw_news "
                    "ADD COLUMN content_simhash BIGINT NULL"
                )
            )
            connection.commit()
            logger.info("content_simhash column added successfully")

            # Check if index exists
            result = connection.execute(
                text(
                    "SELECT indexname FROM pg_indexes "
                    "WHERE tablename='raw_news' AND indexname='ix_raw_news_content_simhash'"
                )
            )
            has_index = result.fetchone() is not None

            if not has_index:
                # Add index
                logger.info("Creating index on content_simhash...")
                connection.execute(
                    text(
                        "CREATE INDEX ix_raw_news_content_simhash "
                        "ON raw_news (content_simhash)"
                    )
                )
                connection.commit()
                logger.info("Index created successfully")
            else:
                logger.info("Index already exists")

        return {
            "status": "success",
            "message": "content_simhash column and index added successfully",
            "added": True
        }

    except Exception as e:
        logger.error(f"Failed to add content_simhash column: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add content_simhash column: {str(e)}"
        )


@router.get(
    "/check-schema",
    summary="Check raw_news table schema",
    description="Check if the raw_news table has all required columns",
    response_model=Dict[str, Any]
)
async def check_schema() -> Dict[str, Any]:
    """Check raw_news table schema.

    Returns:
        Dict with schema status
    """
    try:
        with db_engine.connect() as connection:
            # Get all columns
            result = connection.execute(
                text(
                    "SELECT column_name, data_type "
                    "FROM information_schema.columns "
                    "WHERE table_name='raw_news'"
                )
            )
            columns = {row[0]: row[1] for row in result.fetchall()}

            # Check for required columns
            required_columns = ["content_simhash"]
            missing_columns = [col for col in required_columns if col not in columns]

        return {
            "status": "success",
            "columns": columns,
            "missing_columns": missing_columns,
            "is_complete": len(missing_columns) == 0
        }

    except Exception as e:
        logger.error(f"Failed to check schema: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to check schema: {str(e)}"
        )
