"""شمشیر نابودکننده جهان — نفوذ با هر قتل"""
from __future__ import annotations
from services.persist import get_dict, save as _psave

ITEM_NAME = "شمشیر نابودکننده جهان"
PRICE = 999_000_000_000
CURRENCY = "god"  # سنگ خدا  # ۹۹۹ میلیارد سنگ خدا
PEN_PER_KILL = 15
MAX_PEN = 5000


def _map() -> dict:
    return get_dict("world_blade_kills")


def kills(tg: int) -> int:
    return int(_map().get(str(int(tg)), 0) or 0)


def on_kill(tg: int) -> int:
    m = _map()
    sk = str(int(tg))
    m[sk] = kills(tg) + 1
    _psave("world_blade_kills")
    return int(m[sk])


def penetration_bonus(tg: int) -> int:
    return min(MAX_PEN, kills(tg) * PEN_PER_KILL)


def status(tg: int) -> str:
    k = kills(tg)
    return (
        f"🗡 <b>{ITEM_NAME}</b>" + chr(10)
        + f"قتلهای ثبتشده: {k}" + chr(10)
        + f"نفوذ فعلی: +{penetration_bonus(tg)}" + chr(10)
        + f"هر قتل +{PEN_PER_KILL} نفوذ (سقف {MAX_PEN})"
    )
