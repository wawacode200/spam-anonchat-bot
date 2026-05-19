import asyncio
import logging
from aiogram import Bot
from aiogram.exceptions import TelegramRetryAfter


class TelegramLogHandler(logging.Handler):
    def __init__(
        self,
        bot: Bot,
        chat_id: int,
    ) -> None:
        super().__init__()

        self.bot = bot
        self.chat_id = chat_id

        self.queue = asyncio.Queue()
        self.worker_task = None

    def start(self):
        if self.worker_task:
            return

        self.worker_task = asyncio.create_task(
            self._worker()
        )

    def emit(
        self,
        record: logging.LogRecord,
    ) -> None:
        text = self.format(record)

        self.queue.put_nowait(
            (
                record.created,
                text[:4096],
            )
        )

    async def _worker(self):
        while True:
            _, text = await self.queue.get()

            try:
                await self.bot.send_message(
                    chat_id=self.chat_id,
                    text=text,
                    disable_notification=True,
                )

            except TelegramRetryAfter as e:
                await asyncio.sleep(
                    e.retry_after
                )

            except Exception:
                pass

            finally:
                self.queue.task_done()