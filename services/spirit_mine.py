"""معدن سنگ روح — خرید و ارتقای روزانه"""
from datetime import datetime, date

_mines: dict[int, dict] = {}

BUY_COST = 50
BASE_YIELD = 2


def get_mine(tg_id: int) -> dict | None:
    return _mines.get(tg_id)


def buy_mine(tg_id: int, spirit: int) -> tuple[bool, str, int]:
    if tg_id in _mines:
        return False, "قبلاً معدن داری. /mine /claimmine /upgrademine", spirit
    if spirit < BUY_COST:
        return False, f"نیاز به {BUY_COST} سنگ روحی برای خرید معدن.", spirit
    _mines[tg_id] = {
        "level": 1,
        "last_claim": None,
        "last_upgrade": None,
        "bought": datetime.utcnow().isoformat(),
    }
    msg = (
        f"✅ معدن سنگ روح خریداری شد (−{BUY_COST} سنگ روحی)."
        + chr(10) + "روزانه با /claimmine برداشت کن."
    )
    return True, msg, spirit - BUY_COST


def claim(tg_id: int) -> tuple[bool, str, int]:
    m = _mines.get(tg_id)
    if not m:
        return False, "معدن نداری. /buymine", 0
    today = date.today().isoformat()
    if m.get("last_claim") == today:
        return False, "امروز برداشت کردی. فردا دوباره /claimmine", 0
    amount = BASE_YIELD * int(m.get("level", 1))
    m["last_claim"] = today
    return True, f"⛏ +{amount} سنگ روحی از معدن (سطح {m['level']})", amount


def upgrade(tg_id: int, spirit: int) -> tuple[bool, str, int]:
    m = _mines.get(tg_id)
    if not m:
        return False, "معدن نداری. /buymine", spirit
    today = date.today().isoformat()
    if m.get("last_upgrade") == today:
        return False, "امروز یک‌بار ارتقا دادی. فردا دوباره.", spirit
    lvl = int(m.get("level", 1))
    cost = 20 + lvl * 15
    if spirit < cost:
        return False, f"نیاز به {cost} سنگ روحی برای ارتقا به سطح {lvl+1}.", spirit
    m["level"] = lvl + 1
    m["last_upgrade"] = today
    y = BASE_YIELD * m["level"]
    msg = (
        f"⬆ معدن به سطح {m['level']} ارتقا یافت (−{cost} سنگ)."
        + chr(10) + f"برداشت روزانه: {y}"
    )
    return True, msg, spirit - cost


def status(tg_id: int) -> str:
    m = _mines.get(tg_id)
    if not m:
        return "⛏ معدن نداری." + chr(10) + f"خرید: /buymine ({BUY_COST} سنگ روحی)"
    y = BASE_YIELD * int(m["level"])
    cost = 20 + int(m["level"]) * 15
    return (
        f"⛏ <b>معدن سنگ روح</b>" + chr(10)
        + f"سطح: {m['level']}" + chr(10)
        + f"برداشت روزانه: {y} سنگ روحی" + chr(10)
        + f"آخرین برداشت: {m.get('last_claim') or '—'}" + chr(10)
        + f"هزینه ارتقا بعدی: {cost} سنگ" + chr(10)
        + "/claimmine — برداشت | /upgrademine — ارتقا"
    )
