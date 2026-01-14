"""Клавиатуры для публичных пользователей."""
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.utils.i18n import gettext as _


def subscription_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора тарифа."""
    t = _
    buttons = [
        [
            InlineKeyboardButton(
                text=t("subscription.1month"), callback_data="purchase:1"
            )
        ],
        [
            InlineKeyboardButton(
                text=t("subscription.3months"), callback_data="purchase:3"
            )
        ],
        [
            InlineKeyboardButton(
                text=t("subscription.6months"), callback_data="purchase:6"
            )
        ],
        [
            InlineKeyboardButton(
                text=t("subscription.12months"), callback_data="purchase:12"
            )
        ],
        [InlineKeyboardButton(text=t("nav.back"), callback_data="user:connect")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def payment_method_keyboard(months: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора способа оплаты."""
    t = _
    buttons = [
        [
            InlineKeyboardButton(
                text=t("payment.stars"), callback_data=f"purchase:{months}:method:stars"
            )
        ],
    ]

    # Добавить YooKassa, если настроен
    from src.config import get_settings
    settings = get_settings()
    if settings.YOOKASSA_SHOP_ID and settings.YOOKASSA_SECRET_KEY:
        buttons.append([
            InlineKeyboardButton(
                text=t("payment.yookassa"),
                callback_data=f"purchase:{months}:method:yookassa",
            )
        ])

    buttons.append([
        InlineKeyboardButton(text=t("nav.back"), callback_data=f"purchase:{months}")
    ])

    return InlineKeyboardMarkup(inline_keyboard=buttons)


def yookassa_payment_keyboard(months: int) -> InlineKeyboardMarkup:
    """Клавиатура выбора способа оплаты YooKassa."""
    t = _
    buttons = [
        [
            InlineKeyboardButton(
                text=t("payment.sbp"),
                callback_data=f"purchase:{months}:method:yookassa:sbp",
            )
        ],
        [
            InlineKeyboardButton(
                text=t("payment.card"),
                callback_data=f"purchase:{months}:method:yookassa:card",
            )
        ],
        [
            InlineKeyboardButton(
                text=t("purchase.promo"), callback_data=f"purchase:{months}:promo"
            )
        ],
        [
            InlineKeyboardButton(
                text=t("nav.back"),
                callback_data=f"purchase:{months}:method:yookassa",
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def language_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора языка."""
    t = _
    buttons = [
        [
            InlineKeyboardButton(text="🇷🇺 Русский", callback_data="lang:ru"),
            InlineKeyboardButton(text="🇬🇧 English", callback_data="lang:en"),
        ],
        [InlineKeyboardButton(text=t("nav.back"), callback_data="user:settings")],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def renewal_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для продления подписки."""
    t = _
    buttons = [
        [
            InlineKeyboardButton(
                text=t("renewal.renew"), callback_data="user:renew"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def resume_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для возобновления доступа."""
    t = _
    buttons = [
        [
            InlineKeyboardButton(
                text=t("renewal.resume"), callback_data="user:resume"
            )
        ],
    ]
    return InlineKeyboardMarkup(inline_keyboard=buttons)

