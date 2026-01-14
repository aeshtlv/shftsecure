"""Сервис обработки платежей."""
import json
from datetime import datetime, timedelta
from typing import Dict, Optional

from aiogram import Bot

from src.config import get_settings
from src.database import BotUser, Payment, PromoCode
from src.services.api_client import RemnawaveApiClient
from src.services.notification_service import notify_payment_success
from src.services.referral_service import grant_referral_bonus


async def create_subscription_invoice(
    bot: Bot,
    user_id: int,
    subscription_months: int,
    promo_code: Optional[str] = None,
) -> str:
    """Создать invoice для Telegram Stars."""
    settings = get_settings()

    # Определить цену
    prices = {
        1: settings.SUBSCRIPTION_STARS_1MONTH,
        3: settings.SUBSCRIPTION_STARS_3MONTHS,
        6: settings.SUBSCRIPTION_STARS_6MONTHS,
        12: settings.SUBSCRIPTION_STARS_12MONTHS,
    }
    base_price = prices.get(subscription_months, 100)

    # Применить промокод
    discount = 0
    bonus_days = 0
    if promo_code:
        promo = PromoCode.get(promo_code)
        if promo:
            discount = promo.get("discount_percent", 0)
            bonus_days = promo.get("bonus_days", 0)

    # Вычислить финальную цену
    final_price = int(base_price * (1 - discount / 100))

    # Создать payload
    payload = json.dumps({
        "user_id": user_id,
        "months": subscription_months,
        "promo_code": promo_code,
        "bonus_days": bonus_days,
    })

    # Создать invoice
    invoice_link = await bot.create_invoice_link(
        title=f"Подписка на {subscription_months} месяц(а/ев)",
        description=f"Подписка на Remnawave на {subscription_months} месяц(а/ев)",
        payload=payload,
        provider_token="",  # Для Stars не нужен
        currency="XTR",  # Telegram Stars
        prices=[{"label": "Подписка", "amount": final_price}],
    )

    # Сохранить платеж в БД
    subscription_days = subscription_months * 30 + bonus_days
    Payment.create(
        user_id=user_id,
        stars=final_price,
        amount_rub=0.0,
        invoice_payload=payload,
        subscription_days=subscription_days,
        promo_code=promo_code,
    )

    return invoice_link


async def create_yookassa_payment(
    bot: Bot,
    user_id: int,
    subscription_months: int,
    promo_code: Optional[str] = None,
    payment_method: str = "sbp",
) -> Dict:
    """Создать платеж через YooKassa."""
    settings = get_settings()

    # Определить цену
    prices = {
        1: settings.SUBSCRIPTION_RUB_1MONTH,
        3: settings.SUBSCRIPTION_RUB_3MONTHS,
        6: settings.SUBSCRIPTION_RUB_6MONTHS,
        12: settings.SUBSCRIPTION_RUB_12MONTHS,
    }
    base_price = prices.get(subscription_months, 100.0)

    # Применить промокод
    discount = 0
    bonus_days = 0
    if promo_code:
        promo = PromoCode.get(promo_code)
        if promo:
            discount = promo.get("discount_percent", 0)
            bonus_days = promo.get("bonus_days", 0)

    # Вычислить финальную цену
    final_price = base_price * (1 - discount / 100)

    # Создать payload
    payload = json.dumps({
        "user_id": user_id,
        "months": subscription_months,
        "promo_code": promo_code,
        "bonus_days": bonus_days,
    })

    # Создать платеж
    from src.services.yookassa_service import create_payment, create_sbp_payment

    description = f"Подписка на Remnawave на {subscription_months} месяц(а/ев)"
    metadata = {
        "user_id": str(user_id),
        "subscription_months": str(subscription_months),
        "promo_code": promo_code or "",
    }

    if payment_method == "sbp":
        payment = await create_sbp_payment(
            amount=final_price,
            description=description,
            user_id=user_id,
            subscription_months=subscription_months,
            return_url="https://t.me/your_bot",  # Замените на ваш бот
            metadata=metadata,
        )
    else:
        payment = await create_payment(
            amount=final_price,
            description=description,
            user_id=user_id,
            subscription_months=subscription_months,
            return_url="https://t.me/your_bot",  # Замените на ваш бот
            metadata=metadata,
        )

    # Сохранить платеж в БД
    subscription_days = subscription_months * 30 + bonus_days
    payment_id = Payment.create(
        user_id=user_id,
        stars=0,
        amount_rub=final_price,
        invoice_payload=payload,
        subscription_days=subscription_days,
        promo_code=promo_code,
        payment_method=payment_method,
        yookassa_payment_id=payment.get("id"),
    )

    return payment


