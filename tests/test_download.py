import os
import uuid
from pathlib import Path
import pytest
from httpx import AsyncClient

from app.core.config import settings


@pytest.mark.asyncio
async def test_download_ticket_pdf_success(
    client: AsyncClient,
    internal_headers: dict,
):
    """
    GET /api/v1/tickets/{id}/download serves the binary PDF file.
    """
    # 1. First emit a ticket via batch
    batch_payload = {
        "order_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "customer_name": "Carlos Gomez",
        "customer_email": "carlos@entradasya.com",
        "event_id": str(uuid.uuid4()),
        "event_title": "Concierto Acustico",
        "event_date": "2026-12-01T20:00:00Z",
        "venue": "Teatro Municipal",
        "sector_name": "Palco",
        "quantity": 1,
        "price": 150.00,
    }

    batch_resp = await client.post(
        "/api/v1/tickets/batch",
        json=batch_payload,
        headers=internal_headers,
    )
    assert batch_resp.status_code == 201
    ticket_id = batch_resp.json()["tickets"][0]["id"]
    ticket_code = batch_resp.json()["tickets"][0]["ticket_code"]

    # 2. Download the ticket PDF
    download_resp = await client.get(f"/api/v1/tickets/{ticket_id}/download")

    assert download_resp.status_code == 200
    assert "application/pdf" in download_resp.headers["content-type"]
    assert "attachment" in download_resp.headers.get("content-disposition", "")
    assert ticket_code in download_resp.headers.get("content-disposition", "")

    # Check PDF magic bytes (%PDF-)
    content = download_resp.content
    assert content.startswith(b"%PDF-")
    assert len(content) > 1000


@pytest.mark.asyncio
async def test_download_ticket_regenerates_if_file_missing_from_disk(
    client: AsyncClient,
    internal_headers: dict,
):
    """
    GET /api/v1/tickets/{id}/download regenerates PDF on the fly if deleted from storage.
    """
    batch_payload = {
        "order_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "customer_name": "Fernando Soto",
        "customer_email": "fernando@entradasya.com",
        "event_id": str(uuid.uuid4()),
        "event_title": "Show de Standup",
        "event_date": "2026-12-05T21:00:00Z",
        "venue": "Café Arte",
        "sector_name": "Mesa",
        "quantity": 1,
    }

    batch_resp = await client.post(
        "/api/v1/tickets/batch",
        json=batch_payload,
        headers=internal_headers,
    )
    ticket_id = batch_resp.json()["tickets"][0]["id"]

    # Remove the generated file physically from disk
    storage_dir = settings.get_resolved_storage_path()
    pdf_path = storage_dir / f"ticket_{ticket_id}.pdf"
    assert pdf_path.exists()
    pdf_path.unlink()
    assert not pdf_path.exists()

    # Now attempt download -> service regenerates it automatically!
    download_resp = await client.get(f"/api/v1/tickets/{ticket_id}/download")
    assert download_resp.status_code == 200
    assert download_resp.content.startswith(b"%PDF-")
    assert pdf_path.exists()


@pytest.mark.asyncio
async def test_download_ticket_not_found(client: AsyncClient):
    """
    GET /api/v1/tickets/{id}/download returns 404 for nonexistent ticket.
    """
    fake_id = str(uuid.uuid4())
    resp = await client.get(f"/api/v1/tickets/{fake_id}/download")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_tickets_by_order(
    client: AsyncClient,
    internal_headers: dict,
):
    """
    GET /api/v1/tickets/order/{orderId} returns tickets issued for that order.
    """
    order_id = str(uuid.uuid4())
    batch_payload = {
        "order_id": order_id,
        "customer_id": str(uuid.uuid4()),
        "customer_name": "Lucia Mendez",
        "customer_email": "lucia@entradasya.com",
        "event_id": str(uuid.uuid4()),
        "event_title": "Obra de Teatro",
        "event_date": "2026-11-28T18:00:00Z",
        "venue": "Casa de la Cultura",
        "sector_name": "Platea Baja",
        "quantity": 3,
    }

    # Emit tickets
    await client.post("/api/v1/tickets/batch", json=batch_payload, headers=internal_headers)

    # Query by order
    resp = await client.get(f"/api/v1/tickets/order/{order_id}")
    assert resp.status_code == 200
    tickets = resp.json()
    assert len(tickets) == 3
    assert all(t["order_id"] == order_id for t in tickets)
    assert all("download_url" in t for t in tickets)
