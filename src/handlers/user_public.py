"""Публичные команды для пользователей."""
import logging
from datetime import datetime, timedelta

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _

from src.config import get_settings
from src.database import BotUser
from src.keyboards.main_menu import main_menu_keyboard
from src.keyboards.user_public import (
    language_keyboard,
    renewal_keyboard,
    resume_keyboard,
    subscription_keyboard,
)
from src.services.api_client import RemnawaveApiClient
from src.services.notification_service import notify_trial_activation
from src.services.referral_service import grant_referral_bonus
from src.utils.auth import is_admin

logger = logging.getLogger(__name__)
router = Router()


@router.message(Command("start"))
async def cmd_start(message: Message):
    """Команда /start."""
    t = _
    user_id = message.from_user.id
    username = message.from_user.username

    # Получить или создать пользователя
    BotUser.get_or_create(user_id, username)

    # Проверить реферальную ссылку
    if message.text and len(message.text.split()) > 1:
        referrer_id_str = message.text.split()[1]
        try:
            referrer_id = int(referrer_id_str)
            if referrer_id != user_id:
                BotUser.set_referrer(user_id, referrer_id)
        except ValueError:
            pass

    # Приветствие
    if is_admin(user_id):
        text = t("admin.welcome")
    else:
        text = t("user.welcome")

    await message.answer(
        text=text,
        reply_markup=main_menu_keyboard(user_id),
        parse_mode="Markdown",
    )


@router.callback_query(lambda c: c.data == "user:connect")
async def user_connect(callback: CallbackQuery):
    """Меню подключения."""
    t = _
    text = t("user.connect_menu")
    from src.keyboards.user_public import subscription_keyboard

    await callback.message.edit_text(
        text=text,
        reply_markup=subscription_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "user:buy")
async def user_buy(callback: CallbackQuery):
    """Выбор тарифа."""
    await user_connect(callback)


@router.callback_query(lambda c: c.data == "user:trial")
async def user_trial(callback: CallbackQuery):
    """Активация пробной подписки."""
    t = _
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id)

    # Проверка, использован ли триал
    if user.get("trial_used"):
        await callback.answer(t("trial.already_used"), show_alert=True)
        return

    await callback.answer(t("trial.activating"))

    try:
        settings = get_settings()
        api_client = RemnawaveApiClient()

        # Создать пользователя в Remnawave
        username = user.get("username") or f"user_{user_id}"
        expire_dt = datetime.now() + timedelta(days=settings.TRIAL_DAYS)

        remnawave_user = await api_client.create_user(
            username=username,
            expire_at=expire_dt.isoformat(),
            telegram_id=user_id,
            external_squad_uuid=settings.DEFAULT_EXTERNAL_SQUAD_UUID,
            internal_squad_uuids=settings.internal_squads,
        )

        remnawave_uuid = remnawave_user["uuid"]
        BotUser.set_remnawave_uuid(user_id, remnawave_uuid)
        BotUser.set_trial_used(user_id)

        # Получить ссылку на подписку
        subscriptions = remnawave_user.get("subscriptions", [])
        subscription_link = None
        if subscriptions:
            short_uuid = subscriptions[0].get("short_uuid")
            if short_uuid:
                sub_info = await api_client.get_subscription_info(short_uuid)
                subscription_link = sub_info.get("link")

        # Начислить реферальный бонус
        await grant_referral_bonus(callback.bot, user_id)

        # Отправить уведомление
        await notify_trial_activation(
            callback.bot, user_id, username, settings.TRIAL_DAYS, remnawave_uuid
        )

        # Отправить результат
        if subscription_link:
            text = t("trial.success").format(
                days=settings.TRIAL_DAYS, link=subscription_link
            )
        else:
            text = t("trial.success_no_link").format(days=settings.TRIAL_DAYS)

        await callback.message.edit_text(text=text, parse_mode="Markdown")
    except Exception as e:
        logger.exception(f"Trial activation error: {e}")
        await callback.message.edit_text(
            t("trial.error"), parse_mode="Markdown"
        )


