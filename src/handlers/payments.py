"""Обработка платежей."""
import logging

from aiogram import Router
from aiogram.types import CallbackQuery, Message, PreCheckoutQuery, SuccessfulPayment
from aiogram.utils.i18n import gettext as _

from src.database import Payment
from src.services.payment_service import (
    process_successful_payment,
    process_yookassa_payment,
)

logger = logging.getLogger(__name__)
router = Router()


@router.pre_checkout_query()
async def pre_checkout_handler(query: PreCheckoutQuery):
    """Проверка перед оплатой (Telegram Stars)."""
    try:
        invoice_payload = query.invoice_payload
        payment = Payment.get_by_payload(invoice_payload)

        if not payment:
            await query.answer(ok=False, error_message="Платеж не найден")
            return

        if payment["status"] == "completed":
            await query.answer(ok=False, error_message="Платеж уже обработан")
            return

        if payment["stars"] != query.total_amount:
            await query.answer(ok=False, error_message="Неверная сумма")
            return

        await query.answer(ok=True)
    except Exception as e:
        logger.exception(f"Pre-checkout error: {e}")
        await query.answer(ok=False, error_message="Ошибка проверки платежа")


@router.message(SuccessfulPayment)
async def successful_payment_handler(message: Message):
    """Обработка успешного платежа (Telegram Stars)."""
    t = _
    user_id = message.from_user.id
    payment = message.successful_payment

    try:
        result = await process_successful_payment(
            user_id, payment.invoice_payload, payment.total_amount, message.bot
        )

        subscription_link = result.get("subscription_link")
        expire_at = result.get("expire_at")

        text = t("payment.success").format(expire_at=expire_at)

        if subscription_link:
            text += f"\n\n🔗 {subscription_link}"

        await message.answer(text=text, parse_mode="Markdown")
    except Exception as e:
        logger.exception(f"Payment processing error: {e}")
        await message.answer(t("payment.error"), parse_mode="Markdown")


@router.callback_query(lambda c: c.data.startswith("yookassa:check:"))
async def check_yookassa_payment(callback: CallbackQuery):
    """Проверить статус платежа YooKassa."""
    t = _
    payment_id = callback.data.replace("yookassa:check:", "")

    try:
        result = await process_yookassa_payment(payment_id, callback.bot)

        subscription_link = result.get("subscription_link")
        expire_at = result.get("expire_at")

        text = t("payment.success").format(expire_at=expire_at)

        if subscription_link:
            text += f"\n\n🔗 {subscription_link}"

        await callback.message.edit_text(text=text, parse_mode="Markdown")
        await callback.answer(t("payment.success_short"))
    except Exception as e:
        logger.exception(f"YooKassa payment processing error: {e}")
        await callback.answer(t("payment.error"), show_alert=True)

