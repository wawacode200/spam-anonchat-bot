from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from .keyboards import start_keyboard
from .texts import START_TEXT

router = Router()


@router.message(CommandStart())
async def start_handler(message: Message) -> None:
    await message.answer(
        START_TEXT,
        reply_markup=start_keyboard(),
    )


@router.callback_query(F.data == "start")
async def start_callback(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        START_TEXT,
        reply_markup=start_keyboard(),
    )

    await callback.answer()