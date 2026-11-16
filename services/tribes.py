"""سیستم چندقبیلهای — بنیانگذار، بزرگ، جد"""
from datetime import datetime

# tribe_id -> data
_tribes: dict[str, dict] = {}
_member: dict[int, str] = {}  # tg_id -> tribe_id
_counter = 1000


def create_tribe(tg_id: int, name: str, founder_name: str) -> str:
    global _counter
    if tg_id in _member:
        return "قبلاً عضو قبیلهای."
    name = name.strip()[:32]
    if not name:
        return "نام قبیله را بنویس."
    for t in _tribes.values():
        if t["name"] == name:
            return "این نام گرفته شده."
    _counter += 1
    tid = f"t{_counter}"
    _tribes[tid] = {
        "name": name,
        "founder_id": tg_id,  # بنیانگذار
        "chief_id": tg_id,    # بزرگ قبیله
        "ancestor_id": tg_id, # جد قبیله (اولین بنیانگذار — ثابت)
        "founder_name": founder_name,
        "members": [tg_id],
        "created": datetime.utcnow().isoformat(),
        "points": 0,
    }
    _member[tg_id] = tid
    return (
        f"🏛 قبیله «<b>{name}</b>» تأسیس شد." + chr(10)
        + "تو: بنیانگذار · بزرگ قبیله · جد قبیله" + chr(10)
        + "/tribe · /tribeinvite (ریپلای) · /tribeleave"
    )


def join_tribe(tg_id: int, tribe_name: str) -> str:
    if tg_id in _member:
        return "عضو قبیله دیگری هستی. /tribeleave"
    tid = None
    for k, v in _tribes.items():
        if v["name"] == tribe_name.strip():
            tid = k
            break
    if not tid:
        return "قبیله پیدا نشد. /tribes"
    _tribes[tid]["members"].append(tg_id)
    _member[tg_id] = tid
    return f"وارد قبیله «{_tribes[tid]['name']}» شدی."


def leave(tg_id: int) -> str:
    tid = _member.pop(tg_id, None)
    if not tid or tid not in _tribes:
        return "عضو قبیله نیستی."
    t = _tribes[tid]
    if tg_id in t["members"]:
        t["members"].remove(tg_id)
    if tg_id == t["chief_id"] and t["members"]:
        t["chief_id"] = t["members"][0]
    if not t["members"]:
        del _tribes[tid]
        return "قبیله منحل شد (آخرین عضو)."
    return "از قبیله خارج شدی."


def set_chief(tg_id: int, new_chief_tg: int) -> str:
    tid = _member.get(tg_id)
    if not tid:
        return "قبیله نداری."
    t = _tribes[tid]
    if tg_id not in (t["founder_id"], t["chief_id"]):
        return "فقط بنیانگذار یا بزرگ قبیله."
    if new_chief_tg not in t["members"]:
        return "او عضو قبیله نیست."
    t["chief_id"] = new_chief_tg
    return "بزرگ قبیله جدید تعیین شد."


def info(tg_id: int) -> str:
    tid = _member.get(tg_id)
    if not tid:
        return "عضو قبیله نیستی. /createtribe نام | /tribes"
    t = _tribes[tid]
    role = []
    if tg_id == t["ancestor_id"]:
        role.append("جد قبیله")
    if tg_id == t["founder_id"]:
        role.append("بنیانگذار")
    if tg_id == t["chief_id"]:
        role.append("بزرگ قبیله")
    if not role:
        role.append("عضو")
    return (
        f"🏛 <b>{t['name']}</b>" + chr(10)
        + f"نقش تو: {', '.join(role)}" + chr(10)
        + f"اعضا: {len(t['members'])}" + chr(10)
        + f"امتیاز: {t['points']}" + chr(10)
        + f"جد: {t.get('founder_name', '—')}"
    )


def list_tribes() -> str:
    if not _tribes:
        return "قبیلهای نیست. /createtribe نام"
    lines = ["🏛 <b>قبایل</b>", ""]
    for t in sorted(_tribes.values(), key=lambda x: -x["points"]):
        lines.append(f"• {t['name']} — {len(t['members'])} نفر | {t['points']} امتیاز")
    lines.append("")
    lines.append("/jointribe نام")
    return chr(10).join(lines)
