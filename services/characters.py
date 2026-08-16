"""کاراکتر شانسی — گacha با رتبههای مختلف + ترکیب تکراری"""
from __future__ import annotations
import random
from datetime import datetime, timedelta

# رتبه از رایج تا کمیاب
RARITIES = [
    ("معمولی", 42.0, 5, "⚪"),
    ("غیرمعمولی", 24.0, 12, "🟢"),
    ("نادر", 15.0, 25, "🔵"),
    ("حماسی", 9.0, 50, "🟣"),
    ("افسانهای", 5.0, 100, "🟠"),
    ("اسطورهای", 3.0, 2500, "🔴"),
    ("خدایی", 1.5, 12000, "🟡"),
    ("ازلی", 0.5, 50000, "✨"),
    ("قادر مطلق", 0.00000000000001, 500000, "👑"),
]

# استخر رسمی کاراکترها — نسخه جدید فقط ۳۰ کاراکتر دارد.
# کاراکترهای قدیمیِ بازیکنان حذف نمی‌شوند؛ فقط در شانس‌های جدید ظاهر نمی‌شوند.
POOL = {
    "معمولی": ["شاگرد گمنام", "نگهبان دروازه", "شاگرد آهنگر"],
    "غیرمعمولی": ["شمشیرزن مرزی", "بانوی باد", "سوارکار رخش"],
    "نادر": ["استاد تیغه نقره", "حکیم آناهیتا", "سردار کاوه"],
    "حماسی": ["زال سپیدموی", "رستم نیمه‌اژدها", "آرش کمانگیر", "گردآفرید"],
    "افسانه‌ای": ["جمشید شهریار", "رستم دستان", "آناهیتای مقدس", "سیمرغ زرین"],
    "اسطوره‌ای": ["اهورامزدا‌زاده", "زروان زمان", "آناهیتای ازلی", "فرّ ایزدی"],
    "خدایی": ["خدای پوچی", "بانوی آسمان‌ها", "فرشته مرگ", "خدای تذهیب"],
    "ازلی": ["خالق بی‌نام", "اولین تذهیبگر", "نگهبان صفر مطلق"],
    "قادر مطلق": ["قادر مطلق", "یگانگی محض"],
}

