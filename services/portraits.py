"""پرتره و تصاویر پنل — فقط فایل واقعی محلی؛ بدون تصویر رندوم/DiceBear"""
from __future__ import annotations
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_PANELS = _ROOT / "assets" / "panels"
_CHARS = _ROOT / "assets" / "characters"
_SERVANTS = _ROOT / "assets" / "servants"


def _existing(path: Path) -> str | None:
    """فقط اگر فایل واقعاً وجود داشته باشد مسیر را برمی‌گرداند."""
    try:
        if path.is_file():
            return str(path)
    except Exception:
        pass
    return None


def portrait_url(name: str, gender: str = "زن", race: str = "انسان", size: int = 512) -> str | None:
    """دیگر DiceBear برنمی‌گرداند. فقط None تا فراخوان‌کننده متن بفرستد."""
    return None


def servant_caption(s: dict) -> str:
    tr = "🦋 دگرگونشده" if s.get("transformed") else ""
    return (
        f"👤 <b>{s.get('name')}</b> {tr}" + chr(10)
        + f"نژاد: {s.get('race', '—')} | {s.get('gender', '—')}" + chr(10)
        + f"❤️ وفاداری: {s.get('loyalty', 0)}% | 🧘 تذهیب: {s.get('cult', 1)}" + chr(10)
        + f"⚔ قدرت: {s.get('power', 0)}"
    )


def character_url(name: str, rarity: str = "معمولی") -> str | None:
    """تصویر محلی کاراکتر — اگر نباشد None"""
    meta = {
        "شاگرد گمنام": "01.jpg", "نگهبان دروازه": "02.jpg", "شاگرد آهنگر": "03.jpg",
        "شمشیرزن مرزی": "04.jpg", "بانوی باد": "05.jpg", "سوارکار رخش": "06.jpg",
        "استاد تیغه نقره": "07.jpg", "حکیم آناهیتا": "08.jpg", "سردار کاوه": "09.jpg",
        "زال سپیدموی": "10.jpg", "رستم نیمه‌اژدها": "11.jpg", "آرش کمانگیر": "12.jpg", "گردآفرید": "13.jpg",
        "جمشید شهریار": "14.jpg", "رستم دستان": "15.jpg", "آناهیتای مقدس": "16.jpg", "سیمرغ زرین": "17.jpg",
        "اهورامزدا‌زاده": "18.jpg", "زروان زمان": "19.jpg", "آناهیتای ازلی": "20.jpg", "فرّ ایزدی": "21.jpg",
        "خدای پوچی": "22.jpg", "بانوی آسمان‌ها": "23.jpg", "فرشته مرگ": "24.jpg", "خدای تذهیب": "25.jpg",
        "خالق بی‌نام": "26.jpg", "اولین تذهیبگر": "27.jpg", "نگهبان صفر مطلق": "28.jpg",
        "قادر مطلق": "29.jpg", "یگانگی محض": "30.jpg",
    }
    fname = meta.get(name)
    if fname:
        p = _existing(_CHARS / fname)
        if p:
            return p
    return _existing(_CHARS / "01.jpg")


def pet_url(name: str) -> str | None:
    for fname in ("01.jpg", "02.jpg", "03.jpg"):
        p = _existing(_SERVANTS / fname)
        if p:
            return p
    return _existing(_PANELS / "pets.jpg")


def panel_url(kind: str, gender: str = "مرد", name: str = "Kabulid", size: int = 768) -> str | None:
    """مسیر تصویر پنل فقط اگر فایل وجود داشته باشد؛ وگرنه None (بدون fallback رندوم)."""
    aliases = {
        "job": "jobs",
        "jobs": "jobs",
        "profile": "profile_female" if gender == "زن" else "profile_male",
    }
    key = aliases.get(kind, kind)
    return _existing(_PANELS / f"{key}.jpg")


def servant_image_path(servant_key: str) -> str | None:
    return _existing(_SERVANTS / f"{servant_key}.jpg")
