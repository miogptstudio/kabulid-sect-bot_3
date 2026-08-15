"""خدمتکاران نژادی — وفاداری، شکار اصیل، دگرگونی"""
from __future__ import annotations
import random
from datetime import datetime, timedelta
from services.persist import get_dict, save as _psave

# نژادها: buyable از بازار | purebred فقط با جنگ/شکار
RACES = {
    "انسان": {"purebred": False, "loyalty0": 70, "cult_rate": 1.0, "transform": None},
    "نیمهانسان": {"purebred": False, "loyalty0": 65, "cult_rate": 1.1, "transform": "انسان"},
    "گربهای نیمهانسان": {"purebred": False, "loyalty0": 75, "cult_rate": 1.15, "transform": "نیمهانسان"},
    "گرگنمای": {"purebred": True, "loyalty0": 40, "cult_rate": 1.2, "transform": "نیمهانسان"},
    "روباهنمای": {"purebred": False, "loyalty0": 55, "cult_rate": 1.25, "transform": "نیمهانسان"},
    "اژدهاتبار": {"purebred": True, "loyalty0": 30, "cult_rate": 1.5, "transform": "نیمهانسان"},
    "ققنوستبار": {"purebred": True, "loyalty0": 35, "cult_rate": 1.45, "transform": "نیمهانسان"},
    "جن جنگلی": {"purebred": False, "loyalty0": 60, "cult_rate": 1.2, "transform": "نیمهانسان"},
    "دیوتبار": {"purebred": True, "loyalty0": 25, "cult_rate": 1.4, "transform": "نیمهانسان"},
    "فرشتهتبار": {"purebred": True, "loyalty0": 45, "cult_rate": 1.35, "transform": "نیمهانسان"},
    "اهریمنی": {"purebred": True, "loyalty0": 20, "cult_rate": 1.5, "transform": "دیوتبار"},
    "سیمرغزاده": {"purebred": True, "loyalty0": 40, "cult_rate": 1.55, "transform": "نیمهانسان"},
    "روحپیما": {"purebred": False, "loyalty0": 50, "cult_rate": 1.3, "transform": "نیمهانسان"},
    "خونآشام کهن": {"purebred": True, "loyalty0": 28, "cult_rate": 1.4, "transform": "نیمهانسان"},
    "مهپیما": {"purebred": False, "loyalty0": 58, "cult_rate": 1.2, "transform": "نیمهانسان"},
    # تبارهای الهی — بسیار کمیاب و مناسب خدمتکارهای ردهبالا
    "تبار الهی": {"purebred": False, "loyalty0": 60, "cult_rate": 2.0, "transform": None},
    "الههتبار": {"purebred": False, "loyalty0": 70, "cult_rate": 2.2, "transform": "تبار الهی"},
    "خدایتبار": {"purebred": False, "loyalty0": 55, "cult_rate": 2.4, "transform": "تبار الهی"},
    "آسمانیتبار": {"purebred": False, "loyalty0": 65, "cult_rate": 2.1, "transform": "تبار الهی"},
}

CAT_GIRL_NAMES = [
    "میوکا", "نکو", "ساکورادم", "یورهنکو", "لوناگوش",
    "پیشیمهتاب", "گربهزرین", "دمابریشمی", "چشمزمردی", "پنجهسفید",
]

