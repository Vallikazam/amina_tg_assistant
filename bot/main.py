from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher

from bot.config import Settings
from bot.db import Database
from bot.handlers import commands_router, messages_router
from bot.services import AssistantService


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    settings = Settings.from_env()
    settings.validate()

    db = Database(settings.database_path)
    await db.init()

    assistant = AssistantService(
        db=db,
        api_key=settings.gemini_api_key,
        model=settings.gemini_model,
        history_limit=settings.history_limit,
        max_response_chars=settings.max_response_chars,
    )

    bot = Bot(token=settings.telegram_bot_token)
    dispatcher = Dispatcher(db=db, assistant=assistant)
    dispatcher.include_router(commands_router)
    dispatcher.include_router(messages_router)

    logging.info("Amina Telegram assistant started")
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

