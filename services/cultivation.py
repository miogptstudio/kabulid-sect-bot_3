import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models_v2 import Cultivation, CULTIVATION_REALMS
from database.models_v3 import CultivationTechnique, UserTechnique
from database.models import User

from bot.config import ROOT_UNLOCK_ENERGY, ENERGY_BASE, ENERGY_PER_LEVEL_ADD

MAX_STAGE = 10

# رگ‌های معنوی (بیش از ۳۰ نوع) — هر بازیکن تا ۵ رگ
SPIRITUAL_VEINS = {
    "رگ یانگ": {"mult": 1.12, "desc": "جریان فعال تهاجمی"},
    "رگ یین": {"mult": 1.12, "desc": "جریان آرام پایدار"},
    "رگ آتش": {"mult": 1.14, "desc": "شعله درونی"},
    "رگ آب": {"mult": 1.13, "desc": "جریان سیال"},
    "رگ چوب": {"mult": 1.13, "desc": "رشد و حیات"},
    "رگ فلز": {"mult": 1.15, "desc": "سختی و برش"},
    "رگ خاک": {"mult": 1.12, "desc": "ثبات و دفاع"},
    "رگ رعد": {"mult": 1.16, "desc": "سرعت آذرخش"},
    "رگ یخ": {"mult": 1.14, "desc": "سرمایش و تمرکز"},
    "رگ باد": {"mult": 1.13, "desc": "سبکی و گردش"},
    "رگ نور": {"mult": 1.17, "desc": "پاکی نورانی"},
    "رگ تاریکی": {"mult": 1.17, "desc": "سایه و نهان"},
    "رگ روح": {"mult": 1.18, "desc": "پیوند روحی"},
    "رگ خون": {"mult": 1.15, "desc": "نیروی خون"},
    "رگ استخوان": {"mult": 1.14, "desc": "استحکام بدن"},
    "رگ مغز": {"mult": 1.16, "desc": "ادراک و تکنیک"},
    "رگ قلب": {"mult": 1.15, "desc": "اراده و حیات"},
    "رگ چشم": {"mult": 1.13, "desc": "بینش انرژی"},
    "رگ ستاره": {"mult": 1.19, "desc": "چی ستاره‌ای"},
    "رگ ماه": {"mult": 1.16, "desc": "جزر و مد معنوی"},
    "رگ خورشید": {"mult": 1.18, "desc": "گرمای سلطنتی"},
    "رگ سیمرغ": {"mult": 1.2, "desc": "حکمت ایرانی"},
    "رگ اژدها": {"mult": 1.21, "desc": "قدرت اژدها"},
    "رگ ققنوس": {"mult": 1.2, "desc": "رستاخیز شعله"},
    "رگ آناهیتا": {"mult": 1.19, "desc": "آب‌های مقدس"},
    "رگ رخش": {"mult": 1.17, "desc": "سرعت پهلوانی"},
    "رگ پوچی": {"mult": 1.22, "desc": "خلأ و نابودی"},
    "رگ بهشتی": {"mult": 1.2, "desc": "برکت آسمان"},
    "رگ زیرین": {"mult": 1.18, "desc": "جهان تاریک"},
    "رگ ای‌تری": {"mult": 1.21, "desc": "جریان ای‌تری"},
    "رگ الهی": {"mult": 1.25, "desc": "اراده خدایان"},
    "رگ زمان": {"mult": 1.18, "desc": "کندی و شتاب چی"},
    "رگ مکان": {"mult": 1.17, "desc": "جابه‌جایی انرژی"},
    "رگ خواب": {"mult": 1.12, "desc": "تذهیب در رؤیا"},
    "رگ جنگ": {"mult": 1.16, "desc": "چی رزمی"},
    "رگ صلح": {"mult": 1.14, "desc": "تثبیت آرام"},
}
MAX_VEINS = 5
_user_veins: dict[int, list] = {}

def get_veins(user_id: int) -> list:
    return _user_veins.get(user_id, [])