# توضیح و تصویر اختصاصی هر یک از ۳۰ کاراکتر جدید.
CHARACTER_META = {
    "شاگرد گمنام": {"image": "01.jpg", "desc": "شاگردی تازه‌کار که هنوز نامی در جهان تذهیب ندارد، اما استعداد رشدش بالاست."},
    "نگهبان دروازه": {"image": "02.jpg", "desc": "نگهبانی سخت‌گیر و وفادار که در دفاع و تحمل ضربه مهارت دارد."},
    "شاگرد آهنگر": {"image": "03.jpg", "desc": "شاگرد آهنگری که با آتش و فلز خو گرفته و در مسیر ساخت تجهیزات پیشرفت می‌کند."},
    "شمشیرزن مرزی": {"image": "04.jpg", "desc": "شمشیرزنی باتجربه از مرزهای خطرناک؛ سریع و مناسب نبردهای نزدیک."},
    "بانوی باد": {"image": "05.jpg", "desc": "رزمی‌کاری چابک که نیروی باد را برای افزایش سرعت و جاخالی‌دادن به کار می‌گیرد."},
    "سوارکار رخش": {"image": "06.jpg", "desc": "سوارکاری تهاجمی با پیوندی ویژه با اسب افسانه‌ای؛ مناسب حمله‌های سریع."},
    "استاد تیغه نقره": {"image": "07.jpg", "desc": "استاد شمشیر با تیغه‌ای نقره‌ای که تمرکزش بر ضربات دقیق و مرگبار است."},
    "حکیم آناهیتا": {"image": "08.jpg", "desc": "حکیمی وابسته به آب‌های مقدس که در پشتیبانی و بازیابی نیرو توانمند است."},
    "سردار کاوه": {"image": "09.jpg", "desc": "فرمانده‌ای آتشین و مقاوم که نیروهایش را در میدان نبرد هدایت می‌کند."},
    "زال سپیدموی": {"image": "10.jpg", "desc": "پهلوان خردمند سپیدموی که تجربه و قدرتش در نبردهای طولانی آشکار می‌شود."},
    "رستم نیمه‌اژدها": {"image": "11.jpg", "desc": "پهلوانی با خون اژدها؛ دارای نیروی بدنی و هاله‌ای آتشین و سنگین."},
    "آرش کمانگیر": {"image": "12.jpg", "desc": "کمانداری افسانه‌ای که قدرتش را در حمله‌های دوربرد و ضربه‌های دقیق نشان می‌دهد."},
    "گردآفرید": {"image": "13.jpg", "desc": "جنگجویی دلیر و تاکتیکی که با سرعت و مهارت رزمی در برابر دشمنان بزرگ می‌ایستد."},
    "جمشید شهریار": {"image": "14.jpg", "desc": "شهریاری با فرّ پادشاهی که قدرت فرمانروایی و شکوه ویژه‌ای دارد."},
    "رستم دستان": {"image": "15.jpg", "desc": "پهلوان نامدار ایران؛ نماد قدرت بدنی، استقامت و نبرد مستقیم."},
    "آناهیتای مقدس": {"image": "16.jpg", "desc": "بانوی آب‌های مقدس که هاله‌ای پاک و نیرویی عظیم در اختیار دارد."},
    "سیمرغ زرین": {"image": "17.jpg", "desc": "سیمرغی اسطوره‌ای با بال‌های زرین و نیرویی کهن و آسمانی."},
    "اهورامزدا‌زاده": {"image": "18.jpg", "desc": "فرزندی از تبار نور و خرد که هاله‌ای الهی و نیرویی پاک دارد."},
    "زروان زمان": {"image": "19.jpg", "desc": "موجودی کهن مرتبط با زمان؛ حضورش مانند ساعتی است که قوانین نبرد را تغییر می‌دهد."},
    "آناهیتای ازلی": {"image": "20.jpg", "desc": "صورت ازلی آناهیتا؛ پیوندی فراتر از زمان با آب، حیات و انرژی جهان."},
    "فرّ ایزدی": {"image": "21.jpg", "desc": "تجسم فرّ پادشاهی و شکوه ایزدی که قدرتش از هاله نورانی‌اش سرچشمه می‌گیرد."},
    "خدای پوچی": {"image": "22.jpg", "desc": "موجودی کیهانی که با خلأ و پوچی پیوند دارد و حضورش قوانین عادی را می‌شکند."},
    "بانوی آسمان‌ها": {"image": "23.jpg", "desc": "بانویی الهی که نیروی آسمان، ستارگان و طوفان را در اختیار دارد."},
    "فرشته مرگ": {"image": "24.jpg", "desc": "فرشته‌ای هولناک که نماد پایان نبرد و داوری ارواح است."},
    "خدای تذهیب": {"image": "25.jpg", "desc": "ایزدی کهن مرتبط با مسیر تذهیب و صعود قدرت؛ هاله‌ای طلایی و سنگین دارد."},
    "خالق بی‌نام": {"image": "26.jpg", "desc": "موجودی فراتر از نام و شکل که به عنوان یکی از سرچشمه‌های نخستین جهان شناخته می‌شود."},
    "اولین تذهیبگر": {"image": "27.jpg", "desc": "نخستین کسی که راه تذهیب را گشود؛ دانش او ریشه بسیاری از مسیرهای امروزی است."},
    "نگهبان صفر مطلق": {"image": "28.jpg", "desc": "نگهبان مرزی میان وجود و نیستی که قدرت سرمای مطلق و سکون کامل را در خود دارد."},
    "قادر مطلق": {"image": "29.jpg", "desc": "قدرتی مطلق که محدودیت‌های معمول تذهیب برایش معنای چندانی ندارد."},
    "یگانگی محض": {"image": "30.jpg", "desc": "تجسم یگانگی کامل؛ نیرویی که تضاد میان قدرت‌ها را در وجود خود به وحدت می‌رساند."},
}

