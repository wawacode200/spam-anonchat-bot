import asyncio
import re

from telethon.errors import (
    FloodWaitError,
    SessionRevokedError,
    UserDeactivatedError,
)
from services.openai_service import openai_service

from services.telethon_pool.manager import TelethonPoolManager
from services.telethon_pool.session import PoolSession
import logging

logger = logging.getLogger("app")

class TelethonSender:
    def __init__(
        self,
        pool: TelethonPoolManager,
    ) -> None:
        self.pool = pool

    def extract_button_emojis(self, message) -> list[str]:
        emojis = []

        if not message.buttons:
            return emojis

        for row in message.buttons:
            for button in row:
                if button.text != "Обновить капчу":
                    emojis.append(button.text)

        return emojis

    async def click_emojis_buttons(
            self,
            message,
            emojis: list[str],
    ) -> None:
        if not message.buttons:
            return

        for target_emoji in emojis:
            clicked = False

            for row_index, row in enumerate(message.buttons):
                for button_index, button in enumerate(row):
                    if button.text == target_emoji:
                        await message.click(
                            row_index,
                            button_index,
                        )
                        clicked = True
                        break

                if clicked:
                    break

    async def send(
        self,
        session: PoolSession,
        chat_id: int | str,
        text: str,
    ) -> None:
        try:
            client = await self.pool.get_client(
                session,
            )

            async with client.conversation(chat_id, timeout=10) as conv:
                logger.info(
                    f"📨 {session.name}: запуск поиска собеседника"
                )
                await conv.send_message("/next")

                while True:
                    response = await conv.get_response()
                    response_text = response.raw_text.lower()

                    if "собеседник найден" in response_text:
                        logger.info(
                            f"🎯 {session.name}: собеседник найден"
                        )
                        await asyncio.sleep(1)
                        await client.send_message(entity=chat_id, message="👅 Хочешь грязный анонимный чат?")
                        await asyncio.sleep(0.1)
                        await client.send_message(entity=chat_id, message=text)
                        await asyncio.sleep(1)
                        await client.send_message(entity=chat_id, message="/stop")
                        logger.info(
                            f"✉️ {session.name}: сообщение отправлено"
                        )
                        self.pool.mark_active(session)
                        break

                    elif "лимит на чаты будет снят через" in response_text:
                        pause_seconds = self.parse_limit_seconds(response.raw_text)
                        self.pool.mark_paused(
                            session,
                            "AnonChat daily limit",
                            pause_seconds=pause_seconds,
                        )
                        logger.warning(
                            f"🚫 {session.name}: дневной лимит, пауза {pause_seconds} сек."
                        )
                        break

                    elif "мы временно ограничили вам пользование чатом" in response_text:
                        self.pool.mark_paused(
                            session,
                            f"AnonChat limit block",
                            pause_seconds=15 * 60,
                        )
                        logger.warning(
                            f"🚫 {session.name}: обнаружен лимит"
                        )
                        break

                    elif "чтобы подтвердить, что вы не бот" in response_text:
                        logger.info(
                            f"🤖 {session.name}: обнаружена капча"
                        )
                        if response.photo:
                            button_emojis = self.extract_button_emojis(response)
                            photo_bytes = await response.download_media(file=bytes)

                            emojis = openai_service.recognize_emoji_captcha(
                                image_bytes=photo_bytes,
                                button_emojis=button_emojis,
                            )

                            await self.click_emojis_buttons(response, emojis)
                            logger.info(
                                f"✅ {session.name}: капча решена"
                            )

        except asyncio.TimeoutError:
            self.pool.mark_paused(
                session,
                f"AnonChat not answer 10s",
                pause_seconds=60,
            )
            logger.warning(
                f"⌛ {session.name}: нет ответа более 10 секунд"
            )

        except FloodWaitError as e:
            self.pool.mark_paused(
                session,
                f"FloodWait: {e.seconds}s",
                pause_seconds=e.seconds,
            )
            logger.warning(
                f"⏳ {session.name}: FloodWait {e.seconds} сек."
            )

        except (
            SessionRevokedError,
            UserDeactivatedError,
        ) as e:
            self.pool.mark_dead(
                session,
                str(e),
            )

        except Exception as e:
            logger.error(
                f"❌ {session.name}: {e}"
            )
            error_text = str(e).lower()

            if "captcha" in error_text:
                self.pool.mark_paused(
                    session,
                    "Captcha/manual check required",
                )
            else:
                self.pool.mark_paused(
                    session,
                    str(e),
                )

    def parse_limit_seconds(self, text: str) -> int:
        match = re.search(
            r"через\s+(\d{1,2}):(\d{2}):(\d{2})",
            text,
            re.IGNORECASE,
        )

        if not match:
            return 24 * 60 * 60

        hours, minutes, seconds = (
            int(match.group(1)),
            int(match.group(2)),
            int(match.group(3)),
        )

        return hours * 60 * 60 + minutes * 60 + seconds
