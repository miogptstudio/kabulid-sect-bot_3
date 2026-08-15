"""معدن سنگ روح — خرید و ارتقای روزانه — پایدار"""
from datetime import datetime, date
from services.persist import get_dict, save as _psave

BUY_COST = 50
BASE_YIELD = 2


def _map() -> dict:
    return get_dict("spirit_mine")


def get_mine(tg_id: int) -> dict | None:
    return _map().get(str(int(tg_id)))


def buy_mine(tg_id: int, spirit: int) -> tuple[bool, str, int]:
    m = _map()
    sk = str(int(tg_id))
    if sk in m:
        return False, "قبلاً معدن داری. /mine /claimmine /upgrademine", spirit
    if spirit < BUY_COST:
        return False, f"نیاز به {BUY_COST} سنگ روحی برای خرید معدن.", spirit
    m[sk] = {
        "level": 1,
        "last_claim": None,
        "last_upgrade": None,
        "bought": datetime.utcnow().isoformat(),
    }
    _psave("spirit_mine")
    msg = (
        f"✅ معدن سنگ روح خریداری شد (−{BUY_COST} سنگ روحی)."
        + chr(10) + "روزانه با /claimmine برداشت کن."
    )
    return True, msg, spirit - BUY_COST


def claim(tg_id: int) -> tuple[bool, str, int]:
    m = _map()
    sk = str(int(tg_id))
    mine = m.get(sk)
    if not mine:
        return False, "معدن نداری. /buymine", 0
    today = date.today().isoformat()
    if mine.get("last_claim") == today:
        return False, "امروز برداشت کردی. فردا دوباره /claimmine", 0
    amount = BASE_YIELD * int(mine.get("level", 1))
    mine["last_claim"] = today
    _psave("spirit_mine")
    return True, f"⛏ +{amount} سنگ روحی از معدن (سطح {mine['level']})", amount


def upgrade(tg_id: int, spirit: int) -> tuple[bool, str, int]:
    m = _map()
    sk = str(int(tg_id))
    mine = m.get(sk)
    if not mine:
        return False, "معدن نداری. /buymine", spirit
    today = date.today().isoformat()
    if mine.get("last_upgrade") == today:
        return False, "امروز یکبار ارتقا دادی. فردا دوباره.", spirit
    lvl = int(mine.get("level", 1))
    cost = 20 + lvl * 15
    if spirit < cost:
        return False, f"نیاز به {cost} سنگ روحی برای ارتقا به سطح {lvl+1}.", spirit
    mine["level"] = lvl + 1
    mine["last_upgrade"] = today
    _psave("spirit_mine")
    y = BASE_YIELD * mine["level"]
    msg = (
        f"⬆ معدن به سطح {mine['level']} ارتقا یافت (−{cost} سنگ)."
        + chr(10) + f"برداشت روزانه: {y}"
    )
    return True, msg, spirit - cost


def status(tg_id: int) -> str:
    mine = get_mine(tg_id)
    if not mine:
        return "⛏ معدن نداری." + chr(10) + f"خرید: /buymine ({BUY_COST} سنگ روحی)"
    y = BASE_YIELD * int(mine["level"])
    cost = 20 + int(mine["level"]) * 15
    return (
        f"⛏ <b>معدن سنگ روح</b>" + chr(10)
        + f"سطح: {mine['level']}" + chr(10)
        + f"برداشت روزانه: {y} سنگ روحی" + chr(10)
        + f"آخرین برداشت: {mine.get('last_claim') or '—'}" + chr(10)
        + f"هزینه ارتقا بعدی: {cost} سنگ" + chr(10)
        + "/claimmine — برداشت | /upgrademine — ارتقا"
    )
