import io
import qrcode
from PIL import Image


def generate_qr_image(data: str) -> Image.Image:
    """Generates a PIL Image containing the QR code for data."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    return img


def generate_qr_bytes(data: str) -> io.BytesIO:
    """Generates a BytesIO stream containing the PNG image of the QR code."""
    img = generate_qr_image(data)
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer
