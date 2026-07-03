from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from bot.db import Database
from bot.handlers.callbacks import format_memory_text, help_text
from bot.keyboards import (
    MAIN_MENU_ASK,
    MAIN_MENU_HELP,
    MAIN_MENU_MEMORY,
    MAIN_MENU_RESET,
    MENU_TEXTS,
    main_menu_keyboard,
)
from bot.services import AssistantService

router = Router(name="messages")


def create_messages_router() -> Router:
    fresh_router = Router(name="messages")
    fresh_router.message(F.text)(text_message)
    return fresh_router


@router.message(F.text)
async def text_message(
    message: Message,
    db: Database,
    assistant: AssistantService,
) -> None:
    if message.from_user is None or message.text is None:
        return

    text = message.text.strip()
    if text in MENU_TEXTS:
        await handle_menu_text(message, text, db)
        return

    if text.startswith("/"):
        await message.answer(
            "Не знаю такую команду. Напиши /help, чтобы увидеть список.",
            reply_markup=main_menu_keyboard(),
        )
        return

    user_id = await db.upsert_user(message.from_user)
    await message.bot.send_chat_action(message.chat.id, "typing")
    answer = await assistant.answer(user_id=user_id, prompt=text)
    await message.answer(answer, reply_markup=main_menu_keyboard())


async def handle_menu_text(message: Message, text: str, db: Database) -> None:
    if message.from_user is None:
        return

    user_id = await db.upsert_user(message.from_user)

    if text == MAIN_MENU_ASK:
        await message.answer(
            "Напиши вопрос следующим сообщением, и я отвечу через AI.",
            reply_markup=main_menu_keyboard(),
        )
        return

    if text == MAIN_MENU_MEMORY:
        memories = await db.list_memories(user_id)
        await message.answer(
            format_memory_text(memories),
            reply_markup=main_menu_keyboard(),
        )
        return

    if text == MAIN_MENU_HELP:
        await message.answer(help_text(), reply_markup=main_menu_keyboard())
        return

    if text == MAIN_MENU_RESET:
        await db.clear_messages(user_id)
        await message.answer(
            "История диалога очищена.",
            reply_markup=main_menu_keyboard(),
        )
