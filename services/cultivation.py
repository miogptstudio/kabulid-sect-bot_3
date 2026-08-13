import random
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models_v2 import Cultivation, CULTIVATION_REALMS
from database.models_v3 import CultivationTechnique, UserTechnique
from database.models import User

from bot.config import ROOT_UNLOCK_ENERGY, ENERGY_BASE, ENERGY_PER_LEVEL_ADD

MAX_STAGE = 15

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
from services.persist import get_dict as _vein_get, save as _vein_save
def _veins_map():
    return _vein_get("veins")


def get_veins(user_id: int) -> list:
    return _veins_map().get(str(int(user_id)), [])

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
    cur = _veins_map().setdefault(str(int(user_id)), [])
    if vein in cur:
        return f"قبلاً {vein} داری."
    if len(cur) >= MAX_VEINS:
        return f"حداکثر {MAX_VEINS} رگ معنوی."
    cur.append(vein)
    _vein_save("veins")
    info = SPIRITUAL_VEINS[vein]
    return f"✅ {vein} باز شد — {info['desc']} (×{info['mult']})"

def vein_mult(user_id: int, telegram_id: int | None = None) -> float:
    cur = get_veins(user_id)
    if not cur and telegram_id:
        cur = get_veins(telegram_id)
    if not cur:
        return 1.0
    m = 1.0
    for v in cur:
        m *= float(SPIRITUAL_VEINS.get(v, {}).get("mult", 1.0))
    return m


def root_cult_mult(root: str) -> float:
    """ضریب ریشه با تطبیق تقریبی نام"""
    if not root or root == "بدون ریشه":
        return 1.0
    if root in ROOT_CULT_MULT:
        return float(ROOT_CULT_MULT[root])
    # تطبیق جزئی
    best = 1.0
    for k, v in ROOT_CULT_MULT.items():
        if k in root or root in k:
            best = max(best, float(v))
    return best