def character_description(name: str) -> str:
    return CHARACTER_META.get(name, {}).get("desc", "کاراکتری از جهان تذهیب با توانایی‌ها و مسیر رشد مخصوص به خود.")

# ترکیب تکراری: هر ستاره ≈ +۳۵٪ قدرت پایه رتبه
MAX_STARS = 5
MERGE_POWER_MULT = 0.35  # هر ستاره اضافی


from services.persist import get_dict, save as _psave

def _owned_map():
    return get_dict("chars_owned")

def _pull_map():
    return get_dict("chars_last_pull")

class _D:
    def __init__(self, ns):
        self._ns = ns
    def _m(self):
        return get_dict(self._ns)
    def get(self, k, default=None):
        m = self._m()
        return m.get(str(k), m.get(k, default))
    def __getitem__(self, k):
        m = self._m()
        if str(k) in m:
            return m[str(k)]
        return m[k]
    def __setitem__(self, k, v):
        m = self._m()
        m[str(k)] = v
        _psave(self._ns)
    def __contains__(self, k):
        m = self._m()
        return str(k) in m or k in m
    def setdefault(self, k, default=None):
        m = self._m()
        sk = str(k)
        if sk not in m:
            m[sk] = default if default is not None else []
            _psave(self._ns)
        return m[sk]
    def pop(self, k, *a):
        m = self._m()
        sk = str(k)
        if sk in m:
            v = m.pop(sk)
            _psave(self._ns)
            return v
        if a:
            return m.pop(k, a[0]) if k in m else a[0]
        return m.pop(k)

_owned = _D("chars_owned")
_last_pull = _D("chars_last_pull")

PULL_COST_COINS = 80
PULL_CD = timedelta(seconds=25)


def _rarity_base(rarity: str) -> tuple[int, str]:
    for name, _c, pwr, emoji in RARITIES:
        if name == rarity:
            return int(pwr), emoji
    return 5, "⚪"


def _power_with_stars(base: int, stars: int) -> int:
    stars = max(1, min(MAX_STARS, int(stars or 1)))
    return int(base * (1.0 + (stars - 1) * MERGE_POWER_MULT))


def _pick_rarity() -> tuple[str, int, str]:
    total = sum(r[1] for r in RARITIES)
    roll = random.uniform(0, total)
    acc = 0.0
    for name, chance, pwr, emoji in RARITIES:
        acc += chance
        if roll <= acc:
            return name, int(pwr), emoji
    name, _, pwr, emoji = RARITIES[0]
    return name, int(pwr), emoji


