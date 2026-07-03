from bot.handlers.callbacks import create_callbacks_router
from bot.handlers.commands import create_commands_router
from bot.handlers.messages import create_messages_router

__all__ = [
    "create_callbacks_router",
    "create_commands_router",
    "create_messages_router",
]