# نژاد → نوع تذهیب / ضریب
RACES = [
    "انسان", "جن", "اهریمن", "فرشته", "اژدهازاده", "خون‌آشام", "روح‌پیمان", "غول", "پری", "سایه‌رو",
    "ققنوس‌زاده", "سیرن", "تایتان", "خندق‌نشین", "فرزند رعد", "یخ‌زاد", "جنگل‌رو", "ستاره‌پیمان",
    # نژادهای ایرانی / اساطیری
    "سیمرغ‌زاده", "دیوزاد", "پری‌ایرانی", "آناهیتا‌پیمان", "رخش‌تبار", "جمشید‌تبار",
    "فریدون‌زاده", "زال‌تبار", "رستم‌تبار", "هما‌زاده", "کاوه‌تبار", "ضحاک‌تبار",
    "نامیرا",
]
# نژادهای فقط سازنده/ادمین
ADMIN_RACES = ["خدایان", "قادر مطلق"]
ALL_RACES = RACES + ADMIN_RACES
STERILE_RACES = {"نامیرا", "قادر مطلق", "خدایان"}  # قدرت بالا، بدون تولیدمثل
RACE_CULT = {
    "نامیرا": {"bonus": 2.2, "style": "تذهیب ابدی", "desc": "نمی‌میرد آسان؛ قدرت بالا؛ بدون تولیدمثل"},
    "قادر مطلق": {"bonus": 10.0, "style": "تذهیب مطلق", "desc": "قدرت بی‌کران؛ شانس نزدیک صفر؛ بدون تولیدمثل"},
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
    # پنج عنصر پایه
    "ریشه پنج‌عنصر": 1.0,
    "ریشه آتش": 1.12, "ریشه آب": 1.12, "ریشه چوب": 1.12, "ریشه فلز": 1.15, "ریشه خاک": 1.12,
    "ریشه باد": 1.14, "ریشه رعد": 1.18, "ریشه یخ": 1.16, "ریشه شعله": 1.17,
    # دو عنصری
    "ریشه دو‌عنصری آتش‌آب": 1.28, "ریشه دو‌عنصری چوب‌خاک": 1.26, "ریشه دو‌عنصری فلز‌آتش": 1.3,
    "ریشه دو‌عنصری آب‌چوب": 1.26, "ریشه دو‌عنصری خاک‌فلز": 1.27, "ریشه دو‌عنصری باد‌رعد": 1.32,
    "ریشه دو‌عنصری یخ‌آتش": 1.33, "ریشه دو‌عنصری نور‌تاریکی": 1.4,
    # سه و چهار عنصری
    "ریشه سه‌عنصری": 1.48, "ریشه سه‌عنصری آتش‌آب‌چوب": 1.5, "ریشه سه‌عنصری فلز‌خاک‌رعد": 1.52,
    "ریشه چهار‌عنصری": 1.72, "ریشه چهار‌عنصری کامل": 1.8,
    # نور / تاریکی / روح
    "ریشه نور": 1.42, "ریشه تاریکی": 1.42, "ریشه روحی": 1.52, "ریشه روح": 1.55,
    "ریشه سایه": 1.38, "ریشه مه": 1.3, "ریشه خون": 1.45, "ریشه استخوان": 1.35,
    # آسمانی / الهی
    "ریشه بهشتی": 1.72, "ریشه آسمانی": 1.95, "ریشه الهی": 2.25, "ریشه پوچی": 2.05,
    "ریشه ای‌تری": 1.88, "ریشه دوگانه": 1.62, "ریشه ستاره‌ای": 1.9, "ریشه کهکشانی": 2.1,
    "ریشه زمانی": 1.85, "ریشه مکانی": 1.8, "ریشه خواب": 1.35, "ریشه رویا": 1.4,
    # اساطیر ایرانی
    "ریشه سیمرغ": 1.75, "ریشه دیو": 1.55, "ریشه آناهیتا": 1.65, "ریشه رخش": 1.5,
    "ریشه جمشید": 1.7, "ریشه فریدون": 1.68, "ریشه زال": 1.6, "ریشه رستم": 1.8,
    "ریشه هما": 1.72, "ریشه کاوه": 1.55, "ریشه ضحاک": 1.7, "ریشه مهر": 1.6,
    "ریشه آذر": 1.45, "ریشه ایزدی": 1.9, "ریشه اهریمنی": 1.75,
    # طبیعت و حیوانات معنوی
    "ریشه اژدها": 1.85, "ریشه ققنوس": 1.88, "ریشه ببر": 1.4, "ریشه گرگ": 1.38,
    "ریشه مار": 1.42, "ریشه عقاب": 1.48, "ریشه نهنگ": 1.5, "ریشه لاک‌پشت": 1.35,
    # کمیاب ویژه
    "ریشه هرج‌ومرج": 2.0, "ریشه نظم": 1.7, "ریشه زندگی": 1.65, "ریشه مرگ": 1.7,
    "ریشه آینه": 1.55, "ریشه کریستال": 1.5, "ریشه طلایی": 1.8, "ریشه نقره‌ای": 1.55,
    "ریشه کهن": 1.9, "ریشه ازلی": 2.15, "ریشه بی‌نام": 2.3, "ریشه خالق": 2.5,
    # --- گسترش بهشتی (۱۰+) ---
    "ریشه بهشت‌نور": 1.6, "ریشه فرشته‌بهشتی": 1.65, "ریشه باغ‌عدن": 1.7,
    "ریشه سدر بهشتی": 1.58, "ریشه ابر بهشتی": 1.52, "ریشه بال‌سفید": 1.62,
    "ریشه نیلوفر بهشتی": 1.57, "ریشه سرود بهشتی": 1.54, "ریشه نگهبان بهشت": 1.72,
    "ریشه دروازه بهشت": 1.68, "ریشه شهد بهشتی": 1.5, "ریشه سپیده بهشتی": 1.63,
    # --- گسترش آسمانی (۱۰+) ---
    "ریشه ستاره آسمان": 1.65, "ریشه رعد آسمانی": 1.7, "ریشه ابر آسمان": 1.55,
    "ریشه ماه آسمانی": 1.62, "ریشه خورشید آسمان": 1.75, "ریشه کهکشان آسمانی": 1.85,
    "ریشه شهاب آسمان": 1.68, "ریشه قطبی آسمان": 1.72, "ریشه نسیم آسمانی": 1.5,
    "ریشه تاج آسمان": 1.8, "ریشه پلکان آسمان": 1.7, "ریشه افق آسمانی": 1.66,
    # --- گسترش زیرین (۱۰+) ---
    "ریشه زیرین": 1.55, "ریشه دوزخ‌زیرین": 1.7, "ریشه سایه زیرین": 1.6,
    "ریشه استخوان‌زیرین": 1.65, "ریشه رود زیرین": 1.58, "ریشه گور زیرین": 1.62,
    "ریشه زنجیر زیرین": 1.68, "ریشه خاکستر زیرین": 1.55, "ریشه فریاد زیرین": 1.72,
    "ریشه نگهبان زیرین": 1.78, "ریشه تاریکی‌زیرین": 1.8, "ریشه زهر زیرین": 1.66,
    # --- گسترش خدایی (۱۰+) ---
    "ریشه خدایی": 1.9, "ریشه نیمه‌خدایی": 1.75, "ریشه خون خدایی": 1.95,
    "ریشه چشم خدایی": 1.88, "ریشه کلام خدایی": 1.92, "ریشه تاج خدایی": 2.0,
    "ریشه سپر خدایی": 1.85, "ریشه آتش خدایی": 1.9, "ریشه عدالت خدایی": 1.87,
    "ریشه خشم خدایی": 1.93, "ریشه برکت خدایی": 1.82, "ریشه معبد خدایی": 1.86,
    # --- گسترش خدا (۱۰+) ---
    "ریشه خدا": 2.2, "ریشه خدای‌واحد": 2.4, "ریشه خدای‌نور": 2.25,
    "ریشه خدای‌تاریکی": 2.25, "ریشه خدای‌زمان": 2.35, "ریشه خدای‌مکان": 2.3,
    "ریشه خدای‌مرگ": 2.28, "ریشه خدای‌زندگی": 2.28, "ریشه خدای‌جنگ": 2.2,
    "ریشه خدای‌صلح": 2.15, "ریشه خدای‌آسمان": 2.3, "ریشه خدای‌زیرین": 2.3,
    "ریشه خالق‌خدا": 2.5, "ریشه بی‌نام‌خدا": 2.55,

}
ROOT_HARD_MULT = {
    "ریشه دو‌عنصری آتش‌آب": 1.3, "ریشه دو‌عنصری چوب‌خاک": 1.3, "ریشه دو‌عنصری فلز‌آتش": 1.35,
    "ریشه دو‌عنصری آب‌چوب": 1.3, "ریشه دو‌عنصری خاک‌فلز": 1.32, "ریشه دو‌عنصری باد‌رعد": 1.4,
    "ریشه دو‌عنصری یخ‌آتش": 1.42, "ریشه دو‌عنصری نور‌تاریکی": 1.5,
    "ریشه سه‌عنصری": 1.6, "ریشه سه‌عنصری آتش‌آب‌چوب": 1.65, "ریشه سه‌عنصری فلز‌خاک‌رعد": 1.7,
    "ریشه چهار‌عنصری": 2.0, "ریشه چهار‌عنصری کامل": 2.2,
    "ریشه الهی": 1.5, "ریشه پوچی": 1.6, "ریشه ازلی": 1.8, "ریشه بی‌نام": 2.0, "ریشه خالق": 2.5,
    "ریشه سیمرغ": 1.4, "ریشه اژدها": 1.45, "ریشه ققنوس": 1.45, "ریشه کهکشانی": 1.7,
    "ریشه بهشتی": 1.35, "ریشه آسمانی": 1.45, "ریشه زیرین": 1.4,
    "ریشه خدایی": 1.55, "ریشه خدا": 1.8, "ریشه خدای‌واحد": 2.0,
    "ریشه کهکشان آسمانی": 1.6, "ریشه دوزخ‌زیرین": 1.5, "ریشه تاج خدایی": 1.7,

}

