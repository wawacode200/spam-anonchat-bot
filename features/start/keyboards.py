from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup


def start_keyboard(
    batch_size: int,
    interval: int,
    is_running: bool,
) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="−10", callback_data="bc:batch:dec10"),
                InlineKeyboardButton(text="−1", callback_data="bc:batch:dec1"),
                InlineKeyboardButton(text=f"За раз: {batch_size}", callback_data="bc:noop"),
                InlineKeyboardButton(text="+1", callback_data="bc:batch:inc1"),
                InlineKeyboardButton(text="+10", callback_data="bc:batch:inc10"),
            ],
            [
                InlineKeyboardButton(text="−10s", callback_data="bc:interval:dec10"),
                InlineKeyboardButton(text="−1s", callback_data="bc:interval:dec1"),
                InlineKeyboardButton(text=f"Интервал: {interval}s", callback_data="bc:noop"),
                InlineKeyboardButton(text="+1s", callback_data="bc:interval:inc1"),
                InlineKeyboardButton(text="+10s", callback_data="bc:interval:inc10"),
            ],
            [
                InlineKeyboardButton(
                    text="⏹ Остановить" if is_running else "▶️ Запустить",
                    callback_data="bc:stop" if is_running else "bc:start",
                )
            ],
        ]
    )