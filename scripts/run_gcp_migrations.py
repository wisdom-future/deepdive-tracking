#!/usr/bin/env python3
"""Run Alembic migrations on GCP Cloud SQL database.

This script connects to the Cloud SQL database and runs all pending migrations.

Usage:
    python scripts/run_gcp_migrations.py
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from alembic.config import Config
from alembic import command
from src.database import engine


def run_migrations():
    """Run all pending migrations on the GCP database."""
    print("=" * 80)
    print("Running database migrations on GCP Cloud SQL")
    print("=" * 80)
    print()

    print(f"✓ Connected to database")
    print()

    # Set up Alembic config
    alembic_cfg = Config(str(project_root / "alembic.ini"))
    alembic_cfg.set_main_option("script_location", str(project_root / "alembic"))

    # Run migrations using the existing connection
    with engine.connect() as connection:
        alembic_cfg.attributes["connection"] = connection

        print("Running migrations...")
        try:
            command.upgrade(alembic_cfg, "head")
            print()
            print("=" * 80)
            print("✓ All migrations completed successfully")
            print("=" * 80)
        except Exception as e:
            print()
            print("=" * 80)
            print(f"✗ Migration failed: {e}")
            print("=" * 80)
            raise


if __name__ == "__main__":
    run_migrations()
