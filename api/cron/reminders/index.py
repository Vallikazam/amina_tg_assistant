from __future__ import annotations

import asyncio
import json
from http.server import BaseHTTPRequestHandler

from aiogram import Bot

from bot.config import Settings
from bot.db import Database
from bot.services.time_parser import now_local, to_storage


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        try:
            asyncio.run(self._handle_cron())
        except PermissionError:
            self._send_json(403, {"ok": False, "error": "forbidden"})
        except Exception as error:
            self._send_json(
                500,
                {
                    "ok": False,
                    "error": error.__class__.__name__,
                    "message": str(error),
                },
            )

    async def _handle_cron(self) -> None:
        settings = Settings.from_env()
        settings.validate()
        self._check_secret(settings)

        db = Database(settings.database_path)
        await db.init()

        now_value = to_storage(now_local(settings.app_timezone))
        reminders = await db.get_due_reminders(now_value)
        sent_ids: list[int] = []

        bot = Bot(token=settings.telegram_bot_token)
        try:
            for reminder in reminders:
                await bot.send_message(
                    reminder.telegram_id,
                    f"Напоминание #{reminder.id}: {reminder.text}",
                )
                sent_ids.append(reminder.id)
        finally:
            await bot.session.close()

        await db.mark_reminders_sent(sent_ids)
        self._send_json(200, {"ok": True, "sent": len(sent_ids)})

    def _check_secret(self, settings: Settings) -> None:
        if not settings.cron_secret:
            return

        authorization = self.headers.get("Authorization", "")
        cron_secret = self.headers.get("X-Cron-Secret", "")
        vercel_cron = self.headers.get("X-Vercel-Cron", "")
        expected = f"Bearer {settings.cron_secret}"

        if authorization == expected or cron_secret == settings.cron_secret or vercel_cron == "1":
            return

        raise PermissionError("Invalid cron secret")

    def _send_json(self, status_code: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