MARKET = [
    # انسان / نیمهانسان قابل خرید
    {"id": 1, "name": "آلیس", "gender": "زن", "race": "انسان", "price": 500, "desc": "خدمتکار وفادار"},
    {"id": 2, "name": "لیان", "gender": "زن", "race": "نیمهانسان", "price": 900, "desc": "خدمتکار جنگی"},
    {"id": 3, "name": "مینگ", "gender": "مرد", "race": "انسان", "price": 600, "desc": "نگهبان خانه"},
    {"id": 4, "name": "سارا", "gender": "زن", "race": "انسان", "price": 1200, "desc": "خدمتکار نجیب"},
    {"id": 5, "name": "کای", "gender": "مرد", "race": "نیمهانسان", "price": 1000, "desc": "نگهبان دروازه"},
    {"id": 6, "name": "یوکی", "gender": "زن", "race": "روباهنمای", "price": 1800, "desc": "دم نهگانه"},
    {"id": 7, "name": "رستمیار", "gender": "مرد", "race": "انسان", "price": 2000, "desc": "برده جنگی ایرانی"},
    {"id": 8, "name": "شیرین", "gender": "زن", "race": "انسان", "price": 1800, "desc": "خدمتکار دربار"},
    {"id": 9, "name": "بهرام", "gender": "مرد", "race": "نیمهانسان", "price": 2200, "desc": "شکارچی"},
    {"id": 10, "name": "نرگس", "gender": "زن", "race": "جن جنگلی", "price": 2100, "desc": "باغبان روح"},
    {"id": 11, "name": "آرش", "gender": "مرد", "race": "انسان", "price": 2500, "desc": "کماندار"},
    {"id": 12, "name": "لاله", "gender": "زن", "race": "انسان", "price": 1400, "desc": "آشپزخانه"},
    {"id": 13, "name": "کاوه", "gender": "مرد", "race": "نیمهانسان", "price": 3000, "desc": "آهنگر"},
    {"id": 14, "name": "مهتاب", "gender": "زن", "race": "روحپیما", "price": 3200, "desc": "روحانی"},
    {"id": 15, "name": "سهراب", "gender": "مرد", "race": "انسان", "price": 3500, "desc": "پهلوان"},
    {"id": 16, "name": "پریسا", "gender": "زن", "race": "مهپیما", "price": 3400, "desc": "جادویی"},
    {"id": 17, "name": "توران", "gender": "مرد", "race": "نیمهانسان", "price": 4000, "desc": "نگهبان فرقه"},
    {"id": 18, "name": "آناهیتا", "gender": "زن", "race": "تبار الهی", "price": 999000000000, "desc": "خدمتکار ویژهٔ الههٔ آبها؛ بسیار کمیاب", "special_monthly": True, "monthly_limit": 3},
    {"id": 19, "name": "دیوبنده", "gender": "مرد", "race": "دیوتبار", "price": 7500, "desc": "تاریک"},
    {"id": 20, "name": "فرشتهیار", "gender": "زن", "race": "فرشتهتبار", "price": 8500, "desc": "خدمتکار نور"},
    # گربهای نیمهانسان زن
    {"id": 21, "name": "میوکا", "gender": "زن", "race": "گربهای نیمهانسان", "price": 4500, "desc": "گوش گربهای · وفادار"},
    {"id": 22, "name": "نکوساکورا", "gender": "زن", "race": "گربهای نیمهانسان", "price": 4800, "desc": "دم ابریشمی"},
    {"id": 23, "name": "لوناگوش", "gender": "زن", "race": "گربهای نیمهانسان", "price": 5200, "desc": "چشم مهتاب"},
    {"id": 24, "name": "پیشیزرین", "gender": "زن", "race": "گربهای نیمهانسان", "price": 5600, "desc": "پنجهطلایی"},
    {"id": 25, "name": "یورهنکو", "gender": "زن", "race": "گربهای نیمهانسان", "price": 6000, "desc": "نیمهروح گربه"},
    # خدمتکارهای تبار الهی — خریدنی و بسیار کمیاب
    {"id": 26, "name": "آریانا", "gender": "زن", "race": "الههتبار", "price": 1000000000, "desc": "خدمتکار الهی؛ سرعت بالای تذهیب", "special_weekly": True},
    {"id": 27, "name": "یوناس", "gender": "مرد", "race": "خدایتبار", "price": 1500000000, "desc": "خدمتکار الهی؛ قدرت رزمی عظیم"},
    {"id": 28, "name": "سولارا", "gender": "زن", "race": "آسمانیتبار", "price": 2000000000, "desc": "خدمتکار آسمانی؛ محافظ قلمرو"},
    {"id": 29, "name": "ایلیوس", "gender": "مرد", "race": "تبار الهی", "price": 2500000000, "desc": "خون الهی خالص و کمیاب"},
    {"id": 30, "name": "نریا", "gender": "زن", "race": "تبار الهی", "price": 3000000000, "desc": "خدمتکار الهی؛ وفاداری بالا", "special_weekly": True},
    {"id": 31, "name": "کایروس", "gender": "مرد", "race": "خدایتبار", "price": 5000000000, "desc": "خدمتکار جنگی خدایان"},
    {"id": 32, "name": "آسترا", "gender": "زن", "race": "آسمانیتبار", "price": 7500000000, "desc": "خدمتکار آسمانی؛ تذهیب بسیار سریع"},
    {"id": 33, "name": "اورین", "gender": "مرد", "race": "تبار الهی", "price": 10000000000, "desc": "خدمتکار ردهبالای الهی"},
]

