"""سیستم دانش، نرخ نبرد، لول بدن و روح جدا"""
from __future__ import annotations
from datetime import datetime, timedelta

# --- سطوح دانش ---
KNOWLEDGE_TIERS = [
    (0, "دانش پایه"),
    (100, "دانش متوسط"),
    (300, "دانش پیشرفته"),
    (700, "دانش عالی"),
    (1500, "دانش استادانه"),
    (3000, "دانش حکیم"),
    (6000, "دانش افسانه‌ای"),
    (12000, "دانش خدایی"),
]


from services.persist import get_dict, save as _psave

def _pd(ns: str) -> dict:
    return get_dict(ns)

def _pget(ns: str, tg, default=None):
    d = _pd(ns)
    sk = str(int(tg))
    if sk in d:
        return d[sk]
    return d.get(tg, default)

def _pset(ns: str, tg, val):
    d = _pd(ns)
    d[str(int(tg))] = val
    _psave(ns)

def _ppop(ns: str, tg, default=None):
    d = _pd(ns)
    sk = str(int(tg))
    if sk in d:
        v = d.pop(sk)
        _psave(ns)
        return v
    return default

# namespaces: know_k, know_body, know_spirit, know_pow, know_spd, know_def, know_book, know_wander, know_talk

def _as_dt(v):
    if v is None:
        return None
    if isinstance(v, datetime):
        return v
    try:
        return datetime.fromisoformat(str(v))
    except Exception:
        return None

BOOK_CD_MIN = 30
WANDER_CD_H = 1
TALK_CD_H = 3


def get_knowledge(tg: int) -> int:
    return int(_pget("know_k", tg, 0) or 0)


def knowledge_tier(tg: int) -> str:
    k = get_knowledge(tg)
    name = KNOWLEDGE_TIERS[0][1]
    for thr, n in KNOWLEDGE_TIERS:
        if k >= thr:
            name = n
    return name


def add_knowledge(tg: int, amount: int) -> tuple[int, str]:
    _pset("know_k", tg, get_knowledge(tg) + max(0, int(amount)))
    return get_knowledge(tg), knowledge_tier(tg)


def body_level(tg: int) -> int:
    return int(_pget("know_body", tg, 1) or 1)


def spirit_level(tg: int) -> int:
    return int(_pget("know_spirit", tg, 1) or 1)


def add_body_xp(tg: int, n: int = 1) -> int:
    # هر ۱۰ واحد یک لول
    cur = int(_pget("know_body", tg, 1) or 1)
    nv = min(200, cur + max(1, n))
    _pset("know_body", tg, nv)
    return nv


def add_spirit_xp(tg: int, n: int = 1) -> int:
    cur = int(_pget("know_spirit", tg, 1) or 1)
    nv = min(200, cur + max(1, n))
    _pset("know_spirit", tg, nv)
    return nv


def get_power(tg: int) -> int:
    return 10 + int(_pget("know_pow", tg, 0) or 0) + body_level(tg) * 2


def get_speed(tg: int) -> int:
    return 10 + int(_pget("know_spd", tg, 0) or 0) + spirit_level(tg)


def get_defense(tg: int) -> int:
    return 10 + int(_pget("know_def", tg, 0) or 0) + body_level(tg)


def dodge_rate(tg: int) -> float:
    """درصد جاخالی ۰–۷۵ بر اساس سرعت"""
    s = get_speed(tg)
    return min(75.0, s * 0.35)


def block_rate(tg: int) -> float:
    """درصد دفاع کامل (بلاک ۱۰۰٪ بعضی حملات) ۰–۴۰"""
    d = get_defense(tg)
    return min(40.0, d * 0.2)


def add_combat_stat(tg: int, kind: str, amount: int) -> str:
    """افزایش پایدار قدرت/سرعت/دفاع در persist"""
    amount = int(amount)
    tg = int(tg)
    if kind in ("power", "قدرت"):
        cur = int(_pget("know_pow", tg, 0) or 0)
        _pset("know_pow", tg, cur + amount)
        return f"⚔️ قدرت نبرد +{amount} (کل مؤثر: {get_power(tg)})"
    if kind in ("speed", "سرعت"):
        cur = int(_pget("know_spd", tg, 0) or 0)
        _pset("know_spd", tg, cur + amount)
        return f"💨 سرعت +{amount} | جاخالی: {dodge_rate(tg):.1f}٪"
    if kind in ("defense", "دفاع"):
        cur = int(_pget("know_def", tg, 0) or 0)
        _pset("know_def", tg, cur + amount)
        return f"🛡️ دفاع +{amount} | بلاک کامل: {block_rate(tg):.1f}٪"
    return "نوع نامعتبر"