def unlock_vein(user_id: int, vein: str) -> str:
    vein = vein.strip()
    if vein not in SPIRITUAL_VEINS:
        # fuzzy
        for k in SPIRITUAL_VEINS:
            if vein in k or k in vein:
                vein = k
                break
    if vein not in SPIRITUAL_VEINS:
        return "رگ نامعتبر. /vein برای لیست"
    cur = _user_veins.setdefault(user_id, [])
    if vein in cur:
        return f"قبلاً {vein} داری."
    if len(cur) >= MAX_VEINS:
        return f"حداکثر {MAX_VEINS} رگ معنوی."
    cur.append(vein)
    info = SPIRITUAL_VEINS[vein]
    return f"✅ {vein} باز شد — {info['desc']} (×{info['mult']})"

def vein_mult(user_id: int) -> float:
    cur = get_veins(user_id)
    if not cur:
        return 1.0
    m = 1.0
    for v in cur:
        m *= SPIRITUAL_VEINS.get(v, {}).get("mult", 1.0)
    return m


# نژاد → نوع تذهیب / ضریب
RACES = [
    "انسان", "جن", "اهریمن", "فرشته", "اژدهازاده", "خون‌آشام", "روح‌پیمان", "غول", "پری", "سایه‌رو",
    "ققنوس‌زاده", "سیرن", "تایتان", "خندق‌نشین", "فرزند رعد", "یخ‌زاد", "جنگل‌رو", "ستاره‌پیمان",
    # نژادهای ایرانی / اساطیری
    "سیمرغ‌زاده", "دیوزاد", "پری‌ایرانی", "آناهیتا‌پیمان", "رخش‌تبار", "جمشید‌تبار",
    "فریدون‌زاده", "زال‌تبار", "رستم‌تبار", "هما‌زاده", "کاوه‌تبار", "ضحاک‌تبار",
]
# نژادهای فقط سازنده/ادمین
ADMIN_RACES = ["خدایان"]
ALL_RACES = RACES + ADMIN_RACES
RACE_CULT = {
    "انسان": {"bonus": 1.0, "style": "تذهیب متعادل", "desc": "همه‌فن‌حریف"},
    "جن": {"bonus": 1.25, "style": "تذهیب آتشین", "desc": "چی آتش سریع‌تر"},
    "اهریمن": {"bonus": 1.35, "style": "تذهیب شیطانی", "desc": "قدرت بالا، ریسک بالا"},
    "فرشته": {"bonus": 1.3, "style": "تذهیب نورانی", "desc": "ریشه نور/بهشتی بهتر"},
    "اژدهازاده": {"bonus": 1.4, "style": "تذهیب اژدها", "desc": "بدن و انرژی قوی"},
    "خون‌آشام": {"bonus": 1.2, "style": "تذهیب خون", "desc": "از دوئل انرژی می‌گیرد"},
    "روح‌پیمان": {"bonus": 1.35, "style": "تذهیب روحی", "desc": "قلمرو روح و زیرین"},
    "غول": {"bonus": 1.15, "style": "تذهیب جسمانی", "desc": "خون و زره بهتر"},
    "پری": {"bonus": 1.25, "style": "تذهیب طبیعت", "desc": "گیاه و کیمیاگری"},
    "سایه‌رو": {"bonus": 1.3, "style": "تذهیب تاریکی", "desc": "ریشه تاریکی و جاسوسی"},
    "ققنوس‌زاده": {"bonus": 1.45, "style": "تذهیب رستاخیز", "desc": "پس از مرگ ضعیف‌تر زنده می‌شود"},
    "سیرن": {"bonus": 1.28, "style": "تذهیب صوت", "desc": "چی از صدا و افسون"},
    "تایتان": {"bonus": 1.5, "style": "تذهیب عظمت", "desc": "قدرت و خون بسیار بالا"},
    "خندق‌نشین": {"bonus": 1.22, "style": "تذهیب زیرین", "desc": "دنیای زیرین و سم"},
    "فرزند رعد": {"bonus": 1.38, "style": "تذهیب آذرخش", "desc": "سرعت و ضربه رعد"},
    "یخ‌زاد": {"bonus": 1.32, "style": "تذهیب یخ", "desc": "کنترل و دفاع یخی"},
    "جنگل‌رو": {"bonus": 1.27, "style": "تذهیب بیشه", "desc": "باغ و حیوانات بهتر"},
    "ستاره‌پیمان": {"bonus": 1.48, "style": "تذهیب ستاره‌ای", "desc": "انرژی آسمانی و قلمرو بالا"},
    "سیمرغ‌زاده": {"bonus": 1.55, "style": "تذهیب سیمرغ", "desc": "حکمت و شفا — پرندهٔ اساطیری ایران"},
    "دیوزاد": {"bonus": 1.4, "style": "تذهیب دیو", "desc": "قدرت تاریک دیوان شاهنامه"},
    "پری‌ایرانی": {"bonus": 1.35, "style": "تذهیب پری", "desc": "افسون پری‌های ایرانی"},
    "آناهیتا‌پیمان": {"bonus": 1.5, "style": "تذهیب آب‌های مقدس", "desc": "برکت آناهیتا"},
    "رخش‌تبار": {"bonus": 1.42, "style": "تذهیب شجاعت", "desc": "سرعت و وفاداری رخش"},
    "جمشید‌تبار": {"bonus": 1.48, "style": "تذهیب شهریاری", "desc": "شکوه جمشید"},
    "فریدون‌زاده": {"bonus": 1.46, "style": "تذهیب عدالت", "desc": "پیروزی بر ضحاک"},
    "زال‌تبار": {"bonus": 1.44, "style": "تذهیب سپیدموی", "desc": "فرزند سیمرغ و خرد"},
    "رستم‌تبار": {"bonus": 1.6, "style": "تذهیب پهلوانی", "desc": "نیرومندترین تبار شاهنامه"},
    "هما‌زاده": {"bonus": 1.52, "style": "تذهیب سعادت", "desc": "مرغ سعادت ایرانی"},
    "کاوه‌تبار": {"bonus": 1.38, "style": "تذهیب قیام", "desc": "آهنگر و آزادی"},
    "ضحاک‌تبار": {"bonus": 1.45, "style": "تذهیب مارشانه", "desc": "قدرت نفرین‌شده"},
    "خدایان": {"bonus": 2.5, "style": "تذهیب ابدی", "desc": "نامیرا — فقط ادمین | هیچ‌گاه نمی‌میرد"},
}

