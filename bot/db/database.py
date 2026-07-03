from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Iterable

import aiosqlite
from aiogram.types import User


@dataclass(frozen=True)
class MessageRow:
    role: str
    content: str


@dataclass(frozen=True)
class TodoRow:
    id: int
    text: str
    status: str
    due_at: str | None


@dataclass(frozen=True)
class ReminderRow:
    id: int
    telegram_id: int
    text: str
    remind_at: str
    status: str


class Database:
    def __init__(self, path: str) -> None:
        self.path = path

    async def init(self) -> None:
        parent_dir = os.path.dirname(os.path.abspath(self.path))
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        async with aiosqlite.connect(self.path) as db:
            await db.executescript(
                """
                PRAGMA foreign_keys = ON;

                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER NOT NULL UNIQUE,
                    username TEXT,
                    first_name TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
                );

                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    role TEXT NOT NULL CHECK (role IN ('user', 'assistant')),
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS memories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    content TEXT NOT NULL,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS settings (
                    user_id INTEGER PRIMARY KEY,
                    language TEXT NOT NULL DEFAULT 'ru',
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS todos (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'open'
                        CHECK (status IN ('open', 'done', 'deleted')),
                    due_at TEXT,
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    done_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    text TEXT NOT NULL,
                    remind_at TEXT NOT NULL,
                    status TEXT NOT NULL DEFAULT 'pending'
                        CHECK (status IN ('pending', 'sent', 'cancelled')),
                    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    sent_at TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
                );

                CREATE INDEX IF NOT EXISTS idx_messages_user_created
                    ON messages(user_id, created_at);

                CREATE INDEX IF NOT EXISTS idx_memories_user_created
                    ON memories(user_id, created_at);

                CREATE INDEX IF NOT EXISTS idx_todos_user_status_due
                    ON todos(user_id, status, due_at);

                CREATE INDEX IF NOT EXISTS idx_reminders_status_time
                    ON reminders(status, remind_at);
                """
            )
            await db.commit()

    async def upsert_user(self, telegram_user: User) -> int:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                """
                INSERT INTO users (telegram_id, username, first_name)
                VALUES (?, ?, ?)
                ON CONFLICT(telegram_id) DO UPDATE SET
                    username = excluded.username,
                    first_name = excluded.first_name,
                    updated_at = CURRENT_TIMESTAMP
                """,
                (
                    telegram_user.id,
                    telegram_user.username,
                    telegram_user.first_name,
                ),
            )
            await db.execute(
                """
                INSERT OR IGNORE INTO settings (user_id)
                SELECT id FROM users WHERE telegram_id = ?
                """,
                (telegram_user.id,),
            )
            await db.commit()

            cursor = await db.execute(
                "SELECT id FROM users WHERE telegram_id = ?",
                (telegram_user.id,),
            )
            row = await cursor.fetchone()

        if row is None:
            raise RuntimeError("Could not create or load user")
        return int(row[0])

    async def add_message(self, user_id: int, role: str, content: str) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO messages (user_id, role, content) VALUES (?, ?, ?)",
                (user_id, role, content),
            )
            await db.commit()

    async def get_recent_messages(
        self,
        user_id: int,
        *,
        limit: int,
    ) -> list[MessageRow]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                SELECT role, content
                FROM messages
                WHERE user_id = ?
                ORDER BY id DESC
                LIMIT ?
                """,
                (user_id, limit),
            )
            rows = await cursor.fetchall()

        return [
            MessageRow(role=str(role), content=str(content))
            for role, content in reversed(rows)
        ]

    async def clear_messages(self, user_id: int) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM messages WHERE user_id = ?", (user_id,))
            await db.commit()

    async def add_memory(self, user_id: int, content: str) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute(
                "INSERT INTO memories (user_id, content) VALUES (?, ?)",
                (user_id, content),
            )
            await db.commit()

    async def list_memories(self, user_id: int) -> list[str]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                SELECT content
                FROM memories
                WHERE user_id = ?
                ORDER BY id ASC
                """,
                (user_id,),
            )
            rows = await cursor.fetchall()

        return [str(row[0]) for row in rows]

    async def clear_memories(self, user_id: int) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM memories WHERE user_id = ?", (user_id,))
            await db.commit()

    async def replace_memories(self, user_id: int, memories: Iterable[str]) -> None:
        async with aiosqlite.connect(self.path) as db:
            await db.execute("DELETE FROM memories WHERE user_id = ?", (user_id,))
            await db.executemany(
                "INSERT INTO memories (user_id, content) VALUES (?, ?)",
                [(user_id, memory) for memory in memories],
            )
            await db.commit()

    async def add_todo(self, user_id: int, text: str, due_at: str | None = None) -> int:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "INSERT INTO todos (user_id, text, due_at) VALUES (?, ?, ?)",
                (user_id, text, due_at),
            )
            await db.commit()
            return int(cursor.lastrowid)

    async def list_open_todos(self, user_id: int) -> list[TodoRow]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                SELECT id, text, status, due_at
                FROM todos
                WHERE user_id = ? AND status = 'open'
                ORDER BY due_at IS NULL, due_at ASC, id ASC
                """,
                (user_id,),
            )
            rows = await cursor.fetchall()

        return [TodoRow(id=int(row[0]), text=str(row[1]), status=str(row[2]), due_at=row[3]) for row in rows]

    async def list_todos_between(self, user_id: int, start: str, end: str) -> list[TodoRow]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                SELECT id, text, status, due_at
                FROM todos
                WHERE user_id = ?
                  AND status = 'open'
                  AND due_at IS NOT NULL
                  AND due_at >= ?
                  AND due_at < ?
                ORDER BY due_at ASC, id ASC
                """,
                (user_id, start, end),
            )
            rows = await cursor.fetchall()

        return [TodoRow(id=int(row[0]), text=str(row[1]), status=str(row[2]), due_at=row[3]) for row in rows]

    async def mark_todo_done(self, user_id: int, todo_id: int) -> bool:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                UPDATE todos
                SET status = 'done', done_at = CURRENT_TIMESTAMP
                WHERE user_id = ? AND id = ? AND status = 'open'
                """,
                (user_id, todo_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def delete_todo(self, user_id: int, todo_id: int) -> bool:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                UPDATE todos
                SET status = 'deleted'
                WHERE user_id = ? AND id = ? AND status = 'open'
                """,
                (user_id, todo_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def add_reminder(self, user_id: int, text: str, remind_at: str) -> int:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                "INSERT INTO reminders (user_id, text, remind_at) VALUES (?, ?, ?)",
                (user_id, text, remind_at),
            )
            await db.commit()
            return int(cursor.lastrowid)

    async def list_pending_reminders(self, user_id: int) -> list[ReminderRow]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                SELECT reminders.id, users.telegram_id, reminders.text, reminders.remind_at, reminders.status
                FROM reminders
                JOIN users ON users.id = reminders.user_id
                WHERE reminders.user_id = ? AND reminders.status = 'pending'
                ORDER BY reminders.remind_at ASC, reminders.id ASC
                """,
                (user_id,),
            )
            rows = await cursor.fetchall()

        return [
            ReminderRow(
                id=int(row[0]),
                telegram_id=int(row[1]),
                text=str(row[2]),
                remind_at=str(row[3]),
                status=str(row[4]),
            )
            for row in rows
        ]

    async def cancel_reminder(self, user_id: int, reminder_id: int) -> bool:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                UPDATE reminders
                SET status = 'cancelled'
                WHERE user_id = ? AND id = ? AND status = 'pending'
                """,
                (user_id, reminder_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def get_due_reminders(self, now_value: str, *, limit: int = 25) -> list[ReminderRow]:
        async with aiosqlite.connect(self.path) as db:
            cursor = await db.execute(
                """
                SELECT reminders.id, users.telegram_id, reminders.text, reminders.remind_at, reminders.status
                FROM reminders
                JOIN users ON users.id = reminders.user_id
                WHERE reminders.status = 'pending'
                  AND reminders.remind_at <= ?
                ORDER BY reminders.remind_at ASC, reminders.id ASC
                LIMIT ?
                """,
                (now_value, limit),
            )
            rows = await cursor.fetchall()

        return [
            ReminderRow(
                id=int(row[0]),
                telegram_id=int(row[1]),
                text=str(row[2]),
                remind_at=str(row[3]),
                status=str(row[4]),
            )
            for row in rows
        ]

    async def mark_reminders_sent(self, reminder_ids: Iterable[int]) -> None:
        ids = list(reminder_ids)
        if not ids:
            return

        async with aiosqlite.connect(self.path) as db:
            await db.executemany(
                """
                UPDATE reminders
                SET status = 'sent', sent_at = CURRENT_TIMESTAMP
                WHERE id = ? AND status = 'pending'
                """,
                [(reminder_id,) for reminder_id in ids],
            )
            await db.commit()
