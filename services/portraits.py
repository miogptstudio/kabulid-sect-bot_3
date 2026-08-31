"""پرتره برای خدمتکار، کاراکتر، پت و ... — URL عمومی"""
from __future__ import annotations
from urllib.parse import quote

# استایلهای DiceBear بر اساس نژاد
_STYLE = {
    "انسان": "lorelei",
    "نیمهانسان": "adventurer",
    "گربهای نیمهانسان": "adventurer",
    "روباهنمای": "adventurer",
    "گرگنمای": "adventurer",
    "اژدهاتبار": "lorelei",
    "ققنوستبار": "lorelei",
    "جن جنگلی": "adventurer",
    "دیوتبار": "personas",
    "فرشتهتبار": "lorelei",
    "اهریمنی": "personas",
    "سیمرغزاده": "lorelei",
    "روحپیما": "notionists",
    "خونآشام کهن": "personas",
    "مهپیما": "notionists",
}

_BG = {
    "زن": "ffd1dc",
    "مرد": "b8d4e8",
}

# رنگ کمکی نژاد
_RACE_BG = {
    "گربهای نیمهانسان": "ffe4b5",
    "روباهنمای": "ffcc99",
    "گرگنمای": "c0c0c0",
    "اژدهاتبار": "ff6347",
    "ققنوستبار": "ff8c00",
    "دیوتبار": "4b0082",
    "فرشتهتبار": "fffaf0",
    "اهریمنی": "2f0000",
    "سیمرغزاده": "ffd700",
}


def portrait_url(name: str, gender: str = "زن", race: str = "انسان", size: int = 512) -> str:
    """URL پرتره پایدار بر اساس نام (همیشه یک شکل برای یک نام)"""
    style = _STYLE.get(race, "lorelei")
    # bottts برای گربهای با seed خاص
    seed = quote(f"{race}-{gender}-{name}", safe="")
    bg = _RACE_BG.get(race) or _BG.get(gender, "e8e8e8")
    # DiceBear 7.x PNG
    return (
        f"https://api.dicebear.com/9.x/{style}/png"
        f"?seed={seed}&size={size}&backgroundColor={bg}"
    )


def servant_caption(s: dict) -> str:
    tr = "🦋 دگرگونشده" if s.get("transformed") else ""
    return (
        f"👤 <b>{s.get('name')}</b> {tr}" + chr(10)
        + f"نژاد: {s.get('race', '—')} | {s.get('gender', '—')}" + chr(10)
        + f"❤️ وفاداری: {s.get('loyalty', 0)}% | 🧘 تذهیب: {s.get('cult', 1)}" + chr(10)
        + f"⚔ قدرت: {s.get('power', 0)}"
    )


def character_url(name: str, rarity: str = "معمولی") -> str:
    """تصویر واقعی و اختصاصی هر یک از ۳۰ کاراکتر فعال.

    تصاویر داخل خود پروژه نگهداری میشوند تا با قطع اینترنت یا تغییر سرویس
    تصویر، پنل کاراکترها خراب نشود. کاراکترهای قدیمیِ ذخیرهشده همچنان
    fallback پایدار خودشان را دارند.
    """
    from pathlib import Path
    meta = {
        "شاگرد گمنام":"01.jpg","نگهبان دروازه":"02.jpg","شاگرد آهنگر":"03.jpg",
        "شمشیرزن مرزی":"04.jpg","بانوی باد":"05.jpg","سوارکار رخش":"06.jpg",
        "استاد تیغه نقره":"07.jpg","حکیم آناهیتا":"08.jpg","سردار کاوه":"09.jpg",
        "زال سپیدموی":"10.jpg","رستم نیمه‌اژدها":"11.jpg","آرش کمانگیر":"12.jpg","گردآفرید":"13.jpg",
        "جمشید شهریار":"14.jpg","رستم دستان":"15.jpg","آناهیتای مقدس":"16.jpg","سیمرغ زرین":"17.jpg",
        "اهورامزدا‌زاده":"18.jpg","زروان زمان":"19.jpg","آناهیتای ازلی":"20.jpg","فرّ ایزدی":"21.jpg",
        "خدای پوچی":"22.jpg","بانوی آسمان‌ها":"23.jpg","فرشته مرگ":"24.jpg","خدای تذهیب":"25.jpg",
        "خالق بی‌نام":"26.jpg","اولین تذهیبگر":"27.jpg","نگهبان صفر مطلق":"28.jpg",
        "قادر مطلق":"29.jpg","یگانگی محض":"30.jpg",
    }
    root = Path(__file__).resolve().parent.parent / "assets" / "characters"
    path = root / meta.get(name, "")
    if path.exists():
        return str(path)
    style = {
        "معمولی": "identicon", "غیرمعمولی": "bottts", "نادر": "adventurer",
        "حماسی": "avataaars", "افسانه‌ای": "lorelei", "اسطوره‌ای": "personas",
        "خدایی": "shapes", "ازلی": "shapes", "قادر مطلق": "shapes",
    }.get(rarity, "identicon")
    seed = quote(f"legacy-char-{rarity}-{name}", safe="")
    fallback = root / "01.jpg"
    if fallback.exists():
        return str(fallback)
    return str(root / "panels" / "character_system.jpg")

def pet_url(name: str) -> str:
    seed = quote(f"pet-{name}", safe="")
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent / "assets" / "servants"
    for name in ("01.jpg", "02.jpg", "03.jpg"):
        p = root / name
        if p.exists():
            return str(p)
    return str(Path(__file__).resolve().parent.parent / "assets" / "panels" / "pets.jpg")


# تصاویر پنلهای ربات؛ بر اساس seed ثابت، برای هر بخش تصویر ثابت و قابلتکرار است.
def panel_url(kind: str, gender: str = "مرد", name: str = "Kabulid", size: int = 768) -> str:
    from pathlib import Path
    root = Path(__file__).resolve().parent.parent / "assets" / "panels"
    aliases = {"job":"jobs", "jobs":"jobs", "profile":"profile_female" if gender=="زن" else "profile_male"}
    path = root / (aliases.get(kind, kind) + ".jpg")
    return str(path if path.exists() else root/"settings.jpg")


def servant_image_path(servant_key: str) -> str:
    from pathlib import Path
    path = Path(__file__).resolve().parent.parent / "assets" / "servants" / f"{servant_key}.jpg"
    return str(path)
