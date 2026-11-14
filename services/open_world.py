"""جهان باز جدید: مختصات، نیازهای بقا، رویداد و باس مکان‌محور."""
from __future__ import annotations
from datetime import datetime, timedelta
import random
from services.persist import get_dict, save

WORLD_NAME = "جهان تازه — قلمرو نُه‌گانه"
SKY_NAME = "نُه آسمان نو"

# جهان کامل جدید (قلمروهای قدیمی/ناقص حذف و بازنویسی شدند)
SKIES = {
    1: {
        "name": "آسمان اول — دشت بیدار",
        "min_dist": 0,
        "landmarks": ["شهر آغاز", "بازار هفت‌راه", "جنگل زمزمه‌گر", "رود نقره‌ای", "اردوگاه تازه‌کاران", "چاه چی"],
    },
    2: {
        "name": "آسمان دوم — مهستان",
        "min_dist": 90,
        "landmarks": ["شهر مهتاب", "دریاچه آینه", "دره گرگ سپید", "قلعه مه‌پوش", "معبد فراموشی", "پل صدپژواک"],
    },
    3: {
        "name": "آسمان سوم — سرزمین هزار رود",
        "min_dist": 200,
        "landmarks": ["شهر نُه‌رود", "بندر فیروزه", "معبد آب کهن", "تالار نقشه‌سازان", "جزیره نیلوفر", "سد طلایی"],
    },
    4: {
        "name": "آسمان چهارم — کوهستان اژدها",
        "min_dist": 350,
        "landmarks": ["شهر سنگ‌سرخ", "قله اژدهای خاموش", "دره رعد", "دژ آذرین", "معدن فلس", "غار شعله‌جاوید"],
    },
    5: {
        "name": "آسمان پنجم — دریای ستاره",
        "min_dist": 550,
        "landmarks": ["شهر شناور", "بندر شهاب", "رصدخانه ازلی", "جزیره ساعت شکسته", "فانوس راهگشا", "گرداب نور"],
    },
    6: {
        "name": "آسمان ششم — سرزمین ارواح",
        "min_dist": 800,
        "landmarks": ["شهر ارواح آرام", "کتابخانه بی‌نام", "گورستان پادشاهان", "معبد چراغ خاموش", "بازار سایه", "دروازه خواب"],
    },
    7: {
        "name": "آسمان هفتم — قلمرو عرش",
        "min_dist": 1150,
        "landmarks": ["شهر عرش", "پل طلایی", "معبد ده هزار قانون", "باغ فرشتگان", "سالن داوری", "برج پیمان"],
    },
    8: {
        "name": "آسمان هشتم — مرز پوچی",
        "min_dist": 1550,
        "landmarks": ["شهر خلأ", "شکاف بی‌زمان", "بازار ناشناختگان", "قصر سیاه‌ستاره", "چاه هیچ", "اردوگاه آخرین"],
    },
    9: {
        "name": "آسمان نهم — تاج خالق",
        "min_dist": 2100,
        "landmarks": ["شهر تاج", "قصر نُه‌گانه", "دروازه میلیارد دنیا", "قلب اَبَرجهان", "تخت حکم", "چشمه مطلق"],
    },
}

SKY_LORE = {
    1: "آغاز دوباره. اینجا چی تازه است و هر تازه‌کار می‌تواند ریشه بزند.",
    2: "مه حافظه را می‌آزماید؛ کسانی که راه گم کنند، داستان خود را فراموش می‌کنند.",
    3: "رودها شریان ثروت‌اند. فرقه‌ای که رود را بگیرد، تجارت را می‌گیرد.",
    4: "اژدهایان کهن هنوز در خواب نیمه‌هشیارند؛ غرش‌شان کوه را می‌لرزاند.",
    5: "ستاره‌ها زنده‌اند و گاه دروازه‌ای کوتاه به دنیاهای دور باز می‌کنند.",
    6: "ارواح فرمانروایان شکست‌خورده راز تمدن‌های نابودشده را نگه می‌دارند.",
    7: "قانون اینجا سخت‌تر است؛ بدون پیمان، شهرها دوام نمی‌آورند.",
    8: "پوچی لب مرز جهان است؛ مختصات ممکن است امروز باشد و فردا نباشد.",
    9: "آخرین آسمان. هر شهری که اینجا ساخته شود در تاریخ دنیاها ثبت می‌شود.",
}

