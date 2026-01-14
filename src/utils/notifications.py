"""Утилиты уведомлений."""
from typing import Optional

from aiogram import Bot
from aiogram.types import Message

from src.config import get_settings


async def send_admin_notification(
    bot: Bot, text: str, parse_mode: Optional[str] = "Markdown"
):
    """Отправить уведомление админам."""
    settings = get_settings()
    if not settings.NOTIFICATIONS_CHAT_ID:
        return

    try:
        message_params = {
            "chat_id": settings.NOTIFICATIONS_CHAT_ID,
            "text": text,
        }
        if parse_mode:
            message_params["parse_mode"] = parse_mode
        if settings.NOTIFICATIONS_TOPIC_ID:
            message_params["message_thread_id"] = settings.NOTIFICATIONS_TOPIC_ID

        await bot.send_message(**message_params)
    except Exception:
        pass  # Игнорируем ошибки отправки уведомлений

