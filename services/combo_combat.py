"""سیستم کمبوی رزمی — تکنیک‌های زنجیره‌ای در دوئل"""
from __future__ import annotations
import random
from services.persist import get_dict, save

COMBOS = {
    "slash": {"name": "برش سه‌گانه", "mult": 1.25, "desc": "سه ضربه سریع", "need": 1},
    "thunder": {"name": "غرش رعد", "mult": 1.4, "desc": "نفوذ رعدآسا", "need": 2},
    "guard_break": {"name": "شکست دفاع", "mult": 1.35, "desc": "نادیده گرفتن بخشی از دفاع", "need": 2},
    "arash_shot": {"name": "تیر آرش", "mult": 1.6, "desc": "تیر بی‌خطا — نیاز کمان آرش", "need": 3, "need_arash": True},
    "void_pulse": {"name": "پالس پوچی", "mult": 1.7, "desc": "آسیب پوچی", "need": 4},
    "dragon_fury": {"name": "خشم اژدها", "mult": 1.8, "desc": "کمبوی نهایی", "need": 5},
}


def unlocked(tg: int) -> list[str]:
    d = get_dict("combos")
    base = ["slash"]
    owned = list((d.get(str(int(tg))) or {}).get("unlocked") or [])
    for c in base:
        if c not in owned:
            owned.append(c)
    return owned


def unlock(tg: int, combo_id: str) -> str:
    if combo_id not in COMBOS:
        return "کمبو نامعتبر"
    d = get_dict("combos")
    k = str(int(tg))
    row = d.get(k) or {"unlocked": ["slash"], "mastery": {}}
    u = list(row.get("unlocked") or [])
    if combo_id in u:
        return f"قبلاً «{COMBOS[combo_id]['name']}» را داری."
    u.append(combo_id)
    row["unlocked"] = u
    d[k] = row
    save("combos")
    return f"⚔️ کمبوی جدید: <b>{COMBOS[combo_id]['name']}</b>\n{COMBOS[combo_id]['desc']} (×{COMBOS[combo_id]['mult']})"


def try_combo(tg: int, has_arash: bool = False) -> dict | None:
    """شانس فعال‌سازی کمبو در دوئل"""
    owned = unlocked(tg)
    usable = []
    for cid in owned:
        info = COMBOS[cid]
        if info.get("need_arash") and not has_arash:
            continue
        usable.append(cid)
    if not usable:
        return None
    # شانس بر اساس تعداد کمبو
    chance = min(0.45, 0.12 + 0.05 * len(usable))
    if random.random() > chance:
        return None
    # وزن به سمت کمبوهای قوی‌تر کمی کمتر
    weights = [max(1, 6 - COMBOS[c].get("need", 1)) for c in usable]
    pick = random.choices(usable, weights=weights, k=1)[0]
    info = COMBOS[pick]
    # mastery
    d = get_dict("combos")
    k = str(int(tg))
    row = d.get(k) or {"unlocked": owned, "mastery": {}}
    mastery = dict(row.get("mastery") or {})
    mastery[pick] = int(mastery.get(pick) or 0) + 1
    row["mastery"] = mastery
    d[k] = row
    save("combos")
    bonus = min(0.15, mastery[pick] * 0.01)
    return {
        "id": pick,
        "name": info["name"],
        "mult": float(info["mult"]) + bonus,
        "desc": info["desc"],
        "mastery": mastery[pick],
    }


def status_text(tg: int) -> str:
    owned = unlocked(tg)
    d = get_dict("combos")
    mastery = ((d.get(str(int(tg))) or {}).get("mastery") or {})
    lines = ["⚔️ <b>کمبوهای رزمی</b>", ""]
    for cid, info in COMBOS.items():
        if cid in owned:
            m = int(mastery.get(cid) or 0)
            lines.append(f"✅ <b>{info['name']}</b> ×{info['mult']} — مهارت {m}")
            lines.append(f"   {info['desc']}")
        else:
            lines.append(f"🔒 {info['name']} (نیاز پیشرفت {info['need']})")
    lines.append("\nکمبوها در دوئل به‌صورت تصادفی فعال می‌شوند.")
    lines.append("با برد دوئل و سیاه‌چال کمبوهای جدید باز می‌شوند.")
    return "\n".join(lines)


def unlock_by_progress(tg: int, *, duels_won: int = 0, dungeon_floor: int = 0) -> list[str]:
    msgs = []
    if duels_won >= 3:
        r = unlock(tg, "thunder")
        if "جدید" in r:
            msgs.append(r)
    if duels_won >= 5:
        r = unlock(tg, "guard_break")
        if "جدید" in r:
            msgs.append(r)
    if dungeon_floor >= 3:
        r = unlock(tg, "arash_shot")
        if "جدید" in r:
            msgs.append(r)
    if dungeon_floor >= 5:
        r = unlock(tg, "void_pulse")
        if "جدید" in r:
            msgs.append(r)
    if dungeon_floor >= 8 or duels_won >= 20:
        r = unlock(tg, "dragon_fury")
        if "جدید" in r:
            msgs.append(r)
    return msgs