def is_immortal_race(race: str | None) -> bool:
    return (race or "") == "خدایان"



# هرچه ریشه کمیاب‌تر، بازدهی تذهیب بالاتر؛ چندعنصری سخت‌تر (ضریب انرژی لازم)
ROOT_CULT_MULT = {
    "بدون ریشه": 0.5,
    "ریشه پنج‌عنصر": 1.0,
    "ریشه آتش": 1.1, "ریشه آب": 1.1, "ریشه چوب": 1.1, "ریشه فلز": 1.15, "ریشه خاک": 1.1,
    "ریشه دو‌عنصری آتش‌آب": 1.25, "ریشه دو‌عنصری چوب‌خاک": 1.25, "ریشه دو‌عنصری فلز‌آتش": 1.3,
    "ریشه سه‌عنصری": 1.45, "ریشه چهار‌عنصری": 1.7,
    "ریشه نور": 1.4, "ریشه تاریکی": 1.4, "ریشه روحی": 1.5, "ریشه روح": 1.55,
    "ریشه بهشتی": 1.7, "ریشه آسمانی": 1.9, "ریشه الهی": 2.2, "ریشه پوچی": 2.0,
    "ریشه ای‌تری": 1.85, "ریشه دوگانه": 1.6,
}
ROOT_HARD_MULT = {
    "ریشه دو‌عنصری آتش‌آب": 1.3, "ریشه دو‌عنصری چوب‌خاک": 1.3, "ریشه دو‌عنصری فلز‌آتش": 1.35,
    "ریشه سه‌عنصری": 1.6, "ریشه چهار‌عنصری": 2.0,
}

BODY_TYPES = [
    "بدن معمولی", "بدن چوب زمینی", "بدن بهشتی", "بدن اژدهای اعظم",
    "بدن خدایان", "بدن خدای غبطه‌انگیز", "بدن نورانی", "بدن تاریک", "بدن روحی",
]
BODY_BONUS = {
    "بدن معمولی": 1.0,
    "بدن چوب زمینی": 1.15,
    "بدن بهشتی": 1.4,
    "بدن اژدهای اعظم": 1.6,
    "بدن خدایان": 1.8,
    "بدن خدای غبطه‌انگیز": 2.0,
    "بدن نورانی": 1.35,
    "بدن تاریک": 1.35,
    "بدن روحی": 1.5,
}


