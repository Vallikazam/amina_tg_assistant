from __future__ import annotations

from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


MAIN_MENU_ASK = "Спросить AI"
MAIN_MENU_TODOS = "Задачи"
MAIN_MENU_TODAY = "Сегодня"
MAIN_MENU_REMINDERS = "Напоминания"
MAIN_MENU_MEMORY = "Память"
MAIN_MENU_HELP = "Помощь"
MAIN_MENU_RESET = "Сбросить диалог"

MENU_TEXTS = {
    MAIN_MENU_ASK,
    MAIN_MENU_TODOS,
    MAIN_MENU_TODAY,
    MAIN_MENU_REMINDERS,
    MAIN_MENU_MEMORY,
    MAIN_MENU_HELP,
    MAIN_MENU_RESET,
}


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=MAIN_MENU_ASK),
                KeyboardButton(text=MAIN_MENU_TODOS),
            ],
            [
                KeyboardButton(text=MAIN_MENU_TODAY),
                KeyboardButton(text=MAIN_MENU_REMINDERS),
            ],
            [
                KeyboardButton(text=MAIN_MENU_MEMORY),
                KeyboardButton(text=MAIN_MENU_HELP),
            ],
            [KeyboardButton(text=MAIN_MENU_RESET)],
        ],
        resize_keyboard=True,
        input_field_placeholder="Напиши вопрос или выбери действие",
    )


def start_inline_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Что умеешь?", callback_data="menu:help"),
                InlineKeyboardButton(text="Моя память", callback_data="menu:memory"),
            ],
            [
                InlineKeyboardButton(text="Задачи", callback_data="menu:todos"),
                InlineKeyboardButton(text="Сегодня", callback_data="menu:today"),
            ],
            [
                InlineKeyboardButton(text="Напоминания", callback_data="menu:reminders"),
                InlineKeyboardButton(text="Очистить диалог", callback_data="menu:reset"),
            ],
            [
                InlineKeyboardButton(text="Очистить память", callback_data="menu:forget"),
            ],
        ]
    )
