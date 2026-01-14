"""Общие утилиты для обработчиков."""
import asyncio
from typing import Optional, Union

from aiogram import Bot
from aiogram.types import CallbackQuery, Message

from src.utils.auth import is_admin


async def _cleanup_message(message: Message, delay: float = 2.0):
    """Удалить сообщение с задержкой."""
    await asyncio.sleep(delay)
    try:
        await message.delete()
    except Exception:
        pass


async def _send_clean_message(
    target: Union[Message, CallbackQuery],
    text: str,
    reply_markup=None,
    parse_mode: Optional[str] = "Markdown",
):
    """Отправить или отредактировать сообщение."""
    if isinstance(target, CallbackQuery):
        try:
            await target.message.edit_text(
                text=text, reply_markup=reply_markup, parse_mode=parse_mode
            )
        except Exception:
            await target.message.answer(
                text=text, reply_markup=reply_markup, parse_mode=parse_mode
            )
    else:
        await target.answer(text=text, reply_markup=reply_markup, parse_mode=parse_mode)


def _not_admin(message: Message) -> bool:
    """Проверить, является ли пользователь админом."""
    return not is_admin(message.from_user.id)


def _get_target_user_id(target: Union[Message, CallbackQuery]) -> int:
    """Извлечь user_id."""
    if isinstance(target, CallbackQuery):
        return target.from_user.id
    return target.from_user.id


def _clear_user_state(user_id: int, keep_search: bool = False, keep_subs: bool = False):
    """Очистить состояние пользователя."""
    from src.handlers.state import (
        PENDING_INPUT,
        USER_SEARCH_CONTEXT,
        SUBS_PAGE_BY_USER,
    )

    if not keep_search:
        USER_SEARCH_CONTEXT.pop(user_id, None)
    if not keep_subs:
        SUBS_PAGE_BY_USER.pop(user_id, None)
    PENDING_INPUT.pop(user_id, None)


async def _edit_text_safe(
    message: Message,
    text: str,
    reply_markup=None,
    parse_mode: Optional[str] = "Markdown",
):
    """Безопасно отредактировать текст."""
    try:
        await message.edit_text(
            text=text, reply_markup=reply_markup, parse_mode=parse_mode
        )
    except Exception:
        await message.answer(
            text=text, reply_markup=reply_markup, parse_mode=parse_mode
        )

