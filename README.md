# Telegram CRM-бот для автосервиса

Полноценная CRM-система в Telegram для автоматизации записи клиентов, учёта мастеров и подъемников, напоминаний, отзывов и рассылок.

## Возможности

### Клиентская часть
- Регистрация с согласием на обработку данных
- Добавление автомобилей (марка, модель, год, госномер, VIN)
- Выбор категории и типа услуги
- Автоматический подбор свободных слотов с учётом длительности работ
- Подтверждение, отмена и перенос записи
- Напоминания за 1 день и за 2 часа до визита
- Оценка визита от 1 до 5 с комментарием

### Административная часть
- Расписание на день и на неделю
- Загрузка по мастерам и подъемникам
- Ручное добавление, перенос и отмена записей
- Блокировка/разблокировка временных слотов
- Карточка клиента с историей визитов и оценок
- Маркетинговые рассылки по базе с фильтрами
- Аналитика: записи, отмены, no-show, средняя оценка, повторные визиты

### Роли и права
| Роль | Доступ |
|------|--------|
| Owner | Полный доступ |
| Admin | Расписание, клиенты, рассылки |
| Manager | Создание и перенос записей |
| Master | Просмотр собственных задач |
| Marketing | Управление рассылками |

## Статусы записи

`created` → `confirmed` → `reminder_sent_day_before` → `reminder_sent_2h_before` → `in_progress` → `completed`

Альтернативные переходы: `cancelled_by_client`, `cancelled_by_admin`, `rescheduled`, `no_show`

## Технологический стек

- **Python 3.12+**
- **aiogram 3.x** — Telegram Bot Framework
- **FastAPI** — REST API и webhook
- **PostgreSQL** — основная база данных
- **Redis** — кэширование и очереди
- **SQLAlchemy 2.x** — ORM (async)
- **Alembic** — миграции базы данных
- **APScheduler** — планировщик задач
- **Docker / Docker Compose** — контейнеризация
- **structlog** — структурированное логирование

## Структура проекта

```
src/
├── main.py                 # Точка входа
├── config.py               # Конфигурация (pydantic-settings)
├── database.py             # Подключение к БД (SQLAlchemy async)
├── models/                 # Модели базы данных
│   ├── client.py           # Клиенты
│   ├── car.py              # Автомобили
│   ├── service.py          # Услуги
│   ├── staff.py            # Сотрудники
│   ├── lift.py             # Подъемники
│   ├── appointment.py      # Записи
│   ├── appointment_status_history.py  # История статусов
│   ├── blocked_slot.py     # Заблокированные слоты
│   ├── feedback.py         # Отзывы
│   ├── marketing_campaign.py  # Рассылки
│   └── audit_log.py        # Аудит-лог
├── schemas/                # Pydantic-схемы
├── services/               # Бизнес-логика
│   ├── booking.py          # Запись клиентов
│   ├── availability.py     # Проверка доступности слотов
│   ├── staff_assignment.py # Управление мастерами
│   ├── lift_allocation.py  # Управление подъемниками
│   ├── reminder.py         # Напоминания
│   ├── feedback.py         # Отзывы
│   ├── client_profile.py   # Профили клиентов
│   └── campaign.py         # Рассылки
├── bot/
│   ├── router.py           # Главный роутер
│   ├── client/             # Клиентские хендлеры
│   │   ├── registration.py # Регистрация
│   │   ├── car.py          # Автомобили
│   │   ├── booking.py      # Запись
│   │   ├── cancellation.py # Отмена/перенос
│   │   ├── feedback.py     # Отзывы
│   │   └── profile.py      # Профиль
│   ├── admin/              # Админские хендлеры
│   │   ├── schedule.py     # Расписание
│   │   ├── clients.py      # Клиенты
│   │   ├── appointments.py # Управление записями
│   │   ├── slots.py        # Мастера и подъемники
│   │   ├── campaigns.py    # Рассылки
│   │   └── analytics.py    # Аналитика
│   └── common/             # Общие компоненты
│       ├── keyboards.py    # Клавиатуры
│       ├── filters.py      # Фильтры ролей
│       └── texts.py        # Тексты сообщений
├── api/
│   └── app.py              # FastAPI приложение
├── scheduler/
│   └── tasks.py            # Периодические задачи
└── utils/
    └── logging.py          # Настройка логирования
alembic/                    # Миграции БД
tests/                      # Тесты
```

## Быстрый старт

### 1. Клонирование

```bash
git clone https://github.com/sithortodox/Telegram-CRM-bot.git
cd Telegram-CRM-bot
```

### 2. Настройка окружения

```bash
cp .env.example .env
```

Заполните `.env` файл:

```env
# Telegram
BOT_TOKEN=ваш_токен_от_BotFather

# База данных PostgreSQL
DB_HOST=db
DB_PORT=5432
DB_NAME=crm_autoservice
DB_USER=postgres
DB_PASSWORD=ваш_пароль

# Redis
REDIS_HOST=redis
REDIS_PORT=6379

# ID владельцев (через запятую)
OWNER_IDS=123456789
```

### 3. Запуск через Docker Compose

```bash
docker-compose up --build -d
```

### 4. Миграции базы данных

```bash
docker-compose exec bot alembic upgrade head
```

### 5. Первичная настройка

Добавьте мастера и подъемники через бота:

```
/add_master Иван Иванов
/add_lift Подъемник 1
```

Укажите ваш Telegram ID в `OWNER_IDS` в `.env` для получения прав Owner.

## Локальная разработка

### Установка зависимостей

```bash
python -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
```

### Запуск PostgreSQL и Redis

```bash
docker-compose up -d db redis
```

### Запуск миграций

```bash
alembic upgrade head
```

### Запуск бота

```bash
python -m src.main
```

### Запуск тестов

```bash
pytest -v
```

### Линтинг

```bash
ruff check src/ tests/
mypy src/
```

## Команды администратора

| Команда | Описание |
|---------|----------|
| `/add_master Имя` | Добавить мастера |
| `/add_lift Название` | Добавить подъемник |
| `/block_lift Название \| Дата \| Причина` | Заблокировать подъемник |
| `/deactivate_master Имя` | Деактивировать мастера |
| `/cancel_apt ID` | Отменить запись |
| `/complete_apt ID` | Завершить визит |
| `/noshow ID` | Отметить «не явился» |
| `/search Запрос` | Поиск клиента |
| `/new_campaign Название \| Текст` | Создать рассылку |

## Логика планирования

- Учитывается график работы сервиса (Пн–Сб, 09:00–21:00)
- Проверка доступности мастеров и подъемников
- Защита от пересечений записей (race conditions)
- Кузовной ремонт может блокировать ресурс на несколько дней
- Заблокированные слоты исключаются из поиска

## Лицензия

Частный проект. Все права защищены.
