from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command, CommandObject, CommandStart
from aiogram.types import Message

from bot.db import Database
from bot.handlers.callbacks import format_memory_text, help_text
from bot.keyboards import main_menu_keyboard, start_inline_keyboard
from bot.services import AssistantService
from bot.services.safety import is_sensitive_memory

router = Router(name="commands")


def create_commands_router() -> Router:
    fresh_router = Router(name="commands")
    fresh_router.message(CommandStart())(start)
    fresh_router.message(Command("help"))(help_command)
    fresh_router.message(Command("ask"))(ask)
    fresh_router.message(Command("reset"))(reset)
    fresh_router.message(Command("remember"))(remember)
    fresh_router.message(Command("memory"))(memory)
    fresh_router.message(Command("forget"))(forget)
    return fresh_router


@router.message(CommandStart())
async def start(message: Message, db: Database) -> None:
    if message.from_user is None:
        return

    await db.upsert_user(message.from_user)
    await message.answer(
        "Привет! Я Amina, AI-ассистент в Telegram.\n\n"
        "Напиши вопрос обычным сообщением или выбери действие в меню снизу.",
        reply_markup=main_menu_keyboard(),
    )
    await message.answer(
        "Быстрые действия:",
        reply_markup=start_inline_keyboard(),
    )


@router.message(Command("help"))
async def help_command(message: Message) -> None:
    await message.answer(
        help_text(),
        reply_markup=main_menu_keyboard(),
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
        await message.answer(
            "Напиши вопрос после команды: /ask как выучить Python?",
            reply_markup=main_menu_keyboard(),
        )
        return

    user_id = await db.upsert_user(message.from_user)
    await message.bot.send_chat_action(message.chat.id, "typing")
    answer = await assistant.answer(user_id=user_id, prompt=prompt)
    await message.answer(answer, reply_markup=main_menu_keyboard())


@router.message(Command("reset"))
async def reset(message: Message, db: Database) -> None:
    if message.from_user is None:
        return

    user_id = await db.upsert_user(message.from_user)
    await db.clear_messages(user_id)
    await message.answer("История диалога очищена.", reply_markup=main_menu_keyboard())


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
        await message.answer(
            "Напиши факт после команды: /remember Я учу Python",
            reply_markup=main_menu_keyboard(),
        )
        return

    if is_sensitive_memory(fact):
        await message.answer(
            "Я не буду сохранять пароли, токены, ключи, банковские данные "
            "или чувствительные документы. Лучше держать это вне памяти бота.",
            reply_markup=main_menu_keyboard(),
        )
        return

    user_id = await db.upsert_user(message.from_user)
    await db.add_memory(user_id, fact)
    await message.answer("Запомнила.", reply_markup=main_menu_keyboard())


@router.message(Command("memory"))
async def memory(message: Message, db: Database) -> None:
    if message.from_user is None:
        return

    user_id = await db.upsert_user(message.from_user)
    memories = await db.list_memories(user_id)

    await message.answer(format_memory_text(memories), reply_markup=main_menu_keyboard())


@router.message(Command("forget"))
async def forget(message: Message, db: Database) -> None:
    if message.from_user is None:
        return

    user_id = await db.upsert_user(message.from_user)
    await db.clear_memories(user_id)
    await message.answer("Память очищена.", reply_markup=main_menu_keyboard())
