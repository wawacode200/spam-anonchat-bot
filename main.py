import asyncio
from config import settings
from common.logging.logger import logger

from bot.factory import create_bot, create_dispatcher
from common.logging.telegram_handler import TelegramLogHandler


async def main() -> None:

    bot = create_bot()
    dp = create_dispatcher()

    telegram_handler = TelegramLogHandler(bot=bot, chat_id=settings.ADMINS[0])
    logger.addHandler(telegram_handler)
    telegram_handler.start()

    await bot.delete_webhook(
        drop_pending_updates=True
    )

    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())