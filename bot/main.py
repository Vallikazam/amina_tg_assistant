from __future__ import annotations

import asyncio
import logging

from bot.config import Settings
from bot.factory import create_bot_dispatcher


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    )

    settings = Settings.from_env()
    settings.validate()

    bot, dispatcher = await create_bot_dispatcher(settings)

    logging.info("Amina Telegram assistant started")
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
