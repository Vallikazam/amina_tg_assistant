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
