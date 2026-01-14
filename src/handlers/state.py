"""Глобальное состояние."""
from typing import Dict, Optional

# Ожидаемый ввод от пользователей
PENDING_INPUT: Dict[int, str] = {}

# Последние сообщения бота в каждом чате
LAST_BOT_MESSAGES: Dict[int, int] = {}

# Контекст поиска пользователей
USER_SEARCH_CONTEXT: Dict[int, Dict] = {}

# Целевое меню для возврата
USER_DETAIL_BACK_TARGET: Dict[int, str] = {}

# Текущая страница подписок
SUBS_PAGE_BY_USER: Dict[int, int] = {}

# Константы
ADMIN_COMMAND_DELETE_DELAY = 2.0
SEARCH_PAGE_SIZE = 100
MAX_SEARCH_RESULTS = 10
SUBS_PAGE_SIZE = 8