# وزن بیدار شدن ریشه (عدد بالاتر = شایع‌تر)
ROOT_AWAKEN_WEIGHTS = [
    ("ریشه پنج‌عنصر", 14),
    ("ریشه آتش", 5), ("ریشه آب", 5), ("ریشه چوب", 5), ("ریشه فلز", 5), ("ریشه خاک", 5),
    ("ریشه باد", 4), ("ریشه رعد", 3), ("ریشه یخ", 3), ("ریشه شعله", 3),
    ("ریشه دو‌عنصری آتش‌آب", 3), ("ریشه دو‌عنصری چوب‌خاک", 3), ("ریشه دو‌عنصری فلز‌آتش", 2),
    ("ریشه دو‌عنصری آب‌چوب", 2), ("ریشه دو‌عنصری خاک‌فلز", 2), ("ریشه دو‌عنصری باد‌رعد", 2),
    ("ریشه دو‌عنصری یخ‌آتش", 2), ("ریشه دو‌عنصری نور‌تاریکی", 1),
    ("ریشه سه‌عنصری", 2), ("ریشه سه‌عنصری آتش‌آب‌چوب", 1), ("ریشه سه‌عنصری فلز‌خاک‌رعد", 1),
    ("ریشه چهار‌عنصری", 1), ("ریشه چهار‌عنصری کامل", 1),
    ("ریشه نور", 3), ("ریشه تاریکی", 3), ("ریشه روحی", 2), ("ریشه روح", 2),
    ("ریشه سایه", 2), ("ریشه مه", 2), ("ریشه خون", 2), ("ریشه استخوان", 2),
    ("ریشه بهشتی", 1), ("ریشه آسمانی", 1), ("ریشه الهی", 1), ("ریشه پوچی", 1),
    ("ریشه ای‌تری", 1), ("ریشه دوگانه", 1), ("ریشه ستاره‌ای", 1), ("ریشه کهکشانی", 1),
    ("ریشه زمانی", 1), ("ریشه مکانی", 1), ("ریشه خواب", 2), ("ریشه رویا", 2),
    ("ریشه سیمرغ", 1), ("ریشه دیو", 2), ("ریشه آناهیتا", 1), ("ریشه رخش", 2),
    ("ریشه جمشید", 1), ("ریشه فریدون", 1), ("ریشه زال", 1), ("ریشه رستم", 1),
    ("ریشه هما", 1), ("ریشه کاوه", 2), ("ریشه ضحاک", 1), ("ریشه مهر", 2),
    ("ریشه آذر", 2), ("ریشه ایزدی", 1), ("ریشه اهریمنی", 1),
    ("ریشه اژدها", 1), ("ریشه ققنوس", 1), ("ریشه ببر", 2), ("ریشه گرگ", 2),
    ("ریشه مار", 2), ("ریشه عقاب", 2), ("ریشه نهنگ", 1), ("ریشه لاک‌پشت", 2),
    ("ریشه هرج‌ومرج", 1), ("ریشه نظم", 1), ("ریشه زندگی", 1), ("ریشه مرگ", 1),
    ("ریشه آینه", 1), ("ریشه کریستال", 2), ("ریشه طلایی", 1), ("ریشه نقره‌ای", 2),
    ("ریشه کهن", 1), ("ریشه ازلی", 1), ("ریشه بی‌نام", 1), ("ریشه خالق", 1),
    ("ریشه بهشت‌نور", 1), ("ریشه فرشته‌بهشتی", 1), ("ریشه باغ‌عدن", 1),
    ("ریشه سدر بهشتی", 1), ("ریشه ابر بهشتی", 1), ("ریشه بال‌سفید", 1),
    ("ریشه نیلوفر بهشتی", 1), ("ریشه سرود بهشتی", 1), ("ریشه نگهبان بهشت", 1),
    ("ریشه دروازه بهشت", 1), ("ریشه شهد بهشتی", 1), ("ریشه سپیده بهشتی", 1),
    ("ریشه ستاره آسمان", 1), ("ریشه رعد آسمانی", 1), ("ریشه ابر آسمان", 1),
    ("ریشه ماه آسمانی", 1), ("ریشه خورشید آسمان", 1), ("ریشه کهکشان آسمانی", 1),
    ("ریشه شهاب آسمان", 1), ("ریشه قطبی آسمان", 1), ("ریشه نسیم آسمانی", 1),
    ("ریشه تاج آسمان", 1), ("ریشه پلکان آسمان", 1), ("ریشه افق آسمانی", 1),
    ("ریشه زیرین", 1), ("ریشه دوزخ‌زیرین", 1), ("ریشه سایه زیرین", 1),
    ("ریشه استخوان‌زیرین", 1), ("ریشه رود زیرین", 1), ("ریشه گور زیرین", 1),
    ("ریشه زنجیر زیرین", 1), ("ریشه خاکستر زیرین", 1), ("ریشه فریاد زیرین", 1),
    ("ریشه نگهبان زیرین", 1), ("ریشه تاریکی‌زیرین", 1), ("ریشه زهر زیرین", 1),
    ("ریشه خدایی", 1), ("ریشه نیمه‌خدایی", 1), ("ریشه خون خدایی", 1),
    ("ریشه چشم خدایی", 1), ("ریشه کلام خدایی", 1), ("ریشه تاج خدایی", 1),
    ("ریشه سپر خدایی", 1), ("ریشه آتش خدایی", 1), ("ریشه عدالت خدایی", 1),
    ("ریشه خشم خدایی", 1), ("ریشه برکت خدایی", 1), ("ریشه معبد خدایی", 1),
    ("ریشه خدا", 1), ("ریشه خدای‌واحد", 1), ("ریشه خدای‌نور", 1),
    ("ریشه خدای‌تاریکی", 1), ("ریشه خدای‌زمان", 1), ("ریشه خدای‌مکان", 1),
    ("ریشه خدای‌مرگ", 1), ("ریشه خدای‌زندگی", 1), ("ریشه خدای‌جنگ", 1),
    ("ریشه خدای‌صلح", 1), ("ریشه خدای‌آسمان", 1), ("ریشه خدای‌زیرین", 1),
    ("ریشه خالق‌خدا", 1), ("ریشه بی‌نام‌خدا", 1),

]


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
    """فاصله سطح‌ها بیشتر؛ قلمروهای بالاتر خیلی سخت‌تر"""
    from database.models_v2 import CULTIVATION_REALMS
    s = max(1, stage or 1)
    base = ENERGY_BASE + (s - 1) * ENERGY_PER_LEVEL_ADD
    # ضریب نمایی‌تر با قلمرو
    try:
        ri = CULTIVATION_REALMS.index(realm) if realm in CULTIVATION_REALMS else 0
    except Exception:
        ri = 0
    # فاصله قلمروها خیلی بیشتر
    mult = 1.0 + ri * 0.85 + (ri ** 1.25) * 0.12
    # مرحله‌های آخر هر قلمرو سخت‌تر
    stage_mult = 1.0 + (s - 1) * 0.18
    hard = ROOT_HARD_MULT.get(root or '', 1.0)
    return int(base * mult * stage_mult * hard)




