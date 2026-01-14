"""Системные команды (админ)."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _

from src.services.api_client import RemnawaveApiClient
from src.utils.auth import is_admin

router = Router()


@router.message(Command("health"))
async def cmd_health(message: Message):
    """Команда /health - проверка здоровья системы."""
    if not is_admin(message.from_user.id):
        return

    try:
        api_client = RemnawaveApiClient()
        health = await api_client.get_health()
        await message.answer(f"✅ Система работает\n\n{health}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("stats"))
async def cmd_stats(message: Message):
    """Команда /stats - общая статистика."""
    if not is_admin(message.from_user.id):
        return

    try:
        api_client = RemnawaveApiClient()
        stats = await api_client.get_stats()
        await message.answer(f"📊 Статистика:\n\n{stats}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")


@router.message(Command("bandwidth"))
async def cmd_bandwidth(message: Message):
    """Команда /bandwidth - информация о трафике."""
    if not is_admin(message.from_user.id):
        return

    try:
        api_client = RemnawaveApiClient()
        bandwidth = await api_client.get_bandwidth_stats()
        await message.answer(f"📈 Трафик:\n\n{bandwidth}")
    except Exception as e:
        await message.answer(f"❌ Ошибка: {e}")

