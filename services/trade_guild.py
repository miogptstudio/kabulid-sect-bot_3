"""گروه بازرگانی — چند نفر با هم"""
from datetime import datetime

_guilds: dict[str, dict] = {}
_member: dict[int, str] = {}
_counter = 500


def create(tg_id: int, name: str, uname: str) -> str:
    global _counter
    if tg_id in _member:
        return "عضو گروه بازرگانی هستی."
    name = name.strip()[:32]
    if not name:
        return "نام گروه را بنویس: /tradeguild نام"
    for g in _guilds.values():
        if g["name"] == name:
            return "نام تکراری."
    _counter += 1
    gid = f"g{_counter}"
    _guilds[gid] = {
        "name": name,
        "leader": tg_id,
        "leader_name": uname,
        "members": [tg_id],
        "vault_coins": 0,
        "created": datetime.utcnow().isoformat(),
    }
    _member[tg_id] = gid
    return (
        f"🛒 گروه بازرگانی «<b>{name}</b>» ساخته شد." + chr(10)
        + "تو رهبر هستی." + chr(10)
        + "/tradeinvite (ریپلای) · /tradevault · /tradedeposit مبلغ"
    )


def join(tg_id: int, name: str) -> str:
    if tg_id in _member:
        return "قبلاً عضو گروهی."
    for gid, g in _guilds.items():
        if g["name"] == name.strip():
            g["members"].append(tg_id)
            _member[tg_id] = gid
            return f"وارد «{g['name']}» شدی."
    return "گروه پیدا نشد. /tradelist"


def leave(tg_id: int) -> str:
    gid = _member.pop(tg_id, None)
    if not gid or gid not in _guilds:
        return "عضو نیستی."
    g = _guilds[gid]
    if tg_id in g["members"]:
        g["members"].remove(tg_id)
    if not g["members"]:
        del _guilds[gid]
        return "گروه منحل شد."
    if g["leader"] == tg_id:
        g["leader"] = g["members"][0]
    return "خارج شدی."


def info(tg_id: int) -> str:
    gid = _member.get(tg_id)
    if not gid:
        return "گروه نداری. /tradeguild نام"
    g = _guilds[gid]
    return (
        f"🛒 <b>{g['name']}</b>" + chr(10)
        + f"رهبر: {g['leader_name']}" + chr(10)
        + f"اعضا: {len(g['members'])}" + chr(10)
        + f"صندوق: {g['vault_coins']} سکه" + chr(10)
        + "/tradedeposit مبلغ · /tradewithdraw مبلغ"
    )


def list_all() -> str:
    if not _guilds:
        return "گروهی نیست. /tradeguild نام"
    lines = ["🛒 <b>گروه‌های بازرگانی</b>", ""]
    for g in _guilds.values():
        lines.append(f"• {g['name']} — {len(g['members'])} نفر | صندوق {g['vault_coins']}")
    return chr(10).join(lines)


def deposit(tg_id: int, amount: int) -> tuple[bool, str, int]:
    gid = _member.get(tg_id)
    if not gid:
        return False, "عضو گروه نیستی.", 0
    if amount <= 0:
        return False, "مبلغ نامعتبر.", 0
    return True, gid, amount


def do_deposit(tg_id: int, amount: int):
    gid = _member[tg_id]
    _guilds[gid]["vault_coins"] += amount


def withdraw(tg_id: int, amount: int) -> tuple[bool, str]:
    gid = _member.get(tg_id)
    if not gid:
        return False, "عضو نیستی."
    g = _guilds[gid]
    if tg_id != g["leader"]:
        return False, "فقط رهبر برداشت می‌کند."
    if amount <= 0 or amount > g["vault_coins"]:
        return False, "موجودی کافی نیست."
    g["vault_coins"] -= amount
    return True, f"✅ {amount} سکه از صندوق برداشت شد."
