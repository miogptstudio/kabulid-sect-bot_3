"""سیستم خانه‌سازی"""
from __future__ import annotations

# tg_id -> home dict
from services.persist import get_dict, save as _psave
def _homes_map():
    return get_dict("housing")


LEVELS = {
    0: {"name": "بی‌خانمان", "slots": 0, "bonus": 0},
    1: {"name": "کلبه چوبی", "slots": 2, "bonus": 0.02},
    2: {"name": "خانه سنگی", "slots": 4, "bonus": 0.05},
    3: {"name": "ویلای فرقه", "slots": 6, "bonus": 0.08},
    4: {"name": "عمارت روحی", "slots": 8, "bonus": 0.12},
    5: {"name": "قصر آسمانی", "slots": 12, "bonus": 0.18},
    6: {"name": "کاخ خدایان", "slots": 20, "bonus": 0.25},
}

# هزینه ارتقا به سطح n (سکه معادل)
UPGRADE_COST = {
    1: 2000,
    2: 10000,
    3: 50000,
    4: 200000,
    5: 1000000,
    6: 5000000,
}


def get_home(tg: int) -> dict:
    m = _homes_map(); sk = str(int(tg))
    h = m.get(sk)
    if not h:
        h = {"level": 0, "name": LEVELS[0]["name"], "furniture": []}
        m[sk] = h
        _psave("housing")
    return h


def status(tg: int) -> str:
    h = get_home(tg)
    lv = int(h.get("level") or 0)
    info = LEVELS.get(lv, LEVELS[0])
    lines = [
        f"🏠 <b>خانه</b>: {info['name']} (سطح {lv})",
        f"📦 ظرفیت وسایل: {info['slots']}",
        f"✨ بونوس تذهیب خانه: +{int(info['bonus']*100)}٪",
        "",
    ]
    furn = h.get("furniture") or []
    if furn:
        lines.append("وسایل: " + "، ".join(furn[:20]))
    else:
        lines.append("وسایلی نداری.")
    if lv < max(LEVELS):
        nxt = lv + 1
        lines += ["", f"ارتقا به {LEVELS[nxt]['name']}: {UPGRADE_COST.get(nxt, 0):,} سکه (یا معادل)", "/upgradehome"]
    lines += ["", "/buyfurniture نام — خرید وسیله ساده", "/myhome"]
    return chr(10).join(lines)


async def upgrade(session, user_id: int, tg: int) -> str:
    h = get_home(tg)
    lv = int(h.get("level") or 0)
    if lv >= max(LEVELS):
        return "خانه در حداکثر سطح است."
    nxt = lv + 1
    cost = UPGRADE_COST.get(nxt, 999999999)
    from services.economy import get_or_create_wallet, pay_any_currency
    w = await get_or_create_wallet(session, user_id)
    ok, msg = pay_any_currency(w, cost)
    if not ok:
        return msg
    h["level"] = nxt
    h["name"] = LEVELS[nxt]["name"]
    _psave("housing")
    await session.commit()
    return f"✅ خانه ارتقا یافت → <b>{LEVELS[nxt]['name']}</b>" + chr(10) + msg


FURNITURE_SHOP = {
    "تخت": 500,
    "میز": 300,
    "قفسه کتاب": 800,
    "باغچه": 1200,
    "محراب تذهیب": 5000,
    "چراغ روح": 2500,
    "حفاظ شوالیه": 4000,
}


def buy_furniture(tg: int, name: str) -> tuple[bool, int, str]:
    """returns ok, cost, message — caller pays"""
    name = name.strip()
    if name not in FURNITURE_SHOP:
        return False, 0, "وسایل: " + "، ".join(FURNITURE_SHOP.keys())
    h = get_home(tg)
    lv = int(h.get("level") or 0)
    slots = LEVELS.get(lv, LEVELS[0])["slots"]
    furn = h.setdefault("furniture", [])
    if len(furn) >= slots:
        return False, 0, f"ظرفیت پر است ({slots}). اول خانه را ارتقا بده."
    cost = FURNITURE_SHOP[name]
    furn.append(name)
    _psave("housing")
    return True, cost, f"✅ «{name}» به خانه اضافه شد."


def cult_bonus(tg: int) -> float:
    h = get_home(tg)
    lv = int(h.get("level") or 0)
    return 1.0 + float(LEVELS.get(lv, LEVELS[0])["bonus"])
