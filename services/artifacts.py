"""آرتیفکت‌های افسانه‌ای جهان رزمی"""
from __future__ import annotations
import random
from services.persist import get_dict, save

ARTIFACTS = {
    "blade_origin": {
        "name": "تیغ خاستگاه", "rarity": "نادر", "power": 40,
        "desc": "اولین تیغی که در دشت آغازین ساخته شد.", "slot": "weapon",
    },
    "bow_arash_shard": {
        "name": "تکه کمان آرش", "rarity": "حماسی", "power": 80,
        "desc": "قطعه‌ای از کمان افسانه‌ای — قدرت تیر.", "slot": "weapon",
    },
    "seal_of_nine": {
        "name": "مهر نه‌گانه", "rarity": "حماسی", "power": 70,
        "desc": "طلسم محافظ مسیر ۹ آسمان.", "slot": "talisman",
    },
    "dragon_scale_armor": {
        "name": "زره فلس اژدها", "rarity": "افسانه‌ای", "power": 120,
        "desc": "دفاع افسانه‌ای دشت اژدها.", "slot": "armor",
    },
    "void_core": {
        "name": "هسته پوچی", "rarity": "افسانه‌ای", "power": 150,
        "desc": "قطعه‌ای از مرز جهان — خطرناک و قدرتمند.", "slot": "core",
    },
    "crown_fragment": {
        "name": "تکه تاج خالق", "rarity": "اساطیری", "power": 250,
        "desc": "فقط جنگجویان طبقه ۱۰ سیاه‌چال شانس دارند.", "slot": "relic",
    },
    "thunder_ring": {
        "name": "حلقه رعد", "rarity": "نادر", "power": 35,
        "desc": "سرعت عمل در دوئل.", "slot": "ring",
    },
    "spirit_lantern": {
        "name": "فانوس روح", "rarity": "نادر", "power": 30,
        "desc": "تذهیب شبانه قوی‌تر.", "slot": "tool",
    },
}

DROP_WEIGHTS = {
    "blade_origin": 20,
    "thunder_ring": 18,
    "spirit_lantern": 18,
    "bow_arash_shard": 8,
    "seal_of_nine": 8,
    "dragon_scale_armor": 4,
    "void_core": 3,
    "crown_fragment": 1,
}


def inventory(tg: int) -> list[str]:
    d = get_dict("artifacts")
    return list((d.get(str(int(tg))) or {}).get("owned") or [])


def equipped(tg: int) -> dict:
    d = get_dict("artifacts")
    return dict((d.get(str(int(tg))) or {}).get("eq") or {})


def power_bonus(tg: int) -> int:
    eq = equipped(tg)
    total = 0
    for aid in eq.values():
        info = ARTIFACTS.get(aid)
        if info:
            total += int(info["power"])
    return total


def grant(tg: int, artifact_id: str) -> str:
    if artifact_id not in ARTIFACTS:
        return "آرتیفکت نامعتبر"
    d = get_dict("artifacts")
    k = str(int(tg))
    row = d.get(k) or {"owned": [], "eq": {}}
    owned = list(row.get("owned") or [])
    if artifact_id in owned:
        return f"قبلاً «{ARTIFACTS[artifact_id]['name']}» را داری."
    owned.append(artifact_id)
    row["owned"] = owned
    d[k] = row
    save("artifacts")
    info = ARTIFACTS[artifact_id]
    return f"✨ آرتیفکت جدید: <b>{info['name']}</b> ({info['rarity']})\n{info['desc']}\nقدرت +{info['power']}\n/artifacts"


def try_drop(tg: int, luck: float = 1.0) -> str | None:
    """شانس دراپ بعد از سیاه‌چال/ایونت"""
    if random.random() > min(0.35, 0.08 * luck):
        return None
    ids = list(DROP_WEIGHTS.keys())
    weights = [DROP_WEIGHTS[i] for i in ids]
    pick = random.choices(ids, weights=weights, k=1)[0]
    owned = inventory(tg)
    if pick in owned:
        return None
    return grant(tg, pick)


def equip(tg: int, artifact_id: str) -> str:
    if artifact_id not in inventory(tg):
        return "این آرتیفکت را نداری."
    info = ARTIFACTS.get(artifact_id)
    if not info:
        return "نامعتبر"
    d = get_dict("artifacts")
    k = str(int(tg))
    row = d.get(k) or {"owned": [], "eq": {}}
    eq = dict(row.get("eq") or {})
    eq[info["slot"]] = artifact_id
    row["eq"] = eq
    d[k] = row
    save("artifacts")
    return f"✅ مجهز شد: <b>{info['name']}</b> (اسلات {info['slot']}) | قدرت آرتیفکت کل: +{power_bonus(tg)}"


def status_text(tg: int) -> str:
    owned = inventory(tg)
    eq = equipped(tg)
    lines = ["💎 <b>آرتیفکت‌های جهان رزمی</b>", f"قدرت کل آرتیفکت: +{power_bonus(tg)}", ""]
    if not owned:
        lines.append("هنوز آرتیفکتی نداری. از سیاه‌چال و ایونت‌ها شانس دراپ داری.")
    else:
        for aid in owned:
            info = ARTIFACTS.get(aid, {})
            equipped_mark = ""
            for slot, eid in eq.items():
                if eid == aid:
                    equipped_mark = f" [مجهز:{slot}]"
                    break
            lines.append(
                f"• <b>{info.get('name', aid)}</b> ({info.get('rarity')}) "
                f"+{info.get('power', 0)}{equipped_mark}"
            )
            lines.append(f"  {info.get('desc', '')}")
    lines.append("\n/equipartifact شناسه — تجهیز")
    lines.append("شناسه‌ها: " + ", ".join(ARTIFACTS.keys()))
    return "\n".join(lines)
