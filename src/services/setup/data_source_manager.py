"""Data source management service.

This service handles initialization and management of data sources.
"""

import logging
from typing import Dict, List

from src.database.connection import get_session
from src.models import DataSource
from src.config.data_sources import get_data_sources

logger = logging.getLogger(__name__)


def initialize_data_sources() -> Dict[str, int]:
    """Initialize data sources in the database.

    Adds all predefined data sources that don't already exist.

    Returns:
        dict: Statistics about initialization:
            - total_sources: Total sources in database after init
            - newly_added: Number of sources added
            - skipped: Number of sources already existing

    Raises:
        Exception: If database operation fails
    """
    session = get_session()

    try:
        sources_to_add = get_data_sources()

        # Get existing sources
        existing = session.query(DataSource).all()
        existing_names = {ds.name for ds in existing}
        existing_urls = {ds.url for ds in existing}

        newly_added = 0
        skipped = 0

        # Add new sources
        for source_data in sources_to_add:
            name = source_data.get('name')
            url = source_data.get('url')

            # Skip if already exists
            if name in existing_names or url in existing_urls:
                logger.info(f"Skipped (already exists): {name}")
                skipped += 1
                continue

            try:
                source = DataSource(**source_data)
                session.add(source)
                newly_added += 1
                logger.info(f"Added data source: {name}")
            except Exception as e:
                logger.error(f"Failed to add source {name}: {e}")

        # Commit all changes
        session.commit()

        # Get final count
        total_sources = session.query(DataSource).count()

        logger.info(
            f"Data source initialization complete: "
            f"{newly_added} added, {skipped} skipped, "
            f"{total_sources} total"
        )

        return {
            'total_sources': total_sources,
            'newly_added': newly_added,
            'skipped': skipped,
        }

    except Exception as e:
        session.rollback()
        logger.error(f"Failed to initialize data sources: {e}", exc_info=True)
        raise
    finally:
        session.close()


def list_data_sources(enabled_only: bool = False) -> List[Dict]:
    """List all data sources in the database.

    Args:
        enabled_only: If True, only return enabled sources

    Returns:
        list: List of data source information
    """
    session = get_session()

    try:
        query = session.query(DataSource)
        if enabled_only:
            query = query.filter(DataSource.is_enabled == True)

        sources = query.all()
        return [
            {
                'id': s.id,
                'name': s.name,
                'type': s.type,
                'priority': s.priority,
                'is_enabled': s.is_enabled,
            }
            for s in sources
        ]
    finally:
        session.close()
