from __future__ import annotations

from aiogram.filters import Command, CommandObject
from aiogram.types import Message

from bot.config import Settings
from bot.db import Database, ReminderRow, TodoRow
from bot.keyboards import main_menu_keyboard, reminders_inline_keyboard, todos_inline_keyboard
from bot.services.time_parser import (
    format_local,
    local_day_range,
    local_week_range,
    parse_reminder_text,
    parse_todo_text,
    to_storage,
)


async def todo_command(
    message: Message,
    command: CommandObject,
    db: Database,
    settings: Settings,
) -> None:
    if message.from_user is None:
        return

    raw_text = (command.args or "").strip()
    if not raw_text:
        await message.answer(
            "Напиши задачу после команды: /todo завтра в 10:00 подготовить отчёт",
            reply_markup=main_menu_keyboard(),
        )
        return

    title, due_at = parse_todo_text(raw_text, settings.app_timezone)
    user_id = await db.upsert_user(message.from_user)
    todo_id = await db.add_todo(user_id, title, to_storage(due_at) if due_at else None)
    due_text = f"\nСрок: {due_at.strftime('%d.%m.%Y %H:%M')}" if due_at else ""
    await message.answer(
        f"Задача #{todo_id} добавлена: {title}{due_text}",
        reply_markup=todos_inline_keyboard(await db.list_open_todos(user_id)),
    )


async def todos_command(message: Message, db: Database, settings: Settings) -> None:
    if message.from_user is None:
        return

    user_id = await db.upsert_user(message.from_user)
    todos = await db.list_open_todos(user_id)
    await message.answer(
        format_todos(todos, settings.app_timezone),
        reply_markup=todos_inline_keyboard(todos),
    )


async def done_command(message: Message, command: CommandObject, db: Database) -> None:
    if message.from_user is None:
        return

    todo_id = _parse_id(command.args)
    if todo_id is None:
        await message.answer("Напиши номер задачи: /done 3", reply_markup=main_menu_keyboard())
        return

    user_id = await db.upsert_user(message.from_user)
    done = await db.mark_todo_done(user_id, todo_id)
    text = f"Задача #{todo_id} выполнена." if done else "Не нашла такую открытую задачу."
    await message.answer(text, reply_markup=todos_inline_keyboard(await db.list_open_todos(user_id)))


async def delete_todo_command(message: Message, command: CommandObject, db: Database) -> None:
    if message.from_user is None:
        return

    todo_id = _parse_id(command.args)
    if todo_id is None:
        await message.answer("Напиши номер задачи: /delete_todo 3", reply_markup=main_menu_keyboard())
        return

    user_id = await db.upsert_user(message.from_user)
    deleted = await db.delete_todo(user_id, todo_id)
    text = f"Задача #{todo_id} удалена." if deleted else "Не нашла такую открытую задачу."
    await message.answer(text, reply_markup=todos_inline_keyboard(await db.list_open_todos(user_id)))


async def remind_command(
    message: Message,
    command: CommandObject,
    db: Database,
    settings: Settings,
) -> None:
    if message.from_user is None:
        return

    raw_text = (command.args or "").strip()
    remind_at, title = parse_reminder_text(raw_text, settings.app_timezone)
    if not raw_text or remind_at is None or not title:
        await message.answer(
            "Примеры:\n"
            "/remind через 30 минут размяться\n"
            "/remind завтра в 10:00 позвонить\n"
            "/remind 2026-07-04 09:30 встреча",
            reply_markup=main_menu_keyboard(),
        )
        return

    user_id = await db.upsert_user(message.from_user)
    reminder_id = await db.add_reminder(user_id, title, to_storage(remind_at))
    await message.answer(
        f"Напоминание #{reminder_id} создано: {title}\n"
        f"Когда: {remind_at.strftime('%d.%m.%Y %H:%M')}",
        reply_markup=reminders_inline_keyboard(await db.list_pending_reminders(user_id)),
    )


async def reminders_command(message: Message, db: Database, settings: Settings) -> None:
    if message.from_user is None:
        return

    user_id = await db.upsert_user(message.from_user)
    reminders = await db.list_pending_reminders(user_id)
    await message.answer(
        format_reminders(reminders, settings.app_timezone),
        reply_markup=reminders_inline_keyboard(reminders),
    )


async def cancel_reminder_command(message: Message, command: CommandObject, db: Database) -> None:
    if message.from_user is None:
        return

    reminder_id = _parse_id(command.args)
    if reminder_id is None:
        await message.answer("Напиши номер напоминания: /cancel_reminder 2", reply_markup=main_menu_keyboard())
        return

    user_id = await db.upsert_user(message.from_user)
    cancelled = await db.cancel_reminder(user_id, reminder_id)
    text = f"Напоминание #{reminder_id} отменено." if cancelled else "Не нашла такое активное напоминание."
    await message.answer(text, reply_markup=reminders_inline_keyboard(await db.list_pending_reminders(user_id)))


async def today_command(message: Message, db: Database, settings: Settings) -> None:
    if message.from_user is None:
        return

    user_id = await db.upsert_user(message.from_user)
    start, end = local_day_range(settings.app_timezone)
    todos = await db.list_todos_between(user_id, start, end)
    await message.answer(
        "Сегодня:\n" + format_todos(todos, settings.app_timezone),
        reply_markup=todos_inline_keyboard(todos),
    )


async def week_command(message: Message, db: Database, settings: Settings) -> None:
    if message.from_user is None:
        return

    user_id = await db.upsert_user(message.from_user)
    start, end = local_week_range(settings.app_timezone)
    todos = await db.list_todos_between(user_id, start, end)
    await message.answer(
        "Ближайшие 7 дней:\n" + format_todos(todos, settings.app_timezone),
        reply_markup=todos_inline_keyboard(todos),
    )


def register_productivity_handlers(router) -> None:
    router.message(Command("todo"))(todo_command)
    router.message(Command("todos"))(todos_command)
    router.message(Command("done"))(done_command)
    router.message(Command("delete_todo"))(delete_todo_command)
    router.message(Command("remind"))(remind_command)
    router.message(Command("reminders"))(reminders_command)
    router.message(Command("cancel_reminder"))(cancel_reminder_command)
    router.message(Command("today"))(today_command)
    router.message(Command("week"))(week_command)


def format_todos(todos: list[TodoRow], timezone_name: str) -> str:
    if not todos:
        return "Открытых задач пока нет."

    return "\n".join(
        f"#{todo.id} {todo.text} — {format_local(todo.due_at, timezone_name)}"
        for todo in todos
    )


def format_reminders(reminders: list[ReminderRow], timezone_name: str) -> str:
    if not reminders:
        return "Активных напоминаний пока нет."

    return "\n".join(
        f"#{reminder.id} {format_local(reminder.remind_at, timezone_name)} — {reminder.text}"
        for reminder in reminders
    )


def _parse_id(value: str | None) -> int | None:
    if not value:
        return None

    value = value.strip()
    if not value.isdigit():
        return None

    return int(value)
