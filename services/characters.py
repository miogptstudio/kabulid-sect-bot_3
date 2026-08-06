"""کاراکتر شانسی — گacha با رتبه‌های مختلف"""
from __future__ import annotations
import random
from datetime import datetime, timedelta

# رتبه از رایج تا کمیاب
RARITIES = [
    ("معمولی", 45.0, 5, "⚪"),
    ("غیرمعمولی", 25.0, 12, "🟢"),
    ("نادر", 15.0, 25, "🔵"),
    ("حماسی", 8.0, 50, "🟣"),
    ("افسانه‌ای", 4.0, 100, "🟠"),
    ("اسطوره‌ای", 2.0, 200, "🔴"),
    ("خدایی", 0.8, 400, "🟡"),
    ("ازلی", 0.2, 800, "✨"),
    ("قادر مطلق", 0.00000000000001, 99999, "👑"),
]

# نام کاراکترها بر اساس رتبه
POOL = {
    "معمولی": [
        "شاگرد گمنام", "نگهبان دروازه", "کشاورز چی", "راننده کاروان", "شاگرد آهنگر",
        "پیشخدمت فرقه", "جوان جنگل", "ماهی‌گیر رود", "کاتب ساده", "رهرو تازه‌کار",
    ],
    "غیرمعمولی": [
        "شمشیرزن مرزی", "داروساز کوهستان", "شکارچی روح", "راهب معبد", "جاسوس سایه‌رو",
        "سوارکار رخش", "بانوی باد", "جنگجوی یخ", "نغمه‌خوان", "پاسبان غار",
    ],
    "نادر": [
        "استاد تیغه نقره", "حکیم آناهیتا", "نگهبان سیمرغ", "سرباز فریدون", "جادوگر مه",
        "کاهن مهر", "سردار کاوه", "راهبه نور", "قاصد ستاره", "شکارچی دیو",
    ],
    "حماسی": [
        "زال سپیدموی", "رستم نیمه‌اژدها", "سیمرغ نگهبان", "آذرخش آسمانی", "ملکه سایه",
        "پهلوان هفت‌خوان", "فرمانده خون", "حکیم کهن", "شمشیرزن بی‌نام", "بانوی دریا",
    ],
    "افسانه‌ای": [
        "جمشید شهریار", "فریدون اژدهاکش", "رستم دستان", "آناهیتای مقدس", "سیمرغ زرین",
        "کاوه آهنگر اسطوره", "ضحاک بیدار", "همای فتح", "اردشیر سایه", "بانوی زمان",
    ],
    "اسطوره‌ای": [
        "اهورامزدا‌زاده", "اهریمن‌پیمان", "زروان زمان", "مهرِ شکست‌ناپذیر", "آناهیتای ازلی",
        "سیمرغ مادر", "رخش جاویدان", "روح رستم", "فرّ ایزدی", "دیو سپید بزرگ",
    ],
    "خدایی": [
        "خدای جنگ بی‌نام", "بانوی آسمان‌ها", "خدای پوچی", "نگهبان عرش", "فرشته مرگ",
        "خدای تذهیب", "ملکه بهشت", "ارباب زیرین", "چشم کهکشان", "قلم تقدیر",
    ],
    "ازلی": [
        "خالق بی‌نام", "اولین تذهیب‌گر", "سایهٔ آغاز", "نور ازلی", "فرزند هیچ",
    ],
    "قادر مطلق": [
        "قادر مطلق", "ارادهٔ مطلق", "چشم بی‌کران", "قلم تقدیر نهایی",
    ],
}

# tg_id -> list of owned {name, rarity, power, at}
_owned: dict[int, list] = {}
_last_pull: dict[int, datetime] = {}
PULL_CD = timedelta(seconds=90)
PULL_COST_COINS = 100  # سکه پایه؛ رتبه‌های بالاتر جداگانه هزینه ندارند چون شانسی است


def _pick_rarity() -> str:
    # شانس جدا برای قادر مطلق (۰.۰۰۰۰۰۰۰۰۰۰۰۰۰۱)
    if random.random() < 0.00000000000001:
        return "قادر مطلق"
    names = [r[0] for r in RARITIES if r[0] != "قادر مطلق"]
    weights = [r[1] for r in RARITIES if r[0] != "قادر مطلق"]
    return random.choices(names, weights=weights, k=1)[0]


