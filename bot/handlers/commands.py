from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message

from bot.db import Database
from bot.services import AssistantService
from bot.services.safety import is_sensitive_memory

router = Router(name="commands")


@router.message(CommandStart())
async def start(message: Message, db: Database) -> None:
    if message.from_user is None:
        return

    await db.upsert_user(message.from_user)
    await message.answer(
        "Привет! Я Amina, AI-ассистент в Telegram.\n\n"
        "Напиши вопрос обычным сообщением или используй /ask.\n"
        "Память: /remember, /memory, /forget.\n"
        "История диалога: /reset."
    )


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(
        "Что я умею:\n"
        "/ask <вопрос> — ответить через AI\n"
        "/remember <факт> — сохранить полезный факт о тебе\n"
        "/memory — показать память\n"
        "/forget — очистить память\n"
        "/reset — очистить историю диалога\n\n"
        "Также можно просто отправить текст без команды."
    )


@router.message(Command("ask"))
async def ask(
    message: Message,
    command: CommandObject,
    db: Database,
    assistant: AssistantService,
) -> None:
    if message.from_user is None:
        return

    prompt = (command.args or "").strip()
    if not prompt:
        await message.answer("Напиши вопрос после команды: /ask как выучить Python?")
        return

    user_id = await db.upsert_user(message.from_user)
    await message.bot.send_chat_action(message.chat.id, "typing")
    answer = await assistant.answer(user_id=user_id, prompt=prompt)
    await message.answer(answer)


@router.message(Command("reset"))
async def reset(message: Message, db: Database) -> None:
    if message.from_user is None:
        return

    user_id = await db.upsert_user(message.from_user)
    await db.clear_messages(user_id)
    await message.answer("История диалога очищена.")


@router.message(Command("remember"))
async def remember(
    message: Message,
    command: CommandObject,
    db: Database,
) -> None:
    if message.from_user is None:
        return

    fact = (command.args or "").strip()
    if not fact:
        await message.answer("Напиши факт после команды: /remember Я учу Python")
        return

    if is_sensitive_memory(fact):
        await message.answer(
            "Я не буду сохранять пароли, токены, ключи, банковские данные "
            "или чувствительные документы. Лучше держать это вне памяти бота."
        )
        return

    user_id = await db.upsert_user(message.from_user)
    await db.add_memory(user_id, fact)
    await message.answer("Запомнила.")


@router.message(Command("memory"))
async def memory(message: Message, db: Database) -> None:
    if message.from_user is None:
        return

    user_id = await db.upsert_user(message.from_user)
    memories = await db.list_memories(user_id)

    if not memories:
        await message.answer("Память пока пустая.")
        return

    lines = "\n".join(f"{index}. {memory}" for index, memory in enumerate(memories, 1))
    await message.answer(f"Вот что я помню:\n{lines}")


@router.message(Command("forget"))
async def forget(message: Message, db: Database) -> None:
    if message.from_user is None:
        return

    user_id = await db.upsert_user(message.from_user)
    await db.clear_memories(user_id)
    await message.answer("Память очищена.")