NEW_REALMS = [
    ("آسمان اول", "دشت بیدار", "شهر آغاز"),
    ("آسمان دوم", "مهستان", "شهر مهتاب"),
    ("آسمان سوم", "هزار رود", "شهر نُه‌رود"),
    ("آسمان چهارم", "اژدهاکوه", "شهر سنگ‌سرخ"),
    ("آسمان پنجم", "دریای ستاره", "شهر شناور"),
    ("آسمان ششم", "روحستان", "شهر ارواح آرام"),
    ("آسمان هفتم", "عرش", "شهر عرش"),
    ("آسمان هشتم", "مرز پوچی", "شهر خلأ"),
    ("آسمان نهم", "تاج خالق", "شهر تاج"),
]
START_CITY = "start"  # id شهر آغازین در services.cities
START_X, START_Y = 0, 0
DIRECTIONS = {
    "north": (0, 1, "شمال"), "south": (0, -1, "جنوب"),
    "east": (1, 0, "شرق"), "west": (-1, 0, "غرب"),
}
ALIASES = {
    "شمال": "north", "ش": "north", "north": "north",
    "جنوب": "south", "ج": "south", "south": "south",
    "شرق": "east", "ر": "east", "east": "east",
    "غرب": "west", "غ": "west", "west": "west",
}

EVENTS = [
    ("بارانِ جوهر", "قطره‌های جوهر از آسمان می‌بارند؛ جست‌وجوگران می‌توانند جوهر ازلی پیدا کنند."),
    ("شکافِ بی‌نام", "شکافی در فضا باز شده و هیولایی ناشناخته را به یک مختصات کشانده است."),
    ("کاروانِ گمشده", "یک کاروان در نزدیکی مختصات فعلی گیر افتاده؛ کمکش کن تا پاداش بگیری."),
    ("شبِ خاموش", "برای مدتی کوتاه، نقشه تاریک می‌شود و موجودات نادر ظاهر می‌شوند."),
    ("وارونگیِ جهت", "نیرویی مرموز مسیرهای دوردست را به هم ریخته؛ مسافران باید مراقب باشند."),
    ("پژواک آرش", "سایه آرش کمانگیر بر دشت افتاده؛ تیرهای نوری در آسمان دیده می‌شوند."),
    ("طوفان رعد", "صاعقه‌های چی‌دار کوهستان رعد را می‌لرزاند؛ قدرت رزمی موقتاً افزایش می‌یابد."),
    ("بازار سایه", "بازرگانان مرموز از مرز پوچی آمده‌اند و اقلام نادر می‌فروشند."),
    ("نبرد فرقه‌ها", "دو فرقه بزرگ در دره شمشیرها درگیر شده‌اند؛ بازیکنان می‌توانند طرف انتخاب کنند."),
    ("بیداری اژدها", "غرش دوردست از دشت اژدها می‌آید؛ فلس‌های درخشان در هوا شناورند."),
    ("مه تذهیب", "مه غلیظی سرشار از چی؛ تذهیب در این منطقه دو برابر سریع‌تر است."),
    ("آزمون استاد", "استادی ناشناس در شهر آغازین چالش قدرت برگزار می‌کند."),
]