# توضیحات اختصاصی هر خدمتکار؛ در بازار و پنل اختصاصی نمایش داده میشود.
SERVANT_LORE = {
    "آلیس": "خدمتکاری آرام و منظم که در مدیریت خانه و افزایش ثبات قلمرو مهارت دارد.",
    "لیان": "نیمهانسانی چابک که برای گشتزنی، مراقبت و نبردهای سریع تربیت شده است.",
    "مینگ": "نگهبانی قابلاعتماد با تمرکز بر دفاع و محافظت از اموال صاحبش.",
    "سارا": "خدمتکاری اشرافی با مهارت بالا در اداره تالار و افزایش نظم اجتماعی.",
    "کای": "نگهبان دروازه با استقامت بالا و واکنش سریع در برابر مهاجمان.",
    "یوکی": "روباهنمای زیرک که به سرعت، فریب و پیدا کردن مسیرهای پنهان شهرت دارد.",
    "رستمیار": "جنگجویی نیرومند با روحیه پهلوانی و تمرکز ویژه روی قدرت رزمی.",
    "شیرین": "خدمتکار درباری باهوش که در روابط اجتماعی و مدیریت مهمانیها توانمند است.",
    "بهرام": "شکارچی باتجربه که در ردیابی دشمنان و عملیات خارج از قلمرو مهارت دارد.",
    "نرگس": "جن جنگلی آرام که با طبیعت پیوند دارد و در رشد و نگهداری قلمرو کمک میکند.",
    "آرش": "کمانداری دقیق که از فاصله دور ضربات سنگین و حسابشده وارد میکند.",
    "لاله": "خدمتکاری پرانرژی و متخصص آشپزی که برای پشتیبانی روزمره فرقه مناسب است.",
    "کاوه": "آهنگری قدرتمند که در ساخت و نگهداری تجهیزات رزمی نقش مهمی دارد.",
    "مهتاب": "روحپیمایی مرموز با توانایی کنترل انرژیهای روحی و پشتیبانی معنوی.",
    "سهراب": "پهلوانی جوان و مقاوم که در نبرد مستقیم عملکرد بسیار خوبی دارد.",
    "پریسا": "مهپیما با توانایی پنهانکاری و جابهجایی در میدانهای دشوار.",
    "توران": "نگهبان وفادار فرقه که تمرکز اصلیاش دفاع از اعضا و ساختمانهای مهم است.",
    "آناهیتا": "خدمتکار الهیِ آبها و باروری؛ آرام، باوقار و بسیار کمیاب که تواناییهای حمایتی، دفاعی و رشد قلمرو را تقویت میکند.",
    "دیوبنده": "جنگجویی تاریک و خشن که در شکستن خطوط دفاعی دشمن تخصص دارد.",
    "فرشتهیار": "خدمتکار نورانی با توانایی تقویت روحیه و محافظت از صاحبش.",
    "میوکا": "گربهای چابک با حواس تیز که در سرعت، جاسوسی و واکنش سریع برتری دارد.",
    "نکوساکورا": "گربهای آرام و باهوش با استعداد بالا در حرکت بیصدا و دیدهبانی.",
    "لوناگوش": "گربهای با پیوند قوی با انرژی ماه که در شب قدرت بیشتری پیدا میکند.",
    "پیشیزرین": "گربهای نادر با پنجههای طلایی و استعداد ویژه در پیدا کردن گنج.",
    "یورهنکو": "گربهای روحانی که میان جهان مادی و روحی حرکت میکند.",
    "آریانا": "خدمتکار الههتبار با سرعت بالای تذهیب و توانایی تقویت رشد صاحبش.",
    "یوناس": "خدایتباری سنگینقدرت که در نبرد مستقیم و افزایش قدرت رزمی ممتاز است.",
    "سولارا": "آسمانیتباری محافظ که سپرهای قدرتمند برای صاحب و قلمرو ایجاد میکند.",
    "ایلیوس": "دارنده خون الهی خالص که تعادل خوبی میان قدرت، سرعت و دفاع دارد.",
    "نریا": "خدمتکاری از تبار الهی با وفاداری بالا و استعداد ویژه در پشتیبانی و رشد.",
    "کایروس": "جنگجوی خدایان که برای نبردهای سنگین و رویارویی با دشمنان قدرتمند ساخته شده است.",
    "آسترا": "آسمانیتباری سریع که رشد تذهیب را به شکل چشمگیری افزایش میدهد.",
    "اورین": "خدمتکار ردهبالای الهی با انرژی عظیم و سازگاری بالا با تکنیکهای نادر.",
    "آلیا": "گربهای الهیگونه با چابکی فوقالعاده که در سرعت و جاخالی تخصص دارد.",
    "ناکوبی": "خدمتکاری با بالهای تاریک و حضور سنگین که قدرت رزمی و توان مقابله را افزایش میدهد.",
    "مادر الههگان": "موجودی فراتر از تبارهای معمول الهی؛ نماد حمایت، رشد و قدرت عظیم در کنار صاحبش.",
}

def servant_lore(name: str, fallback: str = "خدمتکاری ویژه با تواناییهای منحصربهفرد.") -> str:
    return SERVANT_LORE.get(name, fallback)

# خدمتکارهای ویژه با خرید هفتگی — هرکدام مستقل
MARKET.extend([
    {"id": 34, "name": "آلیا", "gender": "زن", "race": "گربهای نیمهانسان", "price": 6000000000, "desc": "خدمتکار ویژه؛ تبار گربهای و چابکی بالا", "special_weekly": True},
    {"id": 35, "name": "ناکوبی", "gender": "زن", "race": "اهریمنی", "price": 9000000000, "desc": "خدمتکار ویژه؛ بالهای تاریک و قدرت رزمی بالا", "special_weekly": True},
    {"id": 36, "name": "مادر الههگان", "gender": "زن", "race": "تبار الهی", "price": 50000000000, "desc": "خدمتکار ویژه؛ موجودی فراتر از تبارهای معمول الهی", "special_weekly": True},
])

