import uuid
import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_validate_ticket_success(
    client: AsyncClient,
    internal_headers: dict,
):
    """
    POST /api/v1/tickets/validate returns 200 OK when code exists and matches event_id.
    """
    event_id = str(uuid.uuid4())
    batch_payload = {
        "order_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "customer_name": "Juan Perez",
        "customer_email": "cliente@entradasya.com",
        "event_id": event_id,
        "event_title": "Concierto de Rock Nacional",
        "event_date": "2026-12-15T20:00:00Z",
        "venue": "Teatro al Aire Libre",
        "sector_name": "VIP",
        "quantity": 1,
    }

    batch_resp = await client.post(
        "/api/v1/tickets/batch", json=batch_payload, headers=internal_headers
    )
    assert batch_resp.status_code == 201
    ticket = batch_resp.json()["tickets"][0]
    ticket_code = ticket["ticket_code"]
    ticket_id = ticket["id"]

    # Validate
    val_resp = await client.post(
        "/api/v1/tickets/validate",
        json={"ticket_code": ticket_code, "event_id": event_id},
        headers=internal_headers,
    )

    assert val_resp.status_code == 200
    val_data = val_resp.json()
    assert val_data["valid"] is True
    assert val_data["ticket_id"] == ticket_id
    assert val_data["event_id"] == event_id
    assert val_data["sector_name"] == "VIP"
    assert val_data["customer_name"] == "Juan Perez"
    assert val_data["status"] == "ISSUED"


@pytest.mark.asyncio
async def test_validate_ticket_with_portero_jwt(
    client: AsyncClient,
    internal_headers: dict,
    portero_jwt_headers: dict,
):
    """
    POST /api/v1/tickets/validate allows portero with JWT token.
    """
    event_id = str(uuid.uuid4())
    batch_payload = {
        "order_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "customer_name": "Ana Morales",
        "customer_email": "ana@entradasya.com",
        "event_id": event_id,
        "event_title": "Festival Musical",
        "event_date": "2026-12-20T21:00:00Z",
        "venue": "Estadio Central",
        "sector_name": "General",
        "quantity": 1,
    }

    batch_resp = await client.post(
        "/api/v1/tickets/batch", json=batch_payload, headers=internal_headers
    )
    ticket_code = batch_resp.json()["tickets"][0]["ticket_code"]

    val_resp = await client.post(
        "/api/v1/tickets/validate",
        json={"ticket_code": ticket_code, "event_id": event_id},
        headers=portero_jwt_headers,
    )

    assert val_resp.status_code == 200
    assert val_resp.json()["valid"] is True


@pytest.mark.asyncio
async def test_validate_ticket_invalid_code_not_found(
    client: AsyncClient,
    internal_headers: dict,
):
    """
    POST /api/v1/tickets/validate returns 404 INVALID_CODE when ticket code is nonexistent.
    """
    event_id = str(uuid.uuid4())
    val_resp = await client.post(
        "/api/v1/tickets/validate",
        json={"ticket_code": "EY-FAKE-999999", "event_id": event_id},
        headers=internal_headers,
    )

    assert val_resp.status_code == 404
    data = val_resp.json()
    assert data["valid"] is False
    assert data["reason"] == "INVALID_CODE"
    assert "no existe" in data["message"].lower()


@pytest.mark.asyncio
async def test_validate_ticket_event_mismatch(
    client: AsyncClient,
    internal_headers: dict,
):
    """
    POST /api/v1/tickets/validate returns 400 EVENT_MISMATCH when ticket belongs to another event.
    """
    event_a_id = str(uuid.uuid4())
    event_b_id = str(uuid.uuid4())

    batch_payload = {
        "order_id": str(uuid.uuid4()),
        "customer_id": str(uuid.uuid4()),
        "customer_name": "Juan Perez",
        "customer_email": "cliente@entradasya.com",
        "event_id": event_a_id,
        "event_title": "Festival de Jazz 2026",
        "event_date": "2026-12-15T20:00:00Z",
        "venue": "Teatro al Aire Libre",
        "sector_name": "VIP",
        "quantity": 1,
    }

    batch_resp = await client.post(
        "/api/v1/tickets/batch", json=batch_payload, headers=internal_headers
    )
    ticket_code = batch_resp.json()["tickets"][0]["ticket_code"]

    # Validate against event B instead of A
    val_resp = await client.post(
        "/api/v1/tickets/validate",
        json={"ticket_code": ticket_code, "event_id": event_b_id},
        headers=internal_headers,
    )

    assert val_resp.status_code == 400
    data = val_resp.json()
    assert data["valid"] is False
    assert data["reason"] == "EVENT_MISMATCH"
    assert data["actual_event_title"] == "Festival de Jazz 2026"


@pytest.mark.asyncio
async def test_validate_ticket_unauthorized_without_credentials(
    client: AsyncClient,
):
    """
    POST /api/v1/tickets/validate returns 401 without authentication.
    """
    resp = await client.post(
        "/api/v1/tickets/validate",
        json={"ticket_code": "EY-ROCK-123456", "event_id": str(uuid.uuid4())},
    )
    assert resp.status_code == 401
