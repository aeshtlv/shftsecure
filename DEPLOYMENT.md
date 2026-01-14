# Инструкция по развертыванию на Ubuntu Server

## Вариант 1: Развертывание через Docker (Рекомендуется)

### Шаг 1: Подготовка сервера

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка необходимых пакетов
sudo apt install -y git curl

# Установка Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh

# Установка Docker Compose
sudo apt install -y docker-compose-plugin

# Добавление пользователя в группу docker (чтобы не использовать sudo)
sudo usermod -aG docker $USER
# Выйдите и войдите снова, чтобы изменения вступили в силу
```

### Шаг 2: Клонирование репозитория

```bash
# Перейдите в нужную директорию
cd /opt  # или любая другая директория

# Клонируйте репозиторий
sudo git clone https://github.com/aeshtlv/shftsecure.git
cd shftsecure

# Установите права доступа
sudo chown -R $USER:$USER .
```

### Шаг 3: Настройка переменных окружения

```bash
# Скопируйте пример файла конфигурации
cp env.sample .env

# Откройте файл для редактирования
nano .env
```

Заполните все необходимые переменные:
- `BOT_TOKEN` - токен вашего Telegram бота
- `API_BASE_URL` - URL вашего Remnawave API
- `API_TOKEN` - токен доступа к API
- `ADMINS` - список Telegram ID админов через запятую

### Шаг 4: Создание Docker сети

```bash
# Создайте сеть (если еще не создана)
docker network create remnawave-network
```

### Шаг 5: Запуск бота

```bash
# Соберите и запустите контейнер
docker compose up -d --build

# Проверьте логи
docker compose logs -f bot
```

### Шаг 6: Автозапуск при перезагрузке

Docker Compose с `restart: unless-stopped` уже настроен на автозапуск. Контейнер будет автоматически запускаться при перезагрузке сервера.

### Управление ботом

```bash
# Остановить бота
docker compose down

# Запустить бота
docker compose up -d

# Перезапустить бота
docker compose restart

# Просмотр логов
docker compose logs -f bot

# Просмотр статуса
docker compose ps
```

---

## Вариант 2: Развертывание без Docker

### Шаг 1: Установка Python и зависимостей

```bash
# Обновление системы
sudo apt update && sudo apt upgrade -y

# Установка Python 3.12 и необходимых пакетов
sudo apt install -y python3.12 python3.12-venv python3-pip git

# Создание виртуального окружения (рекомендуется)
python3.12 -m venv venv
source venv/bin/activate
```

### Шаг 2: Клонирование репозитория

```bash
# Перейдите в нужную директорию
cd /opt  # или любая другая директория

# Клонируйте репозиторий
sudo git clone https://github.com/aeshtlv/shftsecure.git
cd shftsecure

# Установите права доступа
sudo chown -R $USER:$USER .
```

### Шаг 3: Установка зависимостей

```bash
# Активируйте виртуальное окружение (если используете)
source venv/bin/activate

# Установите зависимости
pip install -r requirements.txt
```

### Шаг 4: Настройка переменных окружения

```bash
# Скопируйте пример файла конфигурации
cp env.sample .env

# Откройте файл для редактирования
nano .env
```

Заполните все необходимые переменные.

### Шаг 5: Создание systemd сервиса для автозапуска

```bash
# Создайте файл сервиса
sudo nano /etc/systemd/system/remnabuy-bot.service
```

Вставьте следующее содержимое (замените пути на ваши):

```ini
[Unit]
Description=RemnaBuy Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/opt/shftsecure
Environment="PATH=/opt/shftsecure/venv/bin"
ExecStart=/opt/shftsecure/venv/bin/python -m src.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

**Важно:** Замените:
- `your_username` на ваше имя пользователя
- `/opt/shftsecure` на путь к вашему проекту
- `/opt/shftsecure/venv/bin` на путь к виртуальному окружению (если используете)

Если не используете виртуальное окружение:
```ini
[Unit]
Description=RemnaBuy Telegram Bot
After=network.target

[Service]
Type=simple
User=your_username
WorkingDirectory=/opt/shftsecure
ExecStart=/usr/bin/python3 -m src.main
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### Шаг 6: Запуск сервиса

```bash
# Перезагрузите systemd
sudo systemctl daemon-reload

# Включите автозапуск
sudo systemctl enable remnabuy-bot.service

# Запустите сервис
sudo systemctl start remnabuy-bot.service

# Проверьте статус
sudo systemctl status remnabuy-bot.service

# Просмотр логов
sudo journalctl -u remnabuy-bot.service -f
```

### Управление ботом

```bash
# Остановить бота
sudo systemctl stop remnabuy-bot.service

# Запустить бота
sudo systemctl start remnabuy-bot.service

# Перезапустить бота
sudo systemctl restart remnabuy-bot.service

# Просмотр логов
sudo journalctl -u remnabuy-bot.service -f

# Отключить автозапуск
sudo systemctl disable remnabuy-bot.service
```

---

## Проверка работы

После запуска проверьте:

1. **Логи бота** - должны быть сообщения о успешном запуске
2. **Подключение к API** - должно быть сообщение "✅ API connection successful"
3. **Telegram бот** - отправьте команду `/start` боту

## Обновление бота

### При использовании Docker:

```bash
cd /opt/shftsecure
git pull
docker compose up -d --build
```

### При использовании systemd:

```bash
cd /opt/shftsecure
git pull
source venv/bin/activate  # если используете venv
pip install -r requirements.txt
sudo systemctl restart remnabuy-bot.service
```

## Решение проблем

### Бот не запускается

1. Проверьте логи:
   ```bash
   # Docker
   docker compose logs bot
   
   # Systemd
   sudo journalctl -u remnabuy-bot.service -n 50
   ```

2. Проверьте файл `.env` - все ли переменные заполнены

3. Проверьте доступность API:
   ```bash
   curl -H "Authorization: Bearer YOUR_API_TOKEN" https://your-api-url/api/system/health
   ```

### Ошибки базы данных

База данных `bot_data.db` создается автоматически. Убедитесь, что у процесса есть права на запись в директорию проекта.

### Проблемы с сетью Docker

Если используете Docker и бот не может подключиться к API:
```bash
# Проверьте существование сети
docker network ls | grep remnawave-network

# Если сети нет, создайте её
docker network create remnawave-network
```

## Безопасность

1. **Файл `.env`** - не коммитьте его в Git (уже в `.gitignore`)
2. **Права доступа** - убедитесь, что `.env` доступен только владельцу:
   ```bash
   chmod 600 .env
   ```
3. **Firewall** - настройте firewall, если нужно:
   ```bash
   sudo ufw allow 22/tcp  # SSH
   sudo ufw enable
   ```

## Мониторинг

Для мониторинга работы бота можно использовать:

- **Docker stats** (для Docker):
  ```bash
  docker stats remnabuy_bot
  ```

- **Systemd status** (для systemd):
  ```bash
  sudo systemctl status remnabuy-bot.service
  ```

- **Логи** - регулярно проверяйте логи на наличие ошибок

