from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def admin_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="📊 Статистика",
                    callback_data="admin:stats",
                )
            ],
            [
                InlineKeyboardButton(
                    text="⬅ Назад",
                    callback_data="start",
                )
            ],
        ]
    )

def admin_back_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅ Назад",
                    callback_data="admin:menu",
                )
            ]
        ]
    )