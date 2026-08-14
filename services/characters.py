"""کاراکتر شانسی — گacha با رتبه‌های مختلف + ترکیب تکراری"""
from __future__ import annotations
import random
from datetime import datetime, timedelta

# رتبه از رایج تا کمیاب
RARITIES = [
    ("معمولی", 42.0, 5, "⚪"),
    ("غیرمعمولی", 24.0, 12, "🟢"),
    ("نادر", 15.0, 25, "🔵"),
    ("حماسی", 9.0, 50, "🟣"),
    ("افسانه‌ای", 5.0, 100, "🟠"),
    ("اسطوره‌ای", 3.0, 2500, "🔴"),
    ("خدایی", 1.5, 12000, "🟡"),
    ("ازلی", 0.5, 50000, "✨"),
    ("قادر مطلق", 0.00000000000001, 500000, "👑"),
]

# نام کاراکترها — استخر بزرگ‌تر
POOL = {
    "معمولی": [
        "شاگرد گمنام", "نگهبان دروازه", "کشاورز چی", "راننده کاروان", "شاگرد آهنگر",
        "پیشخدمت فرقه", "جوان جنگل", "ماهی‌گیر رود", "کاتب ساده", "رهرو تازه‌کار",
        "حامل مشعل", "جمع‌کننده علف", "نگهبان انبار", "آشپز فرقه", "شوینده ظرف",
        "پیک دهکده", "چوپان دشت", "باغبان کوچک", "شاگرد کیمیا", "نگهبان چاه",
        "فروشنده مهره", "باریک‌اندام دزد", "کارگر معدن", "قصاب روستا", "خیاط ساده",
    ],
    "غیرمعمولی": [
        "شمشیرزن مرزی", "داروساز کوهستان", "شکارچی روح", "راهب معبد", "جاسوس سایه‌رو",
        "سوارکار رخش", "بانوی باد", "جنگجوی یخ", "نغمه‌خوان", "پاسبان غار",
        "تیرانداز نیزار", "سپاهی فریدون", "راهب زرتشت", "شکارچی گراز", "فلزکار جوان",
        "جادوگر مه سبک", "نگهبان پل", "قاصد فرقه", "رقاص شمشیر", "درمانگر صحرا",
        "کماندار کوه", "سرباز نیزه", "بانوی مه", "پهلوان محلی", "کاشف غار",
    ],
    "نادر": [
        "استاد تیغه نقره", "حکیم آناهیتا", "نگهبان سیمرغ", "سرباز فریدون", "جادوگر مه",
        "کاهن مهر", "سردار کاوه", "راهبه نور", "قاصد ستاره", "شکارچی دیو",
        "شمشیرزن ابریشم", "استاد کمان بلند", "حکیم گیاه‌شناس", "نگهبان آتشکده", "سوارکار سیاه",
        "بانوی شمشیر دوگانه", "جادوگر رعد", "پهلوان زره سنگین", "جاسوس دربار", "راهب خلأ",
        "شکارچی اژدهای کوچک", "کاهن ماه", "فرمانده صد نفر", "استاد نیزه سرخ", "سایه‌رو جنگل",
    ],
    "حماسی": [
        "زال سپیدموی", "رستم نیمه‌اژدها", "سیمرغ نگهبان", "آذرخش آسمانی", "ملکه سایه",
        "پهلوان هفت‌خوان", "فرمانده خون", "حکیم کهن", "شمشیرزن بی‌نام", "بانوی دریا",
        "آرش کمانگیر", "سهراب جوان", "گردآفرید", "گیو پهلوان", "گودرز سردار",
        "توس سپهدار", "بیژن دلیر", "منیژه بانوی کاخ", "اسفندیار رویین‌تن", "پیران ویسه",
        "اشکبوس جنگجو", "کاموس کشانی", "بارمان تیرانداز", "همای بلندپرواز", "شیرین کاخ",
    ],
    "افسانه‌ای": [
        "جمشید شهریار", "فریدون اژدهاکش", "رستم دستان", "آناهیتای مقدس", "سیمرغ زرین",
        "کاوه آهنگر اسطوره", "ضحاک بیدار", "همای فتح", "اردشیر سایه", "بانوی زمان",
        "کیخسرو شاه", "لهراسب پیر", "گشتاسب جنگجو", "زریر برادر", "پشوتن نگهبان",
        "آبتین پدر", "فرانک مادر", "ایرج پاک", "توران‌شاه", "سلم غربی",
        "رخش افسانه‌ای", "دیو سپید مازندران", "اکوان دیو", "ارژنگ دیو", "سنجه‌بانو",
    ],
    "اسطوره‌ای": [
        "اهورامزدا‌زاده", "اهریمن‌پیمان", "زروان زمان", "مهرِ شکست‌ناپذیر", "آناهیتای ازلی",
        "سیمرغ مادر", "رخش جاویدان", "روح رستم", "فرّ ایزدی", "دیو سپید بزرگ",
        "سروش پیام‌آور", "بهمن اندیشه", "اردیبهشت حقیقت", "شهریور شهریاری", "سپندارمذ زمین",
        "خرداد کمال", "امرداد بی‌مرگی", "آذر ایزد آتش", "اپام‌نپات آب‌ها", "وایو باد",
        "تیشتر باران", "ونند ستاره", "هوم مقدس", "گوش اورون", "درواسپ",
    ],
    "خدایی": [
        "خدای جنگ بی‌نام", "بانوی آسمان‌ها", "خدای پوچی", "نگهبان عرش", "فرشته مرگ",
        "خدای تذهیب", "ملکه بهشت", "ارباب زیرین", "چشم کهکشان", "قلم تقدیر",
        "ایزد رعد جهانی", "ایزدبانوی ماه سرخ", "خدای دروازه‌ها", "فرشته قضاوت", "ارباب زمان شکسته",
        "خدای قحطی و برکت", "بانوی تیغ هزار لبه", "نگهبان کتاب‌های سوخته", "چشم سوم عرش", "ندای خلقت",
        "سایه تاج و تخت", "نور تاج و تخت", "خدای خواب ابدی", "بانوی بیداری مطلق", "ارباب جنگ ستارگان",
    ],
    "ازلی": [
        "خالق بی‌نام", "اولین تذهیب‌گر", "سایهٔ آغاز", "نور ازلی", "فرزند هیچ",
        "نفس اول جهان", "آخرین شاهدان", "کاتب لوح محفوظ", "نگهبان صفر مطلق", "صدای قبل از کلام",
        "چشم پیش از نور", "دست پیش از شکل", "اراده پیش از زمان", "سکوت پس از همه چیز", "حلقه بی‌آغاز",
    ],
    "قادر مطلق": [
        "قادر مطلق", "ارادهٔ مطلق", "چشم بی‌کران", "قلم تقدیر نهایی",
        "یگانگی محض", "نهایت بی‌نهایت", "آن‌که نام ندارد",
    ],
}

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
                return False, f"⏳ کول‌داون {left}ث. کمی صبر کن.", None
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
    }

    bag = _owned.setdefault(tg_id, [])
    # اگر تکراری هم‌نام و هم‌رتبه → ترکیب خودکار
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
                    + "می‌توانی با /mergechar بقیه تکراری‌ها را ترکیب کنی."
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
    lines.append("/mergechar — ترکیب همه تکراری‌ها | /bestchar | /pullchar")
    return chr(10).join(lines)


