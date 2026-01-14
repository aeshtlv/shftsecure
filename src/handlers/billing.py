"""Биллинг (админ)."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _

from src.utils.auth import is_admin

router = Router()


@router.message(Command("billing"))
async def cmd_billing(message: Message):
    """Команда /billing - информация о биллинге."""
    if not is_admin(message.from_user.id):
        return

    # Упрощенная реализация - требует доработки
    await message.answer("💰 Функция биллинга (требует доработки)")

