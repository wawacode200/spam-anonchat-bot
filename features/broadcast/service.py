import asyncio
from contextlib import suppress

import logging
from config import settings
from database.repositories.broadcast_settings import BroadcastSettingsRepository
from database.repositories.telethon_sessions import TelethonSessionsRepository
from services.telethon_pool.manager import TelethonPoolManager
from services.telethon_pool.sender import TelethonSender
import logging
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger("app")

class BroadcastService:
    def __init__(self) -> None:
        self.desired_batch_size = 5
        self.effective_batch_size = 0
        self.interval = 10
        self.is_running = False
        self.is_checking = False
        self.is_stopping = False
        self.broadcast_text = settings.BROADCAST_TEXT
        self._waiting_text_menus: dict[int, tuple[int, int]] = {}

        self.pool = TelethonPoolManager()
        self.sender = TelethonSender(self.pool)

        self._task: asyncio.Task | None = None

    async def load_settings(self, session: AsyncSession) -> None:
        repository = BroadcastSettingsRepository(session)
        broadcast_settings = await repository.get_or_create()

        self.desired_batch_size = broadcast_settings.batch_size
        self.interval = broadcast_settings.interval
        self.broadcast_text = broadcast_settings.broadcast_text
        self.normalize_batch_size()

    async def save_settings(self, session: AsyncSession) -> None:
        repository = BroadcastSettingsRepository(session)
        broadcast_settings = await repository.get_or_create()

        broadcast_settings.batch_size = self.desired_batch_size
        broadcast_settings.interval = self.interval
        broadcast_settings.broadcast_text = self.broadcast_text

    def change_batch_size(self, action: str) -> None:
        if action == "dec10":
            self.desired_batch_size -= 10
        elif action == "dec1":
            self.desired_batch_size -= 1
        elif action == "inc1":
            self.desired_batch_size += 1
        elif action == "inc10":
            self.desired_batch_size += 10

        self.normalize_batch_size()

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

    def session_files_count(self) -> int:
        return len(list(self.pool.sessions_dir.glob("*.session")))

    def session_file_names(self) -> list[str]:
        return [
            file.stem
            for file in sorted(self.pool.sessions_dir.glob("*.session"))
        ]

    def session_file_names_by_country(self, country_code: str) -> list[str]:
        return [
            name
            for name in self.session_file_names()
            if self.pool.detect_country_code(name) == country_code
        ]

    def available_sessions_count(self) -> int:
        loaded_sessions_count = self.pool.loaded_sessions_count()

        if loaded_sessions_count > 0:
            return self.pool.active_sessions_count()

        return self.session_files_count()

    def normalize_batch_size(
        self,
        sessions_count: int | None = None,
    ) -> None:
        if sessions_count is None:
            sessions_count = self.session_files_count()

        self.desired_batch_size = max(1, self.desired_batch_size)

        if sessions_count == 0:
            self.effective_batch_size = 0
            return

        self.effective_batch_size = min(
            self.desired_batch_size,
            max(0, self.available_sessions_count()),
        )

    def session_status_counts(self) -> dict[str, int]:
        counts = self.pool.status_counts()
        counts["files"] = self.session_files_count()

        return counts

    def recent_errors(self) -> list[str]:
        return self.pool.recent_errors()

    def paused_sessions_summary(self, limit: int | None = None) -> list[str]:
        paused_sessions = self.pool.paused_sessions(limit=limit)

        result = []

        for session in paused_sessions:
            if session.available_at is None:
                result.append(f"{session.name}: без времени возврата")
                continue

            available_at = session.available_at.strftime("%H:%M:%S")
            result.append(f"{session.name}: до {available_at}")

        return result

    async def reset_session_states(
        self,
        session: AsyncSession,
    ) -> tuple[bool, str]:
        if self.is_running:
            return False, "Нельзя сбрасывать статусы во время рассылки"
        if self.is_checking:
            return False, "Нельзя сбрасывать статусы во время проверки сессий"

        repository = TelethonSessionsRepository(session)
        session_names = self.session_file_names()
        db_count = await repository.count_all()
        reset_count = await repository.reset_all()
        file_count = await repository.set_all(
            names=session_names,
            status="active",
        )
        await self.pool.disconnect_all()
        loaded_count = self.pool.clear_runtime_state()
        self.normalize_batch_size()

        if db_count == 0 and file_count == 0 and loaded_count == 0:
            return True, "Статусов сессий для сброса нет"

        return (
            True,
            f"Статусы сброшены: БД {reset_count}, файлов {file_count}, в памяти {loaded_count}",
        )

    async def reset_session_states_by_country(
        self,
        session: AsyncSession,
        country_code: str,
    ) -> tuple[bool, str]:
        if self.is_running:
            return False, "Нельзя сбрасывать статусы во время рассылки"
        if self.is_checking:
            return False, "Нельзя сбрасывать статусы во время проверки сессий"

        session_names = self.session_file_names_by_country(country_code)

        if not session_names:
            return True, f"Нет .session файлов для {country_code.upper()}"

        repository = TelethonSessionsRepository(session)
        reset_count = await repository.set_all(
            names=session_names,
            status="active",
        )
        await self.pool.disconnect_all()
        loaded_count = self.pool.clear_runtime_state()
        self.normalize_batch_size()

        return (
            True,
            f"{country_code.upper()}: сброшено {reset_count}, очищено в памяти {loaded_count}",
        )

    async def kill_session_states(
        self,
        session: AsyncSession,
    ) -> tuple[bool, str]:
        if self.is_running:
            return False, "Нельзя убивать аккаунты во время рассылки"
        if self.is_checking:
            return False, "Нельзя убивать аккаунты во время проверки сессий"

        session_names = self.session_file_names()

        if not session_names:
            return True, "Нет .session файлов для убийства"

        error = "Killed manually"
        repository = TelethonSessionsRepository(session)
        killed_count = await repository.set_all(
            names=session_names,
            status="dead",
            last_error=error,
        )
        await self.pool.disconnect_all()
        loaded_count = self.pool.set_runtime_dead_states(
            names=session_names,
            error=error,
        )
        self.normalize_batch_size()

        return (
            True,
            f"Аккаунты убиты: БД {killed_count}, в памяти {loaded_count}",
        )

    def validate_start(self) -> list[str]:
        errors = []

        if not settings.TARGET_CHAT_ID:
            errors.append("TARGET_CHAT_ID не задан")
        if not settings.APP_ID:
            errors.append("APP_ID не задан")
        if not settings.API_HASH:
            errors.append("API_HASH не задан")
        if not self.broadcast_text.strip():
            errors.append("Текст рассылки пустой")
        if self.session_files_count() == 0:
            errors.append("Нет .session файлов")
        if self.is_checking:
            errors.append("Идёт проверка сессий")
        if self.is_stopping:
            errors.append("Идёт остановка рассылки")

        return errors

    def wait_for_broadcast_text(
        self,
        user_id: int,
        chat_id: int,
        message_id: int,
    ) -> None:
        self._waiting_text_menus[user_id] = (chat_id, message_id)

    def pop_waiting_broadcast_text_menu(
        self,
        user_id: int,
    ) -> tuple[int, int] | None:
        return self._waiting_text_menus.pop(user_id, None)

    def is_waiting_broadcast_text(self, user_id: int) -> bool:
        return user_id in self._waiting_text_menus

    def set_broadcast_text(self, text: str) -> None:
        self.broadcast_text = text

    async def check_sessions(
        self,
        keep_connected: bool = False,
        active_limit: int | None = None,
        file_limit: int | None = None,
        send_start: bool = False,
    ) -> tuple[bool, str]:
        if self.is_running:
            return False, "Нельзя проверять сессии во время рассылки"
        if self.is_checking:
            return False, "Проверка уже идёт"

        self.is_checking = True

        try:
            await self.pool.load_clients(
                active_limit=active_limit,
                file_limit=file_limit,
                send_start=send_start,
            )
            self.normalize_batch_size(
                self.pool.loaded_sessions_count()
            )

            active_count = self.pool.active_sessions_count()

            if active_count == 0:
                return False, "Валидных активных сессий нет"

            return True, f"Активных сессий: {active_count}"

        finally:
            if not keep_connected:
                await self.pool.disconnect_all()

            self.is_checking = False

    async def start(self) -> tuple[bool, str]:
        if self.is_running:
            return False, "Рассылка уже запущена"

        self.normalize_batch_size()
        validation_errors = self.validate_start()

        if validation_errors:
            return False, "\n".join(validation_errors)

        ok, message = await self.check_sessions(
            keep_connected=True,
            active_limit=max(1, self.desired_batch_size),
            send_start=True,
        )

        if not ok:
            return False, message

        self.is_running = True
        self.is_stopping = False
        self._task = asyncio.create_task(self._run())
        logger.info(
            f"🚀 Рассылка запущена | "
            f"За раз={self.desired_batch_size} "
            f"| Доступно={self.effective_batch_size} "
            f"| Интервал={self.interval} сек"
        )

        return True, "Рассылка запущена"

    async def stop(self) -> tuple[bool, str]:
        if not self.is_running and not self._task:
            return False, "Рассылка не запущена"

        if self.is_stopping:
            return False, "Рассылка уже останавливается"

        self.is_stopping = True
        self.is_running = False

        if self._task and not self._task.done():
            self._task.cancel()
            with suppress(asyncio.CancelledError):
                await self._task

        self.pool.reset_after_stop()
        self._task = None
        self.is_stopping = False
        logger.info(
            "🛑 Рассылка остановлена"
        )

        return True, "Рассылка остановлена"

    async def _run(self) -> None:
        self.normalize_batch_size(
            self.pool.loaded_sessions_count()
        )

        if self.effective_batch_size == 0:
            logger.warning(
                "⚠️ Нет валидных Telethon-сессий для рассылки"
            )
            self.is_running = False
            return

        try:
            while self.is_running:
                await self.pool.replenish_clients(
                    active_target=self.desired_batch_size,
                    send_start=True,
                )
                active_sessions_count = self.pool.active_sessions_count()

                if active_sessions_count == 0:
                    logger.warning(
                        "⚠️ Все Telethon-сессии недоступны, рассылка остановлена"
                    )
                    self.is_running = False
                    break

                self.effective_batch_size = min(
                    self.desired_batch_size,
                    active_sessions_count,
                )

                for _ in range(self.effective_batch_size):
                    session = self.pool.get_available_session()

                    if session is None:
                        break

                    await self.sender.send(
                        session=session,
                        chat_id=settings.TARGET_CHAT_ID,
                        text=self.broadcast_text,
                    )

                logger.info(
                    f"⏳ Интервальная пауза: {self.interval}сек."
                )
                await asyncio.gather(
                    asyncio.sleep(self.interval),
                    self.pool.replenish_clients(
                        active_target=self.desired_batch_size,
                        send_start=True,
                    ),
                )

        except asyncio.CancelledError:
            self.pool.reset_after_stop()
            raise

        finally:
            self.is_running = False
            self.is_stopping = False
            await self.pool.disconnect_all()