def energy_needed_for_stage(stage: int, realm: str | None = None, root: str | None = None) -> int:
    """هر مرحله سخت‌تر؛ قلمروهای بالاتر گنجایش بیشتر"""
    from database.models_v2 import CULTIVATION_REALMS
    s = max(1, stage or 1)
    base = ENERGY_BASE + (s - 1) * ENERGY_PER_LEVEL_ADD
    # ضریب قلمرو
    try:
        ri = CULTIVATION_REALMS.index(realm) if realm in CULTIVATION_REALMS else 0
    except Exception:
        ri = 0
    mult = 1.0 + ri * 0.35
    hard = ROOT_HARD_MULT.get(root or '', 1.0)
    return int(base * mult * hard)




FORBIDDEN_TECH_NAME = "پرورش ممنوعه"

DEFAULT_TECHNIQUES = [
    {"name": "تنفس پایه", "description": "تکنیک ساده تذهیب برای مبتدیان", "grade": "پایه", "energy_bonus": 100, "required_root": None},
    {"name": "تنفس مهتاب", "description": "تنفس آرام شبانه — چی پایدار", "grade": "پایه", "energy_bonus": 180, "required_root": None},
    {"name": "تنفس کوهستان", "description": "نفس عمیق کوه — بدن و چی", "grade": "پایه", "energy_bonus": 220, "required_root": None},
    {"name": "تنفس موج آرام", "description": "ریتم آب — چی متوسط", "grade": "پایه", "energy_bonus": 200, "required_root": None},
    {"name": "تنفس جرقه", "description": "نفس آتش کوتاه — چی تند", "grade": "پایه", "energy_bonus": 250, "required_root": None},
    {"name": "تنفس چهارفصل", "description": "چرخش فصل‌ها — چی متعادل بالا", "grade": "متوسط", "energy_bonus": 420, "required_root": None},
    {"name": "تنفس نهان‌گاه", "description": "نفس مخفی سایه‌رو", "grade": "متوسط", "energy_bonus": 380, "required_root": None},
    {"name": "تنفس خون‌جریان", "description": "چی خون‌آشام‌گونه", "grade": "متوسط", "energy_bonus": 450, "required_root": None},
    {"name": "تنفس بال نور", "description": "نفس فرشته‌گون", "grade": "متوسط", "energy_bonus": 480, "required_root": "ریشه نور"},
    {"name": "تنفس دوزخ", "description": "نفس اهریمنی داغ", "grade": "متوسط", "energy_bonus": 500, "required_root": None},
    {"name": "تنفس ریشه کهن", "description": "نفس جنگل و چوب", "grade": "متوسط", "energy_bonus": 410, "required_root": "ریشه چوب"},
    {"name": "تنفس رعد شکسته", "description": "نفس رعد و سرعت", "grade": "بالا", "energy_bonus": 720, "required_root": None},
    {"name": "تنفس یخ ابدی", "description": "نفس یخ‌زاد", "grade": "بالا", "energy_bonus": 680, "required_root": None},
    {"name": "تنفس ققنوس", "description": "رستاخیز شعله — چی قوی", "grade": "بالا", "energy_bonus": 950, "required_root": None},
    {"name": "تنفس ستاره سقوط", "description": "چی ستاره‌ای", "grade": "بالا", "energy_bonus": 1100, "required_root": None},
    {"name": "تنفس تایتان", "description": "نفس عظیم جسمانی", "grade": "بالا", "energy_bonus": 880, "required_root": None},
    {"name": "تنفس خلأ", "description": "نفس پوچی و زیرین", "grade": "پیشرفته", "energy_bonus": 1800, "required_root": "ریشه پوچی"},
    {"name": "تنفس کهکشان", "description": "جریان ستاره و آسمان", "grade": "پیشرفته", "energy_bonus": 2400, "required_root": "ریشه آسمانی"},
    {"name": "تنفس ابدیت", "description": "نفس خدایان — فقط ریشه الهی", "grade": "پیشرفته", "energy_bonus": 5000, "required_root": "ریشه الهی"},
    {"name": "تنفس نه رود", "description": "نه مسیر چی همزمان", "grade": "پیشرفته", "energy_bonus": 2800, "required_root": None},
    {"name": "تنفس خاکستر زرین", "description": "بعد از سوختن قوی‌تر", "grade": "بالا", "energy_bonus": 820, "required_root": None},

    {"name": "جریان پنج‌عنصر", "description": "تکنیک متوسط بر پایه پنج عنصر", "grade": "متوسط", "energy_bonus": 300, "required_root": "ریشه پنج‌عنصر"},
    {"name": "شعله‌ی درونی", "description": "تکنیک آتشین", "grade": "متوسط", "energy_bonus": 350, "required_root": "ریشه آتش"},
    {"name": "موج آب", "description": "تکنیک ریشه آب", "grade": "متوسط", "energy_bonus": 350, "required_root": "ریشه آب"},
    {"name": "ریشه درخت", "description": "تکنیک ریشه چوب", "grade": "متوسط", "energy_bonus": 340, "required_root": "ریشه چوب"},
    {"name": "تیغه فلز", "description": "تکنیک ریشه فلز", "grade": "متوسط", "energy_bonus": 360, "required_root": "ریشه فلز"},
    {"name": "ستون خاک", "description": "تکنیک ریشه خاک", "grade": "متوسط", "energy_bonus": 340, "required_root": "ریشه خاک"},
    {"name": "نفس نورانی", "description": "تکنیک نور", "grade": "بالا", "energy_bonus": 600, "required_root": "ریشه نور"},
    {"name": "سایه ابدی", "description": "تکنیک تاریکی", "grade": "بالا", "energy_bonus": 600, "required_root": "ریشه تاریکی"},
    {"name": "همهمه روح", "description": "تکنیک روحی", "grade": "بالا", "energy_bonus": 700, "required_root": "ریشه روحی"},
    {"name": "تنفس اژدها", "description": "تنفس قوی", "grade": "بالا", "energy_bonus": 800, "required_root": None},
    {"name": "جریان آسمانی", "description": "تکنیک آسمانی", "grade": "پیشرفته", "energy_bonus": 1200, "required_root": None},
    {"name": "سکوت مرگ", "description": "تکنیک دنیای زیرین", "grade": "بالا", "energy_bonus": 900, "required_root": "ریشه روح"},
    {"name": "دعای بهشتی", "description": "تکنیک بهشتی", "grade": "پیشرفته", "energy_bonus": 1500, "required_root": "ریشه بهشتی"},
    {"name": "رعد آسمانی", "description": "تکنیک آسمانی", "grade": "پیشرفته", "energy_bonus": 2000, "required_root": "ریشه آسمانی"},
    {"name": "اراده الهی", "description": "تکنیک الهی", "grade": "پیشرفته", "energy_bonus": 3000, "required_root": "ریشه الهی"},
    {"name": "بلع پوچی", "description": "تکنیک پوچی", "grade": "پیشرفته", "energy_bonus": 2500, "required_root": "ریشه پوچی"},
    {"name": "جریان ای‌تری", "description": "تکنیک ای‌تری", "grade": "پیشرفته", "energy_bonus": 2200, "required_root": "ریشه ای‌تری"},
    {"name": "طوفان روح", "description": "باد و روح", "grade": "بالا", "energy_bonus": 750, "required_root": None},
    {"name": "زره سنگی", "description": "دفاع تذهیب", "grade": "متوسط", "energy_bonus": 280, "required_root": None},
    {"name": "چشم حقیقت", "description": "درک انرژی", "grade": "بالا", "energy_bonus": 500, "required_root": None},
    {"name": "پنجه ببر", "description": "حمله", "grade": "بالا", "energy_bonus": 550, "required_root": None},
    {"name": "مهر خون", "description": "مسیر شیطانی", "grade": "بالا", "energy_bonus": 650, "required_root": None},
    {"name": "نَفَس اژدهای سرخ", "description": "تکنیک اژدهازاده", "grade": "بالا", "energy_bonus": 900, "required_root": None},
    {"name": "سرود فرشتگان", "description": "تکنیک فرشته", "grade": "بالا", "energy_bonus": 850, "required_root": "ریشه نور"},
    {"name": "طلسم اهریمن", "description": "تکنیک اهریمن", "grade": "بالا", "energy_bonus": 950, "required_root": None},
    {"name": "رقص پری", "description": "تکنیک پری", "grade": "متوسط", "energy_bonus": 400, "required_root": None},
    {"name": "سایه سایه‌رو", "description": "تکنیک تاریکی پیشرفته", "grade": "پیشرفته", "energy_bonus": 1600, "required_root": "ریشه تاریکی"},
    {"name": "خون ابدی", "description": "تکنیک خون‌آشام", "grade": "بالا", "energy_bonus": 700, "required_root": None},
    {"name": "ستون غول", "description": "قدرت جسمانی", "grade": "متوسط", "energy_bonus": 380, "required_root": None},
    {"name": "پیمان روح", "description": "تکنیک روح‌پیمان", "grade": "پیشرفته", "energy_bonus": 1400, "required_root": "ریشه روحی"},
    {
        "name": "پرورش ممنوعه",
        "description": "⚠️ ممنوع: بار اول +۱ سطح. بعد قفل ابدی — فقط این تکنیک. هر بار استفاده +۱ چی",
        "grade": "ممنوعه",
        "energy_bonus": 1,
        "required_root": None,
    },
]


