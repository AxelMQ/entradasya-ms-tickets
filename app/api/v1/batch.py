from typing import Any, Dict
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db, verify_internal_token_or_jwt
from app.schemas.ticket import TicketBatchRequest, TicketBatchResponse
from app.services.ticket_service import issue_tickets_batch

router = APIRouter(prefix="/tickets", tags=["Tickets Batch"])


@router.post(
    "/batch",
    response_model=TicketBatchResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Emisión en lote de entradas (llamado por ms-orders)",
)
async def create_tickets_batch(
    request: TicketBatchRequest,
    db: AsyncSession = Depends(get_db),
    auth: Dict[str, Any] = Depends(verify_internal_token_or_jwt),
):
    """
    Creates ticket records in tickets_db and generates corresponding PDF
    files with QR codes on disk in STORAGE_PATH.
    """
    return await issue_tickets_batch(db, request)
