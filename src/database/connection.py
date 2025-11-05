"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from typing import Optional
import os
import sys
import traceback

from src.config import get_settings

# Lazy initialization of database engine and session factory
_engine: Optional[object] = None
_SessionLocal: Optional[sessionmaker] = None


def _init_db():
    """Initialize database engine and session factory (lazy initialization)."""
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_settings()

        # Check if running in Cloud Run environment
        # Cloud Run sets K_SERVICE env var, or we can check for localhost in DB URL
        is_cloud_run = os.getenv("K_SERVICE") or os.getenv("CLOUD_RUN")

        # Check if DATABASE_URL looks like a Unix socket format (contains @/ without host)
        # This indicates Cloud SQL Unix socket which only works with Cloud SQL Connector in Cloud Run
        looks_like_cloud_sql_socket = settings.database_url and "@/" in settings.database_url

        print(f"[DB] Environment check: K_SERVICE={os.getenv('K_SERVICE')}, CLOUD_RUN={os.getenv('CLOUD_RUN')}")
        print(f"[DB] DATABASE_URL pattern: {settings.database_url[:50] if settings.database_url else 'None'}...")

        if is_cloud_run or looks_like_cloud_sql_socket:
            print("[DB] Detected Cloud Run environment - USING Cloud SQL Connector")
            _init_db_cloud_sql(settings)
        else:
            print("[DB] Local environment - using direct connection")
            _init_db_direct(settings)


