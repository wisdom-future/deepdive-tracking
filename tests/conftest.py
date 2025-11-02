"""Pytest configuration and shared fixtures."""

import pytest
from fastapi.testclient import TestClient

from src.config import get_settings
from src.main import create_app


@pytest.fixture
def app():
    """Create test application instance."""
    return create_app()


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def settings():
    """Get test settings."""
    return get_settings()