async def ensure_default_techniques(session: AsyncSession):
    result = await session.execute(select(CultivationTechnique))
    existing = {x.name for x in result.scalars().all()}
    for data in DEFAULT_TECHNIQUES:
        if data["name"] in existing:
            continue
        # فقط فیلدهای مدل
        allowed = {k: v for k, v in data.items() if k in ("name", "description", "grade", "energy_bonus", "required_root")}
        session.add(CultivationTechnique(**allowed))
    await session.commit()


async def get_or_create_cultivation(session: AsyncSession, user_id: int) -> Cultivation:
    result = await session.execute(
        select(Cultivation).where(Cultivation.user_id == user_id)
    )
    cult = result.scalar_one_or_none()
    if cult:
        return cult
    
    cult = Cultivation(
        user_id=user_id,
        spiritual_root="بدون ریشه"  # همه بدون ریشه شروع می‌کنن
    )
    session.add(cult)
    await session.commit()
    await session.refresh(cult)
    return cult


async def get_active_technique(session: AsyncSession, user_id: int) -> CultivationTechnique | None:
    result = await session.execute(
        select(UserTechnique, CultivationTechnique)
        .join(CultivationTechnique, UserTechnique.technique_id == CultivationTechnique.id)
        .where(UserTechnique.user_id == user_id, UserTechnique.is_active == True)
    )
    row = result.first()
    if row:
        return row[1]
    return None


