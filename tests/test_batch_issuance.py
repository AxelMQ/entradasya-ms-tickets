import os
import uuid
from pathlib import Path
import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ticket import Ticket


@pytest.mark.asyncio
async def test_batch_issuance_success_with_internal_token(
    client: AsyncClient,
    internal_headers: dict,
    db_session: AsyncSession,
):
    """
    POST /api/v1/tickets/batch emits tickets and physically creates PDFs on disk.
    """
    order_id = str(uuid.uuid4())
    customer_id = str(uuid.uuid4())
    event_id = str(uuid.uuid4())

    payload = {
        "order_id": order_id,
        "customer_id": customer_id,
        "customer_name": "Juan Perez",
        "customer_email": "cliente@entradasya.com",
        "event_id": event_id,
        "event_title": "Concierto de Rock Nacional",
        "event_date": "2026-12-15T20:00:00Z",
        "venue": "Teatro al Aire Libre",
        "sector_name": "VIP",
        "quantity": 2,
        "price": 200.00,
    }

    response = await client.post(
        "/api/v1/tickets/batch",
        json=payload,
        headers=internal_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == order_id
    assert data["total_tickets"] == 2
    assert len(data["tickets"]) == 2

    # Check ticket structure
    storage_dir = settings.get_resolved_storage_path()
    for ticket_item in data["tickets"]:
        assert "id" in ticket_item
        assert "ticket_code" in ticket_item
        assert "download_url" in ticket_item
        assert ticket_item["ticket_code"].startswith("EY-ROCK-")
        assert f"/api/v1/tickets/{ticket_item['id']}/download" == ticket_item["download_url"]

        # Verify physical PDF exists on disk
        pdf_path = storage_dir / f"ticket_{ticket_item['id']}.pdf"
        assert pdf_path.exists(), f"PDF file {pdf_path} was not created on disk"
        assert pdf_path.stat().st_size > 0

    # Verify records persisted in DB
    query = select(Ticket).where(Ticket.order_id == uuid.UUID(order_id))
    result = await db_session.execute(query)
    db_tickets = list(result.scalars().all())
    assert len(db_tickets) == 2
    assert db_tickets[0].status == "ISSUED"
    assert db_tickets[0].customer_name == "Juan Perez"


@pytest.mark.asyncio
async def test_batch_issuance_success_with_jwt(
    client: AsyncClient,
    client_jwt_headers: dict,
):
    """
    POST /api/v1/tickets/batch succeeds with a valid JWT.
    """
    payload = {
        "order_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "customer_name": "Maria Lopez",
        "customer_email": "maria@entradasya.com",
        "event_id": str(uuid.uuid4()),
        "event_title": "Festival de Jazz 2026",
        "event_date": "2026-11-20T19:30:00Z",
        "venue": "Centro Sinfónico",
        "sector_name": "Platea",
        "quantity": 1,
    }

    response = await client.post(
        "/api/v1/tickets/batch",
        json=payload,
        headers=client_jwt_headers,
    )

    assert response.status_code == 201
    data = response.json()
    assert data["total_tickets"] == 1
    assert data["tickets"][0]["ticket_code"].startswith("EY-JAZZ-")


@pytest.mark.asyncio
async def test_batch_issuance_unauthorized_without_credentials(
    client: AsyncClient,
):
    """
    POST /api/v1/tickets/batch returns 401 without credentials.
    """
    payload = {
        "order_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "customer_name": "Test User",
        "customer_email": "test@entradasya.com",
        "event_id": str(uuid.uuid4()),
        "event_title": "Rock Fest",
        "event_date": "2026-12-15T20:00:00Z",
        "venue": "Estadio",
        "sector_name": "General",
        "quantity": 1,
    }

    response = await client.post("/api/v1/tickets/batch", json=payload)
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_batch_issuance_forbidden_with_invalid_token(
    client: AsyncClient,
):
    """
    POST /api/v1/tickets/batch returns 403 when X-Internal-Token is invalid.
    """
    payload = {
        "order_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "customer_name": "Test User",
        "customer_email": "test@entradasya.com",
        "event_id": str(uuid.uuid4()),
        "event_title": "Rock Fest",
        "event_date": "2026-12-15T20:00:00Z",
        "venue": "Estadio",
        "sector_name": "General",
        "quantity": 1,
    }

    response = await client.post(
        "/api/v1/tickets/batch",
        json=payload,
        headers={"X-Internal-Token": "invalid-secret-token"},
    )
    assert response.status_code == 403


@pytest.mark.asyncio
async def test_batch_issuance_validation_error_zero_quantity(
    client: AsyncClient,
    internal_headers: dict,
):
    """
    POST /api/v1/tickets/batch returns 422 for quantity = 0.
    """
    payload = {
        "order_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "customer_name": "Test User",
        "customer_email": "test@entradasya.com",
        "event_id": str(uuid.uuid4()),
        "event_title": "Rock Fest",
        "event_date": "2026-12-15T20:00:00Z",
        "venue": "Estadio",
        "sector_name": "General",
        "quantity": 0,
    }

    response = await client.post(
        "/api/v1/tickets/batch",
        json=payload,
        headers=internal_headers,
    )
    assert response.status_code == 422
