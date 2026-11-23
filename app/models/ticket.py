import uuid
from datetime import datetime
from sqlalchemy import DateTime, Index, String, Uuid, func
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[uuid.UUID] = mapped_column(Uuid, primary_key=True, default=uuid.uuid4)
    order_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    event_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False, index=True)
    event_title: Mapped[str] = mapped_column(String(200), nullable=False)
    event_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    venue: Mapped[str] = mapped_column(String(200), nullable=False)
    sector_name: Mapped[str] = mapped_column(String(100), nullable=False)
    customer_id: Mapped[uuid.UUID] = mapped_column(Uuid, nullable=False)
    customer_name: Mapped[str] = mapped_column(String(100), nullable=False)
    customer_email: Mapped[str] = mapped_column(String(150), nullable=False)
    ticket_code: Mapped[str] = mapped_column(String(64), nullable=False, unique=True, index=True)
    pdf_filename: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="ISSUED"
    )  # ISSUED, CANCELLED
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    __table_args__ = (
        Index("idx_tickets_code", "ticket_code", unique=True),
        Index("idx_tickets_order_id", "order_id"),
        Index("idx_tickets_event_id", "event_id"),
    )
