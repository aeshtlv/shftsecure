"""Команды админа."""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from aiogram.utils.i18n import gettext as _

from src.keyboards.main_menu import main_menu_keyboard
from src.utils.auth import is_admin

router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Команда /start (для админов)."""
    if not is_admin(message.from_user.id):
        return  # Обрабатывается в user_public

    t = _
    text = t("admin.welcome")
    await message.answer(
        text=text,
        reply_markup=main_menu_keyboard(message.from_user.id),
        parse_mode="Markdown",
    )


@router.message(Command("help"))
async def cmd_help(message: Message):
    """Команда /help."""
    if not is_admin(message.from_user.id):
        return

    t = _
    text = t("admin.help")
    await message.answer(text=text, parse_mode="Markdown")

