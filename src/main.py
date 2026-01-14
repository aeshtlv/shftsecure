"""Точка входа приложения."""
import asyncio
import logging
import sys

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode

from src.config import get_settings
from src.database import init_database
from src.handlers import (
    billing,
    bulk,
    commands,
    errors,
    hosts,
    navigation,
    nodes,
    payments,
    purchase,
    resources,
    system,
    user_public,
    users,
)
from src.services.api_client import RemnawaveApiClient
from src.services.renewal_service import start_renewal_checker
from src.services.yookassa_service import init_yookassa
from src.utils.auth import AdminMiddleware
from src.utils.i18n import get_i18n_middleware
from src.utils.logger import setup_logger

logger = logging.getLogger(__name__)


async def check_api_connection():
    """Проверить подключение к API."""
    try:
        api_client = RemnawaveApiClient()
        await api_client.get_health()
        logger.info("✅ API connection successful")
        return True
    except Exception as e:
        logger.error(f"❌ API connection failed: {e}")
        return False


async def main():
    """Главная функция."""
    # Настройка логирования
    setup_logger()
    logger.info("🚀 Starting RemnaBuy bot...")

    # Загрузка настроек
    settings = get_settings()
    logger.info(f"📋 Loaded settings (locale: {settings.DEFAULT_LOCALE})")

    # Инициализация БД
    init_database()
    logger.info("✅ Database initialized")

    # Проверка подключения к API
    if not await check_api_connection():
        logger.error("❌ Cannot connect to API. Exiting.")
        sys.exit(1)

    # Инициализация YooKassa
    try:
        init_yookassa()
        logger.info("✅ YooKassa initialized")
    except Exception as e:
        logger.warning(f"⚠️ YooKassa not initialized: {e}")

    # Создание бота и диспетчера
    bot = Bot(
        token=settings.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN),
    )
    dp = Dispatcher()

    # Регистрация middleware
    dp.message.middleware(AdminMiddleware())
    dp.callback_query.middleware(AdminMiddleware())
    dp.message.middleware(get_i18n_middleware())
    dp.callback_query.middleware(get_i18n_middleware())

    # Регистрация обработчиков
    dp.include_router(errors.router)
    dp.include_router(commands.router)
    dp.include_router(navigation.router)
    dp.include_router(user_public.router)
    dp.include_router(purchase.router)
    dp.include_router(payments.router)
    dp.include_router(users.router)
    dp.include_router(nodes.router)
    dp.include_router(hosts.router)
    dp.include_router(resources.router)
    dp.include_router(billing.router)
    dp.include_router(bulk.router)
    dp.include_router(system.router)

    # Запуск фоновой задачи автопродления
    asyncio.create_task(start_renewal_checker(bot, interval_hours=6))
    logger.info("✅ Renewal checker started")

    # Запуск polling
    logger.info("✅ Bot started. Polling...")
    await dp.start_polling(bot)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("👋 Bot stopped by user")
    except Exception as e:
        logger.exception(f"❌ Fatal error: {e}")
        sys.exit(1)

