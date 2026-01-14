"""Управление нодами (админ)."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _

from src.utils.auth import is_admin

router = Router()


@router.message(Command("nodes"))
async def cmd_nodes(message: Message):
    """Команда /nodes - список нод."""
    if not is_admin(message.from_user.id):
        return

    # Упрощенная реализация - требует доработки
    await message.answer("🖥 Функция управления нодами (требует доработки)")

