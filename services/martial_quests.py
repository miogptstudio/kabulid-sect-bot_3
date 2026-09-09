"""مأموریت‌های روزانه جهان رزمی"""
from __future__ import annotations
from datetime import datetime
import random
from services.persist import get_dict, save

QUEST_POOL = [
    {"id": "duel1", "name": "یک دوئل پیروز", "desc": "یک دوئل ببر", "target": 1, "stat": "duels_won", "reward_coins": 800, "reward_xp": 50},
    {"id": "duel3", "name": "سه دوئل", "desc": "۳ دوئل انجام بده (برد یا باخت)", "target": 3, "stat": "duels_done", "reward_coins": 1500, "reward_xp": 80},
    {"id": "cult", "name": "تذهیب روزانه", "desc": "۵۰۰۰ انرژی تذهیب جذب کن", "target": 5000, "stat": "energy_gained", "reward_coins": 1000, "reward_xp": 100},
    {"id": "travel", "name": "گشت در جهان", "desc": "۱۰ حرکت در جهان باز", "target": 10, "stat": "moves", "reward_coins": 600, "reward_xp": 40},
    {"id": "shop", "name": "خرید از بازار", "desc": "۲ آیتم بخر", "target": 2, "stat": "buys", "reward_coins": 500, "reward_xp": 30},
    {"id": "pill", "name": "مصرف ایمن", "desc": "۱ قرص بدون overdose مصرف کن", "target": 1, "stat": "pills", "reward_coins": 400, "reward_xp": 25},
    {"id": "arash", "name": "یاد آرش", "desc": "دستور /arash را یک‌بار بزن", "target": 1, "stat": "arash_view", "reward_coins": 300, "reward_xp": 20},
    {"id": "train", "name": "تمرین رزمی", "desc": "۲ بار تمرین یا مأموریت انجام بده", "target": 2, "stat": "trains", "reward_coins": 900, "reward_xp": 60},
]


def _day() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def _user(tg: int) -> dict:
    d = get_dict("martial_quests")
    k = str(int(tg))
    rec = d.get(k) or {}
    if rec.get("day") != _day():
        # سه مأموریت تصادفی روزانه
        picks = random.sample(QUEST_POOL, k=min(3, len(QUEST_POOL)))
        rec = {
            "day": _day(),
            "quests": [{"id": q["id"], "progress": 0, "done": False, "claimed": False} for q in picks],
            "picked": [q["id"] for q in picks],
        }
        d[k] = rec
        save("martial_quests")
    return rec


def _quest_def(qid: str) -> dict | None:
    for q in QUEST_POOL:
        if q["id"] == qid:
            return q
    return None


def status_text(tg: int) -> str:
    rec = _user(tg)
    lines = ["🗡️ <b>مأموریت‌های روزانه جهان رزمی</b>", f"📅 {_day()}", ""]
    for item in rec.get("quests") or []:
        q = _quest_def(item["id"])
        if not q:
            continue
        prog = int(item.get("progress") or 0)
        target = int(q["target"])
        if item.get("claimed"):
            mark = "✅ دریافت‌شده"
        elif item.get("done") or prog >= target:
            mark = "🎁 آماده دریافت — /claimquest"
        else:
            mark = f"⏳ {prog}/{target}"
        lines.append(f"• <b>{q['name']}</b> — {q['desc']}")
        lines.append(f"  {mark} | پاداش: {q['reward_coins']:,} سکه + {q['reward_xp']} XP")
    lines.append("\nپیشرفت خودکار با بازی ثبت می‌شود.")
    lines.append("/claimquest — دریافت پاداش‌های آماده")
    return "\n".join(lines)


def progress(tg: int, stat: str, amount: int = 1) -> None:
    rec = _user(tg)
    changed = False
    for item in rec.get("quests") or []:
        q = _quest_def(item["id"])
        if not q or q.get("stat") != stat:
            continue
        if item.get("claimed"):
            continue
        item["progress"] = int(item.get("progress") or 0) + int(amount)
        if item["progress"] >= int(q["target"]):
            item["done"] = True
        changed = True
    if changed:
        d = get_dict("martial_quests")
        d[str(int(tg))] = rec
        save("martial_quests")


def claim(tg: int) -> tuple[str, int, int]:
    """returns (message, coins, xp)"""
    rec = _user(tg)
    coins = xp = 0
    claimed_names = []
    for item in rec.get("quests") or []:
        q = _quest_def(item["id"])
        if not q:
            continue
        if item.get("claimed"):
            continue
        if item.get("done") or int(item.get("progress") or 0) >= int(q["target"]):
            item["claimed"] = True
            item["done"] = True
            coins += int(q["reward_coins"])
            xp += int(q["reward_xp"])
            claimed_names.append(q["name"])
    d = get_dict("martial_quests")
    d[str(int(tg))] = rec
    save("martial_quests")
    if not claimed_names:
        return "هنوز مأموریت آماده‌ای برای دریافت نداری.", 0, 0
    return (
        "✅ پاداش مأموریت‌ها:\n" + "\n".join(f"• {n}" for n in claimed_names)
        + f"\n💰 +{coins:,} سکه | ✨ +{xp} XP"
    ), coins, xp
