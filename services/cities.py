"""شهرها و سرزمین‌های جهان رزمی — کاملاً بازنویسی‌شده با تم رزمی/تذهیب"""
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User

# ========== جهان رزمی — قلمروهای اصلی ==========
CITIES = [
    # دشت آغازین
    {"id": "start", "name": "شهر آغازین", "country": "دشت آغازین", "province": "مرکز", "stage": "آغاز راه", "bonus": "xp", "desc": "دروازه ورود به جهان رزمی — +۵٪ XP دوئل", "world": "جهان رزمی"},
    {"id": "market_thousand", "name": "بازار هزارراه", "country": "دشت آغازین", "province": "مرکز", "stage": "تجارت", "bonus": "trade", "desc": "بازار بزرگ کاروان‌ها — تجارت پررونق", "world": "جهان رزمی"},
    {"id": "silver_river", "name": "رودخانه نقره‌ای", "country": "دشت آغازین", "province": "شمال", "stage": "بقا", "bonus": "cult", "desc": "آب چی‌دار — تذهیب آرام", "world": "جهان رزمی"},
    {"id": "night_whisper", "name": "جنگل نجوای شب", "country": "دشت آغازین", "province": "شرق", "stage": "شکار", "bonus": "power", "desc": "جانوران روحی و رازهای کهن", "world": "جهان رزمی"},
    {"id": "blade_village", "name": "دهکده تیغ", "country": "دشت آغازین", "province": "غرب", "stage": "آهنگری", "bonus": "craft", "desc": "استادان شمشیرسازی", "world": "جهان رزمی"},
    # کوه رعد
    {"id": "thunder_peak", "name": "قله رعد", "country": "کوهستان رعد", "province": "بلندای رعد", "stage": "آزمایش", "bonus": "power", "desc": "صاعقه و اراده — قدرت رزمی بیشتر", "world": "جهان رزمی"},
    {"id": "storm_forge", "name": "کوره طوفان", "country": "کوهستان رعد", "province": "بلندای رعد", "stage": "ساخت", "bonus": "craft", "desc": "آهن رعدآسا برای سلاح‌های نادر", "world": "جهان رزمی"},
    {"id": "echo_cave", "name": "غار پژواک", "country": "کوهستان رعد", "province": "دره‌ها", "stage": "مراقبه", "bonus": "cult", "desc": "پژواک انرژی درونی", "world": "جهان رزمی"},
    # دره شمشیرها
    {"id": "sword_valley", "name": "دره شمشیرها", "country": "دره فولاد", "province": "مرکز دره", "stage": "دوئل", "bonus": "power", "desc": "میدان آزمون جنگجویان", "world": "جهان رزمی"},
    {"id": "honor_hall", "name": "سالن افتخار", "country": "دره فولاد", "province": "مرکز دره", "stage": "رتبه", "bonus": "xp", "desc": "ثبت نام قهرمانان جهان رزمی", "world": "جهان رزمی"},
    {"id": "blood_arena", "name": "آرنای خون", "country": "دره فولاد", "province": "جنوب", "stage": "نبرد", "bonus": "power", "desc": "نبرد تا آخرین نفس", "world": "جهان رزمی"},
    # سرزمین طلسم
    {"id": "seal_city", "name": "شهر مهرها", "country": "سرزمین طلسم", "province": "مهرستان", "stage": "طلسم", "bonus": "craft", "desc": "استادان طلسم‌نویسی", "world": "جهان رزمی"},
    {"id": "ink_lake", "name": "دریاچه جوهر", "country": "سرزمین طلسم", "province": "مهرستان", "stage": "جوهر", "bonus": "cult", "desc": "جوهر ازلی برای طلسم‌های قوی", "world": "جهان رزمی"},
    {"id": "paper_sanctum", "name": "صومعه کاغذ", "country": "سرزمین طلسم", "province": "غرب", "stage": "دانش", "bonus": "herb", "desc": "کتابخانه تکنیک‌های گمشده", "world": "جهان رزمی"},
    # مرز پوچی
    {"id": "void_gate", "name": "دروازه پوچی", "country": "مرز پوچی", "province": "لبه جهان", "stage": "خطر", "bonus": "power", "desc": "جایی که قوانین سست می‌شوند", "world": "جهان رزمی"},
    {"id": "ash_camp", "name": "اردوگاه خاکستر", "country": "مرز پوچی", "province": "لبه جهان", "stage": "بقا", "bonus": "coin", "desc": "بازماندگان جنگ‌های کهن", "world": "جهان رزمی"},
    {"id": "silent_watch", "name": "دیدهبان خاموش", "country": "مرز پوچی", "province": "برج‌ها", "stage": "دیدهبانی", "bonus": "lifespan", "desc": "نگهبانان مرز — عمر پایدار", "world": "جهان رزمی"},
    # دشت اژدها
    {"id": "dragon_plain", "name": "دشت اژدها", "country": "قلمرو اژدها", "province": "دشت آتش", "stage": "اژدها", "bonus": "power", "desc": "رد پای اژدهایان کهن", "world": "جهان رزمی"},
    {"id": "scale_market", "name": "بازار فلس", "country": "قلمرو اژدها", "province": "دشت آتش", "stage": "تجارت نادر", "bonus": "trade", "desc": "فلس و خون اژدها", "world": "جهان رزمی"},
    {"id": "ember_temple", "name": "معبد اخگر", "country": "قلمرو اژدها", "province": "کوه آتش", "stage": "پرستش", "bonus": "cult", "desc": "آتش درونی و اراده", "world": "جهان رزمی"},
    # آسمان‌شهرها (مختصر برای آسمان‌های بالاتر)
    {"id": "sky_1_gate", "name": "دروازه آسمان اول", "country": "آسمان اول", "province": "دشت چی", "stage": "صعود", "bonus": "xp", "desc": "آغاز مسیر ۹ آسمان", "world": "جهان رزمی"},
    {"id": "mist_city", "name": "شهر مهتاب", "country": "آسمان دوم", "province": "مهستان", "stage": "مه", "bonus": "cult", "desc": "تذهیب در مه ابدی", "world": "جهان رزمی"},
    {"id": "nine_river", "name": "شهر نه‌رود", "country": "آسمان سوم", "province": "نه‌رود", "stage": "جریان", "bonus": "cult", "desc": "۹ رود چی", "world": "جهان رزمی"},
    {"id": "red_stone", "name": "شهر سنگ‌سرخ", "country": "آسمان چهارم", "province": "اژدهاکوه", "stage": "سنگ", "bonus": "power", "desc": "سنگ‌های قدرت‌زا", "world": "جهان رزمی"},
    {"id": "star_float", "name": "شهر شناور ستاره", "country": "آسمان پنجم", "province": "دریای ستاره", "stage": "ستاره", "bonus": "trade", "desc": "تجارت بین‌جهانی", "world": "جهان رزمی"},
    {"id": "spirit_calm", "name": "شهر ارواح آرام", "country": "آسمان ششم", "province": "روحستان", "stage": "روح", "bonus": "lifespan", "desc": "آرامش روح و عمر", "world": "جهان رزمی"},
    {"id": "throne_city", "name": "شهر عرش", "country": "آسمان هفتم", "province": "عرش", "stage": "عرش", "bonus": "power", "desc": "نزدیک به قوانین برتر", "world": "جهان رزمی"},
    {"id": "void_edge", "name": "شهر خلأ", "country": "آسمان هشتم", "province": "مرز پوچی", "stage": "خلأ", "bonus": "power", "desc": "لبه نیستی", "world": "جهان رزمی"},
    {"id": "creator_crown", "name": "شهر تاج خالق", "country": "آسمان نهم", "province": "تاج خالق", "stage": "افسانه", "bonus": "xp", "desc": "پایان مسیر ۹ آسمان — افسانه‌ها", "world": "جهان رزمی"},
]

