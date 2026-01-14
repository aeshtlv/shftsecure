"""Сервис YooKassa."""
import qrcode
import io
from typing import Dict, Optional

import yookassa
from yookassa import Payment, Configuration

from src.config import get_settings


def init_yookassa():
    """Инициализация YooKassa."""
    settings = get_settings()
    if settings.YOOKASSA_SHOP_ID and settings.YOOKASSA_SECRET_KEY:
        Configuration.account_id = settings.YOOKASSA_SHOP_ID
        Configuration.secret_key = settings.YOOKASSA_SECRET_KEY


async def create_payment(
    amount: float,
    description: str,
    user_id: int,
    subscription_months: int,
    return_url: str,
    metadata: Optional[Dict] = None,
) -> Dict:
    """Создать платеж через YooKassa."""
    settings = get_settings()
    if not settings.YOOKASSA_SHOP_ID or not settings.YOOKASSA_SECRET_KEY:
        raise ValueError("YooKassa не настроен")

    payment_data = {
        "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
        "confirmation": {
            "type": "redirect",
            "return_url": return_url,
        },
        "capture": True,
        "description": description,
        "metadata": metadata or {},
    }

    payment = Payment.create(payment_data)
    return payment


async def create_sbp_payment(
    amount: float,
    description: str,
    user_id: int,
    subscription_months: int,
    return_url: str,
    metadata: Optional[Dict] = None,
) -> Dict:
    """Создать платеж через СБП (QR-код)."""
    settings = get_settings()
    if not settings.YOOKASSA_SHOP_ID or not settings.YOOKASSA_SECRET_KEY:
        raise ValueError("YooKassa не настроен")

    payment_data = {
        "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
        "confirmation": {
            "type": "qr",
        },
        "capture": True,
        "description": description,
        "payment_method_data": {
            "type": "sbp",
        },
        "metadata": metadata or {},
    }

    payment = Payment.create(payment_data)
    return payment


def generate_qr_code(qr_data: str) -> bytes:
    """Сгенерировать QR-код."""
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(qr_data)
    qr.make(fit=True)

    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format="PNG")
    return buffer.getvalue()


async def get_payment_status(payment_id: str) -> Dict:
    """Получить статус платежа."""
    payment = Payment.find_one(payment_id)
    return payment

