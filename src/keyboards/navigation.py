"""Навигационные клавиатуры."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _


def nav_row(back_to: str = None) -> list:
    """Строка навигации (кнопка "Назад")."""
    t = _
    buttons = []
    if back_to:
        buttons.append(
            InlineKeyboardButton(text=t("nav.back"), callback_data=f"nav:back:{back_to}")
        )
    buttons.append(
        InlineKeyboardButton(text=t("nav.main"), callback_data="nav:main")
    )
    return buttons

