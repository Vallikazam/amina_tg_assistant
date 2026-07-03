from __future__ import annotations

from aiogram import Bot, Dispatcher

from bot.config import Settings
from bot.db import Database
from bot.handlers import create_commands_router, create_messages_router
from bot.services import AssistantService


async def create_bot_dispatcher(settings: Settings) -> tuple[Bot, Dispatcher]:
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
    dispatcher.include_router(create_commands_router())
    dispatcher.include_router(create_messages_router())

    return bot, dispatcher
