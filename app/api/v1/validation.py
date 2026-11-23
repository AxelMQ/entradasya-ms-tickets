from typing import Any, Dict
from fastapi import APIRouter, Depends, status
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, verify_internal_token_or_jwt
from app.schemas.ticket import TicketValidateRequest, TicketValidateSuccessResponse
from app.services.ticket_service import validate_ticket_for_checkin

router = APIRouter(prefix="/tickets", tags=["Tickets Validation"])


@router.post(
    "/validate",
    summary="Validación de código de entrada (llamado por ms-checkin)",
)
async def validate_ticket(
    request: TicketValidateRequest,
    db: AsyncSession = Depends(get_db),
    auth: Dict[str, Any] = Depends(verify_internal_token_or_jwt),
):
    """
    Validates ticket authenticity for event check-in:
    - 200 OK: Valid ticket for this event
    - 404 Not Found: Ticket code does not exist (INVALID_CODE)
    - 400 Bad Request: Ticket code belongs to another event (EVENT_MISMATCH)
    """
    valid, reason, message, ticket = await validate_ticket_for_checkin(
        db, request.ticket_code, request.event_id
    )

    if not valid:
        if reason == "INVALID_CODE":
            return JSONResponse(
                status_code=status.HTTP_404_NOT_FOUND,
                content={
                    "valid": False,
                    "reason": "INVALID_CODE",
                    "message": message or "El código de entrada no existe en el sistema",
                },
            )
        elif reason == "EVENT_MISMATCH":
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={
                    "valid": False,
                    "reason": "EVENT_MISMATCH",
                    "message": message or "La entrada corresponde a otro evento",
                    "actual_event_title": ticket.event_title if ticket else None,
                },
            )

    return TicketValidateSuccessResponse(
        valid=True,
        ticket_id=ticket.id,
        event_id=ticket.event_id,
        sector_name=ticket.sector_name,
        customer_name=ticket.customer_name,
        status=ticket.status,
    )
