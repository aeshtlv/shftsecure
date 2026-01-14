"""Главное меню."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _

from src.utils.auth import is_admin


def main_menu_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Главное меню (админ или пользователь)."""
    t = _
    buttons = []

    if is_admin(user_id):
        # Админское меню
        buttons.append([
            InlineKeyboardButton(
                text=t("menu.section.users"), callback_data="menu:section:users"
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                text=t("menu.section.nodes"), callback_data="menu:section:nodes"
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                text=t("menu.section.hosts"), callback_data="menu:section:hosts"
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                text=t("menu.section.resources"),
                callback_data="menu:section:resources",
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                text=t("menu.section.billing"), callback_data="menu:section:billing"
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                text=t("menu.section.bulk"), callback_data="menu:section:bulk"
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                text=t("menu.section.system"), callback_data="menu:section:system"
            )
        ])
    else:
        # Пользовательское меню
        buttons.append([
            InlineKeyboardButton(
                text=t("user_menu.connect"), callback_data="user:connect"
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                text=t("user_menu.my_access"), callback_data="user:my_access"
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                text=t("user_menu.settings"), callback_data="user:settings"
            )
        ])
        buttons.append([
            InlineKeyboardButton(
                text=t("user_menu.support"), callback_data="user:support"
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)

