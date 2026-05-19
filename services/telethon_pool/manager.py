import logging
from pathlib import Path
from telethon import TelegramClient

from common.logging.logger import logger
from services.telethon_pool.session import PoolSession


class TelethonPoolManager:
    def __init__(
        self,
        sessions_dir: str = "telethon_sessions",
    ) -> None:
        self.sessions_dir = Path(sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)

        self.sessions: list[PoolSession] = []

        self._clients: dict[str, TelegramClient] = {}
        self._index = 0

    async def load_clients(self) -> None:
        self.sessions.clear()
        self._clients.clear()

        logger.info(
            "🔄 Начинается загрузка сессий..."
        )

        for file in self.sessions_dir.glob("*.session"):
            session_name = file.stem
            client = TelegramClient(
                str(file.with_suffix("")),
                api_id=2040,
                api_hash="b18441a1ff607e10a989891a5462e627",
                # proxy=settings.Sf,
            )

            try:
                await client.connect()

                if not await client.is_user_authorized():
                    logger.warning(
                        f"⚠️ {session_name} не авторизована"
                    )
                    await client.disconnect()
                    continue

                self._clients[session_name] = client

                self.sessions.append(
                    PoolSession(
                        name=session_name,
                    )
                )
                logger.info(
                    f"✅ {session_name} успешно загружена"
                )

            except Exception as e:
                logger.error(
                    f"❌ Ошибка загрузки {session_name}: {e}"
                )
                await client.disconnect()

        logger.info(
            f"📊 Загружено аккаунтов: {len(self.sessions)}"
        )

    def get_available_session(
        self,
    ) -> PoolSession | None:

        available = [
            session
            for session in self.sessions
            if session.status == "active"
        ]

        if not available:
            logger.warning(
                "⚠️ Нет свободных аккаунтов"
            )
            return None

        session = available[
            self._index % len(available)
        ]

        self._index += 1

        session.status = "busy"
        logger.info(
            f"👤 Взята сессия: {session.name}"
        )

        return session

    async def get_client(
        self,
        session: PoolSession,
    ) -> TelegramClient:
        return self._clients[session.name]

    def mark_active(
        self,
        session: PoolSession,
    ) -> None:
        session.status = "active"
        session.last_error = None
        logger.info(
            f"🟢 {session.name} снова активна"
        )

    def mark_dead(
        self,
        session: PoolSession,
        error: str,
    ) -> None:
        session.status = "dead"
        session.last_error = error
        logger.error(
            f"💀 {session.name} умерла: {error}"
        )

    def mark_paused(
        self,
        session: PoolSession,
        error: str | None = None,
    ) -> None:
        session.status = "paused"
        session.last_error = error
        logger.warning(
            f"⏸ {session.name} поставлена на паузу: {error}"
        )

    def reset_after_stop(self) -> None:
        for session in self.sessions:
            if session.status == "busy":
                session.status = "active"

    async def disconnect_all(self) -> None:
        for client in self._clients.values():
            await client.disconnect()

        self._clients.clear()