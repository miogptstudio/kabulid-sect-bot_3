"""محاسبه قدرت رزمی برای دوئل و نمایش پروفایل"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User
from database.models_v3 import UserInventory, ShopItem
from services.cultivation import get_or_create_cultivation

REALM_POWER = {
    "بیداری": 5, "پایه": 10, "متوسط": 25, "بالا": 45, "پیشرفته": 70,
    "هسته": 85, "روح": 95, "نیمه‌خدا": 110, "خدا": 130, "آسمان": 150,
    "ای‌تری": 180, "جاودان": 210, "ابدی": 240, "خلقت": 280, "پوچی": 320,
    "فراپوچی": 360, "مطلق": 400,
}

ROOT_BONUS = {
    "بدون ریشه": 0,
    "ریشه پنج‌عنصر": 5,
    "ریشه آتش": 8,
    "ریشه آب": 8,
    "ریشه چوب": 7,
    "ریشه فلز": 9,
    "ریشه خاک": 7,
    "ریشه نور": 14,
    "ریشه تاریکی": 14,
    "ریشه روحی": 16,
    "ریشه روح": 18,
    "ریشه بهشتی": 22,
    "ریشه آسمانی": 28,
    "ریشه الهی": 40,
    "ریشه پوچی": 35,
    "ریشه ای‌تری": 30,
    "ریشه دوگانه": 20,
}


async def calc_power(session: AsyncSession, user: User) -> dict:
    base = 20 + (user.level or 1) * 3
    spirit_p = 0
    try:
        from services.martial_spirit import power_bonus
        spirit_p = power_bonus(user.telegram_id)
    except Exception:
        spirit_p = 0
    rank_bonus = {"عضو دسته‌های پایین‌تر": 0, "عضو بیرونی": 5, "عضو داخلی": 12, "ارشد": 25, "ارجمند": 40}.get(user.rank, 0)

    cult = await get_or_create_cultivation(session, user.id)
    realm_p = REALM_POWER.get(cult.realm, 10) + (cult.stage or 1) * 8 + min(int(cult.energy or 0) // 10000, 50)
    root_p = ROOT_BONUS.get(cult.spiritual_root or "بدون ریشه", 0)

    # فقط سلاح مجهز + زره در کیف
    weapon_p = 0
    result = await session.execute(
        select(UserInventory, ShopItem)
        .join(ShopItem, UserInventory.item_id == ShopItem.id)
        .where(UserInventory.user_id == user.id)
    )
    eq_id = getattr(user, "equipped_weapon_id", None)
    for inv, item in result.all():
        effect = item.effect or {}
        if not isinstance(effect, dict):
            continue
        dp = int(effect.get("duel_power") or 0)
        if item.item_type in ("armor",) or effect.get("armor"):
            weapon_p += dp + int(effect.get("armor") or 0) // 2
        elif eq_id and inv.item_id == eq_id:
            weapon_p += dp
        elif not eq_id and dp and item.item_type in ("weapon", "weapon_unique"):
            # اگر چیزی مجهز نیست، قوی‌ترین سلاح را حساب کن
            weapon_p = max(weapon_p, dp)

    job_p = 0
    body_p = 0
    char_p = 0
    race_p = 0
    try:
        from services.cultivation import RACE_CULT
        rn = getattr(user, 'race', None) or 'انسان'
        race_p = int(50 * (float(RACE_CULT.get(rn, {}).get('bonus', 1.0)) - 1.0))
    except Exception:
        race_p = 0
    try:
        from services.characters import total_power_bonus
        char_p = int(total_power_bonus(getattr(user, 'telegram_id', 0) or 0))
    except Exception:
        char_p = 0
    race_p = 0
    try:
        from services.cultivation import RACE_CULT
        rn = getattr(user, 'race', None) or 'انسان'
        race_p = int(50 * (float(RACE_CULT.get(rn, {}).get('bonus', 1.0)) - 1.0))
    except Exception:
        race_p = 0
    try:
        from services.body_cult import body_power_bonus
        body_p = body_power_bonus(user.telegram_id)
    except Exception:
        body_p = 0
    char_p = 0
    race_p = 0
    try:
        from services.cultivation import RACE_CULT
        rn = getattr(user, 'race', None) or 'انسان'
        race_p = int(50 * (float(RACE_CULT.get(rn, {}).get('bonus', 1.0)) - 1.0))
    except Exception:
        race_p = 0
    try:
        from services.characters import total_power_bonus
        char_p = int(total_power_bonus(getattr(user, 'telegram_id', 0) or 0))
    except Exception:
        char_p = 0
    race_p = 0
    try:
        from services.cultivation import RACE_CULT
        rn = getattr(user, 'race', None) or 'انسان'
        race_p = int(50 * (float(RACE_CULT.get(rn, {}).get('bonus', 1.0)) - 1.0))
    except Exception:
        race_p = 0
    try:
        from services.jobs import get_job, JOBS
        j = get_job(user.telegram_id)
        if j and JOBS.get(j, {}).get('bonus') == 'duel':
            job_p = int((base + realm_p) * (JOBS[j]['mult'] - 1))
    except Exception:
        job_p = 0
    body_p = 0
    char_p = 0
    race_p = 0
    try:
        from services.cultivation import RACE_CULT
        rn = getattr(user, 'race', None) or 'انسان'
        race_p = int(50 * (float(RACE_CULT.get(rn, {}).get('bonus', 1.0)) - 1.0))
    except Exception:
        race_p = 0
    try:
        from services.characters import total_power_bonus
        char_p = int(total_power_bonus(getattr(user, 'telegram_id', 0) or 0))
    except Exception:
        char_p = 0
    race_p = 0
    try:
        from services.cultivation import RACE_CULT
        rn = getattr(user, 'race', None) or 'انسان'
        race_p = int(50 * (float(RACE_CULT.get(rn, {}).get('bonus', 1.0)) - 1.0))
    except Exception:
        race_p = 0
    try:
        from services.body_cult import body_power_bonus
        body_p = body_power_bonus(user.telegram_id)
    except Exception:
        body_p = 0
    char_p = 0
    race_p = 0
    try:
        from services.cultivation import RACE_CULT
        rn = getattr(user, 'race', None) or 'انسان'
        race_p = int(50 * (float(RACE_CULT.get(rn, {}).get('bonus', 1.0)) - 1.0))
    except Exception:
        race_p = 0
    try:
        from services.characters import total_power_bonus
        char_p = int(total_power_bonus(getattr(user, 'telegram_id', 0) or 0))
    except Exception:
        char_p = 0
    race_p = 0
    try:
        from services.cultivation import RACE_CULT
        rn = getattr(user, 'race', None) or 'انسان'
        race_p = int(50 * (float(RACE_CULT.get(rn, {}).get('bonus', 1.0)) - 1.0))
    except Exception:
        race_p = 0
    total = base + rank_bonus + realm_p + root_p + weapon_p + spirit_p + job_p + body_p + char_p + race_p
    if getattr(user, "is_spirit_raiser", False):
        total += 15

    return {
        "total": total,
        "base": base,
        "rank": rank_bonus,
        "realm": realm_p,
        "root": root_p,
        "weapon": weapon_p,
        "spirit": spirit_p,
        "root_name": cult.spiritual_root,
        "realm_name": cult.realm,
    }


def win_chance(power_a: int, power_b: int) -> float:
    """تقریباً بر اساس قدرت: اختلاف زیاد = برد قطعی قوی‌تر"""
    if power_a + power_b <= 0:
        return 0.5
    # نسبت قدرت
    ratio = power_a / max(power_b, 1)
    if ratio >= 2.0:
        return 0.97
    if ratio <= 0.5:
        return 0.03
    # بین ۰.۵ تا ۲: نرمال‌سازی
    chance = power_a / (power_a + power_b)
    # کمی واریانس خیلی کم
    return max(0.05, min(0.95, chance))


def win_chance_legacy_unused(power_a: int, power_b: int) -> float:
    try:
        from bot.config import DUEL_MIN_WIN_CHANCE, DUEL_MAX_WIN_CHANCE
        lo, hi = DUEL_MIN_WIN_CHANCE, DUEL_MAX_WIN_CHANCE
    except Exception:
        lo, hi = 0.02, 0.60
    if power_a + power_b <= 0:
        return 0.5
    raw = power_a / (power_a + power_b)
    # مکعب برای سخت‌تر کردن
    raw = raw ** 3
    return max(lo, min(hi, raw))
