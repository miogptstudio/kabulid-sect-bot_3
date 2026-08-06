"""ساختمان تزکیه — ارتقا با ارز بازی"""
from __future__ import annotations

# tg_id -> level
_levels: dict[int, int] = {}
MAX_LV = 20
# هزینه هر سطح به سکه (تقریبی) — ارز بالاتر هم قبول
BASE_COST = 5000


def level(tg_id: int) -> int:
    return int(_levels.get(tg_id, 0))


def cost_for(next_lv: int) -> int:
    return BASE_COST * (next_lv ** 2)


def bonus_mult(tg_id: int) -> float:
    return 1.0 + level(tg_id) * 0.08


def status(tg_id: int) -> str:
    lv = level(tg_id)
    nxt = lv + 1
    if lv >= MAX_LV:
        return f"🏛 ساختمان تزکیه سطح {lv}/{MAX_LV} (حداکثر)" + chr(10) + f"ضریب چی: ×{bonus_mult(tg_id):.2f}"
    return (
        f"🏛 <b>ساختمان تزکیه</b> سطح {lv}/{MAX_LV}" + chr(10)
        + f"ضریب جذب چی: ×{bonus_mult(tg_id):.2f}" + chr(10)
        + f"ارتقا به {nxt}: {cost_for(nxt)} سکه (یا معادل)" + chr(10)
        + "/upgradecultbuilding"
    )


async def upgrade(session, user_id: int, tg_id: int) -> str:
    lv = level(tg_id)
    if lv >= MAX_LV:
        return "ساختمان در حداکثر سطح است."
    from services.economy import get_or_create_wallet, pay_any_currency
    w = await get_or_create_wallet(session, user_id)
    cost = cost_for(lv + 1)
    ok, msg = pay_any_currency(w, cost)
    if not ok:
        return msg
    _levels[tg_id] = lv + 1
    await session.commit()
    return (
        f"✅ ساختمان تزکیه → سطح {_levels[tg_id]}" + chr(10)
        + f"ضریب چی: ×{bonus_mult(tg_id):.2f}" + chr(10)
        + msg
    )
