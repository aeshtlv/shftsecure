# RemnaBuy Bot

Telegram-бот для управления подписками через Remnawave API.

## Возможности

- **Публичный интерфейс** для пользователей:
  - Покупка подписок через Telegram Stars и YooKassa
  - Пробный период
  - Реферальная программа
  - Автопродление
  - Настройки пользователя

- **Админ-панель** для управления инфраструктурой Remnawave

## Установка

1. Клонируйте репозиторий
2. Скопируйте `env.sample` в `.env` и заполните переменные
3. Установите зависимости:
   ```bash
   pip install -r requirements.txt
   ```
4. Запустите бота:
   ```bash
   python -m src.main
   ```

## Docker

1. Создайте Docker сеть:
   ```bash
   docker network create remnawave-network
   ```

2. Запустите через docker-compose:
   ```bash
   docker compose up -d --build
   ```

## Конфигурация

См. `env.sample` для списка всех переменных окружения.

## Структура проекта

```
remnabuy/
├── src/              # Исходный код
├── locales/          # Локализация
├── requirements.txt  # Зависимости
├── Dockerfile        # Docker образ
└── docker-compose.yml
```

## Лицензия

MIT

