import logging

from aiogram import Bot, F, Router
from aiogram.exceptions import TelegramBadRequest
from aiogram.filters import CommandStart
from aiogram.types import CallbackQuery, Message
from sqlalchemy.ext.asyncio import AsyncSession

from .keyboards import (
    MAIN_MENU_BUTTON_TEXT,
    START_BUTTON_TEXT,
    STOP_BUTTON_TEXT,
    main_menu_keyboard,
    start_keyboard,
)
from .service import BroadcastService
from .texts import render_start_text

from common.filters import AdminFilter

router = Router()
router.message.filter(AdminFilter())
router.callback_query.filter(AdminFilter())

service = BroadcastService()

TELEGRAM_MESSAGE_LIMIT = 4096


def render_keyboard():
    service.normalize_batch_size()

    return start_keyboard(
        desired_batch_size=service.desired_batch_size,
        effective_batch_size=service.effective_batch_size,
        interval=service.interval,
        is_running=service.is_running,
        is_checking=service.is_checking,
        is_stopping=service.is_stopping,
        reset_country_codes=service.reset_country_codes,
    )


def render_menu_text() -> str:
    service.normalize_batch_size()

    return render_start_text(
        session_status_counts=service.session_status_counts(),
        desired_batch_size=service.desired_batch_size,
        effective_batch_size=service.effective_batch_size,
        broadcast_text=service.broadcast_text,
    )


def is_message_not_modified(error: TelegramBadRequest) -> bool:
    return "message is not modified" in str(error).lower()


async def edit_menu_message(
    bot: Bot,
    chat_id: int,
    message_id: int,
) -> None:
    try:
        await bot.edit_message_text(
            chat_id=chat_id,
            message_id=message_id,
            text=render_menu_text(),
            reply_markup=render_keyboard(),
        )
    except TelegramBadRequest as error:
        if not is_message_not_modified(error):
            raise


async def update_menu(callback: CallbackQuery) -> None:
    if callback.message is None:
        return

    await edit_menu_message(
        bot=callback.bot,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
    )


def split_text(
    text: str,
    limit: int = 3500,
) -> list[str]:
    if len(text) <= limit:
        return [text]

    chunks = []
    current = ""

    for line in text.splitlines():
        if len(line) > limit:
            if current:
                chunks.append(current)
                current = ""

            for start in range(0, len(line), limit):
                chunks.append(line[start:start + limit])

            continue

        next_current = f"{current}\n{line}" if current else line

        if len(next_current) > limit:
            if current:
                chunks.append(current)
            current = line
        else:
            current = next_current

    if current:
        chunks.append(current)

    return chunks


async def answer_long_text(
    message: Message,
    title: str,
    lines: list[str],
) -> None:
    if not lines:
        await message.answer(f"<b>{title}</b>\nнет")
        return

    text = f"<b>{title}</b>\n" + "\n".join(lines)

    for chunk in split_text(text, TELEGRAM_MESSAGE_LIMIT - 500):
        await message.answer(chunk)


async def send_main_menu(
    message: Message,
    session: AsyncSession,
) -> None:
    if message.from_user is not None:
        service.pop_waiting_broadcast_text_menu(message.from_user.id)

    await service.load_settings(session)

    await message.answer(
        render_menu_text(),
        reply_markup=render_keyboard(),
    )

    await message.answer(
        "Кнопка главного меню закреплена ниже",
        reply_markup=main_menu_keyboard(),
    )


async def start_broadcast_action() -> tuple[bool, str]:
    validation_errors = service.validate_start()

    if validation_errors:
        return False, "\n".join(validation_errors)

    return await service.start()


async def stop_broadcast_action() -> tuple[bool, str]:
    return await service.stop()


@router.message(CommandStart())
async def broadcast_menu(
    message: Message,
    session: AsyncSession,
) -> None:
    await send_main_menu(message, session)


@router.message(F.text == MAIN_MENU_BUTTON_TEXT)
async def broadcast_menu_button(
    message: Message,
    session: AsyncSession,
) -> None:
    await send_main_menu(message, session)


@router.message(F.text == START_BUTTON_TEXT)
async def start_broadcast_button(message: Message) -> None:
    await message.answer("Запускаю рассылку...")
    ok, text = await start_broadcast_action()

    await message.answer(
        text,
        reply_markup=main_menu_keyboard(),
    )

    await message.answer(
        render_menu_text(),
        reply_markup=render_keyboard(),
    )

    if not ok:
        logging.getLogger("app").warning(text)


@router.message(F.text == STOP_BUTTON_TEXT)
async def stop_broadcast_button(message: Message) -> None:
    ok, text = await stop_broadcast_action()

    await message.answer(
        text,
        reply_markup=main_menu_keyboard(),
    )

    await message.answer(
        render_menu_text(),
        reply_markup=render_keyboard(),
    )

    if not ok:
        logging.getLogger("app").warning(text)


