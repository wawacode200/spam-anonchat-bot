from pathlib import Path

from aiogram import F, Router, Bot
from aiogram.types import Message, CallbackQuery

from common.filters import AdminFilter

router = Router()
router.message.filter(AdminFilter())

SESSIONS_DIR = Path("telethon_sessions")
SESSIONS_DIR.mkdir(exist_ok=True)


@router.callback_query(F.data == "sessions:add")
async def sessions_menu(callback: CallbackQuery) -> None:
    await callback.answer("Отправь .session файлы")


@router.message(F.document)
async def upload_session(message: Message, bot: Bot) -> None:
    document = message.document

    if not document.file_name.endswith(".session"):
        return

    file_path = SESSIONS_DIR / document.file_name

    if file_path.exists():
        await message.answer(f"Файл уже существует: <code>{document.file_name}</code>")
        return

    await bot.download(
        document,
        destination=file_path,
    )

    await message.delete()

    await message.answer(
        f"✅ Сессия загружена:\n<code>{document.file_name}</code>"
    )