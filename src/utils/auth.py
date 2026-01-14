"""Проверка прав администратора."""
from typing import Callable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from src.config import get_settings


def is_admin(user_id: int) -> bool:
    """Проверить, является ли пользователь админом."""
    return user_id in get_settings().admin_ids


class AdminMiddleware(BaseMiddleware):
    """Middleware для проверки прав администратора."""

    # Список публичных команд, которые доступны всем
    PUBLIC_COMMANDS = {"/start"}

    async def __call__(
        self,
        handler: Callable,
        event: TelegramObject,
        data: dict,
    ):
        """Проверить права администратора."""
        # Получить user_id из события
        user_id = None
        if hasattr(event, "from_user") and event.from_user:
            user_id = event.from_user.id
        elif hasattr(event, "message") and event.message and event.message.from_user:
            user_id = event.message.from_user.id
        elif hasattr(event, "callback_query") and event.callback_query:
            user_id = event.callback_query.from_user.id

        if not user_id:
            return await handler(event, data)

        # Проверить, является ли команда админской
        command = None
        if hasattr(event, "message") and event.message and event.message.text:
            parts = event.message.text.split()
            if parts:
                command = parts[0]
        elif hasattr(event, "callback_query") and event.callback_query:
            # Для callback проверяем по паттерну
            callback_data = event.callback_query.data
            # Админские callback обычно начинаются с определенных префиксов
            admin_prefixes = (
                "user:", "node:", "host:", "token:", "template:", "snippet:",
                "config:", "billing:", "provider:", "bulk:", "system:",
                "menu:section:", "user_edit:", "node_edit:", "host_edit:",
                "subs:", "subs_list", "user_search"
            )
            if callback_data and any(callback_data.startswith(prefix) for prefix in admin_prefixes):
                if not is_admin(user_id):
                    return  # Блокируем админские callback для неадминов

        # Если команда публичная - пропускаем
        if command in self.PUBLIC_COMMANDS:
            return await handler(event, data)

        # Если команда админская (начинается с /) и пользователь не админ - блокируем
        if command and command.startswith("/") and command not in self.PUBLIC_COMMANDS:
            if not is_admin(user_id):
                return  # Блокируем админские команды для неадминов

        return await handler(event, data)

