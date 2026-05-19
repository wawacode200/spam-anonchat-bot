import logging

from aiogram import F, Router
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message

from .keyboards import start_keyboard
from .service import BroadcastService
from .texts import START_TEXT

from common.filters import AdminFilter

router = Router()
router.message.filter(AdminFilter())

service = BroadcastService()


def render_keyboard():
    return start_keyboard(
        batch_size=service.batch_size,
        interval=service.interval,
        is_running=service.is_running,
    )


async def update_menu(callback: CallbackQuery) -> None:
    await callback.message.edit_text(
        START_TEXT,
        reply_markup=render_keyboard(),
    )


@router.message(CommandStart())
async def broadcast_menu(message: Message) -> None:
    await message.answer(
        START_TEXT,
        reply_markup=render_keyboard(),
    )


@router.callback_query(F.data == "bc:noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.startswith("bc:batch:"))
async def change_batch(callback: CallbackQuery) -> None:
    action = callback.data.split(":")[-1]

    service.change_batch_size(action)

    await update_menu(callback)
    await callback.answer()


@router.callback_query(F.data.startswith("bc:interval:"))
async def change_interval(callback: CallbackQuery) -> None:
    action = callback.data.split(":")[-1]

    service.change_interval(action)

    await update_menu(callback)
    await callback.answer()


@router.callback_query(F.data == "bc:broadcast")
async def start_broadcast(callback: CallbackQuery) -> None:
    service.start()

    await update_menu(callback)
    await callback.answer("Рассылка запущена")


@router.callback_query(F.data == "bc:stop")
async def stop_broadcast(callback: CallbackQuery) -> None:
    service.stop()

    await update_menu(callback)
    await callback.answer("Рассылка остановлена")