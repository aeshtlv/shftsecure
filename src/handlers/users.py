"""Управление пользователями (админ)."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _

from src.utils.auth import is_admin

router = Router()


@router.message(Command("user"))
async def cmd_user(message: Message):
    """Команда /user <query> - поиск пользователя."""
    if not is_admin(message.from_user.id):
        return

    # Упрощенная реализация - требует доработки
    await message.answer("🔍 Функция поиска пользователя (требует доработки)")


@router.message(Command("user_create"))
async def cmd_user_create(message: Message):
    """Команда /user_create - создание пользователя."""
    if not is_admin(message.from_user.id):
        return

    # Упрощенная реализация - требует доработки
    await message.answer("➕ Функция создания пользователя (требует доработки)")