# اصیلها فقط با جنگ — قالب برای اسپاون شکار
PUREBRED_TEMPLATES = [
    {"name": "گرگسالار سیاه", "gender": "مرد", "race": "گرگنمای", "power": 80},
    {"name": "گرگنمای ماه", "gender": "زن", "race": "گرگنمای", "power": 90},
    {"name": "اژدهابچه سرخ", "gender": "مرد", "race": "اژدهاتبار", "power": 150},
    {"name": "اژدهبانو", "gender": "زن", "race": "اژدهاتبار", "power": 160},
    {"name": "جوجه ققنوس", "gender": "زن", "race": "ققنوستبار", "power": 140},
    {"name": "شعله ققنوس", "gender": "مرد", "race": "ققنوستبار", "power": 155},
    {"name": "دیو مرز", "gender": "مرد", "race": "دیوتبار", "power": 120},
    {"name": "اهریمنزاده", "gender": "مرد", "race": "اهریمنی", "power": 180},
    {"name": "سیمرغیار", "gender": "زن", "race": "سیمرغزاده", "power": 170},
    {"name": "خونشاه کهن", "gender": "مرد", "race": "خونآشام کهن", "power": 130},
    {"name": "فرشته سقوطکرده", "gender": "زن", "race": "فرشتهتبار", "power": 145},
]

TRANSFORM_CULT = 50  # سطح تذهیب خدمتکار برای دگرگونی
HUNT_CD = timedelta(minutes=20)
BETRAY_CHANCE_BASE = 0.02  # در وفاداری پایین


def _owned() -> dict:
    return get_dict("servants_v2")  # tg -> list of servant instances


def _legacy_ids() -> dict:
    return get_dict("servants")  # old id list


def _hunt_cd() -> dict:
    return get_dict("servant_hunt_cd")


def _marriages() -> dict:
    """ازدواج خدمتکارها را جدا از حافظهٔ موقت برنامه نگه میدارد."""
    return get_dict("servant_marriages")


def _servant_by_selector(tg: int, selector: int):
    """شمارهٔ لیست /myservants یا شمارهٔ بازار را قبول میکند."""
    bag = list_owned(tg)
    if 1 <= selector <= len(bag):
        return bag[selector - 1], selector - 1
    matches = [(i, x) for i, x in enumerate(bag) if int(x.get("base_id") or -1) == selector]
    if matches:
        i, x = matches[0]
        return x, i
    return None, None


def married_uids(tg: int) -> list[str]:
    data = _marriages()
    return [str(x) for x in (data.get(str(int(tg))) or [])]


def is_married(tg: int, servant: dict) -> bool:
    return str(servant.get("uid")) in set(married_uids(tg))


def marry_servant(tg: int, selector: int) -> tuple[bool, str, dict | None]:
    """ازدواج پایدار با خدمتکار؛ selector هم شمارهٔ لیست و هم id بازار است."""
    servant, _ = _servant_by_selector(tg, selector)
    if not servant:
        return False, "خدمتکار پیدا نشد. شمارهٔ /myservants را وارد کن.", None

    uid = str(servant.get("uid"))
    data = _marriages()
    key = str(int(tg))
    married = [str(x) for x in (data.get(key) or [])]

    if uid in married:
        return False, f"قبلاً با «{servant.get('name')}» ازدواج کردهای.", servant

    married.append(uid)
    data[key] = married
    _psave("servant_marriages")

    return True, (
        f"💍 با خدمتکار «{servant.get('name')}» ازدواج کردی!\n"
        f"نژاد: {servant.get('race', '—')} | وفاداری: {servant.get('loyalty', 0)}%\n"
        f"از این به بعد این ازدواج بعد از ریاستارت هم باقی میمونه.\n"
        f"/myservants — مشاهدهٔ خانواده"
    ), servant


SPECIAL_MONTHLY_IDS = {int(s["id"]) for s in MARKET if s.get("special_monthly")}
SPECIAL_MONTHLY_LIMITS = {int(s["id"]): int(s.get("monthly_limit", 3)) for s in MARKET if s.get("special_monthly")}

def _monthly_buy_data() -> dict:
    return get_dict("servant_monthly_buy")

def _month_key() -> str:
    now = datetime.utcnow()
    return f"{now.year:04d}-{now.month:02d}"

def monthly_buy_remaining(tg: int, sid: int) -> tuple[int, int] | None:
    sid = int(sid)
    if sid not in SPECIAL_MONTHLY_IDS:
        return None
    data = _monthly_buy_data()
    month = _month_key()
    rec = data.get(str(sid)) or {}
    if rec.get("month") != month:
        return 0, SPECIAL_MONTHLY_LIMITS.get(sid, 3)
    used = max(0, int(rec.get("used", 0)))
    limit = SPECIAL_MONTHLY_LIMITS.get(sid, 3)
    return used, max(0, limit - used)

def _record_monthly_buy(sid: int) -> None:
    sid = int(sid)
    if sid not in SPECIAL_MONTHLY_IDS:
        return
    data = _monthly_buy_data()
    month = _month_key()
    rec = data.get(str(sid)) or {}
    if rec.get("month") != month:
        rec = {"month": month, "used": 0}
    rec["used"] = int(rec.get("used", 0)) + 1
    data[str(sid)] = rec
    _psave("servant_monthly_buy")

SPECIAL_WEEKLY_COOLDOWN = timedelta(days=7)
SPECIAL_WEEKLY_IDS = {int(s["id"]) for s in MARKET if s.get("special_weekly")}

def _special_buy_cd() -> dict:
    return get_dict("servant_special_buy_cd")

