"""محدودیت مصرف قرص بر اساس قلمرو — زیاده‌روی = انفجار"""
from __future__ import annotations
from datetime import datetime
from services.persist import get_dict, save as _psave

# سقف قرص روزانه بر اساس ایندکس قلمرو
# اوایل (بیداری/پایه/متوسط/بالا): ۵
BASE_LIMIT = 5
PER_REALM_BONUS = 3  # هر قلمرو بالاتر +۳

REALM_ORDER = [
    "بیداری", "پایه", "متوسط", "بالا", "پیشرفته", "هسته", "روح",
    "نیمه‌خدا", "خدا", "آسمان", "ای‌تری", "جاودان", "ابدی",
    "خلقت", "پوچی", "فراپوچی", "مطلق",
]

OVERDOSE_DEATH_CHANCE = 0.60  # ۶۰٪ مرگ در صورت عبور از سقف


def _map() -> dict:
    return get_dict("pill_daily")


def _day() -> str:
    return datetime.utcnow().strftime("%Y-%m-%d")


def realm_index(realm: str) -> int:
    try:
        from database.models_v2 import CULTIVATION_REALMS
        if realm in CULTIVATION_REALMS:
            return list(CULTIVATION_REALMS).index(realm)
    except Exception:
        pass
    if realm in REALM_ORDER:
        return REALM_ORDER.index(realm)
    return 0


def max_pills(realm: str) -> int:
    idx = realm_index(realm or "بیداری")
    # بیداری..بالا ≈ idx 0-3 → حداقل ۵
    return BASE_LIMIT + max(0, idx) * PER_REALM_BONUS


def used_today(tg: int) -> int:
    m = _map()
    sk = str(int(tg))
    rec = m.get(sk) or {}
    if rec.get("day") != _day():
        return 0
    return int(rec.get("count") or 0)


def register_pill(tg: int, realm: str) -> tuple[bool, str, bool]:
    """
    returns (allowed_effect, message, died)
    اگر بیش از سقف: اثر قرص اعمال می‌شود ولی ۶۰٪ مرگ
    """
    import random
    limit = max_pills(realm)
    m = _map()
    sk = str(int(tg))
    rec = m.get(sk) or {}
    if rec.get("day") != _day():
        rec = {"day": _day(), "count": 0}
    count = int(rec.get("count") or 0) + 1
    rec["count"] = count
    m[sk] = rec
    _psave("pill_daily")

    if count <= limit:
        return True, f"💊 قرص امروز: {count}/{limit}", False

    # overdose
    if random.random() < OVERDOSE_DEATH_CHANCE:
        return True, (
            f"💥 زیاده‌روی قرص! ({count}/{limit})" + chr(10)
            + "بدن تحمل نکرد و منفجر شدی." + chr(10)
            + "برای سقف بالاتر، قلمرو تذهیب را ارتقا بده."
        ), True
    return True, (
        f"⚠️ زیاده‌روی قرص ({count}/{limit}) — این بار زنده ماندی (۴۰٪)." + chr(10)
        + f"سقف فعلی قلمرو «{realm}»: {limit} عدد در روز." + chr(10)
        + "ارتقای قلمرو = ظرفیت بیشتر."
    ), False


def status(tg: int, realm: str) -> str:
    limit = max_pills(realm)
    used = used_today(tg)
    return f"💊 مصرف قرص امروز: {used}/{limit} (قلمروه {realm})"
