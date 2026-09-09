"""القاب جهان رزمی — بر اساس دستاورد"""
from __future__ import annotations
from services.persist import get_dict, save

TITLES = {
    "novice": {"name": "نوآموز دشت", "desc": "ورود به جهان رزمی"},
    "duelist": {"name": "جنگجوی دره", "desc": "۱۰ دوئل پیروز"},
    "arash_heir": {"name": "وارث آرش", "desc": "مالک کمان آرش"},
    "sky_walker": {"name": "پیاده‌روی آسمان", "desc": "صعود به آسمان ۲+"},
    "sect_leader": {"name": "رهبر فرقه", "desc": "رهبری یک فرقه فعال"},
    "quest_master": {"name": "کارگزار مأموریت", "desc": "۱۰ مأموریت روزانه"},
    "void_touched": {"name": "لمس‌شده پوچی", "desc": "بازدید دروازه پوچی"},
    "dragon_blood": {"name": "خون اژدها", "desc": "تبار اژدهایی"},
    "legend": {"name": "افسانه جهان رزمی", "desc": "قدرت بسیار بالا"},
}


def get_titles(tg: int) -> list[str]:
    d = get_dict("titles")
    return list((d.get(str(int(tg))) or {}).get("owned") or [])


def active_title(tg: int) -> str | None:
    d = get_dict("titles")
    return (d.get(str(int(tg))) or {}).get("active")


def grant(tg: int, title_id: str) -> bool:
    if title_id not in TITLES:
        return False
    d = get_dict("titles")
    k = str(int(tg))
    row = d.get(k) or {"owned": [], "active": None}
    owned = list(row.get("owned") or [])
    if title_id not in owned:
        owned.append(title_id)
        row["owned"] = owned
        if not row.get("active"):
            row["active"] = title_id
        d[k] = row
        save("titles")
        return True
    return False


def set_active(tg: int, title_id: str) -> str:
    d = get_dict("titles")
    k = str(int(tg))
    row = d.get(k) or {"owned": [], "active": None}
    if title_id not in (row.get("owned") or []):
        return "این لقب را نداری."
    row["active"] = title_id
    d[k] = row
    save("titles")
    return f"لقب فعال: <b>{TITLES[title_id]['name']}</b>"


def status_text(tg: int) -> str:
    owned = get_titles(tg)
    act = active_title(tg)
    lines = ["🏅 <b>القاب جهان رزمی</b>", ""]
    if not owned:
        lines.append("هنوز لقبی نداری. با پیشرفت باز می‌شوند.")
    else:
        for tid in owned:
            info = TITLES.get(tid, {})
            mark = " ✅" if tid == act else ""
            lines.append(f"• {info.get('name', tid)}{mark} — {info.get('desc', '')}")
    lines.append("\n/settitle شناسه — فعال‌سازی")
    lines.append("شناسه‌ها: " + ", ".join(TITLES.keys()))
    return "\n".join(lines)


def auto_check(tg: int, *, duels_won: int = 0, power: int = 0, sky: int = 1, has_arash: bool = False) -> list[str]:
    new = []
    if grant(tg, "novice"):
        new.append(TITLES["novice"]["name"])
    if duels_won >= 10 and grant(tg, "duelist"):
        new.append(TITLES["duelist"]["name"])
    if has_arash and grant(tg, "arash_heir"):
        new.append(TITLES["arash_heir"]["name"])
    if sky >= 2 and grant(tg, "sky_walker"):
        new.append(TITLES["sky_walker"]["name"])
    if power >= 5000 and grant(tg, "legend"):
        new.append(TITLES["legend"]["name"])
    return new
