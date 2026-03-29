# Finder Music Bot

Асинхронный Telegram-бот для поиска, скачивания и организации музыки с упором на production-ready архитектуру, Docker-деплой и масштабируемую backend-структуру.

## Overview

Этот проект показывает не только пользовательский Telegram UX, но и полноценную backend-архитектуру:
- асинхронные обработчики на python-telegram-bot
- PostgreSQL для пользовательских данных
- Redis для кэширования и rate limiting
- yt-dlp и FFmpeg для поиска и загрузки медиа
- Docker и docker-compose для развёртывания
- подписка на канал как access gate

Проект подходит как портфолио-кейс для Python backend / DevOps / Telegram automation.

## Key Features

### User Features
- Поиск музыки по тексту
- Inline search в Telegram
- Скачивание MP3 и MP4
- История действий пользователя
- Избранное
- Очередь треков
- Популярные треки
- Настройки качества аудио и видео
- Многоязычная текстовая база

### Access Control
- Проверка подписки на Telegram-канал
- Бесплатный лимит действий для неподписанных пользователей
- Повторная проверка подписки кнопкой в интерфейсе

### Backend Features
- PostgreSQL с SQLAlchemy async
- Redis как опциональный слой кэша
- Фоновая очистка файлового кэша
- Ограничение частоты запросов
- Централизованные сервисы в application.bot_data
- Docker-ready конфигурация для VPS

## Tech Stack

- Python 3.11+
- python-telegram-bot 20.7
- SQLAlchemy 2.x
- asyncpg
- Redis
- yt-dlp
- FFmpeg
- Docker
- docker compose

## Architecture

Проект организован по слоям:

- [app/main.py](app/main.py) — точка входа, lifecycle приложения, регистрация handlers
- [app/config.py](app/config.py) — конфигурация через environment variables
- [app/handlers](app/handlers) — команды, поиск, загрузка, playback
- [app/services](app/services) — БД, downloader, redis, recognizer и другие сервисы
- [app/utils](app/utils) — логирование, rate limiting, helper-функции, subscription gating
- [docker-compose.yml](docker-compose.yml) — инфраструктура для локального и серверного запуска
- [Dockerfile](Dockerfile) — контейнеризация приложения

Дополнительная документация:
- [ARCHITECTURE.md](ARCHITECTURE.md)
- [DEPLOYMENT.md](DEPLOYMENT.md)
- [QUICKSTART.md](QUICKSTART.md)
- [DEVELOPMENT.md](DEVELOPMENT.md)

## Main Commands

- `/start` — запуск бота и главное меню
- `/help` — справка
- `/search` — поиск музыки
- `/popular` — популярные треки
- `/queue` — очередь
- `/history` — история
- `/favorites` — избранное
- `/settings` — настройки качества и языка
- `/clear_cache` — очистка кэша для администратора

## Environment Variables

Минимально обязательные параметры:

```env
BOT_TOKEN=your_telegram_bot_token
ADMIN_ID=123456789
REQUIRED_CHANNEL_USERNAME=@your_channel
FREE_MUSIC_REQUEST_LIMIT=3
DB_USER=music_bot_user
DB_PASSWORD=strong_password
DB_NAME=music_bot_db
REDIS_ENABLED=true
```

Полный пример конфигурации есть в [.env.example](.env.example).

## Run Locally

### Option 1: Docker

```bash
git clone https://github.com/yourusername/finder-music-bot.git
cd finder-music-bot
cp .env.example .env
# заполните .env
docker compose up -d --build
```

### Option 2: Local Python Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m app.main
```

## Deployment

Проект подготовлен для запуска на Linux VPS.

Базовый сценарий:

```bash
git clone https://github.com/yourusername/finder-music-bot.git /opt/music-bot
cd /opt/music-bot
cp .env.example .env
# заполните .env
bash scripts/deploy_vps.sh
```

Подробный production-гайд:
- [DEPLOYMENT.md](DEPLOYMENT.md)

## Portfolio Value

Этот репозиторий показывает следующие навыки:
- проектирование backend-архитектуры
- асинхронный Python
- интеграция с внешними API и медиа-инструментами
- работа с PostgreSQL и Redis
- Docker-based deployment
- подготовка production-конфигурации
- документирование и структурирование реального проекта

## Current Notes

Что уже реализовано в текущем состоянии проекта:
- optional Redis startup
- DB-backed queue, history and favorites
- subscription gate with free usage limit
- automated cache cleanup loop
- production-prepared Docker setup for VPS deployment

## Security Notes

В репозиторий не должны попадать:
- `.env`
- токены Telegram
- реальные пароли БД
- серверные секреты
- `cache/` и `logs/`

Эти файлы уже исключены через [.gitignore](.gitignore).

## License

Если вы публикуете проект как портфолио, можно добавить MIT License отдельно. Сейчас репозиторий готов к публикации без секретов и с документацией.
