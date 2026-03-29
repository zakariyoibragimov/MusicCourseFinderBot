# 🎵 Finder Music Bot

Полнофункциональный асинхронный Telegram бот для поиска, скачивания и потокового воспроизведения музыки с YouTube, SoundCloud, Vimeo, TikTok, Instagram и Spotify.

## ✨ Основные возможности

### 🔍 Поиск и загрузка
- **Мультиплатформенный поиск** - YouTube, SoundCloud, Vimeo, TikTok, Instagram, Spotify
- **Inline режим** - поиск прямо в чате (@botname query)  
- **Загрузка MP3** - с выбором качества (96, 128, 192, 320 kbps)
- **Загрузка MP4** - видео (480p, 720p, 1080p)
- **Плейлисты** - загрузка целых плейлистов с выборочным скачиванием
- **Автоопределение ссылок** - отправьте ссылку, бот предложит действия

### 🎵 Управление библиотекой
- **❤️ Избранное** - сохранение любимых треков
- **📜 История** - история последних 10 загрузок
- **📊 Популярное** - топовые треки на основе YouTube трендов
- **➕ Очередь** - создание плейлистов и воспроизведение
- **▶️ Воспроизведение** - слушание в чате (для личных сообщений)

### ⚙️ Персональные настройки
- **🎵 Качество аудио** - выбор битрейта
- **📹 Качество видео** - выбор разрешения  
- **🌍 Язык** - русский/английский
- **💾 Кэш** - управление кэш-хранилищем

### ⚡ Техническая оптимизация
- **💾 Интеллектуальное кэширование** - файловый и Redis кэш
- **🔄 Асинхронность** - полная асинхронная архитектура
- **⏱️ Rate Limiting** - защита от спама (5 запросов/мин на пользователя)
- **🚀 Параллельные загрузки** - до 3 файлов одновременно
- **📈 Масштабируемость** - поддержка PostgreSQL и Redis

### 🌐 Облачное хранилище (заглушки)
- **Google Drive** - для файлов > 50 МБ (комментарии как подключить)
- **Dropbox** - альтернативное хранилище (комментарии как подключить)

## 🏗️ Архитектура

```
┌─────────────────────────────────────────────────────────┐
│                  Telegram User                          │
└─────────────────┬───────────────────────────────────────┘
                  │
                  ▼
┌─────────────────────────────────────────────────────────┐
│           Telegram Bot API (python-telegram-bot)        │
└─────────────────┬───────────────────────────────────────┘
                  │
        ┌─────────┴──────────┐
        ▼                    ▼
    ┌────────────┐   ┌─────────────────┐
    │  Handlers  │   │  Search/Download│
    │  (Commands)│   │  (yt-dlp)       │
    └────────────┘   └─────────────────┘
        │                    │
        └─────────┬──────────┘
                  ▼
        ┌─────────────────────┐
        │   Services Layer    │
        ├─────────────────────┤
        │ - Downloader        │
        │ - Cache Manager     │
        │ - Rate Limiter      │
        │ - Cloud Storage     │
        └──────────┬──────────┘
                   │
        ┌──────────┴──────────┐
        ▼                     ▼
    ┌─────────┐          ┌──────────┐
    │PostgreSQL│         │   Redis   │
    │ (Users,  │         │ (Cache,   │
    │ Favs, +) │         │  Queue)   │
    └─────────┘          └──────────┘
```

## 📋 Требования

- **Python** 3.11+
- **PostgreSQL** 15+ (или Docker)
- **Redis** 7+ (или Docker)
- **FFmpeg** (система или Docker)
- **Git**

## 🚀 Установка

### Вариант 1: Docker (рекомендуется)

```bash
# Клонируем репозиторий
git clone https://github.com/yourusername/music-bot.git
cd music-bot

# Копируем конфигурацию
cp .env.example .env

# Редактируем .env и вставляем BOT_TOKEN и ADMIN_ID
nano .env  # или используй свой редактор

# Запускаем с Docker Compose
docker-compose up -d

# Проверяем логи
docker-compose logs -f bot
```

### Вариант 2: Локальная установка

1. **Установка зависимостей системы**

```bash
# Ubuntu/Debian
sudo apt-get update
sudo apt-get install -y python3.11 python3.11-venv postgresql redis-server ffmpeg

# macOS
brew install python@3.11 postgresql redis ffmpeg

# Windows
# Загрузите и установите:
# - Python 3.11 (https://python.org)
# - PostgreSQL (https://postgresql.org)
# - Redis (https://gitforwindows.org или WSL2)
# - FFmpeg (https://ffmpeg.org)
```

2. **Клонируем и настраиваем приложение**

```bash
git clone https://github.com/yourusername/music-bot.git
cd music-bot

# Создаём виртуальное окружение
python3.11 -m venv venv
source venv/bin/activate  # Linux/Mac
# или venv\\Scripts\\activate  # Windows

# Устанавливаем зависимости
pip install --upgrade pip
pip install -r requirements.txt

# Копируем конфигурацию
cp .env.example .env

# Редактируем .env
nano .env  # вставьте BOT_TOKEN и ADMIN_ID
```