FORBIDDEN_TECH_NAME = "پرورش ممنوعه"

# نیازمندی قلمرو/مرحله برای هر تکنیک (و کتاب‌های هم‌نام)
# required_realm: حداقل قلمرو | required_stage: حداقل مرحله در همان قلمرو
TECH_REQUIREMENTS = {
    "تنفس پایه": {"realm": "بیداری", "stage": 1},
    "تنفس مهتاب": {"realm": "بیداری", "stage": 3},
    "تنفس کوهستان": {"realm": "پایه", "stage": 1},
    "تنفس بال نور": {"realm": "متوسط", "stage": 1},
    "تنفس ریشه کهن": {"realm": "پایه", "stage": 5},
    "جریان پنج‌عنصر": {"realm": "متوسط", "stage": 1},
    "شعله‌ی درونی": {"realm": "متوسط", "stage": 2},
    "موج آب": {"realm": "متوسط", "stage": 2},
    "ریشه درخت": {"realm": "متوسط", "stage": 2},
    "تیغه فلز": {"realm": "متوسط", "stage": 3},
    "ستون خاک": {"realm": "متوسط", "stage": 3},
    "نفس نورانی": {"realm": "بالا", "stage": 1},
    "سایه ابدی": {"realm": "بالا", "stage": 1},
    "همهمه روح": {"realm": "روح", "stage": 1},
    "تنفس اژدها": {"realm": "بالا", "stage": 5},
    "تنفس ستاره سقوط": {"realm": "آسمان", "stage": 1},
    "تنفس تایتان": {"realm": "پیشرفته", "stage": 3},
    "تنفس خلأ": {"realm": "پوچی", "stage": 1},
    "تنفس کهکشان": {"realm": "کهکشانی", "stage": 1},
    "تنفس ابدیت": {"realm": "خدا", "stage": 1},
    "ساخت جهان": {"realm": "خدا", "stage": 9},
    "تکنیک ساخت جهان": {"realm": "خدا", "stage": 9},
    "تنفس نه رود": {"realm": "استاد", "stage": 1},
    "تنفس خاکستر زرین": {"realm": "اوج", "stage": 1},
    "پیمان روح": {"realm": "روح", "stage": 3},
    "پرورش ممنوعه": {"realm": "پایه", "stage": 1},
    # کتاب‌ها (اگر به‌عنوان تکنیک ثبت شوند)
    "کتاب تذهیب پایه": {"realm": "بیداری", "stage": 1},
    "کتاب تذهیب میانه": {"realm": "میانه", "stage": 1},
    "کتاب هسته": {"realm": "هسته", "stage": 1},
    "کتاب روح": {"realm": "روح", "stage": 1},
    "کتاب آسمان": {"realm": "آسمان", "stage": 1},
    "کتاب پوچی": {"realm": "پوچی", "stage": 1},
    "کتاب ازلی": {"realm": "ازلی", "stage": 1},
}

