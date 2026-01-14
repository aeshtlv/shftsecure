"""Обработка ошибок."""
import logging

from aiogram import Router
from aiogram.exceptions import (
    TelegramBadRequest,
    TelegramNetworkError,
    TelegramServerError,
)
from aiogram.types import ErrorEvent

from src.services.api_client import ApiClientError, NotFoundError, UnauthorizedError

logger = logging.getLogger(__name__)
router = Router()


@router.errors()
async def errors_handler(event: ErrorEvent):
    """Глобальный обработчик ошибок."""
    exception = event.exception

    # Игнорируем временные сетевые ошибки Telegram
    if isinstance(
        exception, (TelegramNetworkError, TelegramServerError, TelegramBadRequest)
    ):
        logger.warning(f"Telegram error (ignored): {exception}")
        return

    # Обрабатываем ошибки API
    if isinstance(exception, UnauthorizedError):
        logger.error(f"Unauthorized API error: {exception}")
        if event.update.message:
            await event.update.message.answer(
                "❌ Ошибка авторизации. Проверьте настройки API."
            )
        return

    if isinstance(exception, NotFoundError):
        logger.warning(f"Not found: {exception}")
        if event.update.message:
            await event.update.message.answer("❌ Ресурс не найден.")
        return

    if isinstance(exception, ApiClientError):
        logger.error(f"API error: {exception}")
        if event.update.message:
            await event.update.message.answer(
                f"❌ Ошибка API: {str(exception)}"
            )
        return

    # Остальные ошибки
    logger.exception(f"Unhandled error: {exception}", exc_info=exception)
    if event.update.message:
        await event.update.message.answer(
            "❌ Произошла ошибка. Попробуйте позже."
        )

