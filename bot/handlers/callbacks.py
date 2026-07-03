from __future__ import annotations

from aiogram import F, Router
from aiogram.types import CallbackQuery

from bot.config import Settings
from bot.db import Database
from bot.handlers.productivity import format_reminders, format_todos
from bot.keyboards import (
    main_menu_keyboard,
    productivity_inline_keyboard,
    reminders_inline_keyboard,
    start_inline_keyboard,
    todos_inline_keyboard,
)
from bot.services.time_parser import local_day_range, local_week_range


def create_callbacks_router() -> Router:
    router = Router(name="callbacks")
    router.callback_query(F.data == "menu:help")(help_callback)
    router.callback_query(F.data == "menu:memory")(memory_callback)
    router.callback_query(F.data == "menu:todos")(todos_callback)
    router.callback_query(F.data == "menu:today")(today_callback)
    router.callback_query(F.data == "menu:reminders")(reminders_callback)
    router.callback_query(F.data == "productivity:add_todo")(add_todo_callback)
    router.callback_query(F.data == "productivity:add_reminder")(add_reminder_callback)
    router.callback_query(F.data == "productivity:week")(week_callback)
    router.callback_query(F.data.startswith("todo:done:"))(todo_done_callback)
    router.callback_query(F.data.startswith("todo:delete:"))(todo_delete_callback)
    router.callback_query(F.data.startswith("reminder:cancel:"))(reminder_cancel_callback)
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
        reply_markup=todos_inline_keyboard(todos),
    )
    await callback.message.answer(
        "Меню снизу тоже доступно.",
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
        reply_markup=todos_inline_keyboard(todos),
    )
    await callback.message.answer(
        "Календарь задач.",
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
        reply_markup=reminders_inline_keyboard(reminders),
    )
    await callback.message.answer(
        "Меню снизу тоже доступно.",
        reply_markup=main_menu_keyboard(),
    )


async def add_todo_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return

    await callback.message.answer(
        "Чтобы добавить задачу, отправь:\n"
        "/todo купить продукты\n"
        "/todo завтра в 10:00 подготовить отчёт",
        reply_markup=productivity_inline_keyboard(),
    )


async def add_reminder_callback(callback: CallbackQuery) -> None:
    await callback.answer()
    if callback.message is None:
        return

    await callback.message.answer(
        "Чтобы создать напоминание, отправь:\n"
        "/remind через 30 минут размяться\n"
        "/remind завтра в 09:00 созвон",
        reply_markup=productivity_inline_keyboard(),
    )


async def week_callback(callback: CallbackQuery, db: Database, settings: Settings) -> None:
    await callback.answer()
    if callback.from_user is None or callback.message is None:
        return

    user_id = await db.upsert_user(callback.from_user)
    start, end = local_week_range(settings.app_timezone)
    todos = await db.list_todos_between(user_id, start, end)
    await callback.message.answer(
        "Ближайшие 7 дней:\n" + format_todos(todos, settings.app_timezone),
        reply_markup=todos_inline_keyboard(todos),
    )


async def todo_done_callback(callback: CallbackQuery, db: Database, settings: Settings) -> None:
    await callback.answer("Готово")
    if callback.from_user is None or callback.message is None or callback.data is None:
        return

    todo_id = _callback_id(callback.data)
    user_id = await db.upsert_user(callback.from_user)
    done = await db.mark_todo_done(user_id, todo_id)
    todos = await db.list_open_todos(user_id)
    text = f"Задача #{todo_id} выполнена.\n\n" if done else "Не нашла такую открытую задачу.\n\n"
    await callback.message.answer(
        text + format_todos(todos, settings.app_timezone),
        reply_markup=todos_inline_keyboard(todos),
    )


async def todo_delete_callback(callback: CallbackQuery, db: Database, settings: Settings) -> None:
    await callback.answer("Удалено")
    if callback.from_user is None or callback.message is None or callback.data is None:
        return

    todo_id = _callback_id(callback.data)
    user_id = await db.upsert_user(callback.from_user)
    deleted = await db.delete_todo(user_id, todo_id)
    todos = await db.list_open_todos(user_id)
    text = f"Задача #{todo_id} удалена.\n\n" if deleted else "Не нашла такую открытую задачу.\n\n"
    await callback.message.answer(
        text + format_todos(todos, settings.app_timezone),
        reply_markup=todos_inline_keyboard(todos),
    )


async def reminder_cancel_callback(callback: CallbackQuery, db: Database, settings: Settings) -> None:
    await callback.answer("Отменено")
    if callback.from_user is None or callback.message is None or callback.data is None:
        return

    reminder_id = _callback_id(callback.data)
    user_id = await db.upsert_user(callback.from_user)
    cancelled = await db.cancel_reminder(user_id, reminder_id)
    reminders = await db.list_pending_reminders(user_id)
    text = (
        f"Напоминание #{reminder_id} отменено.\n\n"
        if cancelled
        else "Не нашла такое активное напоминание.\n\n"
    )
    await callback.message.answer(
        text + format_reminders(reminders, settings.app_timezone),
        reply_markup=reminders_inline_keyboard(reminders),
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


def _callback_id(data: str) -> int:
    return int(data.rsplit(":", 1)[-1])
