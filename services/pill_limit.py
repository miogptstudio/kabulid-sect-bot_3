"""محدودیت مصرف قرص — کول‌داون ۵ دقیقه‌ای + سقف روزانه بر اساس قلمرو"""
from __future__ import annotations
from datetime import datetime, timedelta
from services.persist import get_dict, save as _psave

# کول‌داون بین هر مصرف (درخواست کاربر: ۵ دقیقه)
COOLDOWN_SECONDS = 5 * 60

# سقف قرص روزانه بر اساس ایندکس قلمرو
BASE_LIMIT = 5
PER_REALM_BONUS = 3  # هر قلمرو بالاتر +۳

REALM_ORDER = [
    "بیداری", "پایه", "متوسط", "بالا", "پیشرفته", "هسته", "روح",
    "نیمهخدا", "خدا", "آسمان", "ایتری", "جاودان", "ابدی",
    "خلقت", "پوچی", "فراپوچی", "مطلق",
]

OVERDOSE_DEATH_CHANCE = 0.60  # ۶۰٪ مرگ در صورت عبور از سقف روزانه


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
    return BASE_LIMIT + max(0, idx) * PER_REALM_BONUS


def used_today(tg: int) -> int:
    m = _map()
    sk = str(int(tg))
    rec = m.get(sk) or {}
    if rec.get("day") != _day():
        return 0
    return int(rec.get("count") or 0)


def _cooldown_left(rec: dict) -> int:
    """ثانیه باقی‌مانده از کول‌داون ۵ دقیقه‌ای؛ ۰ یعنی آزاد."""
    last = rec.get("last_at")
    if not last:
        return 0
    try:
        last_dt = datetime.fromisoformat(str(last))
    except Exception:
        return 0
    elapsed = (datetime.utcnow() - last_dt).total_seconds()
    left = COOLDOWN_SECONDS - elapsed
    return int(left) if left > 0 else 0


def register_pill(tg: int, realm: str, quantity: int = 1) -> tuple[bool, str, bool]:
    """
    returns (allowed_effect, message, died)
    - اول کول‌داون ۵ دقیقه چک می‌شود
    - بعد سقف روزانه؛ اگر بیش از سقف: اثر اعمال می‌شود ولی ۶۰٪ مرگ
    """
    import random
    quantity = max(1, int(quantity or 1))
    limit = max_pills(realm)
    m = _map()
    sk = str(int(tg))
    rec = m.get(sk) or {}
    if rec.get("day") != _day():
        rec = {"day": _day(), "count": 0, "last_at": None}

    # کول‌داون ۵ دقیقه
    left = _cooldown_left(rec)
    if left > 0:
        mins = left // 60
        secs = left % 60
        return False, (
            f"⏳ محدودیت نوشیدن/مصرف قرص: هر ۵ دقیقه یک‌بار.\n"
            f"حدود {mins} دقیقه و {secs} ثانیه دیگر صبر کن."
        ), False

    previous = int(rec.get("count") or 0)
    count = previous + quantity
    rec["count"] = count
    rec["last_at"] = datetime.utcnow().isoformat()
    m[sk] = rec
    _psave("pill_daily")

    if count <= limit:
        return True, (
            f"💊 مصرف ×{quantity} — امروز: {count}/{limit}\n"
            f"⏱ کول‌داون بعدی: ۵ دقیقه"
        ), False

    # overdose
    if random.random() < OVERDOSE_DEATH_CHANCE:
        return True, (
            f"💥 زیادهروی قرص! (مصرف ×{quantity} | {count}/{limit})\n"
            "بدن تحمل نکرد و منفجر شدی.\n"
            "برای سقف بالاتر، قلمرو تذهیب را ارتقا بده."
        ), True
    return True, (
        f"⚠️ زیادهروی قرص ({count}/{limit}) — این بار زنده ماندی (۴۰٪).\n"
        f"سقف فعلی قلمرو «{realm}»: {limit} عدد در روز.\n"
        "ارتقای قلمرو = ظرفیت بیشتر. کول‌داون ۵ دقیقه فعال شد."
    ), False


def status(tg: int, realm: str) -> str:
    limit = max_pills(realm)
    used = used_today(tg)
    m = _map()
    rec = m.get(str(int(tg))) or {}
    left = _cooldown_left(rec)
    cd = f"آزاد ✅" if left <= 0 else f"{left // 60}:{left % 60:02d} باقی"
    return f"💊 مصرف قرص امروز: {used}/{limit} (قلمروه {realm}) | کول‌داون ۵د: {cd}"