async def has_forbidden_lock(session: AsyncSession, user_id: int) -> bool:
    """اگر پرورش ممنوعه یاد گرفته شده باشد قفل است"""
    result = await session.execute(
        select(UserTechnique, CultivationTechnique)
        .join(CultivationTechnique, UserTechnique.technique_id == CultivationTechnique.id)
        .where(UserTechnique.user_id == user_id, CultivationTechnique.name == FORBIDDEN_TECH_NAME)
    )
    return result.first() is not None


async def learn_technique(session: AsyncSession, user_id: int, technique: CultivationTechnique, from_user_id: int | None = None) -> str:
    # چک تکراری
    existing = await session.execute(
        select(UserTechnique).where(
            UserTechnique.user_id == user_id,
            UserTechnique.technique_id == technique.id
        )
    )
    if existing.scalar_one_or_none():
        return "این تکنیک رو قبلاً بلدی."

    cult = await get_or_create_cultivation(session, user_id)

    # قفل پرورش ممنوعه
    if await has_forbidden_lock(session, user_id) and technique.name != FORBIDDEN_TECH_NAME:
        return "⚠️ پرورش ممنوعه را یاد گرفته‌ای؛ دیگر نمی‌توانی تکنیک دیگری یاد بگیری یا فعال کنی."

    # چک ریشه مورد نیاز
    if technique.required_root and cult.spiritual_root != technique.required_root:
        if cult.spiritual_root == "بدون ریشه":
            return "هنوز ریشه معنوی نداری. باید به ریشه پنج‌عنصر برسی."
        return f"این تکنیک نیاز به «{technique.required_root}» داره."
    
    ut = UserTechnique(
        user_id=user_id,
        technique_id=technique.id,
        is_active=False,
        learned_from=from_user_id
    )
    session.add(ut)
    
    # اگر اولین تکنیکشه، فعالش کن
    any_active = await get_active_technique(session, user_id)
    if not any_active:
        ut.is_active = True

    # پرورش ممنوعه: قفل + فعال اجباری
    if technique.name == FORBIDDEN_TECH_NAME:
        result_all = await session.execute(
            select(UserTechnique).where(UserTechnique.user_id == user_id)
        )
        for other in result_all.scalars().all():
            other.is_active = (other.technique_id == technique.id)
        ut.is_active = True
        # علامت اولین استفاده هنوز نشده
        if cult.talent != "forbidden_used":
            cult.talent = "forbidden_ready"
        await session.commit()
        return (
            f"☠️ تکنیک «{FORBIDDEN_TECH_NAME}» یاد گرفته شد و قفل شد.\n"
            f"دیگر نمی‌توانی آن را برداری یا تکنیک دیگری فعال کنی.\n"
            f"اولین تذهیب با آن: +۱ سطح | هر بار استفاده: +۱ چی"
        )

    await session.commit()
    return f"✅ تکنیک «{technique.name}» یاد گرفته شد."


