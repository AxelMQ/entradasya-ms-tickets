import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional
from pydantic import BaseModel, ConfigDict, EmailStr, Field


class TicketBatchRequest(BaseModel):
    order_id: uuid.UUID
    customer_id: uuid.UUID
    customer_name: str = Field(..., min_length=1, max_length=100)
    customer_email: str = Field(..., min_length=3, max_length=150)
    event_id: uuid.UUID
    event_title: str = Field(..., min_length=1, max_length=200)
    event_date: datetime
    venue: str = Field(..., min_length=1, max_length=200)
    sector_name: str = Field(..., min_length=1, max_length=100)
    quantity: int = Field(..., ge=1, le=20)
    price: Optional[Decimal] = None


class TicketItemResponse(BaseModel):
    id: uuid.UUID
    ticket_code: str
    download_url: str

    model_config = ConfigDict(from_attributes=True)


class TicketBatchResponse(BaseModel):
    order_id: uuid.UUID
    total_tickets: int
    tickets: List[TicketItemResponse]


class TicketValidateRequest(BaseModel):
    ticket_code: str = Field(..., min_length=1, max_length=64)
    event_id: uuid.UUID


class TicketValidateSuccessResponse(BaseModel):
    valid: bool = True
    ticket_id: uuid.UUID
    event_id: uuid.UUID
    sector_name: str
    customer_name: str
    status: str

    model_config = ConfigDict(from_attributes=True)


class TicketValidateErrorResponse(BaseModel):
    valid: bool = False
    reason: str
    message: str
    actual_event_title: Optional[str] = None


class TicketResponse(BaseModel):
    id: uuid.UUID
    order_id: uuid.UUID
    event_id: uuid.UUID
    event_title: str
    event_date: datetime
    venue: str
    sector_name: str
    customer_id: uuid.UUID
    customer_name: str
    customer_email: str
    ticket_code: str
    pdf_filename: str
    status: str
    download_url: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
