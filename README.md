# Amina Telegram AI Assistant

Бесплатный стартовый Telegram AI-ассистент на Python, aiogram 3, Gemini API и SQLite.

## Возможности v1

- `/start` и `/help`
- AI-ответы на обычные сообщения
- `/ask <вопрос>` для явного AI-запроса
- история последних сообщений для каждого пользователя
- `/reset` для очистки истории
- `/remember <факт>` для личной памяти
- `/memory` для просмотра памяти
- `/forget` для очистки памяти
- SQLite-база создаётся автоматически

## Быстрый старт

1. Создай виртуальное окружение:

```bash
python -m venv .venv
```

2. Активируй окружение.

Windows PowerShell:

```powershell
.\.venv\Scripts\Activate.ps1
```

3. Установи зависимости:

```bash
pip install -r requirements.txt
```

4. Создай `.env` на основе `.env.example`:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
DATABASE_PATH=assistant.sqlite3
HISTORY_LIMIT=20
MAX_RESPONSE_CHARS=3500
```

5. Запусти бота локально:

```bash
python -m bot.main
```

## Где взять ключи

- Telegram token: создай бота через BotFather и скопируй токен.
- Gemini key: создай API key в Google AI Studio.

## Безопасность памяти

Бот не должен сохранять пароли, токены, API-ключи, банковские данные, паспортные данные и другие чувствительные сведения. Команда `/remember` содержит простую проверку таких данных, но пользователь всё равно должен не отправлять секреты в чат.

## Дальше

Для v2 можно добавить `/todo`, `/summary`, `/remind`, обработку файлов, webhook-деплой на Render и PostgreSQL.

## Деплой на Vercel

Vercel не запускает Telegram-бота через бесконечный `polling`. Для Vercel используется webhook:

```text
https://your-app.vercel.app/api/webhook
```

Endpoint реализован в `api/webhook/index.py`, потому что Vercel распознаёт `index.py` как Python entrypoint.

Локальный запуск через `python -m bot.main` остаётся без изменений.

### 1. Добавь переменные окружения в Vercel

В Vercel Project Settings -> Environment Variables добавь:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
GEMINI_API_KEY=your_gemini_api_key_here
GEMINI_MODEL=gemini-2.5-flash
TELEGRAM_WEBHOOK_SECRET=long_random_secret_here
```

`TELEGRAM_WEBHOOK_SECRET` должен быть одинаковым в Vercel и при регистрации webhook.

### 2. Задеплой проект

Через Vercel Dashboard импортируй GitHub-репозиторий или используй Vercel CLI:

```bash
vercel
vercel --prod
```

После деплоя будет URL вида:

```text
https://your-app.vercel.app
```

### 3. Зарегистрируй webhook в Telegram

Локально добавь в `.env`:

```env
VERCEL_APP_URL=https://your-app.vercel.app
TELEGRAM_WEBHOOK_SECRET=тот_же_секрет_что_в_vercel
```

Затем выполни:

```bash
python -m scripts.set_webhook
```

Если всё хорошо, Telegram вернёт JSON с `"ok": true`.

### 4. Проверь endpoint

Открой в браузере:

```text
https://your-app.vercel.app/api/webhook
```

Ожидаемый ответ:

```json
{"ok": true, "service": "amina-telegram-webhook"}
```

После этого напиши боту в Telegram:

```text
/start
```

### Важно про SQLite на Vercel

На Vercel SQLite в этом проекте используется только как демо-хранилище в `/tmp/assistant.sqlite3`. Оно не гарантирует постоянную память: история и `/remember` могут сбрасываться после перезапуска serverless-функции.

Для стабильной памяти лучше заменить SQLite на внешний PostgreSQL, например Neon или Supabase.
