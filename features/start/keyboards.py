from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def start_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text="",
                    callback_data="profile",
                )
            ],
            [
                InlineKeyboardButton(
                    text="",
                    callback_data="profile",
                )
            ]
        ]
    )