def _init_db_cloud_sql(settings):
    """Initialize database with Cloud SQL Python Connector for Cloud Run."""
    global _engine, _SessionLocal

    try:
        print("[DB] Attempting to import Cloud SQL Connector...")
        from google.cloud.sql.connector import Connector, IPTypes

        print("[DB] Initializing Cloud SQL Connector for Cloud Run")
        instance_name = os.getenv("CLOUDSQL_INSTANCE", "deepdive-engine:asia-east1:deepdive-db")
        print(f"[DB] Connection string: {instance_name}")
        print(f"[DB] Database user: {os.getenv('CLOUDSQL_USER', 'deepdive_user')}")

        # Determine IP type: Use PUBLIC by default since Cloud SQL may not have private IP configured
        # This is safer and works for most Cloud Run setups
        ip_type = IPTypes.PUBLIC
        print(f"[DB] Using IPTypes.PUBLIC for Cloud SQL connection")

        # Create connector - this handles all authentication via GCP service account
        print("[DB] Creating Connector instance...")
        connector = Connector()
        print("[DB] Connector created successfully")

        def getconn():
            """Get a connection from Cloud SQL Connector."""
            print("[DB] getconn() called - requesting connection from Cloud SQL Connector")
            db_user = os.getenv("CLOUDSQL_USER", "deepdive_user")
            db_name = os.getenv("CLOUDSQL_DATABASE", "deepdive_db")
            instance_connection_name = os.getenv(
                "CLOUDSQL_INSTANCE",
                "deepdive-engine:asia-east1:deepdive-db"
            )

            print(f"[DB] Connecting to instance: {instance_connection_name}")
            print(f"[DB] Database: {db_name}, User: {db_user}")
            print("[DB] Using Cloud SQL Connector with IAM authentication (no password required)...")
            # Use IAM authentication - no password needed
            # Cloud SQL Connector automatically uses the service account's IAM credentials
            return connector.connect(
                instance_connection_name,
                "pg8000",
                user=db_user,
                db=db_name,
                ip_type=ip_type,
                enable_iam_auth=True,  # Enable IAM authentication
            )

        # Create engine with Cloud SQL Connector
        print("[DB] Creating SQLAlchemy engine with Cloud SQL Connector...")
        _engine = create_engine(
            "postgresql+pg8000://",
            creator=getconn,
            pool_size=settings.database_pool_size,
            max_overflow=settings.database_max_overflow,
            pool_timeout=settings.database_pool_timeout,
            echo=settings.debug,
            pool_pre_ping=True,  # Test connections before using
        )
        print("[DB] SQLAlchemy engine created successfully")

        _SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=_engine
        )
        print("[DB] Cloud SQL Connector initialized successfully")

    except ImportError as e:
        print(f"[DB] ERROR: Failed to import Cloud SQL Connector: {e}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print(f"[DB] Falling back to direct connection", file=sys.stderr)
        _init_db_direct(settings)
    except Exception as e:
        print(f"[DB] ERROR: Failed to initialize Cloud SQL Connector: {e}", file=sys.stderr)
        print(f"[DB] Exception type: {type(e).__name__}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
        print(f"[DB] Falling back to direct connection", file=sys.stderr)
        _init_db_direct(settings)


def _init_db_direct(settings):
    """Initialize database with direct connection (for local development)."""
    global _engine, _SessionLocal

    print(f"[DB] Initializing direct database connection")
    print(f"[DB] Database URL: {settings.database_url[:50]}...")

    connect_args = {}
    if "sqlite" not in settings.database_url:
        # PostgreSQL-specific arguments
        connect_args["connect_timeout"] = 5

    _engine = create_engine(
        settings.database_url,
        pool_size=settings.database_pool_size,
        max_overflow=settings.database_max_overflow,
        pool_timeout=settings.database_pool_timeout,
        echo=settings.debug,
        connect_args=connect_args,
        pool_pre_ping=True,  # Verify connections are alive
    )

    _SessionLocal = sessionmaker(
        autocommit=False, autoflush=False, bind=_engine
    )
    print("[DB] Direct database connection initialized")


class _SessionLocalProxy:
    """Proxy for lazy-loading SessionLocal."""

    def __call__(self):
        if _SessionLocal is None:
            _init_db()
        return _SessionLocal()

    def __getattr__(self, name):
        if _SessionLocal is None:
            _init_db()
        return getattr(_SessionLocal, name)


# Export SessionLocal as a lazy-loaded proxy
SessionLocal = _SessionLocalProxy()


# Lazy-loaded engine getter (for backward compatibility)
def _get_engine_proxy():
    """Get the database engine (lazy initialization)."""
    if _engine is None:
        _init_db()
    return _engine


# Create a simple proxy for engine that initializes on access
class _EngineProxy:
    """Proxy for lazy-loading the database engine."""

    def __getattr__(self, name):
        if _engine is None:
            _init_db()
        if _engine is None:
            raise RuntimeError("Failed to initialize database engine")
        return getattr(_engine, name)

    def __call__(self, *args, **kwargs):
        if _engine is None:
            _init_db()
        return _engine(*args, **kwargs)


# Export engine as a lazy-loaded proxy for backward compatibility
engine = _EngineProxy()

# Force immediate initialization in Cloud Run to catch errors early
if os.getenv("K_SERVICE") or os.getenv("CLOUD_RUN"):
    print("[DB] Cloud Run detected - initializing database connection immediately...")
    _init_db()


def get_session():
    """Get a database session using the proper connection (Cloud SQL Connector or direct).

    This is the recommended way for scripts to get database sessions,
    as it ensures Cloud SQL Connector is used in Cloud Run.

    Returns:
        Session: SQLAlchemy database session

    Example:
        from src.database.connection import get_session
        session = get_session()
        items = session.query(MyModel).all()
    """
    if _SessionLocal is None:
        _init_db()
    return SessionLocal()


def get_database_url() -> str:
    """Get the database URL for Alembic migrations.

    For Cloud SQL Connector environments, we need to construct a proper URL.
    For direct connections, we use the configured URL directly.

    Returns:
        str: Database URL suitable for SQLAlchemy
    """
    settings = get_settings()

    # Check if running in Cloud Run with Cloud SQL Connector
    is_cloud_run = os.getenv("K_SERVICE") or os.getenv("CLOUD_RUN")
    looks_like_cloud_sql_socket = settings.database_url and "@/" in settings.database_url

    if is_cloud_run or looks_like_cloud_sql_socket:
        # For Cloud SQL Connector, we create a special URL that indicates
        # we're using the connector (environment variables will handle actual connection)
        # We use a dummy URL but Alembic will process via env.py which uses our engine
        db_user = os.getenv("CLOUDSQL_USER", "deepdive_user")
        db_name = os.getenv("CLOUDSQL_DATABASE", "deepdive_db")
        return f"postgresql+pg8000://{db_user}@/deepdive-engine:asia-east1:deepdive-db/{db_name}"
    else:
        # For direct connections, use the configured URL
        return settings.database_url
