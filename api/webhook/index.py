from __future__ import annotations

import asyncio
import json
import logging
from http.server import BaseHTTPRequestHandler

from bot.config import Settings
from bot.factory import create_bot_dispatcher


logger = logging.getLogger(__name__)


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        if self.path.endswith("/debug"):
            asyncio.run(self._handle_debug())
            return

        self._send_json(200, {"ok": True, "service": "amina-telegram-webhook"})

    def do_POST(self) -> None:
        try:
            asyncio.run(self._handle_update())
        except PermissionError:
            logger.exception("Telegram webhook rejected")
            self._send_json(403, {"ok": False, "error": "forbidden"})
        except Exception:
            logger.exception("Telegram webhook failed")
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
            await dispatcher.feed_raw_update(bot, update_data)
        finally:
            await bot.session.close()

        self._send_json(200, {"ok": True})

    async def _handle_debug(self) -> None:
        settings = Settings.from_env()
        settings.validate()

        bot, _dispatcher = await create_bot_dispatcher(settings)
        try:
            await bot.get_me()
        finally:
            await bot.session.close()

        self._send_json(
            200,
            {
                "ok": True,
                "database_path": settings.database_path,
                "model": settings.gemini_model,
            },
        )

    def _send_json(self, status_code: int, payload: dict[str, object]) -> None:
        body = json.dumps(payload).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)
