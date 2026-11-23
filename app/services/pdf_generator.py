import io
import os
from datetime import datetime
from decimal import Decimal
from typing import Optional
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas

from app.services.qr_service import generate_qr_bytes


def generate_ticket_pdf(
    output_path: str | Path,
    ticket_id: str,
    ticket_code: str,
    event_title: str,
    event_date: datetime,
    venue: str,
    sector_name: str,
    customer_name: str,
    price: Optional[Decimal | float] = None,
) -> str:
    """
    Renders a professional event ticket PDF using ReportLab with embedded QR code.
    Saves to output_path and returns the string path.
    """
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    # Dimensions for ticket (width: 620 pt, height: 260 pt)
    width = 620
    height = 260

    c = canvas.Canvas(str(output_path), pagesize=(width, height))
    c.setTitle(f"Ticket - {ticket_code}")

    # Color Palette
    primary_color = HexColor("#4F46E5")      # Indigo primary
    dark_text = HexColor("#0F172A")          # Slate 900
    muted_text = HexColor("#64748B")         # Slate 500
    bg_card = HexColor("#FFFFFF")            # White card
    bg_outer = HexColor("#F8FAFC")           # Slate 50 background
    border_color = HexColor("#CBD5E1")       # Slate 300
    accent_bar = HexColor("#6366F1")         # Indigo accent

    # Outer background
    c.setFillColor(bg_outer)
    c.rect(0, 0, width, height, stroke=0, fill=1)

    # Main Ticket Card (padded)
    margin = 12
    card_w = width - (margin * 2)
    card_h = height - (margin * 2)

    c.setFillColor(bg_card)
    c.setStrokeColor(border_color)
    c.setLineWidth(1)
    c.roundRect(margin, margin, card_w, card_h, radius=8, stroke=1, fill=1)

    # Top accent bar on ticket card
    c.setFillColor(accent_bar)
    c.roundRect(margin, height - margin - 8, card_w, 8, radius=3, stroke=0, fill=1)

    # Left Section: Ticket Info (Width: 410)
    # Header: Branding
    c.setFillColor(primary_color)
    c.setFont("Helvetica-Bold", 16)
    c.drawString(margin + 20, height - margin - 32, "ENTRADASYA")

    c.setFillColor(muted_text)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(margin + 150, height - margin - 30, "|  BOLETO DIGITAL OFICIAL")

    # Event Title
    c.setFillColor(dark_text)
    c.setFont("Helvetica-Bold", 14)
    # Truncate or fit if too long
    display_title = event_title if len(event_title) <= 40 else event_title[:37] + "..."
    c.drawString(margin + 20, height - margin - 60, display_title)

    # Details Grid
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(muted_text)
    c.drawString(margin + 20, height - margin - 84, "FECHA Y HORA")
    c.drawString(margin + 220, height - margin - 84, "LUGAR / VENUE")

    # Format date
    try:
        formatted_date = event_date.strftime("%d/%m/%Y - %H:%M")
    except Exception:
        formatted_date = str(event_date)

    c.setFont("Helvetica", 10)
    c.setFillColor(dark_text)
    c.drawString(margin + 20, height - margin - 98, formatted_date)
    display_venue = venue if len(venue) <= 26 else venue[:24] + "..."
    c.drawString(margin + 220, height - margin - 98, display_venue)

    # Second row details: Comprador & Sector
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(muted_text)
    c.drawString(margin + 20, height - margin - 124, "COMPRADOR")
    c.drawString(margin + 220, height - margin - 124, "SECTOR")

    c.setFont("Helvetica", 10)
    c.setFillColor(dark_text)
    display_buyer = customer_name if len(customer_name) <= 28 else customer_name[:26] + "..."
    c.drawString(margin + 20, height - margin - 138, display_buyer)
    c.drawString(margin + 220, height - margin - 138, sector_name)

    # Third row: Precio (if available) & ID
    c.setFont("Helvetica-Bold", 8)
    c.setFillColor(muted_text)
    c.drawString(margin + 20, height - margin - 164, "PRECIO")
    c.drawString(margin + 220, height - margin - 164, "ID BOLETO")

    c.setFont("Helvetica", 10)
    c.setFillColor(dark_text)
    price_str = f"Bs. {price:.2f}" if price is not None else "COMPRA CONFIRMADA"
    c.drawString(margin + 20, height - margin - 178, price_str)
    c.drawString(margin + 220, height - margin - 178, str(ticket_id)[:18] + "...")

    # Legal notice at bottom
    c.setFont("Helvetica-Oblique", 7.5)
    c.setFillColor(muted_text)
    c.drawString(
        margin + 20,
        margin + 16,
        "Boleto digital válido para un solo ingreso. Prohibida su duplicación o reventa.",
    )

    # Divider line (perforation style)
    divider_x = width - margin - 160
    c.setStrokeColor(HexColor("#CBD5E1"))
    c.setDash(4, 4)
    c.line(divider_x, margin + 8, divider_x, height - margin - 8)
    c.setDash()  # Reset dash

    # Right Section: QR Stub
    qr_buffer = generate_qr_bytes(ticket_code)
    qr_img = ImageReader(qr_buffer)

    qr_size = 120
    qr_x = divider_x + ((width - margin - divider_x - qr_size) / 2)
    qr_y = (height / 2) - (qr_size / 2) + 12

    # Draw QR code
    c.drawImage(qr_img, qr_x, qr_y, width=qr_size, height=qr_size)

    # Ticket Code under QR
    c.setFont("Helvetica-Bold", 9)
    c.setFillColor(dark_text)
    code_text_w = c.stringWidth(ticket_code, "Helvetica-Bold", 9)
    text_x = divider_x + ((width - margin - divider_x - code_text_w) / 2)
    c.drawString(text_x, qr_y - 14, ticket_code)

    # Small label under code
    c.setFont("Helvetica", 7)
    c.setFillColor(muted_text)
    scan_text = "PRESENTAR EN PUERTA"
    scan_w = c.stringWidth(scan_text, "Helvetica", 7)
    c.drawString(divider_x + ((width - margin - divider_x - scan_w) / 2), qr_y - 25, scan_text)

    c.save()
    return str(output_path)
