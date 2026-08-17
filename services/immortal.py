"""نامیرایی با دستور ادمین — بر اساس telegram id"""
from services.persist import get_dict, save as _psave

def _data() -> dict:
    return get_dict("immortal_users")

def is_immortal_tg(telegram_id: int) -> bool:
    d = _data()
    return str(int(telegram_id)) in d

def is_immortal_user(user) -> bool:
    try:
        tid = int(getattr(user, "telegram_id", 0) or 0)
        if tid and is_immortal_tg(tid):
            return True
    except Exception:
        pass
    return False

def set_immortal(telegram_id: int, on: bool = True, by: int | None = None) -> str:
    d = _data()
    key = str(int(telegram_id))
    if on:
        d[key] = {"by": by, "on": True}
        _psave("immortal_users")
        return f"✅ کاربر <code>{telegram_id}</code> نامیرا شد."
    else:
        d.pop(key, None)
        _psave("immortal_users")
        return f"✅ نامیرایی کاربر <code>{telegram_id}</code> برداشته شد."

def list_immortals() -> str:
    d = _data()
    if not d:
        return "لیست نامیراها خالی است."
    lines = ["🛡️ <b>نامیراها</b>", ""]
    for k in sorted(d.keys()):
        lines.append(f"• <code>{k}</code>")
    return "\n".join(lines)
