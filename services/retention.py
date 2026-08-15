"""رویداد هفتگی، استریک پایدار، جنگ قلمرو زماندار، سینک ضدتورم، بازار پیشنهاد"""
from __future__ import annotations
from datetime import datetime, date, timedelta, timezone
from services.persist import get_dict, save as _psave

# ---------- استریک ورود ----------
def _streaks() -> dict:
    return get_dict("login_streaks")

def claim_streak(tg: int) -> dict:
    """return {ok, count, rewards_msg, already}"""
    m = _streaks()
    sk = str(int(tg))
    today = date.today().isoformat()
    info = m.get(sk) or {"last": None, "count": 0, "total_claims": 0}
    if info.get("last") == today:
        return {"ok": False, "already": True, "count": int(info.get("count") or 0), "rewards": []}
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    if info.get("last") == yesterday:
        info["count"] = int(info.get("count") or 0) + 1
    else:
        info["count"] = 1
    info["last"] = today
    info["total_claims"] = int(info.get("total_claims") or 0) + 1
    m[sk] = info
    _psave("login_streaks")
    c = info["count"]
    rewards = [("coins", 30 + c * 10)]
    if c >= 7 and c % 7 == 0:
        rewards.append(("heavenly", 5))
    if c >= 30 and c % 30 == 0:
        rewards.append(("celestial", 1))
        rewards.append(("rare_box", 1))
    if c >= 100:
        rewards.append(("god", 1))
    return {"ok": True, "already": False, "count": c, "rewards": rewards}


# ---------- رویداد هفتگی ----------
# جمعه = تهاجم شیاطین | یکشنبهشبی تا دوشنبه = حراج آسمانی (یا جمعه نوبتی)
def weekly_event_now() -> dict:
    """نوع رویداد فعال بر اساس روز هفته"""
    # Monday=0 ... Friday=4 Sunday=6
    wd = date.today().weekday()
    now = datetime.utcnow()
    if wd == 4:  # جمعه
        return {
            "active": True,
            "kind": "demon_invasion",
            "title": "⚔️ تهاجم شیاطین",
            "desc": "امروز جمعه است! شیاطین به قلمروها حملهور شدهاند. با /eventjoin بپیوند و /eventscore امتیاز بگیر.",
            "ends": "تا پایان جمعه (UTC)",
        }
    if wd == 6:  # یکشنبه
        return {
            "active": True,
            "kind": "heavenly_auction",
            "title": "🏛️ حراج آسمانی",
            "desc": "حراج هفتگی! آیتمهای کمیاب با پیشنهاد. /eventauction و /eventbid",
            "ends": "تا پایان یکشنبه (UTC)",
        }
    # پیشنمایش
    days_to_fri = (4 - wd) % 7
    days_to_sun = (6 - wd) % 7
    return {
        "active": False,
        "kind": None,
        "title": "رویداد هفتگی",
        "desc": f"جمعه: تهاجم شیاطین (مانده {days_to_fri} روز) | یکشنبه: حراج آسمانی (مانده {days_to_sun} روز)",
        "ends": "—",
    }


def _event_scores() -> dict:
    return get_dict("weekly_event_scores")


def event_join(tg: int) -> str:
    ev = weekly_event_now()
    if not ev["active"]:
        return "الان رویداد فعالی نیست.\n" + ev["desc"]
    m = _event_scores()
    key = date.today().isoformat() + ":" + (ev["kind"] or "x")
    bucket = m.setdefault(key, {})
    sk = str(int(tg))
    if sk in bucket:
        return f"قبلاً پیوستی. امتیاز: {bucket[sk]}\n/eventscore برای ثبت امتیاز | /eventtop"
    bucket[sk] = 0
    _psave("weekly_event_scores")
    return f"✅ به {ev['title']} پیوستی!\nبا دوئل، شکار و تذهیب امتیاز بگیر: /eventscore"


def event_add_score(tg: int, points: int = 1) -> int:
    ev = weekly_event_now()
    if not ev.get("active"):
        return 0
    m = _event_scores()
    key = date.today().isoformat() + ":" + (ev["kind"] or "x")
    bucket = m.setdefault(key, {})
    sk = str(int(tg))
    if sk not in bucket:
        return 0
    bucket[sk] = int(bucket.get(sk) or 0) + int(points)
    _psave("weekly_event_scores")
    return bucket[sk]