DEFAULT_TECHNIQUES = [
    
    {"name": "ضربه اژدها", "description": "حمله سنگین | قلمرو بالا", "grade": "حمله", "energy_bonus": 200, "required_root": None},
    {"name": "تیغ باد", "description": "حمله سریع", "grade": "حمله", "energy_bonus": 180, "required_root": "ریشه باد"},
    {"name": "نیش تاریکی", "description": "حمله سایه‌ای", "grade": "حمله", "energy_bonus": 220, "required_root": "ریشه تاریکی"},
    {"name": "سپراه‌آهنین", "description": "دفاع بدنی", "grade": "دفاع", "energy_bonus": 150, "required_root": None},
    {"name": "دیوار نور", "description": "دفاع نورانی", "grade": "دفاع", "energy_bonus": 200, "required_root": "ریشه نور"},
    {"name": "پوسته اژدها", "description": "دفاع سنگین", "grade": "دفاع", "energy_bonus": 250, "required_root": None},
    {"name": "همهمه روح رزمی", "description": "تقویت روحی نبرد", "grade": "روحی", "energy_bonus": 300, "required_root": "ریشه روحی"},
    {"name": "پیوند ارواح", "description": "تکنیک روحی گروهی", "grade": "روحی", "energy_bonus": 280, "required_root": "ریشه روح"},
    {"name": "شعله خشم", "description": "حمله آتشین", "grade": "حمله", "energy_bonus": 240, "required_root": "ریشه آتش"},
    {"name": "موج دفاعی آب", "description": "دفاع آبی", "grade": "دفاع", "energy_bonus": 190, "required_root": "ریشه آب"},

    {"name": "نفس نور قدیس", "description": "ارتدوکس | تنفس نورانی", "grade": "ارتدوکس", "energy_bonus": 200, "required_root": None},
    {"name": "شمشیر عدالت", "description": "ارتدوکس | ضربه مقدس", "grade": "ارتدوکس", "energy_bonus": 280, "required_root": None},
    {"name": "زره فرشته", "description": "ارتدوکس | دفاع نور", "grade": "ارتدوکس", "energy_bonus": 220, "required_root": None},
    {"name": "سرود بهشت", "description": "ارتدوکس | تقویت روح", "grade": "ارتدوکس", "energy_bonus": 300, "required_root": "ریشه نور"},
    {"name": "نفس اهریمنی", "description": "شیطانی | تنفس تاریک", "grade": "شیطانی", "energy_bonus": 210, "required_root": None},
    {"name": "چنگال شیطان", "description": "شیطانی | حمله خونی", "grade": "شیطانی", "energy_bonus": 300, "required_root": None},
    {"name": "زره نفرین‌شده", "description": "شیطانی | دفاع تاریک", "grade": "شیطانی", "energy_bonus": 230, "required_root": None},
    {"name": "پیمان خون", "description": "شیطانی | پیوند اهریمنی", "grade": "شیطانی", "energy_bonus": 320, "required_root": "ریشه تاریکی"},
    {"name": "تنفس پایه", "description": "پایه مبتدیان | قلمرو: بیداری", "grade": "پایه", "energy_bonus": 100, "required_root": None},
    {"name": "تنفس مهتاب", "description": "چی پایدار شب | قلمرو: بیداری س۳+", "grade": "پایه", "energy_bonus": 180, "required_root": None},
    {"name": "تنفس کوهستان", "description": "نفس کوه | قلمرو: پایه", "grade": "پایه", "energy_bonus": 220, "required_root": None},
    {"name": "تنفس ریشه کهن", "description": "جنگل و چوب | پایه س۵+", "grade": "متوسط", "energy_bonus": 410, "required_root": "ریشه چوب"},
    {"name": "جریان پنج‌عنصر", "description": "پنج عنصر | متوسط", "grade": "متوسط", "energy_bonus": 300, "required_root": "ریشه پنج‌عنصر"},
    {"name": "شعله‌ی درونی", "description": "آتش | متوسط س۲", "grade": "متوسط", "energy_bonus": 350, "required_root": "ریشه آتش"},
    {"name": "موج آب", "description": "آب | متوسط س۲", "grade": "متوسط", "energy_bonus": 350, "required_root": "ریشه آب"},
    {"name": "ریشه درخت", "description": "چوب | متوسط", "grade": "متوسط", "energy_bonus": 340, "required_root": "ریشه چوب"},
    {"name": "تیغه فلز", "description": "فلز | متوسط س۳", "grade": "متوسط", "energy_bonus": 360, "required_root": "ریشه فلز"},
    {"name": "ستون خاک", "description": "خاک | متوسط س۳", "grade": "متوسط", "energy_bonus": 340, "required_root": "ریشه خاک"},
    {"name": "نفس نورانی", "description": "نور | قلمرو بالا", "grade": "بالا", "energy_bonus": 600, "required_root": "ریشه نور"},
    {"name": "سایه ابدی", "description": "تاریکی | بالا", "grade": "بالا", "energy_bonus": 600, "required_root": "ریشه تاریکی"},
    {"name": "همهمه روح", "description": "روحی | قلمرو روح", "grade": "بالا", "energy_bonus": 700, "required_root": "ریشه روحی"},
    {"name": "تنفس اژدها", "description": "قوی | بالا س۵", "grade": "بالا", "energy_bonus": 800, "required_root": None},
    {"name": "تنفس بال نور", "description": "فرشته‌گون | متوسط+", "grade": "متوسط", "energy_bonus": 480, "required_root": "ریشه نور"},
    {"name": "تنفس تایتان", "description": "جسمانی | پیشرفته س۳", "grade": "بالا", "energy_bonus": 880, "required_root": None},
    {"name": "تنفس ستاره سقوط", "description": "ستاره‌ای | آسمان", "grade": "بالا", "energy_bonus": 1100, "required_root": None},
    {"name": "تنفس خاکستر زرین", "description": "بعد سوختن | اوج", "grade": "بالا", "energy_bonus": 820, "required_root": None},
    {"name": "تنفس نه رود", "description": "نه مسیر چی | استاد", "grade": "پیشرفته", "energy_bonus": 2800, "required_root": None},
    {"name": "تنفس خلأ", "description": "پوچی | قلمرو پوچی", "grade": "پیشرفته", "energy_bonus": 1800, "required_root": "ریشه پوچی"},
    {"name": "تنفس کهکشان", "description": "کهکشانی", "grade": "پیشرفته", "energy_bonus": 2400, "required_root": "ریشه آسمانی"},
    {"name": "تنفس ابدیت", "description": "خدایان | قلمرو خدا", "grade": "پیشرفته", "energy_bonus": 5000, "required_root": "ریشه الهی"},
    {"name": "ساخت جهان", "description": "تکنیک نهایی | آفرینش پاره‌جهان | قلمرو خدا س۹+ | بی‌طرف | با فعال‌سازی چی عظیم و بونوس قدرت جهان‌ساز", "grade": "افسانه‌ای", "energy_bonus": 50000, "required_root": "ریشه خالق"},
    {"name": "پیمان روح", "description": "روح‌پیمان | روح س۳", "grade": "پیشرفته", "energy_bonus": 1400, "required_root": "ریشه روحی"},
    {"name": "کتاب تذهیب پایه", "description": "کتاب قلمرو بیداری", "grade": "کتاب", "energy_bonus": 150, "required_root": None},
    {"name": "کتاب تذهیب میانه", "description": "کتاب قلمرو میانه", "grade": "کتاب", "energy_bonus": 400, "required_root": None},
    {"name": "کتاب هسته", "description": "کتاب قلمرو هسته", "grade": "کتاب", "energy_bonus": 900, "required_root": None},
    {"name": "کتاب روح", "description": "کتاب قلمرو روح", "grade": "کتاب", "energy_bonus": 1500, "required_root": None},
    {"name": "کتاب آسمان", "description": "کتاب قلمرو آسمان", "grade": "کتاب", "energy_bonus": 2500, "required_root": None},
    {"name": "کتاب پوچی", "description": "کتاب قلمرو پوچی", "grade": "کتاب", "energy_bonus": 4000, "required_root": None},
    {"name": "کتاب ازلی", "description": "کتاب قلمرو ازلی", "grade": "کتاب", "energy_bonus": 8000, "required_root": None},
    {
        "name": "پرورش ممنوعه",
        "description": "⚠️ ممنوع: بار اول +۱ سطح. قفل ابدی. هر بار +۱ چی | حداقل پایه",
        "grade": "ممنوعه",
        "energy_bonus": 1,
        "required_root": None,
    },
]


