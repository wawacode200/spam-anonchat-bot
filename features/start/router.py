from aiogram import F, Router
from aiogram.types import CallbackQuery, Message
from aiogram.filters import Command, CommandStart

from .keyboards import start_keyboard
from .texts import start_text

router = Router()

DEFAULT_BATCH_SIZE = 10
DEFAULT_INTERVAL = 5

broadcast_state = {
    "batch_size": DEFAULT_BATCH_SIZE,
    "interval": DEFAULT_INTERVAL,
    "sent": 0,
    "failed": 0,
    "is_running": False,
}


def render_broadcast_text() -> str:
    return start_text(
        sent=broadcast_state["sent"],
        failed=broadcast_state["failed"],
        batch_size=broadcast_state["batch_size"],
        interval=broadcast_state["interval"],
        is_running=broadcast_state["is_running"],
    )


def render_broadcast_keyboard():
    return start_keyboard(
        batch_size=broadcast_state["batch_size"],
        interval=broadcast_state["interval"],
        is_running=broadcast_state["is_running"],
    )


@router.message(CommandStart())
async def broadcast_menu(message: Message) -> None:
    await message.answer(
        render_broadcast_text(),
        reply_markup=render_broadcast_keyboard(),
    )


@router.callback_query(F.data == "bc:noop")
async def broadcast_noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data.startswith("bc:batch:"))
async def change_batch_size(callback: CallbackQuery) -> None:
    action = callback.data.split(":")[-1]

    if action == "dec10":
        broadcast_state["batch_size"] -= 10
    elif action == "dec1":
        broadcast_state["batch_size"] -= 1
    elif action == "inc1":
        broadcast_state["batch_size"] += 1
    elif action == "inc10":
        broadcast_state["batch_size"] += 10

    broadcast_state["batch_size"] = max(
        1,
        broadcast_state["batch_size"],
    )

    await callback.message.edit_text(
        render_broadcast_text(),
        reply_markup=render_broadcast_keyboard(),
    )

    await callback.answer()


@router.callback_query(F.data.startswith("bc:interval:"))
async def change_interval(callback: CallbackQuery) -> None:
    action = callback.data.split(":")[-1]

    if action == "dec10":
        broadcast_state["interval"] -= 10
    elif action == "dec1":
        broadcast_state["interval"] -= 1
    elif action == "inc1":
        broadcast_state["interval"] += 1
    elif action == "inc10":
        broadcast_state["interval"] += 10

    broadcast_state["interval"] = max(
        1,
        broadcast_state["interval"],
    )

    await callback.message.edit_text(
        render_broadcast_text(),
        reply_markup=render_broadcast_keyboard(),
    )

    await callback.answer()


@router.callback_query(F.data == "bc:start")
async def start_broadcast(callback: CallbackQuery) -> None:
    broadcast_state["is_running"] = True

    await callback.message.edit_text(
        render_broadcast_text(),
        reply_markup=render_broadcast_keyboard(),
    )

    await callback.answer("Рассылка запущена")


@router.callback_query(F.data == "bc:stop")
async def stop_broadcast(callback: CallbackQuery) -> None:
    broadcast_state["is_running"] = False

    await callback.message.edit_text(
        render_broadcast_text(),
        reply_markup=render_broadcast_keyboard(),
    )

    await callback.answer("Рассылка остановлена")