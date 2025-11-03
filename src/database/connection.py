"""Database connection and session management."""

from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from typing import Optional

from src.config import get_settings

# Lazy initialization of database engine and session factory
_engine: Optional[object] = None
_SessionLocal: Optional[sessionmaker] = None


def _init_db():
    """Initialize database engine and session factory (lazy initialization)."""
    global _engine, _SessionLocal
    if _engine is None:
        settings = get_settings()
        connect_args = {"connect_timeout": 5}  # 5 second timeout
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
        )
        _SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=_engine
        )


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