async def process_successful_payment(
    user_id: int,
    invoice_payload: str,
    total_amount: int,
    bot: Bot,
) -> Dict:
    """Обработать успешный платеж через Telegram Stars."""
    # Парсинг payload
    try:
        payload_data = json.loads(invoice_payload)
    except Exception:
        raise ValueError("Неверный формат payload")

    # Получить платеж из БД
    payment = Payment.get_by_payload(invoice_payload)
    if not payment:
        raise ValueError("Платеж не найден")

    if payment["status"] == "completed":
        raise ValueError("Платеж уже обработан")

    # Проверка суммы
    if payment["stars"] != total_amount:
        raise ValueError("Неверная сумма платежа")

    subscription_months = payload_data.get("months", 1)
    promo_code = payload_data.get("promo_code")
    bonus_days = payload_data.get("bonus_days", 0)

    # Получить или создать пользователя в Remnawave
    api_client = RemnawaveApiClient()
    user = BotUser.get_or_create(user_id)

    remnawave_user = None
    if user.get("remnawave_user_uuid"):
        try:
            remnawave_user = await api_client.get_user_by_uuid(
                user["remnawave_user_uuid"]
            )
        except Exception:
            pass

    # Создать или обновить пользователя
    settings = get_settings()
    username = user.get("username") or f"user_{user_id}"

    if remnawave_user:
        # Продлить подписку
        current_expire = remnawave_user.get("expire_at")
        if current_expire:
            expire_dt = datetime.fromisoformat(
                current_expire.replace("Z", "+00:00")
            )
        else:
            expire_dt = datetime.now()

        new_expire = expire_dt + timedelta(
            days=subscription_months * 30 + bonus_days
        )

        await api_client.update_user(
            user["remnawave_user_uuid"], expire_at=new_expire.isoformat()
        )
        remnawave_uuid = user["remnawave_user_uuid"]
        # Получить обновленные данные
        remnawave_user = await api_client.get_user_by_uuid(remnawave_uuid)
    else:
        # Создать нового пользователя
        expire_dt = datetime.now() + timedelta(
            days=subscription_months * 30 + bonus_days
        )
        remnawave_user = await api_client.create_user(
            username=username,
            expire_at=expire_dt.isoformat(),
            telegram_id=user_id,
            external_squad_uuid=settings.DEFAULT_EXTERNAL_SQUAD_UUID,
            internal_squad_uuids=settings.internal_squads,
        )
        remnawave_uuid = remnawave_user["uuid"]
        BotUser.set_remnawave_uuid(user_id, remnawave_uuid)

    # Получить ссылку на подписку
    subscriptions = remnawave_user.get("subscriptions", [])
    subscription_link = None
    if subscriptions:
        short_uuid = subscriptions[0].get("short_uuid")
        if short_uuid:
            try:
                sub_info = await api_client.get_subscription_info(short_uuid)
                subscription_link = sub_info.get("link")
            except Exception:
                pass

    # Обновить статус платежа
    Payment.update_status(
        payment["id"], "completed", remnawave_uuid=remnawave_uuid
    )

    # Применить промокод
    if promo_code:
        PromoCode.use(promo_code, user_id)

    # Начислить реферальный бонус
    await grant_referral_bonus(bot, user_id)

    # Отправить уведомления
    expire_date = expire_dt.isoformat()
    await notify_payment_success(
        bot,
        user_id,
        username,
        subscription_months,
        total_amount,
        promo_code,
        remnawave_uuid,
        expire_date,
    )

    return {
        "remnawave_uuid": remnawave_uuid,
        "subscription_link": subscription_link,
        "expire_at": expire_date,
    }