def pull(tg_id: int) -> tuple[bool, str, dict | None]:
    last = _last_pull.get(tg_id)
    if last:
        try:
            if isinstance(last, str):
                last_dt = datetime.fromisoformat(last)
            else:
                last_dt = last
            if datetime.utcnow() - last_dt < PULL_CD:
                left = int((PULL_CD - (datetime.utcnow() - last_dt)).total_seconds())
                return False, f"⏳ کولداون {left}ث. کمی صبر کن.", None
        except Exception:
            pass

    rarity, base, emoji = _pick_rarity()
    pool = POOL.get(rarity) or POOL["معمولی"]
    name = random.choice(pool)
    stars = 1
    power = _power_with_stars(base, stars)
    card = {
        "name": name,
        "rarity": rarity,
        "power": power,
        "base_power": base,
        "stars": stars,
        "emoji": emoji,
        "at": datetime.utcnow().isoformat(),
        "description": character_description(name),
        "portrait": CHARACTER_META.get(name, {}).get("image"),
    }

    bag = _owned.setdefault(tg_id, [])
    # اگر تکراری همنام و همرتبه → ترکیب خودکار
    merged = False
    for c in bag:
        if c.get("name") == name and c.get("rarity") == rarity:
            old_stars = int(c.get("stars") or 1)
            if old_stars >= MAX_STARS:
                # در سقف ستاره؛ کارت جدا با قدرت کمی کمتر
                card["power"] = max(1, int(power * 0.5))
                card["note"] = "تکراری در سقف ستاره"
                bag.append(card)
                _owned[tg_id] = bag
                _last_pull[tg_id] = datetime.utcnow().isoformat()
                return True, (
                    f"{emoji} <b>{name}</b> — {rarity}" + chr(10)
                    + f"قدرت: +{card['power']} (تکراری؛ ستاره در سقف {MAX_STARS}⭐)" + chr(10)
                    + "میتوانی با /mergechar بقیه تکراریها را ترکیب کنی."
                ), card
            new_stars = old_stars + 1
            c["stars"] = new_stars
            c["base_power"] = base
            c["power"] = _power_with_stars(base, new_stars)
            c["emoji"] = emoji
            merged = True
            _owned[tg_id] = bag
            _last_pull[tg_id] = datetime.utcnow().isoformat()
            return True, (
                f"🔀 <b>ترکیب!</b> {emoji} <b>{name}</b>" + chr(10)
                + f"رتبه: {rarity} | ستاره: {old_stars}⭐ → <b>{new_stars}⭐</b>" + chr(10)
                + f"قدرت: +{c['power']}" + chr(10)
                + f"(هر ستاره حدود +{int(MERGE_POWER_MULT*100)}٪ قدرت پایه)"
            ), c

    bag.append(card)
    _owned[tg_id] = bag
    _last_pull[tg_id] = datetime.utcnow().isoformat()
    return True, (
        f"{emoji} <b>{name}</b>" + chr(10)
        + f"رتبه: {rarity} | ⭐{stars} | قدرت: +{power}" + chr(10)
        + f"تعداد کاراکتر: {len(bag)}"
    ), card


def list_chars(tg_id: int) -> str:
    bag = _owned.get(tg_id) or []
    if not bag:
        return "هنوز کاراکتری نداری. /pullchar یا /کاراکتر"
    ordered = sorted(bag, key=lambda c: c.get("power", 0), reverse=True)
    lines = [f"🎭 <b>کاراکترهای تو</b> ({len(bag)})", ""]
    for i, c in enumerate(ordered[:25], 1):
        st = int(c.get("stars") or 1)
        stars = "⭐" * st
        lines.append(
            f"{i}. {c.get('emoji','')} <b>{c['name']}</b> — {c['rarity']} {stars} (+{c['power']})"
        )
    if len(ordered) > 25:
        lines.append(f"... و {len(ordered)-25} تای دیگر")
    lines.append("")
    lines.append(f"مجموع قدرت (۳تای برتر): {total_power_bonus(tg_id)}")
    lines.append("/mergechar — ترکیب همه تکراریها | /bestchar | /pullchar")
    return chr(10).join(lines)


def best_char(tg_id: int) -> str:
    bag = _owned.get(tg_id) or []
    if not bag:
        return "کاراکتری نداری. /pullchar"
    c = max(bag, key=lambda x: x.get("power", 0))
    st = int(c.get("stars") or 1)
    return (
        f"👑 قویترین کاراکتر" + chr(10)
        + f"{c.get('emoji','')} <b>{c['name']}</b>" + chr(10)
        + f"رتبه: {c['rarity']} | {'⭐'*st} | قدرت: +{c['power']}"
    )


def total_power_bonus(tg_id: int) -> int:
    bag = _owned.get(tg_id) or []
    if not bag:
        return 0
    top = sorted((c.get("power", 0) for c in bag), reverse=True)[:3]
    return int(sum(top))


