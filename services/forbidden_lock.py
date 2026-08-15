"""قفل مصرف بعد از تکنیک/چای ممنوعه — پایدار"""
from __future__ import annotations
from services.persist import get_dict, save as _psave

FORBIDDEN_TEA_NAME = "چای ممنوعه"


def _map() -> dict:
    return get_dict("forbidden_lock")


def lock_consume(telegram_id: int) -> None:
    d = _map()
    d[str(int(telegram_id))] = True
    _psave("forbidden_lock")


def unlock_consume(telegram_id: int) -> None:
    d = _map()
    d.pop(str(int(telegram_id)), None)
    _psave("forbidden_lock")


def is_consume_locked(telegram_id: int) -> bool:
    return bool(_map().get(str(int(telegram_id))))


def clear_all_locks() -> None:
    d = _map()
    d.clear()
    _psave("forbidden_lock")


def lock_message() -> str:
    return (
        "☠️ قفل مصرف فعال است." + chr(10)
        + "چون از تکنیک ممنوعه یا چای ممنوعه استفاده کردهای،"
        + " دیگر هیچ آیتم/چای/قرصی مصرف نمیکنی." + chr(10)
        + "با پاک کردن کامل اکانت (/afterdeath → پوچی) قفل هم برداشته میشود."
    )


def is_forbidden_item(name: str, effect: dict | None) -> bool:
    effect = effect or {}
    if effect.get("forbidden"):
        return True
    n = (name or "").strip()
    if n == FORBIDDEN_TEA_NAME:
        return True
    return False
