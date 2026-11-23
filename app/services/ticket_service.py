import re
import secrets
import string
import uuid
from typing import List, Optional, Tuple
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.ticket import Ticket
from app.schemas.ticket import TicketBatchRequest, TicketBatchResponse, TicketItemResponse
from app.services.pdf_generator import generate_ticket_pdf


STOPWORDS = {
    "de", "del", "la", "el", "los", "las", "un", "una", "en", "y", "o", "a", "al", "con", "por", "para"
}

GENERIC_DESCRIPTORS = {
    "concierto", "festival", "recital", "show", "obra", "evento", "presentacion", "tour", "gira", "gran"
}


def generate_event_short_code(event_title: str) -> str:
    """
    Extracts a 4-letter uppercase code from the event title.
    Prefers specific genre/event name over generic descriptors.
    E.g. 'Concierto de Rock Nacional' -> 'ROCK'
    E.g. 'Festival de Jazz 2026' -> 'JAZZ'
    E.g. 'Concierto 2026' -> 'CONC'
    """
    words = re.findall(r"[A-Za-z0-9]+", event_title)
    meaningful = [w for w in words if w.lower() not in STOPWORDS]

    # First attempt: skip generic descriptors like "Concierto", "Festival"
    specific_words = [w for w in meaningful if w.lower() not in GENERIC_DESCRIPTORS]

    # Look for a word in specific words
    chosen = ""
    for w in specific_words:
        if len(w) >= 3:
            chosen = w[:4].upper()
            break

    # If nothing found, search among all meaningful words
    if not chosen:
        for w in meaningful:
            if len(w) >= 3:
                chosen = w[:4].upper()
                break

    if not chosen and meaningful:
        chosen = meaningful[0][:4].upper().ljust(4, "X")
    elif not chosen:
        chosen = "TICK"

    return chosen.upper()


def generate_ticket_code(event_title: str) -> str:
    """
    Generates a unique ticket code with format: EY-<EVENT_SHORT>-<HASH_ALEATORIO>
    E.g. EY-ROCK-8X4N2Q
    """
    short_code = generate_event_short_code(event_title)
    # 6 random uppercase chars/digits without ambiguous chars
    alphabet = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"
    random_hash = "".join(secrets.choice(alphabet) for _ in range(6))
    return f"EY-{short_code}-{random_hash}"


async def issue_tickets_batch(
    db: AsyncSession,
    request: TicketBatchRequest,
) -> TicketBatchResponse:
    """
    Issues a batch of tickets:
    - Creates records in the database
    - Generates physical PDF ticket files with embedded QR codes in STORAGE_PATH
    - Returns the batch response with download URLs
    """
    storage_dir = settings.get_resolved_storage_path()
    created_tickets: List[Ticket] = []

    for _ in range(request.quantity):
        ticket_id = uuid.uuid4()
        ticket_code = generate_ticket_code(request.event_title)
        pdf_filename = f"ticket_{ticket_id}.pdf"
        pdf_path = storage_dir / pdf_filename

        # Render PDF ticket
        generate_ticket_pdf(
            output_path=pdf_path,
            ticket_id=str(ticket_id),
            ticket_code=ticket_code,
            event_title=request.event_title,
            event_date=request.event_date,
            venue=request.venue,
            sector_name=request.sector_name,
            customer_name=request.customer_name,
            price=request.price,
        )

        ticket = Ticket(
            id=ticket_id,
            order_id=request.order_id,
            event_id=request.event_id,
            event_title=request.event_title,
            event_date=request.event_date,
            venue=request.venue,
            sector_name=request.sector_name,
            customer_id=request.customer_id,
            customer_name=request.customer_name,
            customer_email=request.customer_email,
            ticket_code=ticket_code,
            pdf_filename=pdf_filename,
            status="ISSUED",
        )
        db.add(ticket)
        created_tickets.append(ticket)

    await db.commit()
    for t in created_tickets:
        await db.refresh(t)

    ticket_items = [
        TicketItemResponse(
            id=t.id,
            ticket_code=t.ticket_code,
            download_url=f"/api/v1/tickets/{t.id}/download",
        )
        for t in created_tickets
    ]

    return TicketBatchResponse(
        order_id=request.order_id,
        total_tickets=len(ticket_items),
        tickets=ticket_items,
    )


async def get_ticket_by_id(
    db: AsyncSession,
    ticket_id: uuid.UUID,
) -> Optional[Ticket]:
    """Retrieves a ticket by its ID."""
    query = select(Ticket).where(Ticket.id == ticket_id)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_tickets_by_order_id(
    db: AsyncSession,
    order_id: uuid.UUID,
) -> List[Ticket]:
    """Retrieves all tickets issued for an order."""
    query = select(Ticket).where(Ticket.order_id == order_id).order_by(Ticket.created_at.asc())
    result = await db.execute(query)
    return list(result.scalars().all())


async def validate_ticket_for_checkin(
    db: AsyncSession,
    ticket_code: str,
    event_id: uuid.UUID,
) -> Tuple[bool, Optional[str], Optional[str], Optional[Ticket]]:
    """
    Validates ticket for check-in:
    Returns (valid, reason, message, ticket)
    - If valid: (True, None, None, ticket)
    - If code not found: (False, "INVALID_CODE", "El código de entrada no existe en el sistema", None)
    - If event mismatch: (False, "EVENT_MISMATCH", "La entrada corresponde a otro evento", ticket)
    """
    query = select(Ticket).where(Ticket.ticket_code == ticket_code)
    result = await db.execute(query)
    ticket = result.scalar_one_or_none()

    if not ticket:
        return (
            False,
            "INVALID_CODE",
            "El código de entrada no existe en el sistema",
            None,
        )

    if ticket.event_id != event_id:
        return (
            False,
            "EVENT_MISMATCH",
            "La entrada no pertenece al evento consultado",
            ticket,
        )

    return (True, None, None, ticket)