def _remaining_special_cd(tg: int, sid: int):
    if int(sid) not in SPECIAL_WEEKLY_IDS:
        return None
    data = _special_buy_cd()
    raw = data.get(f"{int(tg)}:{int(sid)}")
    if not raw:
        return None
    try:
        last = datetime.fromisoformat(str(raw))
        left = SPECIAL_WEEKLY_COOLDOWN - (datetime.utcnow() - last)
        if left.total_seconds() <= 0:
            data.pop(f"{int(tg)}:{int(sid)}", None)
            _psave("servant_special_buy_cd")
            return None
        return left
    except Exception:
        return None

def special_buy_remaining_text(tg: int, sid: int) -> str | None:
    left = _remaining_special_cd(tg, sid)
    if left is None:
        return None
    total = max(0, int(left.total_seconds()))
    days, rem = divmod(total, 86400)
    hours, rem = divmod(rem, 3600)
    minutes = rem // 60
    return f"{days} روز، {hours} ساعت و {minutes} دقیقه"

def _record_special_buy(tg: int, sid: int) -> None:
    if int(sid) not in SPECIAL_WEEKLY_IDS:
        return
    data = _special_buy_cd()
    data[f"{int(tg)}:{int(sid)}"] = datetime.utcnow().isoformat()
    _psave("servant_special_buy_cd")
    try:
        import asyncio
        from services.persist import sync_to_db
        asyncio.get_running_loop().create_task(sync_to_db())
    except Exception:
        pass

def market_list() -> str:
    lines = ["🛒 <b>بازار خدمتکار</b>", "نژادهای خریدنی (اصیلها با /huntservant)", ""]
    for s in MARKET:
        race = s.get("race", "انسان")
        pure = "🔒اصیل" if RACES.get(race, {}).get("purebred") else ""
        weekly = " ⏳ خرید هر ۷ روز" if s.get("special_weekly") else ""
        monthly = f" 🌙 فقط {s.get('monthly_limit', 3)} عدد در ماه" if s.get("special_monthly") else ""
        lines.append(
            f"#{s['id']} {s['name']} | {s['gender']} | {race} {pure}{weekly}{monthly}" + chr(10)
            + f"  {s['price']:,} سکه — {servant_lore(s['name'], s.get('desc', "خدمتکار ویژه با تواناییهای منحصربهفرد."))}"
        )
    lines += [
        "",
        "/buyservant شماره",
        "/huntservant — شکار نژاد اصیل",
        "/myservants — لیست با وفاداری",
        "/trainservant شماره — تذهیب خدمتکار",
        "/transformservant شماره — دگرگونی",
        "/loyalty شماره — وضعیت وفاداری",
    ]
    return chr(10).join(lines)


