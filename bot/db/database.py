from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable

import aiosqlite
from aiogram.types import User


@dataclass(frozen=True)
class MessageRow:
    role: str
    content: str


class Database:
    def __init__(self, path: str) -> None:
        self.path = path

    async def init(self) -> None:
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

                CREATE INDEX IF NOT EXISTS idx_messages_user_created
                    ON messages(user_id, created_at);

                CREATE INDEX IF NOT EXISTS idx_memories_user_created
                    ON memories(user_id, created_at);
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

