from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def profile_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="⬅ Назад",
                    callback_data="start",
                )
            ]
        ]
    )