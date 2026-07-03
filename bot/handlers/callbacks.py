from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.config import Settings
from bot.db import Database
from bot.handlers.productivity import format_reminders, format_todos
from bot.keyboards import main_menu_keyboard, start_inline_keyboard
from bot.services.time_parser import local_day_range


def create_callbacks_router() -> Router:
    router = Router(name="callbacks")
    router.callback_query(F.data == "menu:help")(help_callback)
    router.callback_query(F.data == "menu:memory")(memory_callback)
    router.callback_query(F.data == "menu:todos")(todos_callback)
    router.callback_query(F.data == "menu:today")(today_callback)
    router.callback_query(F.data == "menu:reminders")(reminders_callback)
    router.callback_query(F.data == "menu:reset")(reset_callback)
    router.callback_query(F.data == "menu:forget")(forget_callback)
    return router


async def help_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return

    await callback.message.answer(
        help_text(),
        reply_markup=main_menu_keyboard(),
    )


async def memory_callback(callback: CallbackQuery, db: Database) -> None:
    await callback.answer()
    if callback.from_user is None or callback.message is None:
        return

    user_id = await db.upsert_user(callback.from_user)
    memories = await db.list_memories(user_id)
    await callback.message.answer(
        format_memory_text(memories),
        reply_markup=main_menu_keyboard(),
    )


async def todos_callback(callback: CallbackQuery, db: Database, settings: Settings) -> None:
    await callback.answer()
    if callback.from_user is None or callback.message is None:
        return

    user_id = await db.upsert_user(callback.from_user)
    todos = await db.list_open_todos(user_id)
    await callback.message.answer(
        format_todos(todos, settings.app_timezone),
        reply_markup=main_menu_keyboard(),
    )


async def today_callback(callback: CallbackQuery, db: Database, settings: Settings) -> None:
    await callback.answer()
    if callback.from_user is None or callback.message is None:
        return

    user_id = await db.upsert_user(callback.from_user)
    start, end = local_day_range(settings.app_timezone)
    todos = await db.list_todos_between(user_id, start, end)
    await callback.message.answer(
        "Сегодня:\n" + format_todos(todos, settings.app_timezone),
        reply_markup=main_menu_keyboard(),
    )


async def reminders_callback(callback: CallbackQuery, db: Database, settings: Settings) -> None:
    await callback.answer()
    if callback.from_user is None or callback.message is None:
        return

    user_id = await db.upsert_user(callback.from_user)
    reminders = await db.list_pending_reminders(user_id)
    await callback.message.answer(
        format_reminders(reminders, settings.app_timezone),
        reply_markup=main_menu_keyboard(),
    )


async def reset_callback(callback: CallbackQuery, db: Database) -> None:
    await callback.answer("История очищена")
    if callback.from_user is None or callback.message is None:
        return

    user_id = await db.upsert_user(callback.from_user)
    await db.clear_messages(user_id)
    await callback.message.answer(
        "История диалога очищена.",
        reply_markup=main_menu_keyboard(),
    )


async def forget_callback(callback: CallbackQuery, db: Database) -> None:
    await callback.answer("Память очищена")
    if callback.from_user is None or callback.message is None:
        return

    user_id = await db.upsert_user(callback.from_user)
    await db.clear_memories(user_id)
    await callback.message.answer(
        "Память очищена.",
        reply_markup=main_menu_keyboard(),
    )


def help_text() -> str:
    return (
        "Что я умею:\n"
        "/ask <вопрос> — ответить через AI\n"
        "/remember <факт> — сохранить полезный факт о тебе\n"
        "/memory — показать память\n"
        "/forget — очистить память\n"
        "/reset — очистить историю диалога\n"
        "/todo <задача> — добавить задачу\n"
        "/todos — показать задачи\n"
        "/done <id> — отметить задачу выполненной\n"
        "/delete_todo <id> — удалить задачу\n"
        "/remind <когда> <текст> — создать напоминание\n"
        "/reminders — показать напоминания\n"
        "/cancel_reminder <id> — отменить напоминание\n"
        "/today — задачи на сегодня\n"
        "/week — задачи на 7 дней\n\n"
        "Также можно просто отправить текст без команды."
    )


def format_memory_text(memories: list[str]) -> str:
    if not memories:
        return "Память пока пустая."

    lines = "\n".join(f"{index}. {memory}" for index, memory in enumerate(memories, 1))
    return f"Вот что я помню:\n{lines}"
