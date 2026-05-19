from dataclasses import dataclass
from os import getenv

import socks
from dotenv import load_dotenv

load_dotenv()


@dataclass(frozen=True)
class Settings:
    BOT_TOKEN: str
    ADMINS: list[int]
    DATABASE_URL: str
    APP_ID: int
    API_HASH: str
    PROXY: tuple
    TARGET_CHAT_ID: str
    BROADCAST_TEXT: str
    OPENAI_API_KEY: str

def parse_admins(value: str | None) -> list[int]:
    if not value:
        return []

    return [
        int(admin_id.strip())
        for admin_id in value.split(",")
        if admin_id.strip()
    ]


settings = Settings(
    BOT_TOKEN=getenv("BOT_TOKEN", ""),
    ADMINS=parse_admins(getenv("ADMINS")),
    DATABASE_URL=getenv(
        "DATABASE_URL",
        "sqlite+aiosqlite:///database/bot.db",
    ),
    APP_ID=2040,
    API_HASH="b18441a1ff607e10a989891a5462e627",
    PROXY=(
        socks.SOCKS5,
        "gw.dataimpulse.com",
        824,
        True,
        "f5c01921394421f81686__cr.co",
        "eed6a12534c02e07",
    ),
    TARGET_CHAT_ID="AnonRuBot",
    BROADCAST_TEXT=(
        "💋 18+ Анонимный чат @AnonSeaChatRobot\n"
        "🔥 Тысячи онлайн\n"
        "🫶 Интим\n"
        "💕 Найди пару\n"
    ),
    OPENAI_API_KEY=getenv("OPENAI_API_KEY", "")
)