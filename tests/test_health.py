import pytest
from httpx import AsyncClient
from unittest.mock import AsyncMock, patch


@pytest.mark.asyncio
async def test_health_live(client: AsyncClient):
    """
    GET /health/live returns 200 UP.
    """
    response = await client.get("/health/live")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
    assert data["service"] == "ms-tickets"


@pytest.mark.asyncio
async def test_health_ready_success(client: AsyncClient):
    """
    GET /health/ready returns 200 UP when DB connection succeeds.
    """
    with patch("app.main.check_db_ready", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = True
        response = await client.get("/health/ready")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "UP"
        assert data["database"] == "connected"


@pytest.mark.asyncio
async def test_health_ready_db_down(client: AsyncClient):
    """
    GET /health/ready returns 503 DOWN when DB connection fails.
    """
    with patch("app.main.check_db_ready", new_callable=AsyncMock) as mock_check:
        mock_check.return_value = False
        response = await client.get("/health/ready")
        assert response.status_code == 503
        data = response.json()
        assert data["status"] == "DOWN"
        assert data["database"] == "disconnected"


@pytest.mark.asyncio
async def test_health_legacy(client: AsyncClient):
    """
    GET /health returns 200 UP.
    """
    response = await client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "UP"
