"""Локализация."""
import json
import os
from pathlib import Path
from typing import Any, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from aiogram.utils.i18n import I18n
from gettext import GNUTranslations

from src.config import get_settings


class JsonTranslations(GNUTranslations):
    """Обертка для gettext с поддержкой JSON."""

    def __init__(self, translations: Dict[str, Any]):
        self._catalog = translations
        self._fallback = None

    def gettext(self, message: str) -> str:
        """Получить перевод."""
        # Поддержка вложенных ключей через точку
        keys = message.split(".")
        value = self._catalog
        for key in keys:
            if isinstance(value, dict):
                value = value.get(key)
            else:
                break

        if value and isinstance(value, str):
            return value
        return message

    def ngettext(self, msgid1: str, msgid2: str, n: int) -> str:
        """Получить перевод с учетом числа."""
        return self.gettext(msgid1 if n == 1 else msgid2)


class JsonI18n(I18n):
    """Загрузчик локализации из JSON."""

    def __init__(self, path: str, default_locale: str = "ru"):
        self._path = Path(path)  # Сохраняем Path объект отдельно
        self.default_locale = default_locale
        super().__init__(path=str(self._path), default_locale=default_locale)

    def find_locales(self) -> Dict[str, Any]:
        """Найти доступные локали."""
        locales = {}
        if not self._path.exists():
            return locales

        for locale_dir in self._path.iterdir():
            if not locale_dir.is_dir():
                continue

            locale = locale_dir.name
            messages_file = locale_dir / "messages.json"

            if messages_file.exists():
                try:
                    with open(messages_file, "r", encoding="utf-8") as f:
                        translations = json.load(f)
                        locales[locale] = JsonTranslations(translations)
                except Exception:
                    pass

        return locales


_i18n_instance: I18n = None


def get_i18n() -> I18n:
    """Получить экземпляр I18n."""
    global _i18n_instance
    if _i18n_instance is None:
        settings = get_settings()
        locales_path = Path(__file__).parent.parent.parent / "locales"
        _i18n_instance = JsonI18n(
            path=str(locales_path), default_locale=settings.DEFAULT_LOCALE
        )
    return _i18n_instance


class I18nMiddleware(BaseMiddleware):
    """Middleware для локализации."""

    def __init__(self, i18n: I18n):
        self.i18n = i18n

    async def __call__(
        self,
        handler: Callable,
        event: TelegramObject,
        data: dict,
    ):
        """Установить локаль для обработчика."""
        # Получить язык пользователя
        user = None
        if hasattr(event, "from_user") and event.from_user:
            user = event.from_user
        elif hasattr(event, "message") and event.message and event.message.from_user:
            user = event.message.from_user
        elif hasattr(event, "callback_query") and event.callback_query:
            user = event.callback_query.from_user

        if user:
            # Получить язык из БД или использовать язык пользователя
            from src.database import BotUser
            db_user = BotUser.get_or_create(user.id)
            language = db_user.get("language") or user.language_code or "ru"
            
            # Установить локаль
            self.i18n.set_locale(language)
        else:
            # Использовать локаль по умолчанию
            self.i18n.set_locale(get_settings().DEFAULT_LOCALE)

        return await handler(event, data)


def get_i18n_middleware() -> I18nMiddleware:
    """Получить middleware для локализации."""
    return I18nMiddleware(get_i18n())

