from __future__ import annotations

from aiogram import F, Router
from aiogram.types import Message

from bot.db import Database
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
    if text.startswith("/"):
        await message.answer("Не знаю такую команду. Напиши /help, чтобы увидеть список.")
        return

    user_id = await db.upsert_user(message.from_user)
    await message.bot.send_chat_action(message.chat.id, "typing")
    answer = await assistant.answer(user_id=user_id, prompt=text)
    await message.answer(answer)
