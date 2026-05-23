from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)


MAIN_MENU_BUTTON_TEXT = "Главное меню"
START_BUTTON_TEXT = "Запустить"
STOP_BUTTON_TEXT = "Остановить"


def country_flag(country_code: str) -> str:
    return "".join(
        chr(0x1F1E6 + ord(char) - ord("a"))
        for char in country_code.lower()
        if "a" <= char <= "z"
    )


def country_rows(
    country_codes: list[str],
    callback_prefix: str,
) -> list[list[InlineKeyboardButton]]:
    buttons = [
        InlineKeyboardButton(
            text=country_flag(country_code) or country_code.upper(),
            callback_data=f"{callback_prefix}:{country_code}",
        )
        for country_code in country_codes
    ]

    return [
        buttons[start:start + 4]
        for start in range(0, len(buttons), 4)
    ]


def delete_confirmation_keyboard(country_code: str) -> InlineKeyboardMarkup:
    flag = country_flag(country_code)

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(
                    text=f"Удалить {flag}",
                    callback_data=f"bc:delete_confirm:{country_code}",
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Отмена",
                    callback_data="bc:delete_cancel",
                ),
            ],
        ]
    )


def start_keyboard(
    desired_batch_size: int,
    effective_batch_size: int,
    interval: int,
    is_running: bool,
    is_checking: bool,
    is_stopping: bool,
    reset_country_codes: list[str],
) -> InlineKeyboardMarkup:
    if is_stopping:
        start_stop_text = "⏳ Останавливается"
        start_stop_callback = "bc:noop"
    elif is_running:
        start_stop_text = "⏹ Остановить"
        start_stop_callback = "bc:stop"
    else:
        start_stop_text = "▶️ Запустить"
        start_stop_callback = "bc:broadcast"

    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="Изменить текст рассылки", callback_data="bc:text"),
            ],
            [
                InlineKeyboardButton(
                    text="⏳ Проверка идёт" if is_checking else "Проверить сессии",
                    callback_data="bc:noop" if is_checking else "bc:check",
                ),
                InlineKeyboardButton(text="Лежат", callback_data="bc:paused"),
                InlineKeyboardButton(text="Ошибки сессий", callback_data="bc:errors"),
            ],
            [
                InlineKeyboardButton(text=f"Добавить сессии .session", callback_data="sessions:add"),
            ],
            [
                InlineKeyboardButton(text="Сбросить статусы сессий", callback_data="bc:reset_sessions"),
            ],
            *(
                [[InlineKeyboardButton(text="Сброс по странам", callback_data="bc:noop")]]
                if reset_country_codes
                else []
            ),
            *country_rows(reset_country_codes, "bc:reset_country"),
            *(
                [[InlineKeyboardButton(text="Убить по странам", callback_data="bc:noop")]]
                if reset_country_codes
                else []
            ),
            *country_rows(reset_country_codes, "bc:kill_country"),
            *(
                [[InlineKeyboardButton(text="Удалить по странам", callback_data="bc:noop")]]
                if reset_country_codes
                else []
            ),
            *country_rows(reset_country_codes, "bc:delete_country"),
            [
                InlineKeyboardButton(text="За раз", callback_data="bc:noop"),
            ],
            [
                InlineKeyboardButton(text="−10", callback_data="bc:batch:dec10"),
                InlineKeyboardButton(text="−1", callback_data="bc:batch:dec1"),
                InlineKeyboardButton(
                    text=f"{desired_batch_size}/{effective_batch_size}",
                    callback_data="bc:noop",
                ),
                InlineKeyboardButton(text="+1", callback_data="bc:batch:inc1"),
                InlineKeyboardButton(text="+10", callback_data="bc:batch:inc10"),
            ],
            [
                InlineKeyboardButton(text="Интервал", callback_data="bc:noop"),
            ],
            [
                InlineKeyboardButton(text="−10s", callback_data="bc:interval:dec10"),
                InlineKeyboardButton(text="−1s", callback_data="bc:interval:dec1"),
                InlineKeyboardButton(text=f"{interval}сек.", callback_data="bc:noop"),
                InlineKeyboardButton(text="+1s", callback_data="bc:interval:inc1"),
                InlineKeyboardButton(text="+10s", callback_data="bc:interval:inc10"),
            ],
            [
                InlineKeyboardButton(
                    text=start_stop_text,
                    callback_data=start_stop_callback,
                )
            ],
        ]
    )


def main_menu_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [
                KeyboardButton(text=MAIN_MENU_BUTTON_TEXT),
                KeyboardButton(text=START_BUTTON_TEXT),
                KeyboardButton(text=STOP_BUTTON_TEXT),
            ],
        ],
        resize_keyboard=True,
        input_field_placeholder="Выберите действие",
    )
