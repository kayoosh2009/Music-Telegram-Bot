# Telegram Music Bot (Python / aiogram)

Проект: бот для прослушивания музыки, загрузки треков и архивации в Telegram + хранение метаданных в Firebase.

## Как работает
- Код хранится в GitHub.
- GitHub Actions запускает бота (long polling).
- Action расписан каждые 5 часов — чтобы рестартовать бот (ограничение Actions: 6 часов запуска).
- При загрузке трека: бот сохраняет файл в Firebase Storage, метаданные в Firestore и отправляет аудио в архивный канал.

## Secrets (в GitHub -> Settings -> Secrets -> Actions)
Добавь следующие secrets:
- `TELEGRAM_BOT_TOKEN` — токен бота
- `FIREBASE_SERVICE_ACCOUNT_JSON` — JSON сервисного аккаунта Firebase (вся строка JSON)
- `FIREBASE_STORAGE_BUCKET` — например `project-id.appspot.com`
- `LOGS_CHANNEL_ID` — ID канала для логов (например `-100...`)
- `ARCHIVE_CHANNEL_ID` — ID канала для архива
- `ADMIN_USER_IDS` — опционально, CSV из user_id админов, если пусто — загрузка открыта всем

## Деплой
1. Клонируй репозиторий.
2. Запушь на GitHub.
3. Задай Secrets (см. выше).
4. Перейди в Actions и запусти workflow вручную или дождись schedule.

## Примечания
- GitHub Actions не гарантирует 100% «вечную» работу — если требуется постоянный непрерывный сервер — используй VPS или контейнерный хостинг.
- Код даёт рабочую основу; можно расширять поиск, inline-режим и т.д.