def merge_duplicates(tg_id: int) -> str:
    """ترکیب همه جفتهای همنام و همرتبه"""
    bag = list(_owned.get(tg_id) or [])
    if len(bag) < 2:
        return "حداقل دو کاراکتر لازم است."
    # group by name+rarity
    groups: dict[tuple, list[int]] = {}
    for i, c in enumerate(bag):
        key = (c.get("name"), c.get("rarity"))
        groups.setdefault(key, []).append(i)

    merges = 0
    new_bag = []
    used = set()
    for key, idxs in groups.items():
        if len(idxs) == 1:
            if idxs[0] not in used:
                new_bag.append(bag[idxs[0]])
                used.add(idxs[0])
            continue
        # sort by stars desc
        cards = sorted((bag[i] for i in idxs), key=lambda x: int(x.get("stars") or 1), reverse=True)
        base_card = dict(cards[0])
        stars = int(base_card.get("stars") or 1)
        for extra in cards[1:]:
            if stars >= MAX_STARS:
                # باقیماندهها جدا نگه دار
                new_bag.append(extra)
                continue
            add = int(extra.get("stars") or 1)
            stars = min(MAX_STARS, stars + add)
            merges += 1
        rarity = base_card.get("rarity") or "معمولی"
        base_p, emoji = _rarity_base(rarity)
        base_card["stars"] = stars
        base_card["base_power"] = base_p
        base_card["power"] = _power_with_stars(base_p, stars)
        base_card["emoji"] = emoji
        new_bag.append(base_card)

    _owned[tg_id] = new_bag
    if merges == 0:
        return "تکراری قابل ترکیبی نبود (یا همه در سقف ⭐ هستند)."
    return (
        f"🔀 <b>{merges}</b> ترکیب انجام شد." + chr(10)
        + f"تعداد کاراکتر الان: {len(new_bag)}" + chr(10)
        + "/mychars برای دیدن لیست"
    )


def rarity_guide() -> str:
    lines = ["🎭 <b>رتبههای کاراکتر شانسی</b>", ""]
    for name, chance, pwr, emoji in RARITIES:
        lines.append(
            f"{emoji} <b>{name}</b> — شانس ~{chance}% | قدرت پایه ~{pwr}"
            if chance >= 0.01
            else f"{emoji} <b>{name}</b> — شانس ≈{chance} | قدرت پایه ~{pwr}"
        )
    lines += [
        "",
        f"⭐ ترکیب تکراری: تا {MAX_STARS} ستاره (هر ستاره +{int(MERGE_POWER_MULT*100)}٪)",
        f"تعداد نامها در استخر: {sum(len(v) for v in POOL.values())}",
        f"هزینه هر شانس: {PULL_COST_COINS} سکه",
        f"کولداون: {int(PULL_CD.total_seconds())} ثانیه",
        "",
        "/pullchar — کشیدن",
        "/mergechar — ترکیب تکراریها",
        "/mychars — لیست",
        "/bestchar — قویترین",
    ]
    return chr(10).join(lines)


# --- معاوضه و دوئل کاراکتر ---
_pending_trade: dict[str, dict] = {}
_pending_cduel: dict[str, dict] = {}


def list_owned_indexed(tg_id: int) -> str:
    bag = _owned.get(tg_id) or []
    if not bag:
        return "کاراکتری نداری. /pullchar"
    lines = ["🎴 <b>کاراکترهای تو</b> (شماره برای معاوضه/دوئل)", ""]
    for i, c in enumerate(bag):
        st = int(c.get("stars") or 1)
        lines.append(
            f"{i+1}. {c.get('emoji','')} {c['name']} | {c['rarity']} {'⭐'*st} | قدرت +{c.get('power',0)}"
        )
    lines += [
        "",
        "/mergechar — ترکیب تکراریها",
        "/tradechar آیدی شماره_من شماره_او",
        "/charduel آیدی شماره_من شماره_او",
    ]
    return chr(10).join(lines)


def get_char(tg_id: int, idx: int) -> dict | None:
    bag = _owned.get(tg_id) or []
    if idx < 1 or idx > len(bag):
        return None
    return bag[idx - 1]


