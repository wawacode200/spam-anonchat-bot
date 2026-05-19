import asyncio
import logging
from collections import Counter
from datetime import datetime, timedelta
from pathlib import Path
from telethon import TelegramClient

from common.logging.logger import logger
from common.time import MSK, now_msk
from config import settings
from database.repositories.telethon_sessions import TelethonSessionsRepository
from database.session import async_session_maker
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
        self.last_errors: list[str] = []

    async def load_clients(self) -> None:
        await self.disconnect_all()
        self.sessions.clear()
        self._clients.clear()
        self.last_errors.clear()
        persisted_states = await self._load_persisted_states()

        logger.info(
            "🔄 Начинается загрузка сессий..."
        )

        for file in self.sessions_dir.glob("*.session"):
            session_name = file.stem
            client = TelegramClient(
                str(file.with_suffix("")),
                api_id=settings.APP_ID,
                api_hash=settings.API_HASH,
                # proxy=settings.PROXY,
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
                persisted_state = persisted_states.get(session_name)
                pool_session = PoolSession(
                    name=session_name,
                )

                if persisted_state is not None:
                    pool_session.status = persisted_state.status
                    pool_session.available_at = self._ensure_timezone(
                        persisted_state.available_at,
                    )
                    pool_session.last_error = persisted_state.last_error

                    if (
                        pool_session.status == "paused"
                        and pool_session.available_at is not None
                        and pool_session.available_at <= now_msk()
                    ):
                        pool_session.status = "active"
                        pool_session.available_at = None
                        pool_session.last_error = None

                self.sessions.append(pool_session)
                logger.info(
                    f"✅ {session_name} успешно загружена"
                )

            except Exception as e:
                self.last_errors.append(f"{session_name}: {e}")
                logger.error(
                    f"❌ Ошибка загрузки {session_name}: {e}"
                )
                await client.disconnect()

        logger.info(
            f"📊 Загружено аккаунтов: {len(self.sessions)}"
        )

    async def _load_persisted_states(self):
        async with async_session_maker() as session:
            repository = TelethonSessionsRepository(session)
            return await repository.get_all_map()

    async def _save_session_state(self, session: PoolSession) -> None:
        async with async_session_maker() as db_session:
            repository = TelethonSessionsRepository(db_session)
            await repository.upsert(
                name=session.name,
                status=session.status,
                available_at=session.available_at,
                last_error=session.last_error,
            )
            await db_session.commit()

    def _schedule_save_session_state(self, session: PoolSession) -> None:
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            return

        loop.create_task(self._save_session_state(session))

    def _ensure_timezone(
        self,
        value: datetime | None,
    ) -> datetime | None:
        if value is None or value.tzinfo is not None:
            return value

        return value.replace(tzinfo=MSK)

    def get_available_session(
        self,
    ) -> PoolSession | None:
        self.restore_available_sessions()

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

    def restore_available_sessions(self) -> None:
        current_time = now_msk()

        for session in self.sessions:
            if (
                session.status == "paused"
                and session.available_at is not None
                and session.available_at <= current_time
            ):
                self.mark_active(session)

    def active_sessions_count(self) -> int:
        self.restore_available_sessions()

        return sum(
            1
            for session in self.sessions
            if session.status == "active"
        )

    def loaded_sessions_count(self) -> int:
        return len(self.sessions)

    def status_counts(self) -> dict[str, int]:
        self.restore_available_sessions()

        counts = Counter(session.status for session in self.sessions)

        return {
            "loaded": len(self.sessions),
            "active": counts.get("active", 0),
            "busy": counts.get("busy", 0),
            "paused": counts.get("paused", 0),
            "dead": counts.get("dead", 0),
        }

    def recent_errors(self, limit: int = 8) -> list[str]:
        session_errors = [
            f"{session.name}: {session.last_error}"
            for session in self.sessions
            if session.last_error
        ]

        return [*self.last_errors, *session_errors][-limit:]

    def paused_sessions(self, limit: int | None = 5) -> list[PoolSession]:
        self.restore_available_sessions()

        paused = [
            session
            for session in self.sessions
            if session.status == "paused"
        ]

        sorted_sessions = sorted(
            paused,
            key=lambda session: session.available_at or datetime.max.replace(tzinfo=MSK),
        )

        if limit is None:
            return sorted_sessions

        return sorted_sessions[:limit]

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
        session.available_at = None
        self._schedule_save_session_state(session)
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
        session.available_at = None
        self.last_errors.append(f"{session.name}: {error}")
        self._schedule_save_session_state(session)
        logger.error(
            f"💀 {session.name} умерла: {error}"
        )

    def mark_paused(
        self,
        session: PoolSession,
        error: str | None = None,
        pause_seconds: int | None = None,
    ) -> None:
        session.status = "paused"
        session.last_error = error
        session.available_at = (
            now_msk() + timedelta(seconds=pause_seconds)
            if pause_seconds
            else None
        )
        self.last_errors.append(f"{session.name}: {error}")
        self._schedule_save_session_state(session)
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
