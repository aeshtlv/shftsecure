"""Процесс покупки."""
import logging
from io import BytesIO

from aiogram import Router
from aiogram.types import CallbackQuery, Message
from aiogram.utils.i18n import gettext as _

from src.database import PromoCode
from src.keyboards.user_public import (
    payment_method_keyboard,
    subscription_keyboard,
    yookassa_payment_keyboard,
)
from src.handlers.state import PENDING_INPUT
from src.services.payment_service import (
    create_subscription_invoice,
    create_yookassa_payment,
)
from src.services.yookassa_service import generate_qr_code

logger = logging.getLogger(__name__)
router = Router()


@router.callback_query(lambda c: c.data.startswith("purchase:"))
async def purchase_handler(callback: CallbackQuery):
    """Обработка покупки."""
    t = _
    data_parts = callback.data.split(":")

    if len(data_parts) == 2:
        # Выбор тарифа
        months = int(data_parts[1])
        text = t("purchase.select_method").format(months=months)
        await callback.message.edit_text(
            text=text,
            reply_markup=payment_method_keyboard(months),
            parse_mode="Markdown",
        )
        await callback.answer()

    elif len(data_parts) == 4 and data_parts[2] == "method":
        # Выбор способа оплаты
        months = int(data_parts[1])
        method = data_parts[3]

        if method == "stars":
            # Оплата через Telegram Stars
            user_id = callback.from_user.id
            invoice_link = await create_subscription_invoice(
                callback.bot, user_id, months
            )

            text = t("purchase.stars_payment").format(link=invoice_link)
            await callback.message.edit_text(text=text, parse_mode="Markdown")
            await callback.answer()

        elif method == "yookassa":
            # Меню выбора способа оплаты YooKassa
            text = t("purchase.yookassa_select_method").format(months=months)
            await callback.message.edit_text(
                text=text,
                reply_markup=yookassa_payment_keyboard(months),
                parse_mode="Markdown",
            )
            await callback.answer()

    elif len(data_parts) == 5 and data_parts[2] == "method" and data_parts[3] == "yookassa":
        # Выбор конкретного способа оплаты YooKassa
        months = int(data_parts[1])
        payment_method = data_parts[4]  # sbp или card

        user_id = callback.from_user.id
        payment = await create_yookassa_payment(
            callback.bot, user_id, months, payment_method=payment_method
        )

        if payment_method == "sbp":
            # СБП - показать QR-код
            qr_data = payment.get("confirmation", {}).get("confirmation_data", "")
            if qr_data:
                qr_image = generate_qr_code(qr_data)
                await callback.message.answer_photo(
                    photo=BytesIO(qr_image),
                    caption=t("purchase.sbp_qr"),
                    parse_mode="Markdown",
                )
            else:
                await callback.message.edit_text(
                    t("purchase.error"), parse_mode="Markdown"
                )
        else:
            # Карта - показать ссылку
            payment_url = payment.get("confirmation", {}).get("confirmation_url", "")
            if payment_url:
                text = t("purchase.card_payment").format(url=payment_url)
                await callback.message.edit_text(text=text, parse_mode="Markdown")
            else:
                await callback.message.edit_text(
                    t("purchase.error"), parse_mode="Markdown"
                )

        await callback.answer()

    elif len(data_parts) == 3 and data_parts[2] == "promo":
        # Ввод промокода
        months = int(data_parts[1])
        user_id = callback.from_user.id
        PENDING_INPUT[user_id] = f"promo:{months}"

        text = t("purchase.enter_promo")
        await callback.message.edit_text(text=text, parse_mode="Markdown")
        await callback.answer()

    elif len(data_parts) == 4 and data_parts[2] == "promo" and data_parts[3].startswith("apply:"):
        # Применить промокод
        months = int(data_parts[1])
        promo_code = data_parts[3].replace("apply:", "")

        user_id = callback.from_user.id
        can_use, error = PromoCode.can_use(promo_code, user_id)

        if not can_use:
            await callback.answer(error, show_alert=True)
            return

        # Создать платеж с промокодом
        invoice_link = await create_subscription_invoice(
            callback.bot, user_id, months, promo_code
        )

        text = t("purchase.stars_payment").format(link=invoice_link)
        await callback.message.edit_text(text=text, parse_mode="Markdown")
        await callback.answer()


@router.message(lambda m: m.text and not m.text.startswith("/"))
async def handle_promo_input(message: Message):
    """Обработка ввода промокода."""
    user_id = message.from_user.id

    if user_id not in PENDING_INPUT:
        return

    pending = PENDING_INPUT[user_id]
    if not pending.startswith("promo:"):
        return

    months = int(pending.split(":")[1])
    promo_code = message.text.strip().upper()

    can_use, error = PromoCode.can_use(promo_code, user_id)

    if not can_use:
        await message.answer(f"❌ {error}")
        return

    # Применить промокод
    from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
    t = _

    buttons = [
        [
            InlineKeyboardButton(
                text=t("purchase.apply_promo"),
                callback_data=f"purchase:{months}:promo:apply:{promo_code}",
            )
        ],
        [
            InlineKeyboardButton(
                text=t("nav.back"), callback_data=f"purchase:{months}"
            )
        ],
    ]

    promo = PromoCode.get(promo_code)
    discount = promo.get("discount_percent", 0)
    bonus_days = promo.get("bonus_days", 0)

    text = t("purchase.promo_info").format(
        code=promo_code, discount=discount, bonus_days=bonus_days
    )

    await message.answer(
        text=text,
        reply_markup=InlineKeyboardMarkup(inline_keyboard=buttons),
        parse_mode="Markdown",
    )

    del PENDING_INPUT[user_id]