# شهرهای دنیاهای فرعی (برای سازگاری با کد قدیمی — نگاشت به تم رزمی)
def _gen_world_cities(prefix: str, world: str, country: str, province: str, names: list, bonus: str):
    out = []
    for i, name in enumerate(names, 1):
        out.append({
            "id": f"{prefix}_{i}",
            "name": name,
            "country": country,
            "province": province,
            "stage": f"{world}-{i}",
            "bonus": bonus,
            "desc": f"شهر {world}",
            "world": world,
        })
    return out

HEAVEN_CITIES = _gen_world_cities(
    "heaven", "بهشتی", "دنیای بهشتی", "آسمان نور",
    ["دروازه نور", "باغ سپید", "معبد بال", "چشمه حیات", "قصر ابر",
     "بازار نورانی", "قلعه سپیده", "جنگل کریستال", "دره زمزم", "شهر همهمه",
     "صومعه سپید", "آسمان‌آباد", "فردوس کوچک", "گلدسته اعلی", "کوی فرشته",
     "بندر مهتاب", "تپه یاقوت", "وادی سلام", "کاخ عدن", "برج سپیده",
     "دشت حریر", "چاه نور", "گذرگاه بال", "معبد دعا", "شهر آرام",
     "کوی ستاره", "باغ ابدی", "قلعه سپید", "رود نور", "تاج بهشت"],
    "cult",
)
UNDER_CITIES = _gen_world_cities(
    "under", "زیرین", "دنیای زیرین", "تاریکی",
    ["دروازه استخوان", "بازار سایه", "معبد خون", "چاه زهر", "قلعه شب",
     "اردوگاه خاکستر", "غار فریاد", "رود سیاه", "شهر زنجیر", "برج وحشت",
     "کوی شیطان", "دشت استخوان", "معبد نفرین", "بندر تاریک", "تپه جمجمه",
     "وادی گریه", "کاخ ظلمت", "جنگل مرده", "چشمه زهر", "گذرگاه سایه",
     "شهر نفرین", "قلعه خون", "بازار روح", "معبد ترس", "کوی خاکستر",
     "دشت نفرین", "رود خون", "برج شب", "غار مرگ", "تاج زیرین"],
    "power",
)
DEMON_CITIES = _gen_world_cities("demon", "شیطانی", "قلمرو شیطان", "آتش سیاه",
    [f"دژ شیطان {i}" for i in range(1, 16)], "power")