3. **Инициализируем БД**

```bash
# Создаём базу данных PostgreSQL
createdb -U postgres music_bot_db

# Или из Python
python -c "from app.services.database import db_service; await db_service.initialize()"
```

4. **Запускаем бота**

```bash
python -m app.main
```

## 🔧 Конфигурация

### Основные переменные окружения

```env
# Обязательно
BOT_TOKEN=your_telegram_bot_token    # От @BotFather
ADMIN_ID=123456789                   # Ваш user_id

# БД и Redis
DB_HOST=localhost
PostgreSQL_PORT=5432
DB_USER=music_bot_user
DB_PASSWORD=secure_password

REDIS_HOST=localhost
REDIS_PORT=6379

# Качество по умолчанию
DEFAULT_AUDIO_BITRATE=192  # 96, 128, 192, 320
DEFAULT_VIDEO_RESOLUTION=720  # 480, 720, 1080

# Размеры файлов
MAX_FILE_SIZE_MB=50        # Обычный пользователь
PREMIUM_FILE_SIZE_MB=2000  # Premium пользователь

# Кэш
CACHE_MAX_SIZE_GB=10
CACHE_FILE_TTL=604800      # 7 дней
```

Описание всех переменных см. в `.env.example`.

## 📖 Команды бота

### Основные команды
- `/start` - начать работу с ботом
- `/help` - справка по командам
- `/search <запрос>` - поиск музыки
- `/popular` - популярная музыка

### Управление файлами
- `/download <URL>` - загрузить по ссылке
- `/playlist <URL>` - загрузить плейлист

### Управление библиотекой
- `/favorites` - избранное
- `/history` - история загрузок
- `/add <номер>` - добавить трек в очередь
- `/queue` - показать очередь
- `/skip` - пропустить трек
- `/clear` - очистить очередь

### Персональные
- `/settings` - настройки качества
- `/language` - выбрать язык

### Админ команды
- `/clear_cache` - очистить кэш (только админ)

## 🔗 Inline режим

Используйте бота в любом чате:

```
@music_bot_username the beatles yesterday
```

Бот покажет результаты с кнопками для действий.

## 🌐 Облачное хранилище

Для файлов > 50 МБ бот может загружать на облако:

### Google Drive

1. Создайте приложение на https://console.cloud.google.com/
2. Включите Google Drive API
3. Создайте service account с JSON credentialsМодифи
4. Скачайте JSON и сохраните в `/app/secrets/google-credentials.json`
5. В `.env`: `GOOGLE_DRIVE_ENABLED=true`

### Dropbox

1. Создайте приложение на https://www.dropbox.com/developers/apps
2. Сгенерируйте access token
3. В `.env`: `DROPBOX_ENABLED=true` и `DROPBOX_TOKEN=your_token`

## 📊 База данных

### Таблицы

- **users** - информация о пользователях
- **favorites** - избранные треки
- **history** - история загрузок
- **queues** - очереди пользователей
- **file_cache** - кэш загруженных файлов

## 🔐 Безопасность

- **Rate Limiting** - максимум 5 запросов в минуту на пользователя
- **File Size Limits** - ограничение на размер файлов
- **Async Operations** - безопасная обработка параллельных запросов
- **Error Handling** - перехват и логирование всех ошибок
- **Logging** - полное логирование в `/logs/bot.log`

## 🐛 Неполадки

### "BOT_TOKEN не установлен"
```bash
# Проверьте .env файл
cat .env | grep BOT_TOKEN

# Если не установлен, добавьте токен:
echo "BOT_TOKEN=your_token_here" >> .env
```

### "Ошибка подключения к PostgreSQL"
```bash
# Проверьте, что PostgreSQL запущен
pg_isready -h localhost -p 5432

# Проверьте credentials в .env
```

### "FFmpeg не найден"
```bash
# Проверьте путь
which ffmpeg  # Linux/Mac
where ffmpeg  # Windows

# Установите FFmpeg и обновить .env:
FFMPEG_PATH=/usr/bin/ffmpeg  # путь к ffmpeg
```

## 📝 Логирование

Логи сохраняются в `logs/bot.log` с ротацией (10 МБ на файл, 5 бэкапов).

```bash
# Просмотр логов
tail -f logs/bot.log

# В Docker
docker-compose logs -f bot
```

## 🤝 Вклад

Приветствуются pull requests! Для больших изменений сначала откройте Issue.

## 📄 Лицензия

MIT License - см. LICENSE файл

## 💬 Поддержка

- GitHub Issues - для ошибок и предложений
- Telegram - DM для прямой поддержки

---

**Автор:** [Your Name]  
**Последнее обновление:** 2024


3. **Устанавливаем зависимости**
```bash
pip install -r requirements.txt
```