async def set_active_technique(session: AsyncSession, user_id: int, technique_id: int) -> str:
    if await has_forbidden_lock(session, user_id):
        # فقط اجازه فعال بودن همان ممنوعه
        result = await session.execute(
            select(CultivationTechnique).where(CultivationTechnique.id == technique_id)
        )
        tech = result.scalar_one_or_none()
        if not tech or tech.name != FORBIDDEN_TECH_NAME:
            return "⚠️ پرورش ممنوعه قفل است؛ نمی‌توانی تکنیک دیگری فعال کنی."
    result = await session.execute(
        select(UserTechnique).where(UserTechnique.user_id == user_id)
    )
    for ut in result.scalars().all():
        ut.is_active = (ut.technique_id == technique_id)
    await session.commit()
    return "تکنیک فعال تغییر کرد."




def energy_status_line(cult) -> str:
    need = energy_needed_for_stage(cult.stage, cult.realm, cult.spiritual_root)
    cur = int(cult.energy or 0)
    left = max(0, need - cur)
    return f"انرژی: {cur}/{need} | باقی تا سطح بعد: {left} | {cult.realm} مرحله {cult.stage}"

async def add_energy(session: AsyncSession, user_id: int, amount: int) -> dict:
    cult = await get_or_create_cultivation(session, user_id)
    messages = []
    root = cult.spiritual_root or "بدون ریشه"
    rmult = ROOT_CULT_MULT.get(root, 1.0)
    bmult = BODY_BONUS.get(getattr(cult, "body_type", None) or "بدن معمولی", 1.0)
    # race bonus
    race_mult = 1.0
    try:
        from database.models import User as _U
        _u = await session.get(_U, user_id)
        if _u and getattr(_u, "race", None):
            race_mult = float(RACE_CULT.get(_u.race, {}).get("bonus", 1.0))
    except Exception:
        pass
    vmult = 1.0
    try:
        vmult = vein_mult(user_id)
    except Exception:
        pass
    amount = max(1, int(amount * rmult * bmult * race_mult * vmult))

    if root == "بدون ریشه":
        cult.energy += amount
        if cult.energy >= ROOT_UNLOCK_ENERGY:
            roots = [
                ("ریشه پنج‌عنصر", 18),
                ("ریشه آتش", 6), ("ریشه آب", 6), ("ریشه چوب", 6),
                ("ریشه فلز", 6), ("ریشه خاک", 6),
                ("ریشه دو‌عنصری آتش‌آب", 5), ("ریشه دو‌عنصری چوب‌خاک", 5),
                ("ریشه دو‌عنصری فلز‌آتش", 4),
                ("ریشه سه‌عنصری", 3), ("ریشه چهار‌عنصری", 2),
                ("ریشه نور", 4), ("ریشه تاریکی", 4),
                ("ریشه روحی", 3), ("ریشه روح", 3),
                ("ریشه بهشتی", 2), ("ریشه آسمانی", 2),
                ("ریشه الهی", 1), ("ریشه پوچی", 1),
                ("ریشه ای‌تری", 2), ("ریشه دوگانه", 2),
            ]
            names, weights = zip(*roots)
            chosen = random.choices(names, weights=weights, k=1)[0]
            cult.spiritual_root = chosen
            cult.energy = 0
            if cult.realm == "بیداری":
                cult.realm = "پایه"
                cult.stage = 1
            messages.append(f"🌟 ریشه «{chosen}» بیدار شد!")
            messages.append(f"قلمرو: {cult.realm}")
        await session.commit()
        return {
            "energy": cult.energy,
            "stage": cult.stage,
            "realm": cult.realm,
            "root": cult.spiritual_root,
            "messages": messages or [f"در حال بیدار کردن ریشه... ({cult.energy}/{ROOT_UNLOCK_ENERGY})"],
        }

    tech = await get_active_technique(session, user_id)
    # پرورش ممنوعه: هر بار +۱ چی؛ بار اول +۱ سطح
    if tech and tech.name == FORBIDDEN_TECH_NAME:
        amount = amount + 1  # یک چی
        messages.append("☠️ پرورش ممنوعه: +۱ چی")
        if cult.talent == "forbidden_ready":
            cult.stage = (cult.stage or 1) + 1
            if cult.stage > MAX_STAGE:
                cult.stage = 1
                try:
                    idx = CULTIVATION_REALMS.index(cult.realm)
                    if idx < len(CULTIVATION_REALMS) - 1:
                        cult.realm = CULTIVATION_REALMS[idx + 1]
                except ValueError:
                    pass
            cult.talent = "forbidden_used"
            try:
                from database.models import User
                u = await session.get(User, user_id)
                if u:
                    u.level = (u.level or 1) + 1
            except Exception:
                pass
            messages.append("☠️ اولین استفاده پرورش ممنوعه: +۱ سطح تذهیب و +۱ سطح بازی!")
    if not tech:
        messages.append("ℹ️ تکنیک فعال نداری — فقط انرژی پایه ذخیره می‌شود. /learntech")
        bonus = 0
    else:
        bonus = getattr(tech, "energy_bonus", 0) or 0
        amount = amount + int(bonus)
    cult.energy = int(cult.energy or 0) + int(amount)
    messages.append(f"+{amount} انرژی (ریشه ×{rmult:.2f} | بدن ×{bmult:.2f})")

    leveled = False
    while cult.energy >= energy_needed_for_stage(cult.stage, cult.realm, cult.spiritual_root):
        need = energy_needed_for_stage(cult.stage, cult.realm, cult.spiritual_root)
        cult.energy -= need
        cult.stage += 1
        leveled = True
        if cult.stage > MAX_STAGE:
            cult.stage = 1
            try:
                idx = CULTIVATION_REALMS.index(cult.realm)
                if idx < len(CULTIVATION_REALMS) - 1:
                    cult.realm = CULTIVATION_REALMS[idx + 1]
                    messages.append(f"🌟 قلمرو → «{cult.realm}»")
                    try:
                        from services.economy import get_or_create_wallet
                        w = await get_or_create_wallet(session, cult.user_id)
                        import random as _r
                        reward = _r.choice([("coins", 150), ("spirit", 1), ("heavenly", 1)])
                        if reward[0] == "coins":
                            w.coins += reward[1]
                            messages.append(f"🎁 +{reward[1]} سکه")
                        elif reward[0] == "spirit":
                            w.spirit_stones += reward[1]
                            messages.append(f"🎁 +{reward[1]} سنگ روحی")
                        else:
                            w.heavenly_stones = (w.heavenly_stones or 0) + 1
                            messages.append("🎁 +۱ سنگ بهشتی")
                    except Exception:
                        pass
                else:
                    cult.stage = MAX_STAGE
                    cult.energy = energy_needed_for_stage(cult.stage, cult.realm, cult.spiritual_root) - 1
            except ValueError:
                pass
        messages.append(f"⬆️ مرحله {cult.stage}/{MAX_STAGE} | {cult.realm}")

    await session.commit()
    return {
        "energy": cult.energy,
        "stage": cult.stage,
        "realm": cult.realm,
        "root": cult.spiritual_root,
        "messages": messages,
    }