def remove_char(tg_id: int, idx: int) -> dict | None:
    bag = list(_owned.get(tg_id) or [])
    if idx < 1 or idx > len(bag):
        return None
    c = bag.pop(idx - 1)
    _owned[tg_id] = bag
    return c


def add_char(tg_id: int, c: dict) -> None:
    bag = list(_owned.get(tg_id) or [])
    bag.append(c)
    _owned[tg_id] = bag


def propose_trade(a: int, b: int, idx_a: int, idx_b: int) -> tuple[bool, str, str | None]:
    ca = get_char(a, idx_a)
    cb = get_char(b, idx_b)
    if not ca:
        return False, "شماره کاراکتر تو نامعتبر است.", None
    if not cb:
        return False, "شماره کاراکتر طرف نامعتبر است.", None
    key = f"{a}:{b}:{idx_a}:{idx_b}"
    _pending_trade[key] = {"a": a, "b": b, "idx_a": idx_a, "idx_b": idx_b, "ca": ca, "cb": cb}
    return True, (
        f"🔄 پیشنهاد معاوضه" + chr(10)
        + f"تو: {ca.get('emoji','')} {ca['name']} (+{ca.get('power',0)})" + chr(10)
        + f"طرف: {cb.get('emoji','')} {cb['name']} (+{cb.get('power',0)})" + chr(10)
        + f"طرف: /accepttrade {key}"
    ), key


def accept_trade(key: str, acceptor: int) -> str:
    t = _pending_trade.pop(key, None)
    if not t:
        return "پیشنهاد پیدا نشد یا منقضی شده."
    if acceptor != t["b"]:
        return "فقط طرف مقابل میتواند قبول کند."
    def _pop_match(tg, snap):
        bag = list(_owned.get(tg) or [])
        for i, c in enumerate(bag):
            if (c.get("name") == snap.get("name") and c.get("rarity") == snap.get("rarity")
                    and c.get("power") == snap.get("power")):
                bag.pop(i)
                _owned[tg] = bag
                return c
        return None
    ca = _pop_match(t["a"], t["ca"])
    cb = _pop_match(t["b"], t["cb"])
    if not ca or not cb:
        if ca:
            add_char(t["a"], ca)
        if cb:
            add_char(t["b"], cb)
        return "یکی از کاراکترها دیگر موجود نیست."
    add_char(t["a"], cb)
    add_char(t["b"], ca)
    return f"✅ معاوضه انجام شد."


def propose_char_duel(a: int, b: int, idx_a: int, idx_b: int) -> tuple[bool, str, str | None]:
    ca = get_char(a, idx_a)
    cb = get_char(b, idx_b)
    if not ca or not cb:
        return False, "شماره کاراکتر نامعتبر.", None
    key = f"cd:{a}:{b}:{idx_a}:{idx_b}"
    _pending_cduel[key] = {"a": a, "b": b, "ca": ca, "cb": cb}
    return True, (
        f"⚔️ دوئل کاراکتر" + chr(10)
        + f"{ca.get('emoji','')} {ca['name']} (+{ca.get('power',0)}) vs "
        + f"{cb.get('emoji','')} {cb['name']} (+{cb.get('power',0)})" + chr(10)
        + f"طرف: /acceptcharduel {key}" + chr(10)
        + "برنده بر اساس قدرت (بدون شانس)."
    ), key


def accept_char_duel(key: str, acceptor: int) -> str:
    d = _pending_cduel.pop(key, None)
    if not d:
        return "دوئل پیدا نشد."
    if acceptor != d["b"]:
        return "فقط طرف مقابل میتواند قبول کند."
    pa, pb = int(d["ca"].get("power") or 0), int(d["cb"].get("power") or 0)
    if pa == pb:
        return f"تساوی! هر دو قدرت {pa}."
    if pa > pb:
        winner, wname = d["a"], d["ca"]["name"]
    else:
        winner, wname = d["b"], d["cb"]["name"]
    return f"🏆 برنده: {winner} با <b>{wname}</b> ({max(pa,pb)} vs {min(pa,pb)})"
