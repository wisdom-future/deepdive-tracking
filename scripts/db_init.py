#!/usr/bin/env python3
"""Initialize database tables for Cloud Run"""
import sys
import os
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Set environment for Cloud SQL if running in Cloud Run
if os.getenv("K_SERVICE"):
    os.environ["CLOUDSQL_USER"] = os.getenv("CLOUDSQL_USER", "deepdive_user")
    os.environ["CLOUDSQL_PASSWORD"] = os.getenv("CLOUDSQL_PASSWORD", "deepdive_password")
    os.environ["CLOUDSQL_DATABASE"] = os.getenv("CLOUDSQL_DATABASE", "deepdive_db")

print("[DB] Initializing database tables...")

try:
    from alembic.config import Config
    from alembic import command
    
    # Setup alembic
    alembic_cfg = Config(str(project_root / "alembic.ini"))
    
    # Get DB URL from settings
    from src.config import get_settings
    settings = get_settings()
    
    print(f"[DB] Using database: {settings.database_url[:50]}...")
    alembic_cfg.set_main_option("sqlalchemy.url", settings.database_url)
    
    # Run migrations
    print("[DB] Running alembic upgrade head...")
    command.upgrade(alembic_cfg, "head")
    print("[DB] ✓ Database initialization completed successfully!")
    
except Exception as e:
    print(f"[DB] ✗ Database initialization failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
