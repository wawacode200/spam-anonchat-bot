import asyncio

import logging
from config import settings
from services.telethon_pool.manager import TelethonPoolManager
from services.telethon_pool.sender import TelethonSender
import logging

logger = logging.getLogger("app")

class BroadcastService:
    def __init__(self) -> None:
        self.batch_size = 5
        self.interval = 10
        self.is_running = False

        self.pool = TelethonPoolManager()
        self.sender = TelethonSender(self.pool)

        self._task: asyncio.Task | None = None

    def change_batch_size(self, action: str) -> None:
        if action == "dec10":
            self.batch_size -= 10
        elif action == "dec1":
            self.batch_size -= 1
        elif action == "inc1":
            self.batch_size += 1
        elif action == "inc10":
            self.batch_size += 10

        self.batch_size = max(1, self.batch_size)

    def change_interval(self, action: str) -> None:
        if action == "dec10":
            self.interval -= 10
        elif action == "dec1":
            self.interval -= 1
        elif action == "inc1":
            self.interval += 1
        elif action == "inc10":
            self.interval += 10

        self.interval = max(1, self.interval)

    def start(self) -> None:
        if self.is_running:
            return

        self.is_running = True
        self._task = asyncio.create_task(self._run())
        logger.info(
            f"🚀 Рассылка запущена | "
            f"Пакет={self.batch_size} "
            f"| Интервал={self.interval} сек"
        )

    def stop(self) -> None:
        self.is_running = False

        if self._task and not self._task.done():
            self._task.cancel()

        self.pool.reset_after_stop()
        self._task = None
        logger.info(
            "🛑 Рассылка остановлена"
        )

    async def _run(self) -> None:
        await self.pool.load_clients()
        try:
            while self.is_running:
                for _ in range(self.batch_size):
                    session = self.pool.get_available_session()

                    if session is None:
                        break

                    await self.sender.send(
                        session=session,
                        chat_id=settings.TARGET_CHAT_ID,
                        text=settings.BROADCAST_TEXT,
                    )

                logger.info(
                    f"⏳ Интервальная пауза: {self.interval}сек."
                )
                await asyncio.sleep(self.interval)

        except asyncio.CancelledError:
            self.pool.reset_after_stop()
            raise

        finally:
            await self.pool.disconnect_all()
