"""قفل مصرف بعد از تکنیک/چای ممنوعه"""
from __future__ import annotations

# telegram_id -> True
_consume_locked: dict[int, bool] = {}

FORBIDDEN_TEA_NAME = "چای ممنوعه"


def lock_consume(telegram_id: int) -> None:
    _consume_locked[telegram_id] = True


def is_consume_locked(telegram_id: int) -> bool:
    return bool(_consume_locked.get(telegram_id))


def lock_message() -> str:
    return (
        "☠️ قفل مصرف فعال است." + chr(10)
        + "چون از تکنیک ممنوعه یا چای ممنوعه استفاده کرده‌ای،"
        + " دیگر هیچ آیتم/چای/قرصی مصرف نمی‌کنی."
    )
