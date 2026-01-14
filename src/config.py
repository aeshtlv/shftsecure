"""Конфигурация приложения."""
import json
import os
from functools import lru_cache
from typing import List, Optional

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Настройки приложения."""

    # Обязательные
    BOT_TOKEN: str
    API_BASE_URL: str
    API_TOKEN: str
    ADMINS: str  # Список через запятую

    # Опциональные
    DEFAULT_LOCALE: str = Field(default="ru")
    LOG_LEVEL: str = Field(default="INFO")
    NOTIFICATIONS_CHAT_ID: Optional[int] = None
    NOTIFICATIONS_TOPIC_ID: Optional[int] = None

    # Telegram Stars цены
    SUBSCRIPTION_STARS_1MONTH: int = Field(default=100)
    SUBSCRIPTION_STARS_3MONTHS: int = Field(default=250)
    SUBSCRIPTION_STARS_6MONTHS: int = Field(default=450)
    SUBSCRIPTION_STARS_12MONTHS: int = Field(default=800)

    # YooKassa настройки
    YOOKASSA_SHOP_ID: Optional[str] = None
    YOOKASSA_SECRET_KEY: Optional[str] = None
    SUBSCRIPTION_RUB_1MONTH: float = Field(default=100.0)
    SUBSCRIPTION_RUB_3MONTHS: float = Field(default=250.0)
    SUBSCRIPTION_RUB_6MONTHS: float = Field(default=450.0)
    SUBSCRIPTION_RUB_12MONTHS: float = Field(default=800.0)

    # Другие настройки
    TRIAL_DAYS: int = Field(default=3)
    REFERRAL_BONUS_DAYS: int = Field(default=3)
    DEFAULT_EXTERNAL_SQUAD_UUID: Optional[str] = None
    DEFAULT_INTERNAL_SQUADS: str = Field(default="[]")  # JSON или CSV

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    @field_validator("NOTIFICATIONS_CHAT_ID", "NOTIFICATIONS_TOPIC_ID", mode="before")
    @classmethod
    def parse_optional_int(cls, v):
        """Преобразовать пустую строку в None для опциональных int полей."""
        if v == "" or v is None:
            return None
        if isinstance(v, str):
            try:
                return int(v)
            except ValueError:
                return None
        return v

    @property
    def admin_ids(self) -> List[int]:
        """Получить список ID админов."""
        if not self.ADMINS:
            return []
        return [int(admin_id.strip()) for admin_id in self.ADMINS.split(",") if admin_id.strip()]

    @property
    def internal_squads(self) -> List[str]:
        """Получить список UUID внутренних сквадов."""
        if not self.DEFAULT_INTERNAL_SQUADS:
            return []

        # Попытка парсинга как JSON
        try:
            data = json.loads(self.DEFAULT_INTERNAL_SQUADS)
            if isinstance(data, list):
                return data
            if isinstance(data, str):
                return [data]
        except (json.JSONDecodeError, TypeError):
            pass

        # Попытка парсинга как CSV
        return [squad.strip() for squad in self.DEFAULT_INTERNAL_SQUADS.split(",") if squad.strip()]


_settings_cache: Optional[Settings] = None


@lru_cache(maxsize=1)
def get_settings(reload: bool = False) -> Settings:
    """Получить настройки (с кешированием)."""
    global _settings_cache
    if reload or _settings_cache is None:
        _settings_cache = Settings()
    return _settings_cache

