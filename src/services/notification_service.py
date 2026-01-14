"""Сервис уведомлений админам."""
from datetime import datetime
from typing import Optional

from aiogram import Bot

from src.utils.notifications import send_admin_notification


async def notify_trial_activation(
    bot: Bot,
    user_id: int,
    username: str,
    trial_days: int,
    remnawave_uuid: str,
):
    """Уведомление об активации триала."""
    text = f"""🔔 *Активация пробной подписки*

👤 Пользователь: `{username}` (ID: `{user_id}`)
⏱ Пробный период: `{trial_days}` дней
🆔 Remnawave UUID: `{remnawave_uuid}`
📅 Время: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"""

    await send_admin_notification(bot, text)


async def notify_payment_success(
    bot: Bot,
    user_id: int,
    username: str,
    subscription_months: int,
    stars: int,
    promo_code: Optional[str],
    remnawave_uuid: str,
    expire_date: str,
):
    """Уведомление об успешной оплате."""
    promo_text = f" (промокод: `{promo_code}`)" if promo_code else ""
    text = f"""💰 *Успешная оплата*

👤 Пользователь: `{username}` (ID: `{user_id}`)
📦 Подписка: `{subscription_months}` месяцев
⭐ Stars: `{stars}`{promo_text}
🆔 Remnawave UUID: `{remnawave_uuid}`
📅 Истекает: `{expire_date}`
⏰ Время: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"""

    await send_admin_notification(bot, text)


async def notify_promo_usage(
    bot: Bot,
    user_id: int,
    username: str,
    promo_code: str,
    discount_percent: int,
    bonus_days: int,
):
    """Уведомление об использовании промокода."""
    text = f"""🎟 *Использован промокод*

👤 Пользователь: `{username}` (ID: `{user_id}`)
🎫 Промокод: `{promo_code}`
💸 Скидка: `{discount_percent}%`
🎁 Бонусные дни: `{bonus_days}`
⏰ Время: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"""

    await send_admin_notification(bot, text)


async def notify_referral_bonus(
    bot: Bot,
    referrer_id: int,
    referrer_username: str,
    referred_id: int,
    referred_username: str,
    bonus_days: int,
    new_expire: str,
):
    """Уведомление о реферальном бонусе."""
    text = f"""🎁 *Реферальный бонус*

👤 Реферер: `{referrer_username}` (ID: `{referrer_id}`)
👥 Реферал: `{referred_username}` (ID: `{referred_id}`)
🎁 Бонусные дни: `{bonus_days}`
📅 Новая дата истечения: `{new_expire}`
⏰ Время: `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`"""

    await send_admin_notification(bot, text)

