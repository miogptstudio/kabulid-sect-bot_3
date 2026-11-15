"""عکس پروفایل بازیکن — خدمتکار / کاراکتر / پیش‌فرض"""
from __future__ import annotations
from services.persist import get_dict, save as _psave

NS = "profile_avatars"


def _data() -> dict:
    return get_dict(NS)


def get_avatar(tg_id: int) -> dict | None:
    """{type: servant|character|default, index: int, name?: str} یا None=پیش‌فرض"""
    d = _data().get(str(int(tg_id)))
    if not d or not isinstance(d, dict):
        return None
    if d.get("type") in (None, "default", "none", "clear"):
        return None
    return d


def set_servant_avatar(tg_id: int, bag_index: int) -> tuple[bool, str]:
    """bag_index یک‌پایه از لیست خدمتکارهای بازیکن"""
    from services import servants as servmod
    bag = servmod.list_owned(int(tg_id))
    if bag_index < 1 or bag_index > len(bag):
        return False, "شماره خدمتکار نامعتبر است. از /myservants شماره را بردار."
    s = bag[bag_index - 1]
    _data()[str(int(tg_id))] = {
        "type": "servant",
        "index": int(bag_index),
        "base_id": int(s.get("base_id") or s.get("id") or 0),
        "name": s.get("name") or "خدمتکار",
        "gender": s.get("gender") or "",
        "race": s.get("race") or "",
    }
    _psave(NS)
    try:
        from services.persist import save_and_sync
        save_and_sync(NS)
    except Exception:
        pass
    return True, f"✅ عکس پروفایل روی خدمتکار «{s.get('name', '—')}» تنظیم شد.\nبرای برداشتن: /clearavatar یا «حذف عکس پروفایل»"


def set_character_avatar(tg_id: int, bag_index: int) -> tuple[bool, str]:
    from services import characters as chars
    card = chars.get_char(int(tg_id), int(bag_index))
    if not card:
        return False, "شماره کاراکتر نامعتبر است. /mychars"
    _data()[str(int(tg_id))] = {
        "type": "character",
        "index": int(bag_index),
        "name": card.get("name") or "کاراکتر",
        "rarity": card.get("rarity") or "",
    }
    _psave(NS)
    try:
        from services.persist import save_and_sync
        save_and_sync(NS)
    except Exception:
        pass
    return True, f"✅ عکس پروفایل روی کاراکتر «{card.get('name')}» تنظیم شد.\nبرای برداشتن: /clearavatar"


def clear_avatar(tg_id: int) -> str:
    d = _data()
    d.pop(str(int(tg_id)), None)
    _psave(NS)
    try:
        from services.persist import save_and_sync
        save_and_sync(NS)
    except Exception:
        pass
    return "✅ عکس پروفایل به حالت پیش‌فرض برگشت (عکس خدمتکار/کاراکتر برداشته شد)."


def status_text(tg_id: int) -> str:
    av = get_avatar(tg_id)
    if not av:
        return "🖼 عکس پروفایل: <b>پیش‌فرض</b>\nبا /setavatar شماره خدمتکار می‌توانی عوضش کنی."
    if av.get("type") == "servant":
        return f"🖼 عکس پروفایل: خدمتکار <b>{av.get('name','—')}</b> (شماره {av.get('index')})"
    if av.get("type") == "character":
        return f"🖼 عکس پروفایل: کاراکتر <b>{av.get('name','—')}</b> (شماره {av.get('index')})"
    return "🖼 عکس پروفایل: پیش‌فرض"


def resolve_photo_path(tg_id: int) -> str | None:
    """مسیر فایل محلی برای ارسال به تلگرام، یا None"""
    av = get_avatar(tg_id)
    if not av:
        return None
    if av.get("type") == "servant":
        try:
            from bot.utils.servant_panel import get_servant_image_by_id
            base_id = int(av.get("base_id") or 0)
            p = get_servant_image_by_id(base_id)
            if p and getattr(p, "exists", lambda: False)():
                return str(p)
            # fallback: list owned and use current base_id
            from services import servants as servmod
            bag = servmod.list_owned(int(tg_id))
            idx = int(av.get("index") or 0) - 1
            if 0 <= idx < len(bag):
                bid = int(bag[idx].get("base_id") or 0)
                p = get_servant_image_by_id(bid)
                if p and p.exists():
                    return str(p)
        except Exception:
            pass
        return None
    if av.get("type") == "character":
        try:
            from services.portraits import character_url
            path = character_url(av.get("name") or "", av.get("rarity") or "معمولی")
            return path
        except Exception:
            return None
    return None