def status(tg: int) -> str:
    k = get_knowledge(tg)
    return (
        f"📚 <b>دانش</b>: {k} — <b>{knowledge_tier(tg)}</b>" + chr(10)
        + f"💪 لول بدن: {body_level(tg)} (جدا از تذهیب)" + chr(10)
        + f"👻 لول روح: {spirit_level(tg)} (جدا از تذهیب)" + chr(10)
        + f"⚔️ قدرت: {get_power(tg)} | 💨 سرعت: {get_speed(tg)} | 🛡️ دفاع: {get_defense(tg)}" + chr(10)
        + f"🌀 جاخالی: {dodge_rate(tg):.1f}٪ | 🧱 بلاک کامل: {block_rate(tg):.1f}٪" + chr(10) + chr(10)
        + "📖 /readbook — خواندن کتاب (+دانش، هر ۳۰د)" + chr(10)
        + "🌍 /wanderworld — گردش جهان (+دانش، هر ۱س)" + chr(10)
        + "🧙 /talkmaster — گفتگو با استاد (+دانش بیشتر، هر ۳س)" + chr(10)
        + "🏋️ /trainbody — تمرین بدن | 🔮 /trainspirit — تمرین روح"
    )


def read_book(tg: int) -> str:
    now = datetime.utcnow()
    last = _as_dt(_pget("know_book", tg))
    if last and now - last < timedelta(minutes=BOOK_CD_MIN):
        left = int((last + timedelta(minutes=BOOK_CD_MIN) - now).total_seconds() // 60) + 1
        return f"⏳ کتاب بعدی تا {left} دقیقه دیگر."
    _last_book[tg] = now
    gain = 8 + body_level(tg) // 5
    total, tier = add_knowledge(tg, gain)
    return f"📖 کتاب خواندی. +{gain} دانش (کل: {total} — {tier})"


def wander_world(tg: int) -> str:
    now = datetime.utcnow()
    last = _as_dt(_pget("know_wander", tg))
    if last and now - last < timedelta(hours=WANDER_CD_H):
        left = int((last + timedelta(hours=WANDER_CD_H) - now).total_seconds() // 60) + 1
        return f"⏳ گردش بعدی تا {left} دقیقه دیگر (محدودیت ۱ ساعت)."
    _last_wander[tg] = now
    gain = 15 + spirit_level(tg) // 4
    total, tier = add_knowledge(tg, gain)
    return f"🌍 در جهان گردش کردی. +{gain} دانش (کل: {total} — {tier})"


def talk_master(tg: int, has_master: bool) -> str:
    if not has_master:
        return "استاد نداری. با /askmaster درخواست شاگردی بده."
    now = datetime.utcnow()
    last = _as_dt(_pget("know_talk", tg))
    if last and now - last < timedelta(hours=TALK_CD_H):
        left = int((last + timedelta(hours=TALK_CD_H) - now).total_seconds() // 60) + 1
        return f"⏳ گفتگوی بعدی با استاد تا {left} دقیقه دیگر (هر ۳ ساعت)."
    _last_talk[tg] = now
    gain = 25 + get_knowledge(tg) // 50
    total, tier = add_knowledge(tg, gain)
    return (
        f"🧙 با استاد گفتگو کردی. +{gain} دانش (کل: {total} — {tier})" + chr(10)
        + "استاد-شاگردی دانش را سریع‌تر می‌کند."
    )


def train_body(tg: int) -> str:
    lv = add_body_xp(tg, 1)
    return f"💪 تمرین بدن انجام شد. لول بدن: {lv}"


def train_spirit(tg: int) -> str:
    lv = add_spirit_xp(tg, 1)
    try:
        from services.body_spirit_realms import add_spirit_realm_xp
        extra = add_spirit_realm_xp(tg, 15)
    except Exception:
        extra = ""
    return f"👻 تمرین روح انجام شد. لول روح: {lv}" + (chr(10) + extra if extra else "")


# دانش روی کیمیاگری / قدرت قرص
def alchemy_bonus(tg: int) -> float:
    """ضریب موفقیت/قدرت ساخت بر اساس دانش"""
    k = get_knowledge(tg)
    return 1.0 + min(1.5, k / 2000.0)


def pill_power_mult(tg: int) -> float:
    return 1.0 + min(1.0, get_knowledge(tg) / 3000.0)
