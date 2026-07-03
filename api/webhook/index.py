from __future__ import annotations

import asyncio
import json
from http.server import BaseHTTPRequestHandler

from aiogram.types import Update

from bot.config import Settings
from bot.factory import create_bot_dispatcher


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        self._send_json(200, {"ok": True, "service": "amina-telegram-webhook"})

    def do_POST(self) -> None:
        try:
            asyncio.run(self._handle_update())
        except PermissionError:
            self._send_json(403, {"ok": False, "error": "forbidden"})
        except Exception:
            self._send_json(500, {"ok": False, "error": "internal_error"})

    async def _handle_update(self) -> None:
        settings = Settings.from_env()
        settings.validate()

        if settings.telegram_webhook_secret:
            actual_secret = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if actual_secret != settings.telegram_webhook_secret:
                raise PermissionError("Invalid Telegram webhook secret")

        content_length = int(self.headers.get("Content-Length", "0"))
        payload = self.rfile.read(content_length)
        update_data = json.loads(payload.decode("utf-8"))

        bot, dispatcher = await create_bot_dispatcher(settings)
        try:
            update = Update.model_validate(update_data, context={"bot": bot})
            await dispatcher.feed_update(bot, update)
        finally:
            await bot.session.close()

        self._send_json(200, {"ok": True})

    def _send_json(self, status_code: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