SKY_CITIES = _gen_world_cities("sky", "آسمانی", "قلمرو آسمان", "ابرها",
    [f"ابرشهر {i}" for i in range(1, 16)], "cult")
SPIRIT_CITIES = _gen_world_cities("spirit", "روحی", "قلمرو روح", "مه روح",
    [f"شهر روح {i}" for i in range(1, 16)], "lifespan")
ICE_CITIES = _gen_world_cities("ice", "یخی", "قلمرو یخ", "قطب",
    [f"دژ یخ {i}" for i in range(1, 16)], "power")
FIRE_CITIES = _gen_world_cities("fire", "آتشین", "قلمرو آتش", "ماگما",
    [f"شهر اخگر {i}" for i in range(1, 16)], "power")
VOID_CITIES = _gen_world_cities("void", "پوچی", "قلمرو پوچی", "خلأ",
    [f"نقطه خلأ {i}" for i in range(1, 16)], "power")
ETHEREAL_CITIES = _gen_world_cities("eth", "ایتری", "قلمرو ایتری", "اتر",
    [f"شهر اتر {i}" for i in range(1, 16)], "cult")
FOREST_CITIES = _gen_world_cities("forest", "جنگلی", "قلمرو جنگل", "بیشه",
    [f"دهکده بیشه {i}" for i in range(1, 16)], "herb")
STAR_CITIES = _gen_world_cities("star", "ستاره‌ای", "قلمرو ستاره", "کهکشان",
    [f"بندر ستاره {i}" for i in range(1, 16)], "trade")
DRAGON_CITIES = _gen_world_cities("dragon", "اژدهایی", "قلمرو اژدها", "فلس",
    [f"لانه اژدها {i}" for i in range(1, 16)], "power")

WORLD_DEFAULT_CITY = {
    "جهان رزمی": "start",
    "فانی": "start",
    "بهشتی": "heaven_1",
    "زیرین": "under_1",
    "شیطانی": "demon_1",
    "آسمانی": "sky_1",
    "روحی": "spirit_1",
    "یخی": "ice_1",
    "آتشین": "fire_1",
    "پوچی": "void_1",
    "ایتری": "eth_1",
    "جنگلی": "forest_1",
    "ستاره‌ای": "star_1",
    "اژدهایی": "dragon_1",
}

ALL_WORLDS = list(WORLD_DEFAULT_CITY.keys())
ALL_CITIES = CITIES + HEAVEN_CITIES + UNDER_CITIES + DEMON_CITIES + SKY_CITIES + SPIRIT_CITIES + ICE_CITIES + FIRE_CITIES + VOID_CITIES + ETHEREAL_CITIES + FOREST_CITIES + STAR_CITIES + DRAGON_CITIES

