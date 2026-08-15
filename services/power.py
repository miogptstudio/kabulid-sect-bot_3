"""محاسبه قدرت رزمی برای دوئل و نمایش پروفایل"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User
from database.models_v3 import UserInventory, ShopItem
from services.cultivation import get_or_create_cultivation

REALM_POWER = {
    "بیداری": 5, "پایه": 10, "متوسط": 25, "بالا": 45, "پیشرفته": 70,
    "هسته": 85, "روح": 95, "نیمهخدا": 110, "خدا": 130, "آسمان": 150,
    "ایتری": 180, "جاودان": 210, "ابدی": 240, "خلقت": 280, "پوچی": 320,
    "فراپوچی": 360, "مطلق": 400,
}

ROOT_BONUS = {
    "بدون ریشه": 0,
    "ریشه پنجعنصر": 5,
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
    "ریشه ایتری": 30,
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
    rank_bonus = {"عضو دستههای پایینتر": 0, "عضو بیرونی": 5, "عضو داخلی": 12, "ارشد": 25, "ارجمند": 40}.get(user.rank, 0)

    cult = await get_or_create_cultivation(session, user.id)
    realm_p = REALM_POWER.get(cult.realm, 10) + (cult.stage or 1) * 8 + min(int(cult.energy or 0) // 10000, 50)
    root_p = ROOT_BONUS.get(cult.spiritual_root or "بدون ریشه", 0)

    # فقط سلاح مجهز + زره در کیف
    weapon_p = 0
    pen_p = 0
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
        if item.item_type in ("armor", "shield") or effect.get("armor"):
            weapon_p += dp + int(effect.get("armor") or 0) // 2
        elif eq_id and inv.item_id == eq_id:
            weapon_p += dp
            pen_p += int(effect.get("penetration") or effect.get("armor_pen") or 0)
        elif not eq_id and dp and item.item_type in ("weapon", "weapon_unique"):
            # اگر چیزی مجهز نیست، قویترین سلاح را حساب کن
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
        from services.body_spirit_realms import body_realm_power_bonus, spirit_realm_power_bonus
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
        from services.body_spirit_realms import body_realm_power_bonus, spirit_realm_power_bonus
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
    admin_p = 0
    try:
        from services.knowledge import get_admin_power_bonus
        admin_p = get_admin_power_bonus(int(getattr(user, "telegram_id", 0) or 0))
    except Exception:
        admin_p = 0
    total = base + rank_bonus + realm_p + root_p + weapon_p + spirit_p + job_p + body_p + char_p + race_p + admin_p
    try:
        from services.advanced_systems import bloodline_bonus
        total = int(total * float(bloodline_bonus(int(getattr(user, "telegram_id", 0) or 0))))
    except Exception:
        pass
    if getattr(user, "is_spirit_raiser", False):
        total += 15

    # Derived combat stats: speed/defense/lifespan now affect effective combat power.
    try:
        from services.knowledge import get_speed, get_defense, dodge_rate, block_rate
        speed = int(get_speed(int(user.telegram_id)))
        defense = int(get_defense(int(user.telegram_id)))
        dodge = float(dodge_rate(int(user.telegram_id)))
        block = float(block_rate(int(user.telegram_id)))
    except Exception:
        speed, defense, dodge, block = 10, 10, 0.0, 0.0
    lifespan = max(0, int(getattr(user, "lifespan", 100) or 100))
    # Speed, defense and remaining lifespan contribute to combat survivability.
    total += speed * 2 + defense * 2 + lifespan // 2

    try:
        from services.cult_paths import mults
        _m = mults(int(getattr(user, "telegram_id", 0) or 0))
        total = int(total * float(_m.get("power", 1.0)))
    except Exception:
        pass
    try:
        from services.world_blade import penetration_bonus
        pen_p = int(pen_p) + int(penetration_bonus(int(getattr(user, "telegram_id", 0) or 0)))
    except Exception:
        pass
    return {
        "total": total,
        "base": base,
        "rank": rank_bonus,
        "realm": realm_p,
        "root": root_p,
        "weapon": weapon_p,
        "admin": admin_p,
        "spirit": spirit_p,
        "root_name": cult.spiritual_root,
        "realm_name": cult.realm,
        "speed": speed,
        "defense": defense,
        "lifespan": lifespan,
        "dodge": dodge,
        "block": block,
    }


def win_chance(power_a: int, power_b: int) -> float:
    """بدون شانس — فقط قدرت. اگر a قویتر است ۱ وگرنه ۰ (تساوی ۰.۵ فقط برای نمایش)."""
    a, b = int(power_a or 0), int(power_b or 0)
    if a > b:
        return 1.0
    if a < b:
        return 0.0
    return 0.5


def win_chance_legacy_unused(power_a: int, power_b: int) -> float:
    try:
        from bot.config import DUEL_MIN_WIN_CHANCE, DUEL_MAX_WIN_CHANCE
        lo, hi = DUEL_MIN_WIN_CHANCE, DUEL_MAX_WIN_CHANCE
    except Exception:
        lo, hi = 0.02, 0.60
    if power_a + power_b <= 0:
        return 0.5
    raw = power_a / (power_a + power_b)
    # مکعب برای سختتر کردن
    raw = raw ** 3
    return max(lo, min(hi, raw))


def combat_rates_text(tg_id: int) -> str:
    try:
        from services.knowledge import get_power, get_speed, get_defense, dodge_rate, block_rate
        from services.knights import protect_percent
        return (
            f"قدرت:{get_power(tg_id)} سرعت:{get_speed(tg_id)} دفاع:{get_defense(tg_id)} "
            f"جاخالی:{dodge_rate(tg_id):.0f}% بلاک:{block_rate(tg_id):.0f}% شوالیه:{protect_percent(tg_id)}%"
        )
    except Exception:
        return ""
