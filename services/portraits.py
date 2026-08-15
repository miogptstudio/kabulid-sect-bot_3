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
    style = {
        "معمولی": "identicon",
        "غیرمعمولی": "bottts",
        "نادر": "adventurer",
        "حماسی": "avataaars",
        "افسانهای": "lorelei",
        "اسطورهای": "personas",
        "خدایی": "shapes",
        "ازلی": "shapes",
        "قادر مطلق": "shapes",
    }.get(rarity, "identicon")
    seed = quote(f"char-{rarity}-{name}", safe="")
    return f"https://api.dicebear.com/9.x/{style}/png?seed={seed}&size=512"


def pet_url(name: str) -> str:
    seed = quote(f"pet-{name}", safe="")
    return f"https://api.dicebear.com/9.x/bottts/png?seed={seed}&size=512"


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
