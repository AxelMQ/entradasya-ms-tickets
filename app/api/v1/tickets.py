import os
import uuid
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_db
from app.core.config import settings
from app.schemas.ticket import TicketResponse
from app.services.pdf_generator import generate_ticket_pdf
from app.services.ticket_service import get_ticket_by_id, get_tickets_by_order_id

router = APIRouter(prefix="/tickets", tags=["Tickets"])


@router.get(
    "/{id}/download",
    response_class=FileResponse,
    summary="Descarga de entrada en PDF",
)
async def download_ticket(
    id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Downloads the ticket PDF file.
    Returns application/pdf with Content-Disposition header.
    """
    ticket = await get_ticket_by_id(db, id)
    if not ticket:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Boleto no encontrado",
        )

    storage_dir = settings.get_resolved_storage_path()
    file_path = storage_dir / ticket.pdf_filename

    # If the file does not exist on disk, regenerate it on the fly
    if not file_path.exists():
        generate_ticket_pdf(
            output_path=file_path,
            ticket_id=str(ticket.id),
            ticket_code=ticket.ticket_code,
            event_title=ticket.event_title,
            event_date=ticket.event_date,
            venue=ticket.venue,
            sector_name=ticket.sector_name,
            customer_name=ticket.customer_name,
        )

    download_filename = f"ticket_{ticket.ticket_code}.pdf"

    return FileResponse(
        path=file_path,
        media_type="application/pdf",
        filename=download_filename,
    )


@router.get(
    "/order/{orderId}",
    response_model=List[TicketResponse],
    summary="Lista de tickets emitidos para una orden",
)
async def get_tickets_by_order(
    orderId: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """
    Retrieves all tickets issued for the specified order_id.
    """
    tickets = await get_tickets_by_order_id(db, orderId)
    return [
        TicketResponse(
            id=t.id,
            order_id=t.order_id,
            event_id=t.event_id,
            event_title=t.event_title,
            event_date=t.event_date,
            venue=t.venue,
            sector_name=t.sector_name,
            customer_id=t.customer_id,
            customer_name=t.customer_name,
            customer_email=t.customer_email,
            ticket_code=t.ticket_code,
            pdf_filename=t.pdf_filename,
            status=t.status,
            download_url=f"/api/v1/tickets/{t.id}/download",
            created_at=t.created_at,
        )
        for t in tickets
    ]