@router.callback_query(lambda c: c.data == "user:my_access")
async def user_my_access(callback: CallbackQuery):
    """Информация о текущей подписке."""
    t = _
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id)
    remnawave_uuid = user.get("remnawave_user_uuid")

    if not remnawave_uuid:
        await callback.message.edit_text(
            t("user.no_subscription"), parse_mode="Markdown"
        )
        await callback.answer()
        return

    try:
        api_client = RemnawaveApiClient()
        remnawave_user = await api_client.get_user_by_uuid(remnawave_uuid)

        expire_at = remnawave_user.get("expire_at", "")
        subscriptions = remnawave_user.get("subscriptions", [])

        text = t("user.subscription_info").format(expire_at=expire_at)

        if subscriptions:
            short_uuid = subscriptions[0].get("short_uuid")
            if short_uuid:
                sub_info = await api_client.get_subscription_info(short_uuid)
                subscription_link = sub_info.get("link")
                if subscription_link:
                    text += f"\n\n🔗 {subscription_link}"

        await callback.message.edit_text(text=text, parse_mode="Markdown")
    except Exception as e:
        logger.exception(f"Get subscription error: {e}")
        await callback.message.edit_text(t("user.error"), parse_mode="Markdown")

    await callback.answer()


@router.callback_query(lambda c: c.data == "user:settings")
async def user_settings(callback: CallbackQuery):
    """Настройки пользователя."""
    t = _
    user_id = callback.from_user.id
    user = BotUser.get_or_create(user_id)

    auto_renewal = BotUser.get_auto_renewal(user_id)
    language = user.get("language", "ru")

    # Генерация реферальной ссылки
    bot_info = await callback.bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start={user_id}"

    text = t("user.settings").format(
        language=language,
        auto_renewal=t("common.yes") if auto_renewal else t("common.no"),
        referral_link=referral_link,
    )

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    buttons = [
        [
            InlineKeyboardButton(
                text=t("user.change_language"), callback_data="user:change_language"
            )
        ],
        [
            InlineKeyboardButton(
                text=t("user.toggle_auto_renewal"),
                callback_data="auto_renewal:toggle",
            )
        ],
        [
            InlineKeyboardButton(
                text=t("user.referral"), callback_data="user:referral"
            )
        ],
        [
            InlineKeyboardButton(
                text=t("nav.back"), callback_data="nav:main"
            )
        ],
    ]

    await callback.message.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "user:change_language")
async def user_change_language(callback: CallbackQuery):
    """Смена языка."""
    t = _
    await callback.message.edit_text(
        text=t("user.select_language"),
        reply_markup=language_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(lambda c: c.data.startswith("lang:"))
async def user_set_language(callback: CallbackQuery):
    """Установить язык."""
    t = _
    lang = callback.data.split(":")[1]
    user_id = callback.from_user.id

    BotUser.update_language(user_id, lang)

    # Обновить локаль
    from src.utils.i18n import get_i18n
    i18n = get_i18n()
    i18n.set_locale(lang)

    await callback.answer(t("user.language_changed"))
    await user_settings(callback)


@router.callback_query(lambda c: c.data == "auto_renewal:toggle")
async def toggle_auto_renewal(callback: CallbackQuery):
    """Включить/выключить автопродление."""
    t = _
    user_id = callback.from_user.id
    current = BotUser.get_auto_renewal(user_id)
    BotUser.set_auto_renewal(user_id, not current)

    await callback.answer(
        t("user.auto_renewal_enabled")
        if not current
        else t("user.auto_renewal_disabled")
    )
    await user_settings(callback)


@router.callback_query(lambda c: c.data == "user:referral")
async def user_referral(callback: CallbackQuery):
    """Реферальная программа."""
    t = _
    user_id = callback.from_user.id

    from src.database import Referral

    referrals_count = Referral.get_referrals_count(user_id)
    bonus_days = Referral.get_bonus_days(user_id)

    bot_info = await callback.bot.get_me()
    referral_link = f"https://t.me/{bot_info.username}?start={user_id}"

    text = t("user.referral_info").format(
        referrals_count=referrals_count,
        bonus_days=bonus_days,
        referral_link=referral_link,
    )

    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup

    buttons = [
        [
            InlineKeyboardButton(
                text=t("nav.back"), callback_data="user:settings"
            )
        ]
    ]

    await callback.message.edit_text(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(lambda c: c.data == "user:resume")
async def user_resume(callback: CallbackQuery):
    """Возобновить доступ."""
    await user_connect(callback)


@router.callback_query(lambda c: c.data == "user:renew")
async def user_renew(callback: CallbackQuery):
    """Продлить доступ."""
    await user_connect(callback)


@router.callback_query(lambda c: c.data == "user:support")
async def user_support(callback: CallbackQuery):
    """Поддержка."""
    t = _
    text = t("user.support")
    await callback.message.edit_text(text=text, parse_mode="Markdown")
    await callback.answer()

