"""خدمتکاران نژادی — وفاداری، شکار اصیل، دگرگونی"""
from __future__ import annotations
import random
from datetime import datetime, timedelta
from services.persist import get_dict, save as _psave

# نژادها: buyable از بازار | purebred فقط با جنگ/شکار
RACES = {
    "انسان": {"purebred": False, "loyalty0": 70, "cult_rate": 1.0, "transform": None},
    "نیمه‌انسان": {"purebred": False, "loyalty0": 65, "cult_rate": 1.1, "transform": "انسان"},
    "گربه‌ای نیمه‌انسان": {"purebred": False, "loyalty0": 75, "cult_rate": 1.15, "transform": "نیمه‌انسان"},
    "گرگ‌نمای": {"purebred": True, "loyalty0": 40, "cult_rate": 1.2, "transform": "نیمه‌انسان"},
    "روباه‌نمای": {"purebred": False, "loyalty0": 55, "cult_rate": 1.25, "transform": "نیمه‌انسان"},
    "اژدها‌تبار": {"purebred": True, "loyalty0": 30, "cult_rate": 1.5, "transform": "نیمه‌انسان"},
    "ققنوس‌تبار": {"purebred": True, "loyalty0": 35, "cult_rate": 1.45, "transform": "نیمه‌انسان"},
    "جن جنگلی": {"purebred": False, "loyalty0": 60, "cult_rate": 1.2, "transform": "نیمه‌انسان"},
    "دیو‌تبار": {"purebred": True, "loyalty0": 25, "cult_rate": 1.4, "transform": "نیمه‌انسان"},
    "فرشته‌تبار": {"purebred": True, "loyalty0": 45, "cult_rate": 1.35, "transform": "نیمه‌انسان"},
    "اهریمنی": {"purebred": True, "loyalty0": 20, "cult_rate": 1.5, "transform": "دیو‌تبار"},
    "سیمرغ‌زاده": {"purebred": True, "loyalty0": 40, "cult_rate": 1.55, "transform": "نیمه‌انسان"},
    "روح‌پیما": {"purebred": False, "loyalty0": 50, "cult_rate": 1.3, "transform": "نیمه‌انسان"},
    "خون‌آشام کهن": {"purebred": True, "loyalty0": 28, "cult_rate": 1.4, "transform": "نیمه‌انسان"},
    "مه‌پیما": {"purebred": False, "loyalty0": 58, "cult_rate": 1.2, "transform": "نیمه‌انسان"},
    # تبارهای الهی — بسیار کمیاب و مناسب خدمتکارهای رده‌بالا
    "تبار الهی": {"purebred": False, "loyalty0": 60, "cult_rate": 2.0, "transform": None},
    "الهه‌تبار": {"purebred": False, "loyalty0": 70, "cult_rate": 2.2, "transform": "تبار الهی"},
    "خدای‌تبار": {"purebred": False, "loyalty0": 55, "cult_rate": 2.4, "transform": "تبار الهی"},
    "آسمانی‌تبار": {"purebred": False, "loyalty0": 65, "cult_rate": 2.1, "transform": "تبار الهی"},
}

CAT_GIRL_NAMES = [
    "میوکا", "نکو", "ساکورا‌دم", "یوره‌نکو", "لونا‌گوش",
    "پیشی‌مهتاب", "گربه‌زرین", "دم‌ابریشمی", "چشم‌زمردی", "پنجه‌سفید",
]

