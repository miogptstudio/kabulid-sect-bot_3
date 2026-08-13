"""ساختمان تذهیب شخصی — پایدار"""
from __future__ import annotations
from services.persist import get_dict, save as _psave

MAX_LEVEL = 20
BASE_COST = 500  # سکه


def _map() -> dict:
    return get_dict("cult_building")


def level(tg: int) -> int:
    return int(_map().get(str(int(tg)), 0) or 0)


def bonus_mult(tg: int) -> float:
    return 1.0 + level(tg) * 0.03


def upgrade_cost(tg: int) -> int:
    lv = level(tg)
    return int(BASE_COST * (1.6 ** lv))


def upgrade(tg: int) -> tuple[int, int]:
    """returns new_level, cost — caller pays"""
    m = _map()
    sk = str(int(tg))
    lv = int(m.get(sk, 0) or 0)
    if lv >= MAX_LEVEL:
        return lv, 0
    cost = int(BASE_COST * (1.6 ** lv))
    m[sk] = lv + 1
    _psave("cult_building")
    return lv + 1, cost


def status(tg: int) -> str:
    lv = level(tg)
    return (
        f"🏛 <b>ساختمان تذهیب</b> سطح {lv}/{MAX_LEVEL}" + chr(10)
        + f"بونوس انرژی: +{int((bonus_mult(tg)-1)*100)}٪" + chr(10)
        + f"هزینه ارتقا: {upgrade_cost(tg):,} سکه" + chr(10)
        + "/upgradecultbuilding"
    )
