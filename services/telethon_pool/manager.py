import asyncio
import logging
import re
import sqlite3
from collections import Counter
from contextlib import suppress
from datetime import datetime, timedelta
from pathlib import Path
from telethon.sessions import SQLiteSession
from telethon import TelegramClient

from common.logging.logger import logger
from common.time import MSK, now_msk
from config import settings
from database.repositories.telethon_sessions import TelethonSessionsRepository
from database.session import async_session_maker
from services.telethon_pool.session import PoolSession


CANADIAN_AREA_CODES = {
    "204", "226", "236", "249", "250", "263", "289", "306", "343",
    "354", "365", "367", "368", "382", "403", "416", "418", "431",
    "437", "438", "450", "468", "474", "506", "514", "519", "548",
    "579", "581", "584", "587", "604", "613", "639", "647", "672",
    "683", "705", "709", "742", "778", "780", "782", "807", "819",
    "825", "867", "873", "879", "902", "905",
}

COUNTRY_CODES_BY_CALLING_CODE = {
    "34": "es",
    "39": "it",
    "44": "gb",
    "49": "de",
    "51": "pe",
    "52": "mx",
    "54": "ar",
    "55": "br",
    "56": "cl",
    "57": "co",
    "58": "ve",
    "593": "ec",
    "591": "bo",
    "598": "uy",
}

PHONE_SESSION_RE = re.compile(r"^\+\d{8,20}$")
SESSION_CHECK_CONCURRENCY = 40
SESSION_SQLITE_BUSY_TIMEOUT_MS = 30_000


