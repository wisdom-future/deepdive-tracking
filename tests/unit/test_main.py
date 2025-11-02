"""Tests for the main application."""

import pytest
from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """Test health check endpoint.

    Args:
        client: FastAPI test client.
    """
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_root_endpoint(client: TestClient) -> None:
    """Test root endpoint.

    Args:
        client: FastAPI test client.
    """
    response = client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()
