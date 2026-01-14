"""Навигация по меню."""
from aiogram import Router
from aiogram.types import CallbackQuery
from aiogram.utils.i18n import gettext as _

from src.keyboards.main_menu import main_menu_keyboard

router = Router()


@router.callback_query(lambda c: c.data == "nav:main")
async def nav_main(callback: CallbackQuery):
    """Вернуться в главное меню."""
    user_id = callback.from_user.id
    await callback.message.edit_reply_markup(
        reply_markup=main_menu_keyboard(user_id)
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("nav:back:"))
async def nav_back(callback: CallbackQuery):
    """Назад."""
    # Упрощенная реализация - просто возврат в главное меню
    await nav_main(callback)