BOSS = {
    "name": "سیمرغِ خطوطِ غبارآلود",
    "subtitle": "نگهبانِ اوراقِ فراموش‌شده",
    "hp": 5_000_000,
    "max_hp": 5_000_000,
    "attacks": [
        "خطوطِ طلا — پرتوهای طلایی از زمین می‌شکافند.",
        "اسلیمیِ چرخنده — نقش‌های اسلیمی اطراف تالار می‌چرخند.",
        "پرتابِ رنگدانه‌ها — لاجورد، شنگرف و اخرا با اثرهای متفاوت.",
        "طرحِ غافلگیرکننده — یک الگوی هندسی مرگبار روی زمین ظاهر می‌شود.",
        "سیمرغِ شکاری — بال‌های تذهیب‌شده و شراره‌های رنگی.",
        "اوراقِ سرنوشت — دست‌نوشته‌های نورانی اثرهای تصادفی دارند.",
        "ختمِ کلام — ضربه نهایی تمام تالار را می‌پوشاند.",
    ],
}


def geographic_cell(x: int, y: int, sky: int = 1) -> dict:
    """توصیف جغرافیایی پایدار برای هر مختصات؛ بدون نیاز به سرویس نقشه خارجی."""
    seed = abs(x * 92821 + y * 68917 + sky * 31337)
    terrains = [
        ("دشت", "grass", "آب‌وهوای معتدل", 20), ("جنگل", "forest", "مرطوب", 35),
        ("کوهستان", "mountain", "سرد و بادخیز", 75), ("بیابان", "desert", "خشک و گرم", 60),
        ("تالاب", "swamp", "مه‌آلود و مرطوب", 40), ("ساحل", "coast", "نمناک و دریایی", 15),
        ("دریا", "sea", "طوفانی", 5), ("خرابه", "ruins", "ناپایدار", 70),
    ]
    name, code, climate, base_danger = terrains[seed % len(terrains)]
    # نوارهای جغرافیایی باعث می‌شوند نقشه حس قاره/اقلیم داشته باشد.
    if abs(y) >= 18: name, code, climate = "سرزمین یخ‌زده", "ice", "یخبندان"
    if abs(x) >= 28 and abs(y) < 18: name, code, climate = "کرانه دوردست", "frontier", "بادهای مرزی"
    elevation = int((seed * 37) % 4200)
    water = code in {"sea", "coast", "swamp"}
    road = ((x + 2*y + sky) % 7 == 0)
    return {"name": name, "code": code, "climate": climate, "elevation": elevation, "water": water, "road": road, "danger": min(100, base_danger + (abs(x)+abs(y))//8)}


def world_state() -> dict:
    d = get_dict("open_world")
    if not d:
        d.update({
            "world_id": "new-world-001",
            "world_name": WORLD_NAME,
            "sky_system": SKY_NAME,
            "created_at": datetime.utcnow().isoformat(),
            "epoch": 1,
            "portal_done": False,
            "event": None,
            "boss": None,
            "cities": {"start": {"name": "شهر آغازین", "x": 0, "y": 0, "owner": None, "level": 1}},
            "countries": {},
        })
        save("open_world")
    return d


def portal_story() -> str:
    return (
        "🌌 <b>افتتاح جهان رزمی</b>\n\n"
        "جهان قدیم در جنگ فرقه‌ها و سقوط قوانین فرو ریخت. بازماندگان از میان خاکستر برخاستند.\n\n"
        "اکنون <b>جهان رزمی</b> گشوده شده است: دشت آغازین، کوهستان رعد، دره شمشیرها، سرزمین طلسم، "
        "مرز پوچی و دشت اژدها در برابر توست.\n\n"
        "همه جنگجویان به <b>شهر آغازین</b> منتقل شدند. قدرت، تذهیب و دارایی‌ات حفظ شده؛ "
        "اما مکان و فرقه‌های جهان قدیم از بین رفته‌اند.\n\n"
        "مسیر ۹ آسمان باز است. اراده‌ات را ثابت کن."
    )


def weekly_story(week: int | None = None) -> str:
    """داستان هفتگی جهان رزمی — چرخه ۱۲ هفته‌ای"""
    from datetime import datetime
    if week is None:
        week = datetime.utcnow().isocalendar()[1]
    stories = [
        "فصل اول — بیدار شدن دشت: باد از شرق آمد و شهر آغازین را لرزاند. جنگجویان نوپا تیغ‌های خود را تیز کردند.",
        "فصل دوم — بازار هزارراه: کاروان‌هایی از مرز پوچی رسیدند و خبر از سلاحی گمشده دادند.",
        "فصل سوم — قله رعد: صاعقه نه بار بر قله نشست و کسی که ایستاد، نشان رعد گرفت.",
        "فصل چهارم — دره شمشیرها: دوئل بزرگ آغاز شد؛ نام قهرمانان روی سنگ افتخار حک شد.",
        "فصل پنجم — شهر مهرها: طلسم‌نویسان جوهر ازلی را کشف کردند و قوانین مبارزه تغییر کرد.",
        "فصل ششم — پژواک آرش: سایه کمانگیر افسانه‌ای بر دشت افتاد؛ دو نفر در روز حق خرید کمان او را یافتند.",
        "فصل هفتم — دشت اژدها: فلس‌های سرخ از آسمان بارید و قدرت کسانی که جمع کردند دوچندان شد.",
        "فصل هشتم — دروازه پوچی: شکافی باز شد و هیولایی بدون نام بیرون آمد؛ جهان رزمی متحد شد.",
        "فصل نهم — پلکان ۹ آسمان: کسانی که قلمرو پیشرفته داشتند، به آسمان اول فراخوانده شدند.",
        "فصل دهم — شهر مهتاب: مه تذهیب همه را فرا گرفت؛ انرژی دو برابر رشد کرد.",
        "فصل یازدهم — نبرد فرقه‌ها: اتحادها شکست و جنگ داخلی آغاز شد؛ رهبران ضعیف سقوط کردند.",
        "فصل دوازدهم — تاج خالق: در دوردست‌ترین آسمان، نوری دیده شد که فقط برای افسانه‌ها بود.",
    ]
    idx = (int(week) - 1) % len(stories)
    return f"📖 <b>داستان هفتگی جهان رزمی</b>\n\n{stories[idx]}\n\n هفته {week} — مسیرت را با قدرت و اراده بساز."


def migrate_player_position(user) -> bool:
    """همگام‌سازی بازیکن با جهان رزمی و شهر آغازین در صورت شهر قدیمی."""
    changed = False
    if getattr(user, "world", None) != WORLD_NAME:
        user.world = WORLD_NAME
        changed = True
    old_cities = {
        "tehran", "ray", "shahrerey", "mashhad", "neyshabur", "sabzevar",
        "isfahan", "kashan", "najafabad", "shiraz", "marvdasht", "lar",
        "bandarabbas", "khamir", "lengeh", "tabriz", "ahvaz", "kerman",
        "rasht", "newyork", "moscow", "فانی", "بهشتی", "زیرین", None, "",
    }
    city = getattr(user, "city", None)
    if not city or city in old_cities:
        user.city = START_CITY
        user.world_x = START_X
        user.world_y = START_Y
        changed = True
    if not getattr(user, "city", None) or user.city in {"tehran", "فانی", "بهشتی", "زیرین"}:
        user.city = START_CITY
        changed = True
    return changed


def current_sky(user) -> int:
    return max(1, min(9, int(getattr(user, "sky", 1) or 1)))


def sky_info(user) -> dict:
    n = current_sky(user)
    info = dict(SKIES[n])
    info["number"] = n
    info["lore"] = SKY_LORE[n]
    return info


def realm_above_advanced(realm: str) -> bool:
    # منبع واحد قلمروها را از مدل تذهیب می‌خوانیم تا با اضافه‌شدن
    # قلمروهای جدید، صعود اجباری دوباره از کار نیفتد.
    try:
        from database.models_v2 import CULTIVATION_REALMS
        advanced_index = CULTIVATION_REALMS.index("پیشرفته")
        return CULTIVATION_REALMS.index(realm or "بیداری") > advanced_index
    except (ValueError, TypeError):
        return False


def can_challenge_stair(user) -> tuple[bool, str]:
    sky = current_sky(user)
    if sky >= 9:
        return False, "به آسمان نهم رسیده‌ای؛ پلکان بالاتری وجود ندارد."
    if getattr(user, "sky_trial", False):
        return False, "در حال حاضر در وضعیت پلکان بهشت هستی."
    return True, "آماده‌ای."


def challenge_heaven_stair(user, power: int) -> dict:
    ok, reason = can_challenge_stair(user)
    if not ok:
        return {"ok": False, "message": reason}
    sky = current_sky(user)
    # شانس پایه با قدرت؛ شکست فقط انرژی/بقا را کمی کم می‌کند و مرگ ایجاد نمی‌کند.
    target = 80 + sky * 35
    score = max(1, int(power)) + random.randint(0, max(20, int(power * 0.25)))
    if score >= target:
        user.sky = sky + 1
        user.sky_trial = False
        user.sky_ascended_at = datetime.utcnow()
        user.world_x = 0
        user.world_y = 0
        user.city = SKIES[user.sky]["landmarks"][0]
        user.hunger = max(40, int(getattr(user, "hunger", 100) or 0))
        user.thirst = max(40, int(getattr(user, "thirst", 100) or 0))
        return {"ok": True, "sky": user.sky, "message": f"🌤️ پلکان بهشت را شکستی و به <b>{SKIES[user.sky]['name']}</b> صعود کردی!"}
    user.sky_trial = False
    return {"ok": False, "message": f"🪨 پلکان تو را پس زد. قدرت لازم تقریبی: {target:,}. قدرت فعلی: {power:,}. دوباره بعداً تلاش کن."}


def forced_sky_ascension(user, realm: str) -> dict | None:
    if not realm_above_advanced(realm) or current_sky(user) >= 9:
        return None
    sky = current_sky(user)
    user.sky = sky + 1
    user.sky_trial = False
    user.sky_ascended_at = datetime.utcnow()
    user.world_x = 0
    user.world_y = 0
    user.city = SKIES[user.sky]["landmarks"][0]
    return {"sky": user.sky, "name": SKIES[user.sky]["name"]}


def _location_landmark(x: int, y: int, sky: int) -> str:
    info = SKIES[sky]
    # نقاط خاص هر 17 خانه یک نشانه نام‌گذاری‌شده دارند.
    idx = (abs(x) * 7 + abs(y) * 11 + sky) % len(info["landmarks"])
    if x == 0 and y == 0:
        return info["landmarks"][0]
    if (abs(x) + abs(y)) % 17 == 0:
        return info["landmarks"][idx]
    if (abs(x) + abs(y)) % 11 == 0:
        return "ویرانه‌ای ناشناخته"
    if (abs(x) + abs(y)) % 7 == 0:
        return "دشت/جنگل ناشناخته"
    return "ناحیه وحشی"


def _survival_cost(user, steps=1):
    # هر حرکت فقط نیازهای بقا را کم می‌کند؛ مرگ خودکار نداریم.
    user.hunger = max(0, int(getattr(user, "hunger", 100) or 0) - 2 * steps)
    user.thirst = max(0, int(getattr(user, "thirst", 100) or 0) - 3 * steps)


def move(user, direction: str) -> dict:
    direction = ALIASES.get(str(direction or "").strip().lower(), str(direction or "").strip().lower())
    d = DIRECTIONS.get(direction)
    if not d:
        return {"ok": False, "error": "جهت نامعتبر است؛ شمال، جنوب، شرق یا غرب را انتخاب کن."}
    now = datetime.utcnow()
    last = getattr(user, "last_world_move_at", None)
    if last:
        try:
            left = 2.0 - (now - last).total_seconds()
            if left > 0:
                return {"cooldown": round(left, 1), "x": int(getattr(user, "world_x", 0) or 0), "y": int(getattr(user, "world_y", 0) or 0), "direction": d[2], "danger": 0, "encounter": None}
        except Exception:
            pass
    user.world_x = int(getattr(user, "world_x", 0) or 0) + d[0]
    user.world_y = int(getattr(user, "world_y", 0) or 0) + d[1]
    user.last_world_move_at = now
    _survival_cost(user)
    x, y = user.world_x, user.world_y
    danger = min(100, 8 + (abs(x) + abs(y)) // 5)
    encounter = None
    if random.random() < min(0.18, danger / 500):
        encounter = random.choice([
            "ردپای یک هیولای ناشناس",
            "قطعه‌ای از یک نقشه باستانی",
            "سنگ درخشانِ جوهر ازلی",
            "کاروانی که به کمک نیاز دارد",
        ])
    return {"x": x, "y": y, "direction": d[2], "danger": danger, "encounter": encounter}


def location_text(user) -> str:
    x, y = int(getattr(user, "world_x", 0) or 0), int(getattr(user, "world_y", 0) or 0)
    d = world_state()
    lines = [
        f"🌌 <b>{d.get('world_name', WORLD_NAME)}</b>",
        f"☁️ <b>۹ آسمان</b> — آسمان {current_sky(user)}: <b>{SKIES[current_sky(user)]['name']}</b>",
        f"📍 مختصات: <b>({x}, {y})</b>",
        f"🗺️ نقطه: <b>{_location_landmark(x, y, current_sky(user))}</b>",
        f"🏙️ شهر/مکان: <b>{getattr(user, 'city', None) or 'دشت ناشناخته'}</b>",
        f"🍖 گرسنگی: <b>{getattr(user, 'hunger', 100)}%</b>",
        f"💧 تشنگی: <b>{getattr(user, 'thirst', 100)}%</b>",
        f"☠️ خطر تقریبی منطقه: <b>{min(100, 8 + (abs(x)+abs(y))//5)}%</b>",
        "\nحرکت: شمال | جنوب | شرق | غرب",
    ]
    event = d.get("event")
    boss = d.get("boss")
    if event and event.get("x") == x and event.get("y") == y:
        lines.append(f"\n⚠️ <b>رویداد این مختصات:</b> {event['name']}\n{event['desc']}")
    if boss and boss.get("x") == x and boss.get("y") == y and boss.get("hp", 0) > 0:
        lines.append(f"\n👑 <b>{boss['name']}</b> — HP {boss['hp']:,}/{boss['max_hp']:,}\n{boss['subtitle']}")
    return "\n".join(lines)


def spawn_event(force=False):
    d = world_state()
    if d.get("event") and not force:
        return d["event"]
    x, y = random.randint(-30, 30), random.randint(-30, 30)
    name, desc = random.choice(EVENTS)
    d["event"] = {"name": name, "desc": desc, "x": x, "y": y, "at": datetime.utcnow().isoformat()}
    save("open_world")
    return d["event"]


def spawn_boss(force=False):
    d = world_state()
    if d.get("boss") and d["boss"].get("hp", 0) > 0 and not force:
        return d["boss"]
    x, y = random.randint(-40, 40), random.randint(-40, 40)
    b = dict(BOSS)
    b.update({"x": x, "y": y, "spawned_at": datetime.utcnow().isoformat(), "participants": {}})
    d["boss"] = b
    save("open_world")
    return b


def boss_phase(boss: dict) -> int:
    hp = float(boss.get("hp", 0)); mx = max(1, float(boss.get("max_hp", 1)))
    ratio = hp / mx
    if ratio <= 0.20: return 3
    if ratio <= 0.60: return 2
    return 1


def boss_attack_text(boss: dict) -> str:
    phase = boss_phase(boss)
    labels = {1: "نقشِ اولیه", 2: "رنگ‌آمیزیِ خطرناک", 3: "اوجِ هنرِ فراموش‌شده"}
    attacks = boss.get("attacks") or []
    idx = random.randrange(len(attacks)) if attacks else 0
    return f"فاز {phase}: <b>{labels[phase]}</b>\n⚡ حمله: {attacks[idx] if attacks else 'حمله ناشناخته'}"


def hit_boss(user_id: int, damage: int):
    d = world_state(); b = d.get("boss")
    if not b or b.get("hp", 0) <= 0:
        return None, 0
    dmg = max(1, min(int(damage), int(b["hp"])))
    b["hp"] -= dmg
    p = b.setdefault("participants", {})
    p[str(user_id)] = int(p.get(str(user_id), 0)) + dmg
    save("open_world")
    return b, dmg


def create_city(user, name: str):
    d = world_state(); name = name.strip()[:40]
    if not name:
        return False, "نام شهر خالی است."
    cities = d.setdefault("cities", {})
    key = name
    if key in cities:
        return False, "این شهر قبلاً ساخته شده."
    x, y = int(getattr(user, "world_x", 0) or 0), int(getattr(user, "world_y", 0) or 0)
    if abs(x) + abs(y) < 10:
        return False, "برای ساخت شهر باید حداقل ۱۰ خانه از شهر آغازین دور شده باشی."
    cities[key] = {"name": name, "x": x, "y": y, "owner": int(user.telegram_id), "level": 1}
    user.city = name
    save("open_world")
    return True, f"🏙️ شهر «{name}» در مختصات ({x}, {y}) ساخته شد."


def create_country(user, name: str):
    d = world_state(); name = name.strip()[:40]
    if not name:
        return False, "نام کشور خالی است."
    countries = d.setdefault("countries", {})
    key = str(user.telegram_id)
    x, y = int(getattr(user, "world_x", 0) or 0), int(getattr(user, "world_y", 0) or 0)
    if abs(x) + abs(y) < 20:
        return False, "برای ساخت کشور باید حداقل ۲۰ خانه از شهر آغازین دور شده باشی."
    if key in countries:
        return False, "قبلاً یک کشور داری."
    countries[key] = {"name": name, "ruler": int(user.telegram_id), "cities": [getattr(user, 'city', START_CITY)], "created_at": datetime.utcnow().isoformat()}
    save("open_world")
    return True, f"👑 کشور «{name}» در مختصات فعلی بنیان‌گذاری شد."


def feed(user, amount=25):
    user.hunger = min(100, int(getattr(user, "hunger", 100) or 0) + amount)


def drink(user, amount=30):
    user.thirst = min(100, int(getattr(user, "thirst", 100) or 0) + amount)

async def launch_portal_once(session) -> bool:
    """انتقال یک‌باره تمام کاربران به جهان جدید؛ پیشرفت حساب حفظ می‌شود اما مکان/فرقه‌های جهان قدیم از بین می‌روند."""
    d = world_state()
    if d.get("portal_done"):
        return False
    from sqlalchemy import select, delete
    from database.models import User
    from database.models_v2 import Sect, SectMember
    from database.models_v3 import Territory
    users = (await session.execute(select(User))).scalars().all()
    for u in users:
        u.world = WORLD_NAME
        u.city = START_CITY
        u.world_x = 0
        u.world_y = 0
        u.sky = 1
        u.sky_trial = False
        u.sky_ascended_at = None
        u.hunger = 100
        u.thirst = 100
    try:
        await session.execute(delete(SectMember))
    except Exception:
        pass
    try:
        await session.execute(delete(Territory))
    except Exception:
        pass
    try:
        sects = (await session.execute(select(Sect))).scalars().all()
        for s in sects:
            s.is_active = False
            s.member_count = 0
            s.leader_id = None
            # آزاد کردن نام یکتا تا ساخت فرقه جدید ممکن باشد
            try:
                base = (s.name or "فرقه")[:40]
                s.name = f"بایگانی-{s.id}-{base}"[:64]
            except Exception:
                s.name = f"archived-{s.id}"[:64]
    except Exception:
        pass
    # پاکسازی جهان‌های حافظه‌ای قدیمی؛ حساب، قدرت و کاراکتر بازیکن‌ها حفظ می‌شود.
    for ns in ("kingdoms", "world_map", "alliances", "sect_wars"):
        old = get_dict(ns)
        old.clear()
        save(ns)
    d["portal_done"] = True
    d["portal_launched_at"] = datetime.utcnow().isoformat()
    save("open_world")
    await session.commit()
    return True
