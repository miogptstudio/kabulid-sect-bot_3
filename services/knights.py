"""شوالیهها — محافظت از بازیکن/فرقه"""
from __future__ import annotations
from services.persist import PersistentMap, save as _psave

KNIGHTS = [
    {"id": 1, "name": "شوالیه آهنی", "price": 2000, "protect": 15},
    {"id": 2, "name": "شوالیه نقرهای", "price": 8000, "protect": 30},
    {"id": 3, "name": "شوالیه طلایی", "price": 25000, "protect": 50},
    {"id": 4, "name": "شوالیه اژدها", "price": 80000, "protect": 75},
    {"id": 5, "name": "شوالیه بهشتی", "price": 200000, "protect": 90},
]

_owned = PersistentMap("knights_owned")  # tg -> list[int]


def list_text() -> str:
    lines = ["⚔️ <b>شوالیهها (محافظت)</b>", ""]
    for k in KNIGHTS:
        lines.append(f"{k['id']}. {k['name']} — {k['price']} سکه | محافظت {k['protect']}٪")
    lines += ["", "/buyknight شماره", "/myknights"]
    return chr(10).join(lines)


def protect_percent(tg: int) -> int:
    ids = list(_owned.get(int(tg), []) or [])
    total = 0
    for k in KNIGHTS:
        if k["id"] in ids:
            total += k["protect"]
    return min(95, total)


def buy(tg: int, kid: int, coins: int) -> tuple[bool, str, int]:
    k = next((x for x in KNIGHTS if x["id"] == kid), None)
    if not k:
        return False, "شوالیه پیدا نشد.", coins
    ids = list(_owned.get(int(tg), []) or [])
    if kid in ids:
        return False, "قبلاً این شوالیه را داری.", coins
    if coins < k["price"]:
        return False, "سکه کافی نیست.", coins
    ids.append(kid)
    _owned[int(tg)] = ids
    return True, f"✅ {k['name']} استخدام شد. محافظت کل: {protect_percent(tg)}٪", coins - k["price"]


def my_knights(tg: int) -> str:
    ids = list(_owned.get(int(tg), []) or [])
    if not ids:
        return "شوالیهای نداری. /knights"
    lines = ["⚔️ <b>شوالیههای تو</b>", ""]
    for k in KNIGHTS:
        if k["id"] in ids:
            lines.append(f"• {k['name']} ({k['protect']}٪)")
    lines.append(f"محافظت کل: {protect_percent(tg)}٪")
    return chr(10).join(lines)
