from datetime import datetime
from zoneinfo import ZoneInfo


MSK = ZoneInfo("Europe/Moscow")


def now_msk() -> datetime:
    return datetime.now(MSK)