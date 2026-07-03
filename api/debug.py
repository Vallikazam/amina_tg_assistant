from __future__ import annotations

import asyncio
import json
from http.server import BaseHTTPRequestHandler

from bot.config import Settings
from bot.factory import create_bot_dispatcher


class handler(BaseHTTPRequestHandler):
    def do_GET(self) -> None:
        try:
            asyncio.run(self._handle_debug())
        except Exception as error:
            self._send_json(
                500,
                {
                    "ok": False,
                    "error": error.__class__.__name__,
                    "message": str(error),
                },
            )

    async def _handle_debug(self) -> None:
        settings = Settings.from_env()
        settings.validate()

        bot, _dispatcher = await create_bot_dispatcher(settings)
        try:
            bot_info = await bot.get_me()
        finally:
            await bot.session.close()

        self._send_json(
            200,
            {
                "ok": True,
                "bot_username": bot_info.username,
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

