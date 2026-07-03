from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    telegram_bot_token: str
    gemini_api_key: str
    gemini_model: str
    database_path: str
    telegram_webhook_secret: str
    cron_secret: str
    app_timezone: str
    history_limit: int
    max_response_chars: int

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()

        return cls(
            telegram_bot_token=os.getenv("TELEGRAM_BOT_TOKEN", "").strip(),
            gemini_api_key=os.getenv("GEMINI_API_KEY", "").strip(),
            gemini_model=os.getenv("GEMINI_MODEL", "gemini-2.5-flash").strip(),
            database_path=_database_path_from_env(),
            telegram_webhook_secret=os.getenv("TELEGRAM_WEBHOOK_SECRET", "").strip(),
            cron_secret=os.getenv("CRON_SECRET", "").strip(),
            app_timezone=os.getenv("APP_TIMEZONE", "Asia/Qyzylorda").strip(),
            history_limit=_int_env("HISTORY_LIMIT", default=20, minimum=1, maximum=50),
            max_response_chars=_int_env(
                "MAX_RESPONSE_CHARS",
                default=3500,
                minimum=500,
                maximum=4000,
            ),
        )

    def validate(self) -> None:
        missing = []
        if not self.telegram_bot_token:
            missing.append("TELEGRAM_BOT_TOKEN")
        if not self.gemini_api_key:
            missing.append("GEMINI_API_KEY")

        if missing:
            names = ", ".join(missing)
            raise RuntimeError(f"Missing required environment variables: {names}")


def _int_env(name: str, *, default: int, minimum: int, maximum: int) -> int:
    raw_value = os.getenv(name, "").strip()
    if not raw_value:
        return default

    try:
        value = int(raw_value)
    except ValueError:
        return default

    return max(minimum, min(maximum, value))


def _database_path_from_env() -> str:
    if os.getenv("VERCEL"):
        return "/tmp/assistant.sqlite3"

    return os.getenv("DATABASE_PATH", "assistant.sqlite3").strip() or "assistant.sqlite3"