def can_learn_tech(cult, technique_name: str) -> tuple[bool, str]:
    """چک قلمرو و مرحله برای یادگیری تکنیک/کتاب"""
    req = TECH_REQUIREMENTS.get(technique_name)
    if not req:
        return True, ""
    need_realm = req.get("realm")
    need_stage = int(req.get("stage") or 1)
    from database.models_v2 import CULTIVATION_REALMS
    cur_realm = cult.realm or "بیداری"
    cur_stage = int(cult.stage or 1)
    try:
        ci = CULTIVATION_REALMS.index(cur_realm) if cur_realm in CULTIVATION_REALMS else 0
        ni = CULTIVATION_REALMS.index(need_realm) if need_realm in CULTIVATION_REALMS else 0
    except Exception:
        ci, ni = 0, 0
    if ci < ni:
        return False, f"نیاز به قلمرو «{need_realm}» یا بالاتر (الان: {cur_realm})"
    if ci == ni and cur_stage < need_stage:
        return False, f"در قلمرو {need_realm} حداقل مرحله {need_stage} لازم است (الان: {cur_stage})"
    return True, ""


async def ensure_default_techniques(session: AsyncSession):
    result = await session.execute(select(CultivationTechnique))
    existing = {x.name for x in result.scalars().all()}
    for data in DEFAULT_TECHNIQUES:
        if data['name'] in existing:
            continue
        allowed = {k: v for k, v in data.items() if k in ('name', 'description', 'grade', 'energy_bonus', 'required_root')}
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

    # چک قلمرو / مرحله
    ok, why = can_learn_tech(cult, technique.name)
    if not ok:
        return f"🔒 {why}"

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
        try:
            from services.forbidden_lock import lock_consume
            # user telegram id via User
            from database.models import User
            u = await session.get(User, user_id)
            if u and getattr(u, "telegram_id", None):
                lock_consume(int(u.telegram_id))
        except Exception:
            pass
        return (
            f"☠️ تکنیک «{FORBIDDEN_TECH_NAME}» یاد گرفته شد و قفل شد.\n"
            f"دیگر نمی‌توانی آن را برداری یا تکنیک دیگری فعال کنی.\n"
            f"اولین تذهیب با آن: +۱ سطح | هر بار استفاده: +۱ چی\n"
            f"☠️ قفل مصرف: دیگر هیچ چای/قرص/آیتمی مصرف نمی‌کنی."
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
    """جمع انرژی با اعمال همه ضریب‌ها: ریشه، بدن، نژاد، رگ، مسیر، برج فرقه، خانه، ساختمان تذهیب، تکنیک"""
    base_amount = max(0, int(amount or 0))
    cult = await get_or_create_cultivation(session, user_id)
    messages: list[str] = []
    breakdown: list[str] = []

    tg = None
    user_obj = None
    try:
        from database.models import User as _U
        user_obj = await session.get(_U, user_id)
        if user_obj:
            tg = int(getattr(user_obj, "telegram_id", 0) or 0) or None
    except Exception:
        pass

    root = cult.spiritual_root or "بدون ریشه"
    rmult = root_cult_mult(root) if "root_cult_mult" in dir() else float(ROOT_CULT_MULT.get(root, 1.0))
    try:
        rmult = root_cult_mult(root)
    except Exception:
        rmult = float(ROOT_CULT_MULT.get(root, 1.0))
    bmult = float(BODY_BONUS.get(getattr(cult, "body_type", None) or "بدن معمولی", 1.0))

    race_mult = 1.0
    if user_obj and getattr(user_obj, "race", None):
        race_mult = float(RACE_CULT.get(user_obj.race, {}).get("bonus", 1.0))

    vmult = 1.0
    try:
        vmult = float(vein_mult(user_id, tg))
    except Exception:
        try:
            vmult = float(vein_mult(user_id))
        except Exception:
            vmult = 1.0

    # مسیر تذهیب (قدرت/سرعت/دفاع) — روی انرژی هم اثر می‌گذارد
    path_mult = 1.0
    path_name = "خالص"
    if tg:
        try:
            from services.cult_paths import mults, get_path
            path_name = get_path(tg)
            pm = mults(tg)
            # میانگین ضرایب مسیر به‌عنوان ضریب جذب چی
            path_mult = (float(pm.get("power", 1)) + float(pm.get("speed", 1)) + float(pm.get("defense", 1))) / 3.0
        except Exception:
            path_mult = 1.0

    # برج تهذیب فرقه
    tower_m = 1.0
    if user_obj:
        try:
            from services.sects import get_user_sect
            from services.sect_systems import tower_bonus
            mem = await get_user_sect(session, user_id)
            if mem:
                tower_m = float(tower_bonus(mem.sect_id))
        except Exception:
            tower_m = 1.0

    # ساختمان تذهیب شخصی
    build_m = 1.0
    if tg:
        try:
            from services.cult_building import bonus_mult
            build_m = float(bonus_mult(tg))
        except Exception:
            build_m = 1.0

    # خانه
    home_m = 1.0
    if tg:
        try:
            from services.housing import cult_bonus
            home_m = float(cult_bonus(tg))
        except Exception:
            home_m = 1.0

    # تکنیک فعال
    tech_bonus = 0
    tech_name = "—"
    try:
        tech = await get_active_technique(session, user_id)
        if tech:
            tech_name = tech.name
            tech_bonus = int(getattr(tech, "energy_bonus", 0) or 0)
    except Exception:
        tech = None

    # محاسبه نهایی
    mult_total = rmult * bmult * race_mult * vmult * path_mult * tower_m * build_m * home_m
    amount = max(1, int(base_amount * mult_total) + tech_bonus)

    breakdown.append(f"پایه: {base_amount}")
    if rmult != 1.0:
        breakdown.append(f"ریشه ×{rmult:.2f}")
    if bmult != 1.0:
        breakdown.append(f"بدن ×{bmult:.2f}")
    if race_mult != 1.0:
        breakdown.append(f"نژاد ×{race_mult:.2f}")
    if vmult != 1.0:
        breakdown.append(f"رگ ×{vmult:.2f}")
    if path_mult != 1.0:
        breakdown.append(f"مسیر({path_name}) ×{path_mult:.2f}")
    if tower_m != 1.0:
        breakdown.append(f"برج‌فرقه ×{tower_m:.2f}")
    if build_m != 1.0:
        breakdown.append(f"ساختمان‌تذهیب ×{build_m:.2f}")
    if home_m != 1.0:
        breakdown.append(f"خانه ×{home_m:.2f}")
    if tech_bonus:
        breakdown.append(f"تکنیک({tech_name}) +{tech_bonus}")

    # پرورش ممنوعه
    if tech and getattr(tech, "name", None) == FORBIDDEN_TECH_NAME:
        amount = amount + 1
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
            if user_obj:
                user_obj.level = (user_obj.level or 1) + 1
            messages.append("☠️ اولین استفاده پرورش ممنوعه: +۱ سطح")
            try:
                from services.forbidden_lock import lock_consume
                if tg:
                    lock_consume(tg)
            except Exception:
                pass

    if root == "بدون ریشه":
        cult.energy = int(cult.energy or 0) + amount
        if cult.energy >= ROOT_UNLOCK_ENERGY:
            roots = list(ROOT_AWAKEN_WEIGHTS)
            names, weights = zip(*roots)
            chosen = random.choices(names, weights=weights, k=1)[0]
            cult.spiritual_root = chosen
            cult.energy = 0
            if cult.realm == "بیداری":
                cult.realm = "پایه"
                cult.stage = 1
            messages.append(f"🌟 ریشه «{chosen}» بیدار شد!")
            messages.append(f"قلمرو: {cult.realm}")
        messages.append("📊 " + " | ".join(breakdown))
        messages.append(f"⚡ چی نهایی: +{amount}")
        await session.commit()
        return {
            "gained": amount,
            "energy": cult.energy,
            "stage": cult.stage,
            "realm": cult.realm,
            "root": cult.spiritual_root,
            "messages": messages or [f"در حال بیدار کردن ریشه... ({cult.energy}/{ROOT_UNLOCK_ENERGY})"],
        }

    if not tech:
        messages.append("ℹ️ تکنیک فعال نداری — /learntech")

    cult.energy = int(cult.energy or 0) + int(amount)
    messages.append("📊 " + " | ".join(breakdown))
    messages.append(f"⚡ چی نهایی: +{amount}")

    # ارتقای مرحله
    while True:
        need = energy_needed_for_stage(cult.stage or 1, cult.realm, cult.spiritual_root)
        if int(cult.energy or 0) < need:
            break
        cult.energy = int(cult.energy or 0) - need
        cult.stage = int(cult.stage or 1) + 1
        if cult.stage > MAX_STAGE:
            cult.stage = 1
            try:
                idx = CULTIVATION_REALMS.index(cult.realm)
                if idx < len(CULTIVATION_REALMS) - 1:
                    cult.realm = CULTIVATION_REALMS[idx + 1]
                    messages.append(f"🌌 عروج قلمرو → <b>{cult.realm}</b>")
                    # پاداش شانسی ساده
                    try:
                        from services.economy import get_or_create_wallet
                        w = await get_or_create_wallet(session, user_id)
                        w.coins = int(w.coins or 0) + 100
                        messages.append("🎁 +۱۰۰ سکه عروج")
                    except Exception:
                        pass
                else:
                    cult.stage = MAX_STAGE
                    cult.energy = need - 1
                    break
            except ValueError:
                break
        messages.append(f"⬆️ مرحله {cult.stage}/{MAX_STAGE} | {cult.realm}")

    await session.commit()
    return {
        "gained": amount,
        "energy": cult.energy,
        "stage": cult.stage,
        "realm": cult.realm,
        "root": cult.spiritual_root,
        "messages": messages,
    }