def _power_for(rarity: str) -> int:
    for name, _w, pwr, _emoji in RARITIES:
        if name == rarity:
            # کمی نوسان
            return int(pwr * random.uniform(0.85, 1.2))
    return 5


def pull(tg_id: int) -> tuple[bool, str, dict | None]:
    now = datetime.utcnow()
    last = _last_pull.get(tg_id)
    if last and now - last < PULL_CD:
        left = int((PULL_CD - (now - last)).total_seconds())
        return False, f"⏳ هر {int(PULL_CD.total_seconds())}ث یک‌بار. {left}ث صبر کن.", None

    rarity = _pick_rarity()
    names = POOL.get(rarity) or POOL["معمولی"]
    name = random.choice(names)
    power = _power_for(rarity)
    emoji = next((e for n, _w, _p, e in RARITIES if n == rarity), "⚪")

    card = {
        "name": name,
        "rarity": rarity,
        "power": power,
        "emoji": emoji,
        "at": now.isoformat(),
    }
    bag = _owned.setdefault(tg_id, [])
    bag.append(card)
    # حداکثر ۵۰ کاراکتر نگه دار
    if len(bag) > 50:
        bag.sort(key=lambda c: c.get("power", 0))
        del bag[: len(bag) - 50]
    _last_pull[tg_id] = now

    msg = (
        f"{emoji} <b>کاراکتر شانسی!</b>" + chr(10)
        + f"نام: <b>{name}</b>" + chr(10)
        + f"رتبه: <b>{rarity}</b>" + chr(10)
        + f"قدرت کمکی: +{power}" + chr(10)
        + f"تعداد کل کاراکترها: {len(bag)}" + chr(10)
        + "/mychars — لیست | /bestchar — قوی‌ترین"
    )
    return True, msg, card


def list_chars(tg_id: int) -> str:
    bag = _owned.get(tg_id) or []
    if not bag:
        return "هنوز کاراکتری نداری. /pullchar یا /کاراکتر"
    # مرتب بر اساس قدرت
    ordered = sorted(bag, key=lambda c: c.get("power", 0), reverse=True)
    lines = [f"🎭 <b>کاراکترهای تو</b> ({len(bag)})", ""]
    for i, c in enumerate(ordered[:20], 1):
        lines.append(
            f"{i}. {c.get('emoji','')} <b>{c['name']}</b> — {c['rarity']} (+{c['power']})"
        )
    if len(ordered) > 20:
        lines.append(f"... و {len(ordered)-20} تای دیگر")
    lines.append("")
    lines.append(f"مجموع قدرت کاراکتر: {sum(c.get('power',0) for c in bag)}")
    lines.append("/bestchar — قوی‌ترین | /pullchar — شانس دوباره")
    return chr(10).join(lines)


def best_char(tg_id: int) -> str:
    bag = _owned.get(tg_id) or []
    if not bag:
        return "کاراکتری نداری. /pullchar"
    c = max(bag, key=lambda x: x.get("power", 0))
    return (
        f"👑 قوی‌ترین کاراکتر" + chr(10)
        + f"{c.get('emoji','')} <b>{c['name']}</b>" + chr(10)
        + f"رتبه: {c['rarity']} | قدرت: +{c['power']}"
    )


def total_power_bonus(tg_id: int) -> int:
    bag = _owned.get(tg_id) or []
    if not bag:
        return 0
    # فقط ۳ تای قوی‌تر در قدرت دوئل حساب شود
    top = sorted((c.get("power", 0) for c in bag), reverse=True)[:3]
    return int(sum(top))


def rarity_guide() -> str:
    lines = ["🎭 <b>رتبه‌های کاراکتر شانسی</b>", ""]
    for name, chance, pwr, emoji in RARITIES:
        lines.append(f"{emoji} <b>{name}</b> — شانس ~{chance}% | قدرت پایه ~{pwr}" if chance >= 0.01 else f"{emoji} <b>{name}</b> — شانس ≈{chance} | قدرت پایه ~{pwr}")
    lines += [
        "",
        f"هزینه هر شانس: {PULL_COST_COINS} سکه",
        f"کول‌داون: {int(PULL_CD.total_seconds())} ثانیه",
        "",
        "/pullchar یا /کاراکتر — کشیدن شانسی",
        "/mychars — لیست",
        "/bestchar — قوی‌ترین",
        "/charrates — همین راهنما",
    ]
    return chr(10).join(lines)
