"""جنگ قبایل"""
import random
from datetime import datetime, timedelta
from services import tribes as T

_wars: dict[str, dict] = {}
_last_declare: dict[int, datetime] = {}


def declare(attacker_tg: int, target_tribe_name: str) -> str:
    tid = T._member.get(attacker_tg)
    if not tid or tid not in T._tribes:
        return "اول عضو قبیله شو. /createtribe یا /jointribe"
    me = T._tribes[tid]
    if attacker_tg not in (me["chief_id"], me["founder_id"]):
        return "فقط بزرگ یا بنیانگذار میتواند جنگ اعلام کند."
    now = datetime.utcnow()
    last = _last_declare.get(attacker_tg)
    if last and now - last < timedelta(hours=6):
        return "هر ۶ ساعت یکبار اعلام جنگ."
    target = None
    for k, v in T._tribes.items():
        if v["name"] == target_tribe_name.strip() and k != tid:
            target = k
            break
    if not target:
        return "قبیله هدف پیدا نشد. /tribes"
    war_id = f"{tid}_{target}_{int(now.timestamp())}"
    _wars[war_id] = {
        "a": tid, "b": target, "start": now.isoformat(),
        "score_a": 0, "score_b": 0, "ends": (now + timedelta(hours=12)).isoformat(),
    }
    _last_declare[attacker_tg] = now
    return (
        f"⚔️ جنگ قبایل اعلام شد!" + chr(10)
        + f"{me['name']} vs {T._tribes[target]['name']}" + chr(10)
        + "مدت: ۱۲ ساعت | /tribewarfight — شرکت در نبرد" + chr(10)
        + f"/tribewar — وضعیت"
    )


def status(tg_id: int) -> str:
    tid = T._member.get(tg_id)
    active = [w for w in _wars.values() if tid in (w["a"], w["b"])]
    if not active:
        return "جنگ فعالی نیست. /declarewar نامقبیله"
    lines = ["⚔️ <b>جنگهای فعال</b>", ""]
    for w in active:
        na = T._tribes.get(w["a"], {}).get("name", "?")
        nb = T._tribes.get(w["b"], {}).get("name", "?")
        lines.append(f"{na} {w['score_a']} — {w['score_b']} {nb}")
    return chr(10).join(lines)


def fight(tg_id: int) -> str:
    tid = T._member.get(tg_id)
    if not tid:
        return "عضو قبیله نیستی."
    war = next((w for w in _wars.values() if tid in (w["a"], w["b"])), None)
    if not war:
        return "جنگ فعالی نیست."
    # simple roll
    roll = random.randint(1, 100)
    if tid == war["a"]:
        if roll > 40:
            war["score_a"] += 1
            T._tribes[tid]["points"] = T._tribes[tid].get("points", 0) + 2
            return f"✅ ضربه قبیلهات +۱ | امتیاز {war['score_a']}—{war['score_b']}"
        return f"❌ این نبرد را باختید | {war['score_a']}—{war['score_b']}"
    else:
        if roll > 40:
            war["score_b"] += 1
            T._tribes[tid]["points"] = T._tribes[tid].get("points", 0) + 2
            return f"✅ ضربه قبیلهات +۱ | {war['score_a']}—{war['score_b']}"
        return f"❌ باخت | {war['score_a']}—{war['score_b']}"