# سلاح مخفی اولین بازدید — تم رزمی
CITY_HIDDEN_WEAPONS = {
    "start": ("خنجر نوآموز", 15),
    "blade_village": ("شمشیر دهکده تیغ", 28),
    "thunder_peak": ("نیزه رعد", 35),
    "sword_valley": ("تیغ افتخار", 40),
    "seal_city": ("خنجر مهر", 32),
    "void_gate": ("تیغ پوچی", 48),
    "dragon_plain": ("نیش اژدها", 55),
    "blood_arena": ("داس آرنا", 45),
    "ember_temple": ("شمشیر اخگر", 50),
    "creator_crown": ("تاج‌شکن", 70),
    "heaven_1": ("نیزه نور", 45),
    "heaven_10": ("شمشیر سپید", 50),
    "under_1": ("خنجر استخوان", 38),
    "under_10": ("شمشیر خون", 52),
}

NAME_TO_ID = {}
for c in ALL_CITIES:
    NAME_TO_ID[c["name"]] = c["id"]
    NAME_TO_ID[c["id"]] = c["id"]


async def ensure_user_city(session: AsyncSession, user: User) -> str:
    """اطمینان از شهر معتبر؛ شهرهای قدیمی ایران به شهر آغازین منتقل می‌شوند."""
    old_ids = {
        "tehran", "ray", "shahrerey", "mashhad", "neyshabur", "sabzevar",
        "isfahan", "kashan", "najafabad", "shiraz", "marvdasht", "lar",
        "bandarabbas", "khamir", "lengeh", "tabriz", "ahvaz", "kerman",
        "rasht", "newyork", "moscow", "فانی",
    }
    city = getattr(user, "city", None)
    if not city or city in old_ids or city not in NAME_TO_ID:
        user.city = "start"
        user.world = "جهان رزمی"
        try:
            await session.commit()
        except Exception:
            pass
    return user.city or "start"


def get_city(city_id: str) -> dict:
    for c in ALL_CITIES:
        if c["id"] == city_id:
            return c
    return CITIES[0]


def cities_for_world(world: str) -> list:
    w = world or "جهان رزمی"
    if w in ("جهان رزمی", "فانی"):
        return CITIES
    if w == "بهشتی":
        return HEAVEN_CITIES
    if w == "زیرین":
        return UNDER_CITIES
    if w == "شیطانی":
        return DEMON_CITIES
    if w == "آسمانی":
        return SKY_CITIES
    if w == "روحی":
        return SPIRIT_CITIES
    if w == "یخی":
        return ICE_CITIES
    if w == "آتشین":
        return FIRE_CITIES
    if w == "پوچی":
        return VOID_CITIES
    if w == "ایتری":
        return ETHEREAL_CITIES
    if w == "جنگلی":
        return FOREST_CITIES
    if w in ("ستاره‌ای", "ستارهای"):
        return STAR_CITIES
    if w in ("اژدهایی", "اژدها"):
        return DRAGON_CITIES
    return CITIES


def list_cities_text(current_id: str, limit_per_country: int = 6, world: str = "جهان رزمی") -> str:
    pool = cities_for_world(world)
    by_country = {}
    for c in pool:
        by_country.setdefault(c["country"], []).append(c)
    lines = [f"🏙 <b>شهرهای {world}</b>\n"]
    for country, items in by_country.items():
        lines.append(f"\n<b>{country}</b>")
        for c in items[:limit_per_country]:
            mark = " ✅" if c["id"] == current_id else ""
            lines.append(f"• {c['name']} — {c['stage']}{mark}")
        if len(items) > limit_per_country:
            lines.append(f"  … و {len(items) - limit_per_country} شهر دیگر")
    return "\n".join(lines)


def city_detail_text(city: dict) -> str:
    return (
        f"🏙 <b>{city['name']}</b>\n"
        f"کشور/قلمرو: {city.get('country', '—')}\n"
        f"استان: {city.get('province', '—')}\n"
        f"مرحله خاص: <b>{city['stage']}</b>\n"
        f"بونوس: {city.get('bonus', '—')}\n"
        f"{city.get('desc', '')}"
    )
