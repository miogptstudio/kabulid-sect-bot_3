from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from database.models_v3 import Building, ShopItem, UserInventory
from database.models import User


# آیتم‌های پیش‌فرض: قرص، طلسم، مواد، گیاه، سلاح
DEFAULT_ITEMS = [
    # ===== داروخانه =====
    {
        "building_type": "داروخانه",
        "name": "قرص انرژی پایه",
        "item_type": "pill",
        "description": "۲۵ انرژی تذهیب می‌دهد",
        "price": 30,
        "effect": {"energy": 25}
    },
    {
        "building_type": "داروخانه",
        "name": "قرص بهبودی",
        "item_type": "pill",
        "description": "کمی XP می‌دهد",
        "price": 50,
        "effect": {"xp": 20}
    },
    # ===== طلسم‌خانه =====
    {
        "building_type": "طلسم‌خانه",
        "name": "طلسم محافظ ضعیف",
        "item_type": "talisman",
        "description": "یک بار از باخت سنگین جلوگیری می‌کند",
        "price": 100,
        "effect": {"protect": 1}
    },
    {
        "building_type": "طلسم‌خانه",
        "name": "کاغذ طلسم معمولی",
        "item_type": "talisman_paper",
        "description": "کاغذ پایه برای کشیدن طلسم",
        "price": 25,
        "effect": {}
    },
    {
        "building_type": "طلسم‌خانه",
        "name": "کاغذ طلسم معنوی",
        "item_type": "talisman_paper",
        "description": "کاغذ نادر با جوهر روح برای طلسم‌های قوی",
        "price": 90,
        "effect": {}
    },
    {
        "building_type": "طلسم‌خانه",
        "name": "جوهر روح",
        "item_type": "material",
        "description": "جوهر مخصوص نوشتن طلسم‌های معنوی",
        "price": 60,
        "effect": {}
    },
    # ===== کیمیاگری =====
    {
        "building_type": "کیمیاگری",
        "name": "مواد اولیه کیمیا",
        "item_type": "material",
        "description": "بسته پایه مواد کیمیاگری",
        "price": 20,
        "effect": {}
    },
    {
        "building_type": "کیمیاگری",
        "name": "پودر گوگرد",
        "item_type": "material",
        "description": "ماده شیمیایی برای معجون‌های آتشین",
        "price": 35,
        "effect": {}
    },
    {
        "building_type": "کیمیاگری",
        "name": "شیشه کیمیا",
        "item_type": "material",
        "description": "شیشه مخصوص نگهداری معجون",
        "price": 15,
        "effect": {}
    },
    {
        "building_type": "کیمیاگری",
        "name": "کریستال خالص",
        "item_type": "material",
        "description": "کریستال کمیاب برای معجون‌های پیشرفته",
        "price": 100,
        "effect": {}
    },
    # ===== باغ گیاهان =====
    {
        "building_type": "باغ گیاهان",
        "name": "گیاه معمولی - گل بهار",
        "item_type": "herb_normal",
        "description": "گیاه معمولی برای معجون‌های پایه",
        "price": 15,
        "effect": {}
    },
    {
        "building_type": "باغ گیاهان",
        "name": "گیاه معمولی - ریشه کوهی",
        "item_type": "herb_normal",
        "description": "ریشه مقاوم برای معجون‌های متوسط",
        "price": 25,
        "effect": {}
    },
    {
        "building_type": "باغ گیاهان",
        "name": "گیاه معنوی - برگ روح",
        "item_type": "herb_spiritual",
        "description": "گیاه معنوی کمیاب",
        "price": 80,
        "effect": {"energy": 10}
    },
    {
        "building_type": "باغ گیاهان",
        "name": "گیاه معنوی - گل ماه",
        "item_type": "herb_spiritual",
        "description": "گل معنوی نادر برای طلسم‌های قوی",
        "price": 120,
        "effect": {}
    },
    # ===== آهنگری =====
    {
        "building_type": "آهنگری",
        "name": "شمشیر آهنی",
        "item_type": "weapon",
        "description": "سلاح پایه",
        "price": 150,
        "effect": {"duel_power": 5}
    },
    {
        "building_type": "آهنگری",
        "name": "نیزه فولادی",
        "item_type": "weapon",
        "description": "سلاح متوسط",
        "price": 280,
        "effect": {"duel_power": 12}
    },
    {
        "building_type": "آهنگری",
        "name": "شمشیر روح‌دار",
        "item_type": "weapon",
        "description": "سلاح معنوی قوی",
        "price": 500,
        "effect": {"duel_power": 25}
    },
    {
        "building_type": "آهنگری",
        "name": "آهن خام",
        "item_type": "material",
        "description": "ماده اولیه برای ساخت سلاح",
        "price": 40,
        "effect": {}
    },
    {
        "building_type": "آهنگری",
        "name": "فولاد تصفیه‌شده",
        "item_type": "material",
        "description": "فولاد باکیفیت برای سلاح‌های بهتر",
        "price": 90,
        "effect": {}
    },
    {
        "building_type": "آهنگری",
        "name": "سنگ روح",
        "item_type": "material",
        "description": "سنگ معنوی برای ساخت سلاح روح‌دار",
        "price": 150,
        "effect": {}
    },

    {"building_type": "سالن تکنیک", "name": "کتاب تنفس پایه", "item_type": "tech_book", "description": "یادگیری تنفس پایه", "price": 100, "effect": {"learn_tech": "تنفس پایه"}},
    {"building_type": "سالن تکنیک", "name": "کتاب جریان پنج‌عنصر", "item_type": "tech_book", "description": "تکنیک پنج‌عنصر", "price": 250, "effect": {"learn_tech": "جریان پنج‌عنصر"}},
    {"building_type": "سالن تکنیک", "name": "کتاب شعله درونی", "item_type": "tech_book", "description": "تکنیک آتش", "price": 300, "effect": {"learn_tech": "شعله‌ی درونی"}},
    {"building_type": "سالن تکنیک", "name": "کتاب طوفان روح", "item_type": "tech_book", "description": "باد و روح", "price": 400, "effect": {"learn_tech": "طوفان روح"}},
    {"building_type": "سالن تکنیک", "name": "کتاب زره سنگی", "item_type": "tech_book", "description": "دفاع", "price": 280, "effect": {"learn_tech": "زره سنگی"}},
    {"building_type": "سالن تکنیک", "name": "کتاب چشم حقیقت", "item_type": "tech_book", "description": "درک انرژی", "price": 320, "effect": {"learn_tech": "چشم حقیقت"}},
    {"building_type": "سالن تکنیک", "name": "کتاب پنجه ببر", "item_type": "tech_book", "description": "حمله", "price": 450, "effect": {"learn_tech": "پنجه ببر"}},
    {"building_type": "سالن تکنیک", "name": "کتاب موج آسمانی", "item_type": "tech_book", "description": "پیشرفته", "price": 800, "effect": {"learn_tech": "موج آسمانی"}},
    {"building_type": "سالن تکنیک", "name": "کتاب نفس یخ", "item_type": "tech_book", "description": "یخ", "price": 400, "effect": {"learn_tech": "نفس یخ"}},
    {"building_type": "سالن تکنیک", "name": "کتاب تنفس اژدها", "item_type": "tech_book", "description": "اژدها", "price": 600, "effect": {"learn_tech": "تنفس اژدها"}},
    {"building_type": "سالن تکنیک", "name": "کتاب جریان آسمانی", "item_type": "tech_book", "description": "آسمانی", "price": 700, "effect": {"learn_tech": "جریان آسمانی"}},
    {"building_type": "سالن تکنیک", "name": "کتاب سکوت مرگ", "item_type": "tech_book", "description": "زیرین", "price": 900, "effect": {"learn_tech": "سکوت مرگ"}},
    {"building_type": "آهنگری", "name": "شمشیر آسمانی", "item_type": "weapon", "description": "سلاح قلمرو آسمان", "price": 2000, "effect": {"duel_power": 40}},
    {"building_type": "آهنگری", "name": "نیزه ای‌تری", "item_type": "weapon", "description": "سلاح ای‌تری", "price": 5000, "effect": {"duel_power": 80}},
    {"building_type": "آهنگری", "name": "خنجر شیطانی", "item_type": "weapon", "description": "مسیر شیطانی", "price": 1500, "effect": {"duel_power": 35}},
    {"building_type": "طلسم‌خانه", "name": "طلسم محافظ", "item_type": "talisman", "description": "کاهش آسیب", "price": 200, "effect": {}},
    {"building_type": "طلسم‌خانه", "name": "طلسم آتش", "item_type": "talisman", "description": "حمله آتشین", "price": 350, "effect": {"duel_power": 8}},
    {"building_type": "طلسم‌خانه", "name": "طلسم ای‌تری", "item_type": "talisman", "description": "قدرت اتر", "price": 2000, "effect": {"duel_power": 25}},
    {"building_type": "داروخانه", "name": "قرص عمر", "item_type": "pill", "description": "+۱۰ عمر", "price": 300, "effect": {"lifespan": 10}},
    {"building_type": "داروخانه", "name": "قرص چی بزرگ", "item_type": "pill", "description": "+۵۰۰۰ انرژی", "price": 400, "effect": {"energy": 5000}},
    {"building_type": "داروخانه", "name": "قرص خدا", "item_type": "pill", "description": "کمیاب", "price": 10000, "effect": {"energy": 20000}},
    {"building_type": "کیمیاگری", "name": "دستور معجون سرعت", "item_type": "recipe", "description": "دستور ساخت", "price": 150, "effect": {}},
    {"building_type": "کیمیاگری", "name": "دستور معجون قدرت", "item_type": "recipe", "description": "دستور ساخت", "price": 200, "effect": {}},
{"building_type": "آهنگری", "name": "شمشیر نور", "item_type": "weapon", "description": "سلاح ریشه نور", "price": 2500, "effect": {"duel_power": 45}},
    {"building_type": "آهنگری", "name": "خنجر تاریکی", "item_type": "weapon", "description": "سلاح تاریکی", "price": 2500, "effect": {"duel_power": 45}},
    {"building_type": "آهنگری", "name": "نیزه روح", "item_type": "weapon", "description": "سلاح روحی", "price": 3000, "effect": {"duel_power": 55}},
    {"building_type": "آهنگری", "name": "تیغ الهی", "item_type": "weapon", "description": "کمیاب", "price": 15000, "effect": {"duel_power": 120}},
    {"building_type": "طلسم‌خانه", "name": "طلسم نور", "item_type": "talisman", "description": "محافظ نورانی", "price": 500, "effect": {"duel_power": 12}},
    {"building_type": "طلسم‌خانه", "name": "طلسم تاریکی", "item_type": "talisman", "description": "قدرت تاریک", "price": 500, "effect": {"duel_power": 12}},
    {"building_type": "طلسم‌خانه", "name": "طلسم تسخیر", "item_type": "talisman", "description": "برای ارواح", "price": 2000, "effect": {}},
    {"building_type": "داروخانه", "name": "قرص ریشه", "item_type": "pill", "description": "کمک بیداری ریشه", "price": 800, "effect": {"energy": 10000}},
    {"building_type": "داروخانه", "name": "قرص روحی", "item_type": "pill", "description": "انرژی روح", "price": 1200, "effect": {"energy": 15000}},
    {"building_type": "داروخانه", "name": "قرص نور", "item_type": "pill", "description": "پاکسازی", "price": 900, "effect": {"energy": 8000}},
    {"building_type": "کیمیاگری", "name": "گرد نور", "item_type": "material", "description": "ماده کیمیاگری نور", "price": 200, "effect": {}},
    {"building_type": "کیمیاگری", "name": "گرد تاریکی", "item_type": "material", "description": "ماده تاریک", "price": 200, "effect": {}},
    {"building_type": "کیمیاگری", "name": "خون روح", "item_type": "material", "description": "ماده کمیاب", "price": 600, "effect": {}},
    {"building_type": "کیمیاگری", "name": "گرد ای‌تری", "item_type": "material", "description": "ماده ای‌تری", "price": 1000, "effect": {}},
    {"building_type": "سالن تکنیک", "name": "کتاب نفس نورانی", "item_type": "tech_book", "description": "تکنیک نور", "price": 500, "effect": {"learn_tech": "نفس نورانی"}},
    {"building_type": "سالن تکنیک", "name": "کتاب سایه ابدی", "item_type": "tech_book", "description": "تکنیک تاریکی", "price": 500, "effect": {"learn_tech": "سایه ابدی"}},
    {"building_type": "سالن تکنیک", "name": "کتاب همهمه روح", "item_type": "tech_book", "description": "تکنیک روحی", "price": 700, "effect": {"learn_tech": "همهمه روح"}},
    {"building_type": "آهنگری", "name": "شمشیر ذوالفقار", "item_type": "weapon_unique", "description": "شمشیر ایرانی افسانه‌ای — فقط یکی در کل بازی", "price": 999999, "effect": {"duel_power": 500, "unique": "zulfiqar"}},
    {"building_type": "آهنگری", "name": "زره اژدها", "item_type": "armor", "description": "کاهش آسیب عجیب — پوست اژدها", "price": 4000, "effect": {"duel_power": 30, "armor": 40}},
    {"building_type": "آهنگری", "name": "زره غیب", "item_type": "armor", "description": "گاهی ضربه را محو می‌کند", "price": 6000, "effect": {"duel_power": 20, "armor": 50, "weird": "vanish"}},
    {"building_type": "آهنگری", "name": "زره خدایان", "item_type": "armor", "description": "بدن را سخت‌تر می‌کند", "price": 20000, "effect": {"duel_power": 60, "armor": 100}},
    {"building_type": "آهنگری", "name": "زره نفرین", "item_type": "armor", "description": "قدرت می‌دهد اما عمر می‌گیرد", "price": 3000, "effect": {"duel_power": 45, "armor": 25, "weird": "curse"}},
    {"building_type": "آهنگری", "name": "نیزه رستم", "item_type": "weapon", "description": "سلاح حماسی ایرانی", "price": 8000, "effect": {"duel_power": 90}},
    {"building_type": "آهنگری", "name": "گرز گرشاسب", "item_type": "weapon", "description": "گرز افسانه‌ای", "price": 7000, "effect": {"duel_power": 85}},
    {"building_type": "آهنگری", "name": "شمشیر کوروش بزرگ", "item_type": "weapon_unique", "description": "شمشیر شاه ایران — فقط یکی؛ صاحب نمی‌میرد؛ یک ضربه = نابودی ابدی دشمن", "price": 5000000, "effect": {"duel_power": 999, "unique": "cyrus"}},
    {"building_type": "داروخانه", "name": "قرص سلامتی", "item_type": "pill", "description": "پاک کردن سم و ترمیم خون", "price": 150, "effect": {"heal": 1}},
    {"building_type": "داروخانه", "name": "پادزهر", "item_type": "pill", "description": "سم را خنثی می‌کند", "price": 200, "effect": {"heal": 1}},
    {"building_type": "آهنگری", "name": "کلت پنهان", "item_type": "weapon", "description": "سلاح گرم", "price": 3000, "effect": {"duel_power": 25}},
    {"building_type": "آهنگری", "name": "کلاشنیکف کهنه", "item_type": "weapon", "description": "سلاح گرم سنگین", "price": 5000, "effect": {"duel_power": 40}},
    {"building_type": "داروخانه", "name": "قرص سلامتی", "item_type": "pill", "description": "پاک کردن سم و ترمیم خون", "price": 150, "effect": {"heal": 1}},
    {"building_type": "داروخانه", "name": "پادزهر", "item_type": "pill", "description": "خنثی کردن سم", "price": 200, "effect": {"heal": 1}},
    {"building_type": "آهنگری", "name": "کلت پنهان", "item_type": "weapon", "description": "سلاح گرم", "price": 3000, "effect": {"duel_power": 25}},
    {"building_type": "آهنگری", "name": "کلاشنیکف کهنه", "item_type": "weapon", "description": "سلاح گرم سنگین", "price": 5000, "effect": {"duel_power": 40}},
    {"building_type": "داروخانه", "name": "چای تذهیب", "item_type": "tea", "description": "+۸۰۰۰ انرژی تذهیب — هر ۱۰ دقیقه یک‌بار", "price": 500, "effect": {"energy": 8000, "cooldown_min": 10}},
    {"building_type": "داروخانه", "name": "قرص نژاد اژدها", "item_type": "pill", "description": "+۱۲۰۰۰ انرژی", "price": 500, "effect": {"energy": 12000}},
    {"building_type": "داروخانه", "name": "قرص نور فرشته", "item_type": "pill", "description": "+۹۰۰۰ انرژی نور", "price": 400, "effect": {"energy": 9000}},
    {"building_type": "داروخانه", "name": "معجون خون", "item_type": "pill", "description": "ترمیم خون +۴۰", "price": 200, "effect": {"heal": 1}},
    {"building_type": "طلسم‌خانه", "name": "طلسم سپر", "item_type": "talisman", "description": "کاهش آسیب", "price": 350, "effect": {"armor": 20}},
    {"building_type": "طلسم‌خانه", "name": "طلسم آتش", "item_type": "talisman", "description": "قدرت دوئل", "price": 400, "effect": {"duel_power": 15}},
    {"building_type": "طلسم‌خانه", "name": "طلسم سایه", "item_type": "talisman", "description": "فرار از مرگ یک‌بار", "price": 2000, "effect": {"duel_power": 5}},
    {"building_type": "آهنگری", "name": "شمشیر نوری", "item_type": "weapon", "description": "سلاح نور", "price": 4500, "effect": {"duel_power": 55}},
    {"building_type": "آهنگری", "name": "خنجر اهریمن", "item_type": "weapon", "description": "سلاح شیطانی", "price": 4800, "effect": {"duel_power": 60}},
    {"building_type": "آهنگری", "name": "کمان پری", "item_type": "weapon", "description": "سلاح دور", "price": 3200, "effect": {"duel_power": 40}},
    {"building_type": "آهنگری", "name": "گرز غول", "item_type": "weapon", "description": "ضربه سنگین", "price": 5000, "effect": {"duel_power": 70}},
    {"building_type": "کیمیاگری", "name": "گرد اژدها", "item_type": "material", "description": "ماده ساخت پیشرفته", "price": 800, "effect": {}},
    {"building_type": "کیمیاگری", "name": "اشک فرشته", "item_type": "material", "description": "ماده نادر", "price": 1200, "effect": {}},
    {"building_type": "کیمیاگری", "name": "پودر سایه", "item_type": "material", "description": "ماده تاریکی", "price": 900, "effect": {}},
    {"building_type": "باغ گیاهان", "name": "گل ماه", "item_type": "herb_spiritual", "description": "گیاه معنوی", "price": 250, "effect": {}},
    {"building_type": "باغ گیاهان", "name": "ریشه خون", "item_type": "herb_spiritual", "description": "گیاه خون‌آشام", "price": 300, "effect": {}},
    {"building_type": "سالن تکنیک", "name": "کتاب نَفَس اژدهای سرخ", "item_type": "tech_book", "description": "یادگیری تکنیک", "price": 800, "effect": {"learn_tech": "نَفَس اژدهای سرخ"}},
    {"building_type": "سالن تکنیک", "name": "کتاب سرود فرشتگان", "item_type": "tech_book", "description": "یادگیری", "price": 800, "effect": {"learn_tech": "سرود فرشتگان"}},
    {"building_type": "چای‌خانه", "name": "چای سبز ساده", "item_type": "tea", "description": "انرژی پایه | +2000 انرژی | CD 5د", "price": 50, "effect": {"energy": 2000, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای سیاه کوهستان", "item_type": "tea", "description": "انرژی متوسط | +3500 انرژی | CD 5د", "price": 80, "effect": {"energy": 3500, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای سفید مه", "item_type": "tea", "description": "آرامش + انرژی | +4000 انرژی | CD 5د", "price": 100, "effect": {"energy": 4000, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای اولانگ", "item_type": "tea", "description": "تمرکز | +3800 انرژی | CD 5د", "price": 90, "effect": {"energy": 3800, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای تذهیب کلاسیک", "item_type": "tea", "description": "تذهیب قوی — کول‌داون ۱۰د | +8000 انرژی | CD 10د", "price": 80, "effect": {"energy": 8000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای ریشه آتش", "item_type": "tea", "description": "بونوس ریشه آتش | +5000 انرژی | CD 5د", "price": 120, "effect": {"energy": 5000, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای ریشه آب", "item_type": "tea", "description": "بونوس ریشه آب | +5000 انرژی | CD 5د", "price": 120, "effect": {"energy": 5000, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای ریشه چوب", "item_type": "tea", "description": "بونوس ریشه چوب | +5000 انرژی | CD 5د", "price": 120, "effect": {"energy": 5000, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای ریشه فلز", "item_type": "tea", "description": "بونوس ریشه فلز | +5000 انرژی | CD 5د", "price": 120, "effect": {"energy": 5000, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای ریشه خاک", "item_type": "tea", "description": "بونوس ریشه خاک | +5000 انرژی | CD 5د", "price": 120, "effect": {"energy": 5000, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای نورانی", "item_type": "tea", "description": "ریشه نور | +7000 انرژی | CD 5د", "price": 200, "effect": {"energy": 7000, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای تاریکی", "item_type": "tea", "description": "ریشه تاریکی | +7000 انرژی | CD 5د", "price": 200, "effect": {"energy": 7000, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای روح", "item_type": "tea", "description": "ریشه روحی | +9000 انرژی | CD 10د", "price": 250, "effect": {"energy": 9000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای بهشتی", "item_type": "tea", "description": "سنگ بهشتی حس | +12000 انرژی | CD 10د", "price": 400, "effect": {"energy": 12000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای آسمانی", "item_type": "tea", "description": "انرژی آسمان | +15000 انرژی | CD 10د", "price": 600, "effect": {"energy": 15000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای الهی", "item_type": "tea", "description": "انرژی الهی | +25000 انرژی | CD 10د", "price": 1000, "effect": {"energy": 25000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای پوچی", "item_type": "tea", "description": "خطرناک اما قوی | +20000 انرژی | CD 10د", "price": 800, "effect": {"energy": 20000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای ای‌تری", "item_type": "tea", "description": "قلمرو ای‌تری | +18000 انرژی | CD 10د", "price": 700, "effect": {"energy": 18000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای اژدها", "item_type": "tea", "description": "نژاد اژدهازاده | +14000 انرژی | CD 10د", "price": 500, "effect": {"energy": 14000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای فرشته", "item_type": "tea", "description": "نژاد فرشته | +13000 انرژی | CD 10د", "price": 450, "effect": {"energy": 13000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای اهریمن", "item_type": "tea", "description": "نژاد اهریمن | +13500 انرژی | CD 10د", "price": 480, "effect": {"energy": 13500, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای جن", "item_type": "tea", "description": "نژاد جن | +10000 انرژی | CD 10د", "price": 350, "effect": {"energy": 10000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای خون", "item_type": "tea", "description": "خون‌آشام | +9000 انرژی | CD 10د", "price": 300, "effect": {"energy": 9000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای پری", "item_type": "tea", "description": "پری | +9500 انرژی | CD 10د", "price": 320, "effect": {"energy": 9500, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای غول", "item_type": "tea", "description": "غول | +8500 انرژی | CD 10د", "price": 280, "effect": {"energy": 8500, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای سایه", "item_type": "tea", "description": "سایه‌رو | +11000 انرژی | CD 10د", "price": 360, "effect": {"energy": 11000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای روح‌پیمان", "item_type": "tea", "description": "روح‌پیمان | +11500 انرژی | CD 10د", "price": 380, "effect": {"energy": 11500, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای یانگ", "item_type": "tea", "description": "افزایش یانگ | +6000 انرژی | CD 5د", "price": 150, "effect": {"energy": 6000, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای یین", "item_type": "tea", "description": "افزایش یین | +6000 انرژی | CD 5د", "price": 150, "effect": {"energy": 6000, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای عمر", "item_type": "tea", "description": "عمر +۵ | +5000 انرژی | CD 5د", "price": 500, "effect": {"energy": 5000, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای خون‌سازی", "item_type": "tea", "description": "خون +۳۰ | +3000 انرژی | CD 5د", "price": 180, "effect": {"energy": 3000, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای پادزهر گیاهی", "item_type": "tea", "description": "سم‌زدایی | +1000 انرژی | CD 5د", "price": 100, "effect": {"energy": 1000, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای مدیتیشن", "item_type": "tea", "description": "مدیتیت | +4500 انرژی | CD 5د", "price": 70, "effect": {"energy": 4500, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای شب", "item_type": "tea", "description": "آرامش شبانه | +2500 انرژی | CD 5د", "price": 60, "effect": {"energy": 2500, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای سحر", "item_type": "tea", "description": "صبحگاه | +2500 انرژی | CD 5د", "price": 60, "effect": {"energy": 2500, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای چهارفصل", "item_type": "tea", "description": "فصل‌ها | +8000 انرژی | CD 10د", "price": 200, "effect": {"energy": 8000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای پنج‌عنصر", "item_type": "tea", "description": "پنج عنصر | +10000 انرژی | CD 10د", "price": 250, "effect": {"energy": 10000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای هفت‌ستاره", "item_type": "tea", "description": "ستارگان | +12000 انرژی | CD 10د", "price": 350, "effect": {"energy": 12000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای نه اژدها", "item_type": "tea", "description": "افسانه | +16000 انرژی | CD 10د", "price": 550, "effect": {"energy": 16000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای جاودانگی", "item_type": "tea", "description": "بسیار نادر | +50000 انرژی | CD 10د", "price": 2000, "effect": {"energy": 50000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای رعد", "item_type": "tea", "description": "رعد آسمانی | +7500 انرژی | CD 5د", "price": 220, "effect": {"energy": 7500, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای یخ", "item_type": "tea", "description": "سردی مطلق | +7500 انرژی | CD 5د", "price": 220, "effect": {"energy": 7500, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای خاکستر", "item_type": "tea", "description": "خاکستر آتش | +7000 انرژی | CD 5د", "price": 200, "effect": {"energy": 7000, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای مه جنگل", "item_type": "tea", "description": "طبیعت | +4000 انرژی | CD 5د", "price": 90, "effect": {"energy": 4000, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای صحرا", "item_type": "tea", "description": "گرما | +3800 انرژی | CD 5د", "price": 85, "effect": {"energy": 3800, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای کوهستان برفی", "item_type": "tea", "description": "برف | +4200 انرژی | CD 5د", "price": 95, "effect": {"energy": 4200, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای دریا", "item_type": "tea", "description": "موج | +3900 انرژی | CD 5د", "price": 88, "effect": {"energy": 3900, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای شهر تهران", "item_type": "tea", "description": "شهری | +3000 انرژی | CD 5د", "price": 70, "effect": {"energy": 3000, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای اصفهان", "item_type": "tea", "description": "سنتی | +3200 انرژی | CD 5د", "price": 75, "effect": {"energy": 3200, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای شیراز", "item_type": "tea", "description": "عطر گل | +3200 انرژی | CD 5د", "price": 75, "effect": {"energy": 3200, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای تبریز", "item_type": "tea", "description": "قوی | +3100 انرژی | CD 5د", "price": 70, "effect": {"energy": 3100, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای مشهد", "item_type": "tea", "description": "زائری | +3100 انرژی | CD 5د", "price": 70, "effect": {"energy": 3100, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای بندرعباس", "item_type": "tea", "description": "گرمسیری | +3500 انرژی | CD 5د", "price": 80, "effect": {"energy": 3500, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای گیلان", "item_type": "tea", "description": "باران | +2800 انرژی | CD 5د", "price": 65, "effect": {"energy": 2800, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای کردستان", "item_type": "tea", "description": "کوه | +3000 انرژی | CD 5د", "price": 70, "effect": {"energy": 3000, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای ممنوعه", "item_type": "tea", "description": "⚠️ مثل پرورش ممنوعه — خطر | +1 انرژی | CD 60د", "price": 50, "effect": {"energy": 1, "cooldown_min": 60}},
    {"building_type": "چای‌خانه", "name": "چای طلایی", "item_type": "tea", "description": "لوکس | +30000 انرژی | CD 10د", "price": 1500, "effect": {"energy": 30000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای نقره‌ای", "item_type": "tea", "description": "لوکس | +18000 انرژی | CD 10د", "price": 800, "effect": {"energy": 18000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای برنزی", "item_type": "tea", "description": "عادی لوکس | +6000 انرژی | CD 5د", "price": 200, "effect": {"energy": 6000, "cooldown_min": 5}},
    {"building_type": "چای‌خانه", "name": "چای الماس", "item_type": "tea", "description": "نهایت | +60000 انرژی | CD 10د", "price": 3000, "effect": {"energy": 60000, "cooldown_min": 10}},
    {"building_type": "چای‌خانه", "name": "چای خدایان", "item_type": "tea", "description": "افسانه‌ای | +100000 انرژی | CD 10د", "price": 5000, "effect": {"energy": 100000, "cooldown_min": 10}},
]

async def ensure_default_buildings_and_items(session: AsyncSession):
    """ساختمان‌ها و آیتم‌های پیش‌فرض را در صورت نبودن اضافه می‌کند"""
    types = ["داروخانه", "کیمیاگری", "طلسم‌خانه", "باغ گیاهان", "آهنگری", "سالن تکنیک", "چای‌خانه"]
    result = await session.execute(select(Building))
    existing = {b.building_type: b for b in result.scalars().all()}
    buildings = dict(existing)
    for btype in types:
        if btype not in buildings:
            b = Building(name=btype, building_type=btype, description=f"ساختمان {btype}")
            session.add(b)
            await session.flush()
            buildings[btype] = b

    # آیتم‌های موجود
    result = await session.execute(select(ShopItem))
    existing_names = {i.name for i in result.scalars().all()}
    for item_data in DEFAULT_ITEMS:
        if item_data["name"] in existing_names:
            continue
        b = buildings.get(item_data["building_type"])
        if not b:
            continue
        item = ShopItem(
            building_id=b.id,
            name=item_data["name"],
            item_type=item_data["item_type"],
            description=item_data["description"],
            price=item_data["price"],
            effect=item_data["effect"],
        )
        session.add(item)
    await session.commit()


async def get_buildings(session: AsyncSession):
    result = await session.execute(select(Building).where(Building.is_active == True))
    return result.scalars().all()


async def get_items_of_building(session: AsyncSession, building_id: int):
    result = await session.execute(
        select(ShopItem).where(ShopItem.building_id == building_id, ShopItem.is_active == True)
    )
    return result.scalars().all()


async def buy_item(session: AsyncSession, user: User, item: ShopItem) -> str:
    if item.item_type == "weapon_unique" or (isinstance(item.effect, dict) and item.effect.get("unique")):
        from sqlalchemy import select as sel
        owned = await session.execute(
            sel(UserInventory).join(ShopItem, UserInventory.item_id == ShopItem.id).where(
                ShopItem.name == item.name
            )
        )
        if owned.first():
            return "❌ این آیتم یکتاست و قبلاً کسی آن را دارد."

    from services.economy import get_or_create_wallet, pay_any_currency
    w = await get_or_create_wallet(session, user.id)
    ok, pay_msg = pay_any_currency(w, int(item.price or 0))
    if not ok:
        return pay_msg
    effect = item.effect or {}
    extra = ""

    # کتاب تکنیک → یادگیری مستقیم
    if item.item_type == "tech_book" or (isinstance(effect, dict) and effect.get("learn_tech")):
        tech_name = effect.get("learn_tech") if isinstance(effect, dict) else None
        if tech_name:
            from services.cultivation import ensure_default_techniques, learn_technique
            from database.models_v3 import CultivationTechnique
            from sqlalchemy import select as sel
            await ensure_default_techniques(session)
            r = await session.execute(
                sel(CultivationTechnique).where(CultivationTechnique.name == tech_name)
            )
            tech = r.scalar_one_or_none()
            if tech:
                extra = await learn_technique(session, user.id, tech)
            else:
                extra = f"تکنیک «{tech_name}» در دیتابیس نبود."
        await session.commit()
        return f"✅ «{item.name}» خریداری شد.\n{extra}\n{pay_msg}"

    result = await session.execute(
        select(UserInventory).where(
            UserInventory.user_id == user.id,
            UserInventory.item_id == item.id,
        )
    )
    inv = result.scalar_one_or_none()
    if inv:
        inv.quantity += 1
    else:
        inv = UserInventory(user_id=user.id, item_id=item.id, quantity=1)
        session.add(inv)

    await session.commit()
    return f"✅ «{item.name}» خریداری شد. {pay_msg}"