MARKET = [
    # انسان / نیمه‌انسان قابل خرید
    {"id": 1, "name": "آلیس", "gender": "زن", "race": "انسان", "price": 500, "desc": "خدمتکار وفادار"},
    {"id": 2, "name": "لیان", "gender": "زن", "race": "نیمه‌انسان", "price": 900, "desc": "خدمتکار جنگی"},
    {"id": 3, "name": "مینگ", "gender": "مرد", "race": "انسان", "price": 600, "desc": "نگهبان خانه"},
    {"id": 4, "name": "سارا", "gender": "زن", "race": "انسان", "price": 1200, "desc": "خدمتکار نجیب"},
    {"id": 5, "name": "کای", "gender": "مرد", "race": "نیمه‌انسان", "price": 1000, "desc": "نگهبان دروازه"},
    {"id": 6, "name": "یوکی", "gender": "زن", "race": "روباه‌نمای", "price": 1800, "desc": "دم نهگانه"},
    {"id": 7, "name": "رستم‌یار", "gender": "مرد", "race": "انسان", "price": 2000, "desc": "برده جنگی ایرانی"},
    {"id": 8, "name": "شیرین", "gender": "زن", "race": "انسان", "price": 1800, "desc": "خدمتکار دربار"},
    {"id": 9, "name": "بهرام", "gender": "مرد", "race": "نیمه‌انسان", "price": 2200, "desc": "شکارچی"},
    {"id": 10, "name": "نرگس", "gender": "زن", "race": "جن جنگلی", "price": 2100, "desc": "باغبان روح"},
    {"id": 11, "name": "آرش", "gender": "مرد", "race": "انسان", "price": 2500, "desc": "کماندار"},
    {"id": 12, "name": "لاله", "gender": "زن", "race": "انسان", "price": 1400, "desc": "آشپزخانه"},
    {"id": 13, "name": "کاوه", "gender": "مرد", "race": "نیمه‌انسان", "price": 3000, "desc": "آهنگر"},
    {"id": 14, "name": "مهتاب", "gender": "زن", "race": "روح‌پیما", "price": 3200, "desc": "روحانی"},
    {"id": 15, "name": "سهراب", "gender": "مرد", "race": "انسان", "price": 3500, "desc": "پهلوان"},
    {"id": 16, "name": "پریسا", "gender": "زن", "race": "مه‌پیما", "price": 3400, "desc": "جادویی"},
    {"id": 17, "name": "توران", "gender": "مرد", "race": "نیمه‌انسان", "price": 4000, "desc": "نگهبان فرقه"},
    {"id": 18, "name": "آناهیتا", "gender": "زن", "race": "فرشته‌تبار", "price": 8000, "desc": "نورانی (کمیاب بازار)"},
    {"id": 19, "name": "دیو‌بنده", "gender": "مرد", "race": "دیو‌تبار", "price": 7500, "desc": "تاریک"},
    {"id": 20, "name": "فرشته‌یار", "gender": "زن", "race": "فرشته‌تبار", "price": 8500, "desc": "خدمتکار نور"},
    # گربه‌ای نیمه‌انسان زن
    {"id": 21, "name": "میوکا", "gender": "زن", "race": "گربه‌ای نیمه‌انسان", "price": 4500, "desc": "گوش گربه‌ای · وفادار"},
    {"id": 22, "name": "نکو‌ساکورا", "gender": "زن", "race": "گربه‌ای نیمه‌انسان", "price": 4800, "desc": "دم ابریشمی"},
    {"id": 23, "name": "لونا‌گوش", "gender": "زن", "race": "گربه‌ای نیمه‌انسان", "price": 5200, "desc": "چشم مهتاب"},
    {"id": 24, "name": "پیشی‌زرین", "gender": "زن", "race": "گربه‌ای نیمه‌انسان", "price": 5600, "desc": "پنجه‌طلایی"},
    {"id": 25, "name": "یوره‌نکو", "gender": "زن", "race": "گربه‌ای نیمه‌انسان", "price": 6000, "desc": "نیمه‌روح گربه"},
    # خدمتکارهای تبار الهی — خریدنی و بسیار کمیاب
    {"id": 26, "name": "آریانا", "gender": "زن", "race": "الهه‌تبار", "price": 1000000000, "desc": "خدمتکار الهی؛ سرعت بالای تذهیب"},
    {"id": 27, "name": "یوناس", "gender": "مرد", "race": "خدای‌تبار", "price": 1500000000, "desc": "خدمتکار الهی؛ قدرت رزمی عظیم"},
    {"id": 28, "name": "سولارا", "gender": "زن", "race": "آسمانی‌تبار", "price": 2000000000, "desc": "خدمتکار آسمانی؛ محافظ قلمرو"},
    {"id": 29, "name": "ایلیوس", "gender": "مرد", "race": "تبار الهی", "price": 2500000000, "desc": "خون الهی خالص و کمیاب"},
    {"id": 30, "name": "نِریا", "gender": "زن", "race": "تبار الهی", "price": 3000000000, "desc": "خدمتکار الهی؛ وفاداری بالا"},
    {"id": 31, "name": "کایروس", "gender": "مرد", "race": "خدای‌تبار", "price": 5000000000, "desc": "خدمتکار جنگی خدایان"},
    {"id": 32, "name": "آسترا", "gender": "زن", "race": "آسمانی‌تبار", "price": 7500000000, "desc": "خدمتکار آسمانی؛ تذهیب بسیار سریع"},
    {"id": 33, "name": "اورین", "gender": "مرد", "race": "تبار الهی", "price": 10000000000, "desc": "خدمتکار رده‌بالای الهی"},
]