async def process_yookassa_payment(yookassa_payment_id: str, bot: Bot) -> Dict:
    """Обработать успешный платеж через YooKassa."""
    from src.services.yookassa_service import get_payment_status

    # Получить платеж из YooKassa
    payment = await get_payment_status(yookassa_payment_id)

    if payment.get("status") != "succeeded":
        raise ValueError("Платеж не завершен")

    # Получить платеж из БД
    db_payment = Payment.get_by_yookassa_payment_id(yookassa_payment_id)
    if not db_payment:
        raise ValueError("Платеж не найден в БД")

    if db_payment["status"] == "completed":
        raise ValueError("Платеж уже обработан")

    # Парсинг payload
    try:
        payload_data = json.loads(db_payment["invoice_payload"])
    except Exception:
        raise ValueError("Неверный формат payload")

    user_id = payload_data.get("user_id")
    subscription_months = payload_data.get("months", 1)
    promo_code = payload_data.get("promo_code")
    bonus_days = payload_data.get("bonus_days", 0)

    # Получить или создать пользователя в Remnawave
    api_client = RemnawaveApiClient()
    user = BotUser.get_or_create(user_id)

    remnawave_user = None
    if user.get("remnawave_user_uuid"):
        try:
            remnawave_user = await api_client.get_user_by_uuid(
                user["remnawave_user_uuid"]
            )
        except Exception:
            pass

    # Создать или обновить пользователя
    settings = get_settings()
    username = user.get("username") or f"user_{user_id}"

    if remnawave_user:
        # Продлить подписку
        current_expire = remnawave_user.get("expire_at")
        if current_expire:
            expire_dt = datetime.fromisoformat(
                current_expire.replace("Z", "+00:00")
            )
        else:
            expire_dt = datetime.now()

        new_expire = expire_dt + timedelta(
            days=subscription_months * 30 + bonus_days
        )

        await api_client.update_user(
            user["remnawave_user_uuid"], expire_at=new_expire.isoformat()
        )
        remnawave_uuid = user["remnawave_user_uuid"]
        # Получить обновленные данные
        remnawave_user = await api_client.get_user_by_uuid(remnawave_uuid)
    else:
        # Создать нового пользователя
        expire_dt = datetime.now() + timedelta(
            days=subscription_months * 30 + bonus_days
        )
        remnawave_user = await api_client.create_user(
            username=username,
            expire_at=expire_dt.isoformat(),
            telegram_id=user_id,
            external_squad_uuid=settings.DEFAULT_EXTERNAL_SQUAD_UUID,
            internal_squad_uuids=settings.internal_squads,
        )
        remnawave_uuid = remnawave_user["uuid"]
        BotUser.set_remnawave_uuid(user_id, remnawave_uuid)

    # Получить ссылку на подписку
    subscriptions = remnawave_user.get("subscriptions", [])
    subscription_link = None
    if subscriptions:
        short_uuid = subscriptions[0].get("short_uuid")
        if short_uuid:
            try:
                sub_info = await api_client.get_subscription_info(short_uuid)
                subscription_link = sub_info.get("link")
            except Exception:
                pass

    # Обновить статус платежа
    Payment.update_status(
        db_payment["id"], "completed", remnawave_uuid=remnawave_uuid
    )

    # Применить промокод
    if promo_code:
        PromoCode.use(promo_code, user_id)

    # Начислить реферальный бонус
    await grant_referral_bonus(bot, user_id)

    # Отправить уведомления
    expire_date = expire_dt.isoformat()
    await notify_payment_success(
        bot,
        user_id,
        username,
        subscription_months,
        0,  # Stars не используется
        promo_code,
        remnawave_uuid,
        expire_date,
    )

    return {
        "remnawave_uuid": remnawave_uuid,
        "subscription_link": subscription_link,
        "expire_at": expire_date,
    }