def event_top(limit: int = 10) -> str:
    ev = weekly_event_now()
    m = _event_scores()
    key = date.today().isoformat() + ":" + (ev.get("kind") or "x")
    bucket = m.get(key) or {}
    ranked = sorted(bucket.items(), key=lambda x: -int(x[1]))[:limit]
    if not ranked:
        return "هنوز امتیازی ثبت نشده. /eventjoin"
    lines = [f"🏆 {ev.get('title') or 'رویداد'} — برترینها", ""]
    medals = ["🥇", "🥈", "🥉"]
    for i, (uid, sc) in enumerate(ranked):
        med = medals[i] if i < 3 else f"{i+1}."
        lines.append(f"{med} `{uid}` — {sc} امتیاز")
    return "\n".join(lines)


# ---------- جنگ قلمرو زماندار ----------
# هر ۳ روز یک پنجره ۲ ساعته از ساعت ۱۸:۰۰ UTC
WAR_EPOCH = date(2026, 1, 2)  # پنجشنبه مبنا
WAR_DURATION_HOURS = 2
WAR_HOUR_UTC = 18


def territory_war_window() -> dict:
    today = date.today()
    days_since = (today - WAR_EPOCH).days
    cycle_day = days_since % 3  # 0 = روز جنگ
    now = datetime.utcnow()
    if cycle_day == 0 and WAR_HOUR_UTC <= now.hour < WAR_HOUR_UTC + WAR_DURATION_HOURS:
        end = now.replace(hour=WAR_HOUR_UTC + WAR_DURATION_HOURS, minute=0, second=0, microsecond=0)
        left = int((end - now).total_seconds() // 60)
        return {
            "open": True,
            "msg": f"🏰 جنگ قلمرو باز است! حدود {left} دقیقه مانده.\n/sectwar یا /attackterritory",
        }
    # زمان بعدی
    days_to = (3 - cycle_day) % 3
    if days_to == 0 and now.hour >= WAR_HOUR_UTC + WAR_DURATION_HOURS:
        days_to = 3
    next_day = today + timedelta(days=days_to if days_to else 0)
    if cycle_day == 0 and now.hour < WAR_HOUR_UTC:
        next_day = today
        days_to = 0
    return {
        "open": False,
        "msg": (
            f"🏰 جنگ قلمرو بسته است.\n"
            f"پنجره بعدی: هر ۳ روز، ساعت {WAR_HOUR_UTC}:00 UTC بهمدت {WAR_DURATION_HOURS} ساعت.\n"
            f"تقریباً {days_to} روز تا روز جنگ | امروز روز سیکل: {cycle_day}/3"
        ),
    }


def war_is_open() -> bool:
    return bool(territory_war_window().get("open"))


# ---------- ضد تورم / سینک ----------
SECT_TAX_RATE = 0.05          # ۵٪ مالیات فرقه روی درآمد روزانه
REPAIR_BUILDING_COST = 500    # سکه
REVIVE_COST_COINS = 200       # هزینه احیا
MARKET_FEE_RATE = 0.03        # ۳٪ کارمزد بازار


def apply_sect_tax(coins: int) -> tuple[int, int]:
    """returns (kept, tax)"""
    tax = max(0, int(coins * SECT_TAX_RATE))
    return coins - tax, tax


def revive_cost() -> int:
    return REVIVE_COST_COINS


def market_fee(price: int) -> int:
    return max(1, int(price * MARKET_FEE_RATE))


# ---------- بازار پیشنهاد (bid) ----------
def _offers() -> dict:
    return get_dict("market_offers")


def place_offer(listing_id: int, buyer_tg: int, price: int) -> str:
    m = _offers()
    key = str(int(listing_id))
    arr = m.setdefault(key, [])
    arr.append({"buyer": int(buyer_tg), "price": int(price), "at": datetime.utcnow().isoformat()})
    arr.sort(key=lambda x: -x["price"])
    m[key] = arr[:20]
    _psave("market_offers")
    return f"✅ پیشنهاد {price} سکه ثبت شد (کارمزد نهایی {MARKET_FEE_RATE*100:.0f}٪)."


def list_offers(listing_id: int) -> str:
    arr = _offers().get(str(int(listing_id))) or []
    if not arr:
        return "پیشنهادی نیست."
    lines = [f"پیشنهادها برای آگهی #{listing_id}:"]
    for i, o in enumerate(arr[:10], 1):
        lines.append(f"{i}. {o['price']} سکه — خریدار `{o['buyer']}`")
    return "\n".join(lines)