@router.callback_query(F.data == "bc:text")
async def ask_broadcast_text(callback: CallbackQuery) -> None:
    if callback.message is None:
        await callback.answer()
        return

    service.wait_for_broadcast_text(
        user_id=callback.from_user.id,
        chat_id=callback.message.chat.id,
        message_id=callback.message.message_id,
    )
    await callback.answer("Отправьте текст рассылки")


def is_waiting_broadcast_text(message: Message) -> bool:
    return (
        message.from_user is not None
        and service.is_waiting_broadcast_text(message.from_user.id)
    )


@router.message(F.text, is_waiting_broadcast_text)
async def save_broadcast_text(
    message: Message,
    bot: Bot,
    session: AsyncSession,
) -> None:
    if message.from_user is None or message.text is None:
        return

    menu = service.pop_waiting_broadcast_text_menu(message.from_user.id)
    service.set_broadcast_text(message.text)
    await service.save_settings(session)
    await message.delete()

    if menu is None:
        return

    chat_id, message_id = menu

    await edit_menu_message(
        bot=bot,
        chat_id=chat_id,
        message_id=message_id,
    )


@router.callback_query(F.data == "bc:noop")
async def noop(callback: CallbackQuery) -> None:
    await callback.answer()


@router.callback_query(F.data == "bc:check")
async def check_sessions(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    await callback.answer("Проверяю сессии...")
    ok, message = await service.check_sessions()
    await service.refresh_session_state_cache(session)

    await update_menu(callback)
    if not ok:
        logging.getLogger("app").warning(message)


@router.callback_query(F.data == "bc:errors")
async def show_session_errors(callback: CallbackQuery) -> None:
    errors = service.recent_errors()

    await callback.answer()

    if callback.message is None:
        return

    await answer_long_text(
        message=callback.message,
        title="Ошибки сессий",
        lines=errors,
    )


@router.callback_query(F.data == "bc:paused")
async def show_paused_sessions(callback: CallbackQuery) -> None:
    paused = service.paused_sessions_summary(limit=None)

    await callback.answer()

    if callback.message is None:
        return

    await answer_long_text(
        message=callback.message,
        title="Лежат до восстановления",
        lines=paused,
    )


@router.callback_query(F.data == "bc:reset_sessions")
async def reset_session_states(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    ok, message = await service.reset_session_states(session)

    await update_menu(callback)
    await callback.answer(message, show_alert=True)

    if not ok:
        logging.getLogger("app").warning(message)


@router.callback_query(F.data == "bc:kill_sessions")
async def kill_session_states(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    ok, message = await service.kill_session_states(session)

    await update_menu(callback)
    await callback.answer(message, show_alert=True)

    if not ok:
        logging.getLogger("app").warning(message)


@router.callback_query(F.data.startswith("bc:kill_country:"))
async def kill_session_states_by_country(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    country_code = callback.data.split(":")[-1]
    ok, message = await service.kill_session_states_by_country(
        session=session,
        country_code=country_code,
    )

    await update_menu(callback)
    await callback.answer(message, show_alert=True)

    if not ok:
        logging.getLogger("app").warning(message)


@router.callback_query(F.data == "bc:delete_session_files")
async def delete_session_files(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    ok, message = await service.delete_session_files(session)

    await update_menu(callback)
    await callback.answer(message, show_alert=True)

    if not ok:
        logging.getLogger("app").warning(message)


@router.callback_query(F.data.startswith("bc:delete_country:"))
async def delete_session_files_by_country(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    country_code = callback.data.split(":")[-1]
    ok, message = await service.delete_session_files_by_country(
        session=session,
        country_code=country_code,
    )

    await update_menu(callback)
    await callback.answer(message, show_alert=True)

    if not ok:
        logging.getLogger("app").warning(message)


@router.callback_query(F.data.startswith("bc:reset_country:"))
async def reset_session_states_by_country(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    country_code = callback.data.split(":")[-1]
    ok, message = await service.reset_session_states_by_country(
        session=session,
        country_code=country_code,
    )

    await update_menu(callback)
    await callback.answer(message, show_alert=True)

    if not ok:
        logging.getLogger("app").warning(message)


@router.callback_query(F.data.startswith("bc:batch:"))
async def change_batch(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    action = callback.data.split(":")[-1]

    service.change_batch_size(action)
    await service.save_settings(session)

    await update_menu(callback)
    await callback.answer()


@router.callback_query(F.data.startswith("bc:interval:"))
async def change_interval(
    callback: CallbackQuery,
    session: AsyncSession,
) -> None:
    action = callback.data.split(":")[-1]

    service.change_interval(action)
    await service.save_settings(session)

    await update_menu(callback)
    await callback.answer()


@router.callback_query(F.data == "bc:broadcast")
async def start_broadcast(callback: CallbackQuery) -> None:
    await callback.answer("Запускаю рассылку...")
    ok, message = await start_broadcast_action()

    await update_menu(callback)
    if not ok:
        logging.getLogger("app").warning(message)


@router.callback_query(F.data == "bc:stop")
async def stop_broadcast(callback: CallbackQuery) -> None:
    ok, message = await stop_broadcast_action()

    await update_menu(callback)
    await callback.answer(message, show_alert=not ok)