def best_char(tg_id: int) -> str:
    bag = _owned.get(tg_id) or []
    if not bag:
        return "کاراکتری نداری. /pullchar"
    c = max(bag, key=lambda x: x.get("power", 0))
    st = int(c.get("stars") or 1)
    return (
        f"👑 قوی‌ترین کاراکتر" + chr(10)
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
    """ترکیب همه جفت‌های هم‌نام و هم‌رتبه"""
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
                # باقی‌مانده‌ها جدا نگه دار
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
    lines = ["🎭 <b>رتبه‌های کاراکتر شانسی</b>", ""]
    for name, chance, pwr, emoji in RARITIES:
        lines.append(
            f"{emoji} <b>{name}</b> — شانس ~{chance}% | قدرت پایه ~{pwr}"
            if chance >= 0.01
            else f"{emoji} <b>{name}</b> — شانس ≈{chance} | قدرت پایه ~{pwr}"
        )
    lines += [
        "",
        f"⭐ ترکیب تکراری: تا {MAX_STARS} ستاره (هر ستاره +{int(MERGE_POWER_MULT*100)}٪)",
        f"تعداد نام‌ها در استخر: {sum(len(v) for v in POOL.values())}",
        f"هزینه هر شانس: {PULL_COST_COINS} سکه",
        f"کول‌داون: {int(PULL_CD.total_seconds())} ثانیه",
        "",
        "/pullchar — کشیدن",
        "/mergechar — ترکیب تکراری‌ها",
        "/mychars — لیست",
        "/bestchar — قوی‌ترین",
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
        "/mergechar — ترکیب تکراری‌ها",
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
        return "فقط طرف مقابل می‌تواند قبول کند."
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
        return "فقط طرف مقابل می‌تواند قبول کند."
    pa, pb = int(d["ca"].get("power") or 0), int(d["cb"].get("power") or 0)
    if pa == pb:
        return f"تساوی! هر دو قدرت {pa}."
    if pa > pb:
        winner, wname = d["a"], d["ca"]["name"]
    else:
        winner, wname = d["b"], d["cb"]["name"]
    return f"🏆 برنده: {winner} با <b>{wname}</b> ({max(pa,pb)} vs {min(pa,pb)})"
