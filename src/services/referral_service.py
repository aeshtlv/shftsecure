"""Сервис реферальной программы."""
from datetime import datetime, timedelta

from aiogram import Bot

from src.config import get_settings
from src.database import BotUser, Referral
from src.services.api_client import RemnawaveApiClient
from src.services.notification_service import notify_referral_bonus


async def grant_referral_bonus(bot: Bot, referred_user_id: int):
    """Начислить бонус рефереру."""
    # Получить пользователя из БД
    user = BotUser.get_or_create(referred_user_id)
    referrer_id = user.get("referrer_id")

    if not referrer_id:
        return  # Нет реферера

    # Проверить, не начислен ли уже бонус
    if Referral.has_bonus_been_granted(referrer_id, referred_user_id):
        return  # Бонус уже начислен

    # Получить реферера из БД
    referrer = BotUser.get_or_create(referrer_id)
    referrer_remnawave_uuid = referrer.get("remnawave_user_uuid")

    if not referrer_remnawave_uuid:
        return  # У реферера нет аккаунта в Remnawave

    # Получить текущую подписку реферера
    api_client = RemnawaveApiClient()
    try:
        referrer_user = await api_client.get_user_by_uuid(referrer_remnawave_uuid)
        current_expire = referrer_user.get("expire_at")

        if not current_expire:
            return  # Нет активной подписки

        # Вычислить новую дату истечения
        expire_dt = datetime.fromisoformat(current_expire.replace("Z", "+00:00"))
        settings = get_settings()
        new_expire = expire_dt + timedelta(days=settings.REFERRAL_BONUS_DAYS)

        # Продлить подписку
        await api_client.update_user(
            referrer_remnawave_uuid, expire_at=new_expire.isoformat()
        )

        # Обновить запись в БД
        Referral.grant_bonus(
            referrer_id, referred_user_id, settings.REFERRAL_BONUS_DAYS
        )

        # Отправить уведомление
        referred_user = BotUser.get_or_create(referred_user_id)
        await notify_referral_bonus(
            bot,
            referrer_id,
            referrer.get("username", "N/A"),
            referred_user_id,
            referred_user.get("username", "N/A"),
            settings.REFERRAL_BONUS_DAYS,
            new_expire.isoformat(),
        )

    except Exception:
        pass  # Игнорируем ошибки