def _new_instance(template: dict, source: str = "buy") -> dict:
    race = template.get("race") or "انسان"
    info = RACES.get(race, RACES["انسان"])
    return {
        "uid": f"{template.get('id', random.randint(1000,9999))}_{random.randint(100,999)}",
        "base_id": template.get("id"),
        "name": template["name"],
        "gender": template.get("gender", "زن"),
        "race": race,
        "loyalty": int(info.get("loyalty0", 50)),
        "cult": 1,
        "power": int(template.get("power") or 20),
        "speed": int(template.get("speed") or (12 + int(template.get("power") or 20) // 8)),
        "defense": int(template.get("defense") or (10 + int(template.get("power") or 20) // 10)),
        "lifespan": int(template.get("lifespan") or 100),
        "source": source,
        "special_weekly": bool(template.get("special_weekly")),
        "transformed": False,
        "at": datetime.utcnow().isoformat(),
    }


def list_owned(tg: int) -> list[dict]:
    m = _owned()
    sk = str(int(tg))
    bag = list(m.get(sk) or [])
    # migrate legacy ids
    leg = _legacy_ids().get(sk) or []
    if leg and not bag:
        for i in leg:
            s = next((x for x in MARKET if x["id"] == i), None)
            if s:
                bag.append(_new_instance(s, "legacy"))
        m[sk] = bag
        _psave("servants_v2")
    return bag


def save_owned(tg: int, bag: list) -> None:
    m = _owned()
    m[str(int(tg))] = bag
    _psave("servants_v2")


def buy(tg: int, sid: int, coins: int) -> tuple[bool, str, int]:
    s = next((x for x in MARKET if x["id"] == sid), None)
    if not s:
        return False, "شماره نامعتبر. /servants", coins
    race = s.get("race", "انسان")
    monthly = monthly_buy_remaining(tg, sid)
    if monthly is not None:
        used, remaining = monthly
        if remaining <= 0:
            return False, f"⛔ خرید «{s['name']}» برای این ماه تمام شده است.\nسهم ماهانه: {SPECIAL_MONTHLY_LIMITS.get(sid, 3)} عدد — ماه بعد دوباره فعال میشود.", coins
    left_text = special_buy_remaining_text(tg, sid)
    if left_text:
        return False, f"⏳ خرید «{s['name']}» محدود به هر ۷ روز است.\nزمان باقیمانده: {left_text}", coins
    if RACES.get(race, {}).get("purebred") and s["price"] < 7000:
        # rare market purebreds allowed if expensive
        pass
    if coins < s["price"]:
        return False, f"سکه کافی نیست (نیاز {s['price']:,}).", coins
    bag = list_owned(tg)
    if any(x.get("base_id") == sid and x.get("source") == "buy" for x in bag):
        # allow multiple of same market? yes with different uid - limit 1 of same base for buy
        if sum(1 for x in bag if x.get("base_id") == sid) >= 2:
            return False, "از این مدل حداکثر ۲ تا.", coins
    inst = _new_instance(s, "buy")
    bag.append(inst)
    save_owned(tg, bag)
    _record_special_buy(tg, sid)
    _record_monthly_buy(sid)
    # legacy sync
    leg = _legacy_ids()
    ids = list(leg.get(str(int(tg))) or [])
    if sid not in ids:
        ids.append(sid)
        leg[str(int(tg))] = ids
        _psave("servants")
    return True, (
        f"✅ {s['name']} ({race}) خرید شد." + chr(10)
        + f"وفاداری: {inst['loyalty']}% | تذهیب: {inst['cult']}"
    ), coins - s["price"]


def servant_panel_text(s: dict, index: int = 1, purchased: bool = False) -> str:
    title = "🛒 خرید انجام شد" if purchased else "🧑🤝🧑 پنل خدمتکار"
    lines = [
        f"{title}",
        "",
        f"👤 <b>{s.get('name','—')}</b>  · شماره {index}",
        f"🧬 تبار: {s.get('race','—')}",
        f"⚧ جنسیت: {s.get('gender','—')}",
    ]
    if s.get("special_monthly"):
        used, remaining = monthly_buy_remaining(0, int(s.get("base_id") or 0)) or (0, int(s.get("monthly_limit", 3)))
        lines.append(f"🌙 خرید ویژه: فقط {s.get('monthly_limit', 3)} عدد در هر ماه | باقیمانده بازار: {remaining}")
    elif s.get("special_weekly"):
        lines.append("⏳ خرید ویژه: هر ۷ روز یکبار")
    lines.extend([
        f"❤️ وفاداری: <b>{s.get('loyalty',0)}٪</b>",
        f"🧘 تذهیب: <b>{s.get('cult',1)}</b>",
        f"⚔️ قدرت: <b>{s.get('power',0)}</b>",
        f"💨 سرعت: <b>{s.get('speed',0)}</b>",
        f"🛡️ دفاع: <b>{s.get('defense',0)}</b>",
        f"⏳ عمر: <b>{s.get('lifespan',100)}</b>",
        f"✨ وضعیت: {'دگرگونشده' if s.get('transformed') else 'طبیعی'}",
        "",
        f"برای ارتقا: /trainservant {index}",
        f"برای وفاداری: /feedloyalty {index}",
        f"برای ازدواج با خدمتکار: /marry servant {index}",
    ])
    return "\n".join(lines)

def owned_text(tg: int) -> str:
    bag = list_owned(tg)
    if not bag:
        return "خدمتکاری نداری. /servants یا /huntservant"
    lines = [f"👤 <b>خدمتکارهای تو</b> ({len(bag)})", ""]
    for i, s in enumerate(bag, 1):
        tr = "🦋دگرگون" if s.get("transformed") else ""
        married = " 💍 همسر" if is_married(tg, s) else ""
        lines.append(
            f"{i}. {s['name']} | {s['gender']} | {s.get('race')} {tr}{married}" + chr(10)
            + f"   ❤️وفاداری {s.get('loyalty',0)}% | 🧘تذهیب {s.get('cult',1)} | ⚔{s.get('power',0)} | 💨{s.get('speed',0)} | 🛡️{s.get('defense',0)} | ⏳{s.get('lifespan',100)}"
        )
    lines += [
        "",
        "/trainservant شماره — پرورش تذهیب",
        "/transformservant شماره — دگرگونی (تذهیب≥{TRANSFORM_CULT})".replace("{TRANSFORM_CULT}", str(TRANSFORM_CULT)),
        "/feedloyalty شماره — افزایش وفاداری",
        "/checkbetray — بررسی خیانت احتمالی",
    ]
    return chr(10).join(lines)


def train(tg: int, idx: int) -> str:
    bag = list_owned(tg)
    if idx < 1 or idx > len(bag):
        return "شماره نامعتبر."
    s = bag[idx - 1]
    rate = float(RACES.get(s.get("race"), {}).get("cult_rate", 1.0))
    gain = max(1, int(random.randint(1, 3) * rate))
    s["cult"] = int(s.get("cult") or 1) + gain
    s["power"] = int(s.get("power") or 20) + gain * 2
    s["speed"] = int(s.get("speed") or 10) + max(1, gain // 2)
    s["defense"] = int(s.get("defense") or 10) + max(1, gain // 2)
    s["lifespan"] = min(500, int(s.get("lifespan") or 100) + max(0, gain // 3))
    # کمی وفاداری از توجه
    s["loyalty"] = min(100, int(s.get("loyalty") or 50) + random.randint(0, 2))
    bag[idx - 1] = s
    save_owned(tg, bag)
    msg = f"🧘 {s['name']}: تذهیب {s['cult']} (+{gain}) | قدرت {s['power']}"
    if s["cult"] >= TRANSFORM_CULT and not s.get("transformed"):
        msg += chr(10) + f"✨ آماده دگرگونی! /transformservant {idx}"
    return msg


def transform(tg: int, idx: int) -> str:
    bag = list_owned(tg)
    if idx < 1 or idx > len(bag):
        return "شماره نامعتبر."
    s = bag[idx - 1]
    if s.get("transformed"):
        return "قبلاً دگرگون شده."
    if int(s.get("cult") or 1) < TRANSFORM_CULT:
        return f"تذهیب کم است (نیاز {TRANSFORM_CULT}، الان {s.get('cult')})."
    race = s.get("race") or "انسان"
    nxt = RACES.get(race, {}).get("transform")
    if not nxt:
        return "این نژاد دگرگونی ندارد."
    old = race
    s["race"] = nxt
    s["transformed"] = True
    s["power"] = int(s.get("power") or 0) + 40
    s["speed"] = int(s.get("speed") or 10) + 12
    s["defense"] = int(s.get("defense") or 10) + 12
    s["lifespan"] = min(500, int(s.get("lifespan") or 100) + 25)
    s["loyalty"] = min(100, int(s.get("loyalty") or 50) + 10)
    # گربهای → نیمهانسان با حفظ لقب
    if old == "گربهای نیمهانسان":
        s["name"] = s["name"] + " (انسانیشده)"
    bag[idx - 1] = s
    save_owned(tg, bag)
    return (
        f"🦋 دگرگونی کامل!" + chr(10)
        + f"{s['name']}: {old} → <b>{nxt}</b>" + chr(10)
        + f"قدرت +۴۰ | وفاداری {s['loyalty']}%"
    )


def feed_loyalty(tg: int, idx: int, coins: int) -> tuple[str, int]:
    bag = list_owned(tg)
    if idx < 1 or idx > len(bag):
        return "شماره نامعتبر.", coins
    cost = 50
    if coins < cost:
        return "۵۰ سکه لازم است.", coins
    s = bag[idx - 1]
    old_loyalty = max(0, min(100, int(s.get("loyalty") or 50)))
    if old_loyalty >= 100:
        return f"❤️ وفاداری «{s['name']}» همین الان ۱۰۰٪ است.", coins
    gain = min(8, 100 - old_loyalty)
    s["loyalty"] = old_loyalty + gain
    bag[idx - 1] = s
    save_owned(tg, bag)
    return (
        f"❤️ وفاداری «{s['name']}»: {s['loyalty']}% "
        f"(+{gain} | هزینه: {cost} سکه)"
    ), coins - cost


def check_betrayal(tg: int) -> str:
    bag = list_owned(tg)
    if not bag:
        return "خدمتکاری نیست."
    lines = ["🕵️ بررسی وفاداری", ""]
    fled = []
    for i, s in enumerate(list(bag)):
        loy = int(s.get("loyalty") or 50)
        chance = 0.0
        if loy < 20:
            chance = 0.35
        elif loy < 40:
            chance = 0.12
        elif loy < 55:
            chance = 0.04
        else:
            chance = 0.0
        if chance > 0 and random.random() < chance:
            lines.append(f"⚠️ {s['name']} خیانت کرد و فرار کرد! (وفاداری {loy}%)")
            fled.append(i)
        else:
            lines.append(f"• {s['name']}: {loy}% — امن" if loy >= 55 else f"• {s['name']}: {loy}% — در خطر")
    for i in reversed(fled):
        bag.pop(i)
    if fled:
        save_owned(tg, bag)
    return chr(10).join(lines)


def hunt(tg: int, player_power: int) -> str:
    cd = _hunt_cd()
    sk = str(int(tg))
    last = cd.get(sk)
    if last:
        try:
            if datetime.utcnow() - datetime.fromisoformat(last) < HUNT_CD:
                left = int((HUNT_CD - (datetime.utcnow() - datetime.fromisoformat(last))).total_seconds())
                return f"⏳ شکار هر {int(HUNT_CD.total_seconds()//60)}د. {left}ث صبر کن."
        except Exception:
            pass
    target = random.choice(PUREBRED_TEMPLATES)
    # fight
    margin = player_power - int(target["power"])
    if margin < -40:
        cd[sk] = datetime.utcnow().isoformat()
        _psave("servant_hunt_cd")
        return (
            f"🐺 با <b>{target['name']}</b> ({target['race']}) جنگیدی و باختید." + chr(10)
            + f"قدرت او {target['power']} — قدرت تو {player_power}"
        )
    # capture chance
    chance = 0.35 + max(0, margin) * 0.01
    chance = min(0.85, chance)
    cd[sk] = datetime.utcnow().isoformat()
    _psave("servant_hunt_cd")
    if random.random() > chance:
        return (
            f"⚔ {target['name']} را زدی اما فرار کرد." + chr(10)
            + f"شانس تسخیر: {int(chance*100)}%"
        )
    inst = _new_instance(
        {"id": random.randint(9000, 9999), "name": target["name"], "gender": target["gender"],
         "race": target["race"], "power": target["power"]},
        source="hunt",
    )
    # captured purebreds start lower loyalty
    inst["loyalty"] = max(15, int(RACES.get(target["race"], {}).get("loyalty0", 30)) - 10)
    bag = list_owned(tg)
    bag.append(inst)
    save_owned(tg, bag)
    return (
        f"⛓ تسخیر موفق!" + chr(10)
        + f"<b>{inst['name']}</b> | {inst['race']} | {inst['gender']}" + chr(10)
        + f"وفاداری اولیه: {inst['loyalty']}% (کم — مراقب خیانت باش)" + chr(10)
        + f"/trainservant {len(bag)} | /feedloyalty {len(bag)}"
    )


# سازگاری با کد قدیم
SERVANTS = MARKET


# ==================== دوئل اختصاصی خدمتکارها ====================

def servant_duel_score(servant: dict) -> int:
    """امتیاز رزمی خدمتکار؛ مستقل از قدرت اصلی صاحب."""
    power = max(0, int(servant.get("power") or 0))
    speed = max(0, int(servant.get("speed") or 0))
    defense = max(0, int(servant.get("defense") or 0))
    cult = max(1, int(servant.get("cult") or 1))
    loyalty = max(0, min(100, int(servant.get("loyalty") or 0)))
    lifespan = max(0, int(servant.get("lifespan") or 0))
    return power + speed + defense + (cult * 4) + (loyalty * 2) + min(lifespan, 100)

def propose_servant_duel(a_tg: int, b_tg: int, idx_a: int, idx_b: int) -> tuple[bool, str, str | None]:
    """درخواست دوئل خدمتکار؛ داده درخواست پایدار است تا با ریاستارت از بین نرود."""
    a = list_owned(a_tg)
    b = list_owned(b_tg)
    if idx_a < 1 or idx_a > len(a):
        return False, "شماره خدمتکار خودت نامعتبر است.", None
    if idx_b < 1 or idx_b > len(b):
        return False, "شماره خدمتکار حریف نامعتبر است.", None
    if int(a_tg) == int(b_tg):
        return False, "با خدمتکار خودت نمیتوانی دوئل کنی.", None

    sa, sb = a[idx_a - 1], b[idx_b - 1]
    key = f"sd:{int(a_tg)}:{int(b_tg)}:{str(sa.get('uid', idx_a))}:{str(sb.get('uid', idx_b))}"
    pending = get_dict("servant_duel_pending")
    pending[key] = {
        "a": int(a_tg), "b": int(b_tg),
        "sa": dict(sa), "sb": dict(sb),
        "created_at": datetime.utcnow().isoformat(),
    }
    _psave("servant_duel_pending")
    pa, pb = servant_duel_score(sa), servant_duel_score(sb)
    return True, (
        "⚔️ <b>درخواست دوئل خدمتکاران</b>\n\n"
        f"🧑 {sa.get('name','—')} — قدرت نبرد {pa:,}\n"
        f"🧑 {sb.get('name','—')} — قدرت نبرد {pb:,}\n\n"
        f"حریف باید بنویسد: <code>/acceptservduel {key}</code>\n"
        "این نبرد فقط بین دو خدمتکار انجام میشود و قدرت صاحبها مستقیماً وارد محاسبه نمیشود."
    ), key

def accept_servant_duel(key: str, acceptor_tg: int) -> tuple[bool, str]:
    pending = get_dict("servant_duel_pending")
    d = pending.get(key)
    if not d:
        return False, "این درخواست پیدا نشد یا قبلاً پاسخ داده شده است."
    if int(acceptor_tg) != int(d["b"]):
        return False, "فقط صاحب خدمتکار دوم میتواند این درخواست را قبول کند."

    # اطمینان از اینکه هر دو خدمتکار هنوز در اختیار صاحبانشان هستند.
    a = list_owned(d["a"])
    b = list_owned(d["b"])
    uid_a = str(d["sa"].get("uid"))
    uid_b = str(d["sb"].get("uid"))
    sa = next((x for x in a if str(x.get("uid")) == uid_a), None)
    sb = next((x for x in b if str(x.get("uid")) == uid_b), None)
    if not sa or not sb:
        pending.pop(key, None)
        _psave("servant_duel_pending")
        return False, "یکی از خدمتکارها دیگر در اختیار صاحبش نیست؛ دوئل لغو شد."

    pending.pop(key, None)
    _psave("servant_duel_pending")
    pa, pb = servant_duel_score(sa), servant_duel_score(sb)

    if pa == pb:
        result = "🤝 نتیجه: تساوی"
    elif pa > pb:
        result = f"🏆 برنده: {sa.get('name','—')}"
    else:
        result = f"🏆 برنده: {sb.get('name','—')}"

    return True, (
        "⚔️ <b>نتیجه دوئل خدمتکاران</b>\n\n"
        f"🧑 {sa.get('name','—')}: {pa:,}\n"
        f"🧑 {sb.get('name','—')}: {pb:,}\n\n"
        f"{result}\n"
        "📌 محاسبه بر اساس قدرت، سرعت، دفاع، تذهیب، وفاداری و عمر خدمتکار انجام شد."
    )
