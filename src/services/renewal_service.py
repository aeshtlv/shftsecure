"""Сервис автопродления."""
import asyncio
from datetime import datetime, timedelta
from typing import Optional

from aiogram import Bot

from src.config import get_settings
from src.database import BotUser
from src.services.api_client import RemnawaveApiClient
from src.services.payment_service import create_subscription_invoice


async def check_expiring_subscriptions(bot: Bot):
    """Проверить истекающие подписки."""
    api_client = RemnawaveApiClient()
    settings = get_settings()

    # Получить пользователей с автопродлением
    users_with_renewal = BotUser.get_users_with_auto_renewal()

    for user in users_with_renewal:
        user_id = user["telegram_id"]
        remnawave_uuid = user.get("remnawave_user_uuid")

        if not remnawave_uuid:
            continue

        try:
            # Получить пользователя из Remnawave
            remnawave_user = await api_client.get_user_by_uuid(remnawave_uuid)
            expire_at = remnawave_user.get("expire_at")

            if not expire_at:
                continue

            expire_dt = datetime.fromisoformat(expire_at.replace("Z", "+00:00"))
            now = datetime.now(expire_dt.tzinfo) if expire_dt.tzinfo else datetime.now()
            days_until_expiry = (expire_dt - now).days

            # Проверить, нужно ли отправить напоминание
            last_notification = user.get("last_renewal_notification")
            if last_notification:
                last_notif_dt = datetime.fromisoformat(last_notification)
                hours_since_notif = (now - last_notif_dt).total_seconds() / 3600
            else:
                hours_since_notif = 999

            # Напоминание за 3-5 дней
            if 3 <= days_until_expiry <= 5 and hours_since_notif >= 24:
                await send_renewal_reminder(
                    bot, user_id, days_until_expiry, "early", expire_at
                )
                BotUser.update_last_renewal_notification(user_id)

            # Напоминание за 1 день
            elif days_until_expiry == 1 and hours_since_notif >= 12:
                await send_renewal_reminder(
                    bot, user_id, days_until_expiry, "urgent", expire_at
                )
                BotUser.update_last_renewal_notification(user_id)

            # После истечения
            elif days_until_expiry < 0 and hours_since_notif >= 24:
                await send_renewal_reminder(
                    bot, user_id, days_until_expiry, "expired", expire_at
                )
                BotUser.update_last_renewal_notification(user_id)

        except Exception:
            continue  # Игнорируем ошибки


async def send_renewal_reminder(
    bot: Bot,
    user_id: int,
    days_until_expiry: int,
    reminder_type: str,
    expire_at: str,
):
    """Отправить напоминание о продлении."""
    from aiogram.utils.i18n import gettext as _
    from src.keyboards.user_public import renewal_keyboard

    t = _

    if reminder_type == "expired":
        text = t("renewal.expired").format(expire_at=expire_at)
    elif reminder_type == "urgent":
        text = t("renewal.urgent").format(days=days_until_expiry)
    else:
        text = t("renewal.early").format(days=days_until_expiry)

    try:
        await bot.send_message(
            chat_id=user_id,
            text=text,
            reply_markup=renewal_keyboard(),
            parse_mode="Markdown",
        )
    except Exception:
        pass  # Игнорируем ошибки отправки


async def start_renewal_checker(bot: Bot, interval_hours: int = 6):
    """Запустить фоновую задачу проверки подписок."""
    while True:
        try:
            await check_expiring_subscriptions(bot)
        except Exception:
            pass  # Игнорируем ошибки

        await asyncio.sleep(interval_hours * 3600)