class BusyTimeoutSQLiteSession(SQLiteSession):
    def _cursor(self):
        if self._conn is None:
            self._conn = sqlite3.connect(
                self.filename,
                check_same_thread=False,
                timeout=SESSION_SQLITE_BUSY_TIMEOUT_MS / 1000,
            )
            self._conn.execute(
                f"PRAGMA busy_timeout={SESSION_SQLITE_BUSY_TIMEOUT_MS}"
            )

        return self._conn.cursor()

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
        self._load_lock = asyncio.Lock()
        self._sessions_lock = asyncio.Lock()

    async def load_clients(
        self,
        active_limit: int | None = None,
        file_limit: int | None = None,
        send_start: bool = False,
    ) -> None:
        async with self._load_lock:
            await self.disconnect_all()
            self.sessions.clear()
            self._clients.clear()
            self.last_errors.clear()
            persisted_states = await self._load_persisted_states()

            logger.info(
                "🔄 Начинается загрузка сессий..."
            )

            files = sorted(self.sessions_dir.glob("*.session"))

            if file_limit is not None:
                files = files[:file_limit]

            if active_limit is None:
                await self._load_all_clients(
                    files=files,
                    persisted_states=persisted_states,
                    send_start=send_start,
                )
            else:
                await self._load_clients_until_limit(
                    files=files,
                    persisted_states=persisted_states,
                    active_limit=active_limit,
                    send_start=send_start,
                )

            logger.info(
                f"📊 Загружено аккаунтов: {len(self.sessions)}"
            )

    async def replenish_clients(
        self,
        active_target: int,
        send_start: bool = False,
    ) -> None:
        async with self._load_lock:
            self.restore_available_sessions()

            if self.active_sessions_count() >= active_target:
                return

            persisted_states = await self._load_persisted_states()
            known_session_names = {
                session.name
                for session in self.sessions
            }
            files = [
                file
                for file in sorted(self.sessions_dir.glob("*.session"))
                if file.stem not in known_session_names
            ]

            if not files:
                return

            logger.info(
                f"🔄 Добор сессий до {active_target} активных..."
            )
            await self._load_clients_until_limit(
                files=files,
                persisted_states=persisted_states,
                active_limit=active_target,
                send_start=send_start,
            )
            logger.info(
                f"📊 Активных после добора: {self.active_sessions_count()}"
            )

    async def _load_all_clients(
        self,
        files: list[Path],
        persisted_states,
        send_start: bool,
    ) -> None:
        semaphore = asyncio.Semaphore(SESSION_CHECK_CONCURRENCY)
        tasks = [
            self._load_client(
                file=file,
                persisted_states=persisted_states,
                semaphore=semaphore,
                active_limit=None,
                send_start=send_start,
            )
            for file in files
        ]

        await asyncio.gather(*tasks)

    async def _load_clients_until_limit(
        self,
        files: list[Path],
        persisted_states,
        active_limit: int,
        send_start: bool,
    ) -> None:
        concurrency = min(
            SESSION_CHECK_CONCURRENCY,
            max(1, active_limit),
        )
        semaphore = asyncio.Semaphore(concurrency)
        file_iterator = iter(files)
        pending: set[asyncio.Task] = set()

        def schedule_next() -> bool:
            if self.active_sessions_count() >= active_limit:
                return False

            try:
                file = next(file_iterator)
            except StopIteration:
                return False

            pending.add(
                asyncio.create_task(
                    self._load_client(
                        file=file,
                        persisted_states=persisted_states,
                        semaphore=semaphore,
                        active_limit=active_limit,
                        send_start=send_start,
                    )
                )
            )
            return True

        for _ in range(concurrency):
            if not schedule_next():
                break

        while pending:
            done, pending = await asyncio.wait(
                pending,
                return_when=asyncio.FIRST_COMPLETED,
            )

            for task in done:
                await task

            if self.active_sessions_count() >= active_limit:
                await asyncio.gather(
                    *pending,
                    return_exceptions=True,
                )
                break

            while len(pending) < concurrency:
                if not schedule_next():
                    break

    async def _load_client(
        self,
        file: Path,
        persisted_states,
        semaphore: asyncio.Semaphore,
        active_limit: int | None,
        send_start: bool,
    ) -> None:
        async with semaphore:
            if (
                active_limit is not None
                and self.active_sessions_count() >= active_limit
            ):
                return

            session_name = file.stem
            persisted_state = persisted_states.get(session_name)

            if persisted_state is not None and persisted_state.status == "dead":
                return

            country_code = self.detect_country_code(session_name)

            if country_code is None:
                error = "invalid phone session name"
                self.last_errors.append(f"{session_name}: {error}")
                logger.warning(
                    f"⚠️ {session_name} пропущена: имя должно быть номером телефона"
                )
                return

            proxy = self.build_proxy(country_code)

            if proxy is None:
                error = f"proxy not configured for country {country_code}"
                self.last_errors.append(f"{session_name}: {error}")
                logger.warning(
                    f"⚠️ {session_name} пропущена: прокси не настроен"
                )
                return

            client = TelegramClient(
                BusyTimeoutSQLiteSession(
                    str(file.with_suffix(""))
                ),
                api_id=settings.APP_ID,
                api_hash=settings.API_HASH,
                proxy=proxy,
                connection_retries=1,
                timeout=10,
            )

            try:
                await client.connect()

                if not await client.is_user_authorized():
                    logger.warning(
                        f"⚠️ {session_name} не авторизована"
                    )
                    await self._safe_disconnect(client, session_name)
                    return

                pool_session = self._build_pool_session(
                    session_name=session_name,
                    persisted_state=persisted_state,
                )

                if pool_session.status != "active":
                    async with self._sessions_lock:
                        self.sessions.append(pool_session)
                    await self._save_session_state(pool_session)
                    await self._safe_disconnect(client, session_name)
                    logger.info(
                        f"⏸ {session_name} загружена со статусом {pool_session.status}"
                    )
                    return

                async with self._sessions_lock:
                    if (
                        active_limit is not None
                        and self.active_sessions_count() >= active_limit
                    ):
                        await self._safe_disconnect(client, session_name)
                        return

                    if send_start and settings.TARGET_CHAT_ID:
                        await client.send_message(
                            entity=settings.TARGET_CHAT_ID,
                            message="/start",
                        )
                        logger.info(
                            f"▶️ {session_name}: /start отправлен в целевой чат"
                        )

                    self._clients[session_name] = client
                    self.sessions.append(pool_session)
                    await self._save_session_state(pool_session)
                    logger.info(
                        f"✅ {session_name} успешно загружена со статусом active"
                    )

            except Exception as e:
                error_text = str(e)
                self.last_errors.append(f"{session_name}: {error_text}")
                logger.error(
                    f"❌ Ошибка загрузки {session_name}: {error_text}"
                )
                await self._safe_disconnect(client, session_name)

    async def _safe_disconnect(
        self,
        client: TelegramClient,
        session_name: str,
    ) -> None:
        with suppress(Exception):
            await client.disconnect()

    def _build_pool_session(
        self,
        session_name: str,
        persisted_state,
    ) -> PoolSession:
        pool_session = PoolSession(
            name=session_name,
        )

        if persisted_state is None:
            return pool_session

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

        return pool_session

    def detect_country_code(self, session_name: str) -> str | None:
        if not PHONE_SESSION_RE.fullmatch(session_name):
            return None

        digits = session_name[1:]

        if digits.startswith("1"):
            area_code = digits[1:4]

            if area_code in CANADIAN_AREA_CODES:
                return "ca"

            return "us"

        for calling_code, country_code in sorted(
            COUNTRY_CODES_BY_CALLING_CODE.items(),
            key=lambda item: len(item[0]),
            reverse=True,
        ):
            if digits.startswith(calling_code):
                return country_code

        return None

    def build_proxy(self, country_code: str) -> tuple | None:
        if settings.PROXY is None:
            return None

        proxy_type, host, port, rdns, username, password = settings.PROXY

        if not username:
            return settings.PROXY

        return (
            proxy_type,
            host,
            port,
            rdns,
            f"{username}{country_code}",
            password,
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
                self._schedule_save_session_state(session)

    def clear_runtime_state(self) -> int:
        count = len(self.sessions)
        self.sessions.clear()
        self.last_errors.clear()
        self._index = 0

        return count

    def set_runtime_dead_states(
        self,
        names: list[str],
        error: str,
    ) -> int:
        self.sessions = [
            PoolSession(
                name=name,
                status="dead",
                last_error=error,
            )
            for name in names
        ]
        self.last_errors.clear()
        self._index = 0

        return len(self.sessions)

    async def disconnect_all(self) -> None:
        for session_name, client in self._clients.items():
            await self._safe_disconnect(client, session_name)

        self._clients.clear()