# اصیل‌ها فقط با جنگ — قالب برای اسپاون شکار
PUREBRED_TEMPLATES = [
    {"name": "گرگ‌سالار سیاه", "gender": "مرد", "race": "گرگ‌نمای", "power": 80},
    {"name": "گرگنمای ماه", "gender": "زن", "race": "گرگ‌نمای", "power": 90},
    {"name": "اژدها‌بچه سرخ", "gender": "مرد", "race": "اژدها‌تبار", "power": 150},
    {"name": "اژده‌بانو", "gender": "زن", "race": "اژدها‌تبار", "power": 160},
    {"name": "جوجه ققنوس", "gender": "زن", "race": "ققنوس‌تبار", "power": 140},
    {"name": "شعله ققنوس", "gender": "مرد", "race": "ققنوس‌تبار", "power": 155},
    {"name": "دیو مرز", "gender": "مرد", "race": "دیو‌تبار", "power": 120},
    {"name": "اهریمن‌زاده", "gender": "مرد", "race": "اهریمنی", "power": 180},
    {"name": "سیمرغ‌یار", "gender": "زن", "race": "سیمرغ‌زاده", "power": 170},
    {"name": "خون‌شاه کهن", "gender": "مرد", "race": "خون‌آشام کهن", "power": 130},
    {"name": "فرشته سقوط‌کرده", "gender": "زن", "race": "فرشته‌تبار", "power": 145},
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
    """ازدواج خدمتکارها را جدا از حافظهٔ موقت برنامه نگه می‌دارد."""
    return get_dict("servant_marriages")


def _servant_by_selector(tg: int, selector: int):
    """شمارهٔ لیست /myservants یا شمارهٔ بازار را قبول می‌کند."""
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
        return False, f"قبلاً با «{servant.get('name')}» ازدواج کرده‌ای.", servant

    married.append(uid)
    data[key] = married
    _psave("servant_marriages")

    return True, (
        f"💍 با خدمتکار «{servant.get('name')}» ازدواج کردی!\n"
        f"نژاد: {servant.get('race', '—')} | وفاداری: {servant.get('loyalty', 0)}%\n"
        f"از این به بعد این ازدواج بعد از ری‌استارت هم باقی می‌مونه.\n"
        f"/myservants — مشاهدهٔ خانواده"
    ), servant


def market_list() -> str:
    lines = ["🛒 <b>بازار خدمتکار</b>", "نژادهای خریدنی (اصیل‌ها با /huntservant)", ""]
    for s in MARKET:
        race = s.get("race", "انسان")
        pure = "🔒اصیل" if RACES.get(race, {}).get("purebred") else ""
        lines.append(
            f"#{s['id']} {s['name']} | {s['gender']} | {race} {pure}" + chr(10)
            + f"  {s['price']:,} سکه — {s['desc']}"
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
        "source": source,
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
            + f"   ❤️وفاداری {s.get('loyalty',0)}% | 🧘تذهیب {s.get('cult',1)} | ⚔{s.get('power',0)}"
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
    s["loyalty"] = min(100, int(s.get("loyalty") or 50) + 10)
    # گربه‌ای → نیمه‌انسان با حفظ لقب
    if old == "گربه‌ای نیمه‌انسان":
        s["name"] = s["name"] + " (انسانی‌شده)"
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