4. **Настраиваем переменные окружения**
```bash
cp .env.example .env
# Отредактируйте .env с вашими параметрами
```

5. **Обеспечиваем работу PostgreSQL и Redis**
```bash
# Убедитесь что postgres и redis запущены локально
# Или используйте Docker Compose (см. ниже)
```

6. **Запускаем бота**
```bash
python -m app.main
```

### Docker Compose

Самый простой способ запустить всё:

```bash
# Скопируйте .env и отредактируйте BOT_TOKEN и ADMIN_ID
cp .env.example .env

# Запускаем все сервисы
docker-compose up -d

# Просмотр логов
docker-compose logs -f bot

# Остановка
docker-compose down
```

## 📋 Команды бота

### Поиск и загрузка
```
/search <запрос>         - поиск музыки
/download <URL>          - загрузить по ссылке
/playlist <URL>          - загрузить плейлист
```

### Воспроизведение
```
/play <номер>            - воспроизвести трек
/queue                   - показать очередь
/skip                    - пропустить трек
/pause                   - пауза
/resume                  - возобновить
```

### Управление
```
/favorites               - избранное
/history                 - история загрузок
/settings                - настройки качества
/popular                 - популярные треки
/clear_cache             - очистить кэш (админ)
```

## 🏗️ Структура проекта

```
music-bot/
├── app/
│   ├── __init__.py
│   ├── config.py              # Конфигурация
│   ├── main.py                # Точка входа
│   ├── db/
│   │   ├── __init__.py
│   │   └── database.py        # PostgreSQL
│   ├── handlers/
│   │   ├── __init__.py
│   │   ├── commands.py        # /start, /help
│   │   ├── search.py          # /search
│   │   └── download.py        # /download
│   ├── models/
│   │   └── __init__.py        # SQLAlchemy модели
│   ├── services/
│   │   ├── __init__.py
│   │   ├── downloader.py      # yt-dlp интеграция
│   │   └── redis_client.py    # Redis операции
│   └── utils/
│       ├── __init__.py
│       ├── logger.py          # Логирование
│       └── rate_limiter.py    # Rate limiting
├── cache/                     # Локальный кэш файлов
├── logs/                      # Логи приложения
├── .env                       # Переменные окружения
├── requirements.txt           # Python зависимости
├── Dockerfile                 # Docker образ
├── docker-compose.yml         # Docker Compose
└── README.md                  # Этот файл
```

## ⚙️ Конфигурация

### Переменные окружения (.env)

**Обязательные:**
- `BOT_TOKEN` - токен Telegram бота от @BotFather
- `ADMIN_ID` - ваш Telegram ID для админ-команд

**База данных:**
- `DATABASE_URL` - подключение PostgreSQL
- `REDIS_URL` - подключение Redis

**Качество:**
- `DEFAULT_AUDIO_BITRATE` - битрейт MP3 (96, 128, 192, 320)
- `DEFAULT_VIDEO_RESOLUTION` - разрешение видео (480, 720, 1080)

**Кэш:**
- `CACHE_TTL` - TTL кэша в секундах (600 = 10 мин)
- `CACHE_MAX_SIZE_GB` - максимальный размер кэша (10 ГБ)
- `MAX_FILE_SIZE_MB` - максимальный размер файла (50 МБ)

## 📊 Архитектура

### Database Layer
- **PostgreSQL** с asyncpg для асинхронных операций
- **SQLAlchemy ORM** для работы с БД
- Таблицы: users, tracks, favorites, history, queue, popular_tracks, file_cache

### Redis Cache
- Кэширование поисков (TTL 10 мин)
- Rate limiting
- Временные очереди

### Services
- **MusicDownloader** - yt-dlp для загрузки
- **RedisClient** - работа с Redis
- **Database** - асинхронная работа с PostgreSQL

### Handlers
- **Commands** - базовые команды (/start, /help)
- **Search** - поиск музыки
- **Download** - загрузка файлов
- **Playback** - воспроизведение

## 🔐 Безопасность

- Rate limiting (5 запросов в минуту на пользователя)
- Проверка размера файлов
- Валидация URL
- Логирование всех действий
- Обработка исключений

## 📈 Масштабируемость

- Асинхронная архитектура с asyncio
- Ограничение параллельных загрузок
- Кэширование для уменьшения нагрузки
- Поддержка Redis для распределённого кэша
- Docker Compose для легкого развёртывания

## 🐛 Логирование

Логи записываются в `logs/bot.log` с ротацией:
- Максимум один файл 10 МБ
- Сохраняются последние 5 файлов
- Также выводятся в консоль

## 📝 Лицензия

MIT

## 👥 支поддержка

Если возникают проблемы:
1. Проверьте конфигурацию в .env
2. Убедитесь что PostgreSQL и Redis запущены
3. Проверьте логи в `logs/bot.log`
4. Откройте issue на GitHub

## 🔄 Обновления

```bash
git pull
pip install -r requirements.txt
# Перезапустите бота
```

---

**Made with ❤️ for music lovers**
