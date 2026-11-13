"""محاسبه قدرت رزمی برای دوئل و نمایش پروفایل — نسخه پاک‌سازی و تقویت‌شده v61"""
from __future__ import annotations

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

RANK_BONUS = {
    "عضو دستههای پایینتر": 0,
    "عضو بیرونی": 5,
    "عضو داخلی": 12,
    "ارشد": 25,
    "ارجمند": 40,
}


async def calc_power(session: AsyncSession, user: User) -> dict:
    """محاسبه کامل و تمیز قدرت رزمی کاربر.
    همه بونوس‌ها یک‌بار و بدون بازنویسی محاسبه می‌شوند.
    """
    tg_id = int(getattr(user, "telegram_id", 0) or 0)
    level = int(getattr(user, "level", 1) or 1)

    # پایه
    base = 20 + level * 3

    # روح رزمی
    spirit_p = 0
    try:
        from services.martial_spirit import power_bonus
        spirit_p = int(power_bonus(tg_id) or 0)
    except Exception:
        pass

    # رتبه فرقه
    rank_bonus = RANK_BONUS.get(getattr(user, "rank", None) or "", 0)

    # قلمرو و ریشه
    cult = await get_or_create_cultivation(session, user.id)
    realm_name = cult.realm or "بیداری"
    stage = int(cult.stage or 1)
    energy = int(cult.energy or 0)
    realm_p = REALM_POWER.get(realm_name, 10) + stage * 8 + min(energy // 10000, 50)
    root_name = cult.spiritual_root or "بدون ریشه"
    root_p = ROOT_BONUS.get(root_name, 0)

    # سلاح و زره از موجودی
    weapon_p = 0
    pen_p = 0
    try:
        result = await session.execute(
            select(UserInventory, ShopItem)
            .join(ShopItem, UserInventory.item_id == ShopItem.id)
            .where(UserInventory.user_id == user.id)
        )
        eq_id = getattr(user, "equipped_weapon_id", None)
        best_unequipped = 0
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
                best_unequipped = max(best_unequipped, dp)
        if not eq_id:
            weapon_p += best_unequipped
    except Exception:
        pass

    # شغل
    job_p = 0
    try:
        from services.jobs import get_job, JOBS
        j = get_job(tg_id)
        if j and JOBS.get(j, {}).get("bonus") == "duel":
            job_p = int((base + realm_p) * (float(JOBS[j].get("mult", 1.0)) - 1.0))
    except Exception:
        pass

    # بدن و روح بدن
    body_p = 0
    try:
        from services.body_cult import body_power_bonus
        from services.body_spirit_realms import body_realm_power_bonus, spirit_realm_power_bonus
        body_p = int(body_power_bonus(tg_id) or 0)
        body_p += int(body_realm_power_bonus(tg_id) or 0)
        body_p += int(spirit_realm_power_bonus(tg_id) or 0)
    except Exception:
        try:
            from services.body_cult import body_power_bonus
            body_p = int(body_power_bonus(tg_id) or 0)
        except Exception:
            pass

    # شخصیت‌ها
    char_p = 0
    try:
        from services.characters import total_power_bonus
        char_p = int(total_power_bonus(tg_id) or 0)
    except Exception:
        pass

    # نژاد
    race_p = 0
    try:
        from services.cultivation import RACE_CULT
        rn = getattr(user, "race", None) or "انسان"
        bonus = float(RACE_CULT.get(rn, {}).get("bonus", 1.0))
        race_p = int(50 * (bonus - 1.0))
    except Exception:
        pass

    # بونوس ادمین / دانش
    admin_p = 0
    try:
        from services.knowledge import get_admin_power_bonus
        admin_p = int(get_admin_power_bonus(tg_id) or 0)
    except Exception:
        pass

    # جمع اولیه
    total = (
        base + rank_bonus + realm_p + root_p + weapon_p
        + spirit_p + job_p + body_p + char_p + race_p + admin_p
    )

    # آرتیفکت‌ها
    try:
        from services.artifacts import power_bonus as art_bonus
        art = int(art_bonus(tg_id) or 0)
        weapon_p += art
        total += art
    except Exception:
        pass

    # ایونت آرش کمانگیر: +۱۵٪
    try:
        from services.persist import get_dict
        owners = (get_dict("arash_event") or {}).get("owners") or {}
        if str(tg_id) in owners:
            total = int(total * 1.15)
            weapon_p = int(weapon_p + max(10, total * 0.02))
    except Exception:
        pass

    # تبار
    try:
        from services.advanced_systems import bloodline_bonus
        total = int(total * float(bloodline_bonus(tg_id) or 1.0))
    except Exception:
        pass

    if getattr(user, "is_spirit_raiser", False):
        total += 15

    # سرعت / دفاع / عمر
    speed = 10
    defense = 10
    dodge = 0.0
    block = 0.0
    try:
        from services.knowledge import get_speed, get_defense, dodge_rate, block_rate
        speed = int(get_speed(tg_id) or 10)
        defense = int(get_defense(tg_id) or 10)
        dodge = float(dodge_rate(tg_id) or 0.0)
        block = float(block_rate(tg_id) or 0.0)
    except Exception:
        pass

    lifespan = max(0, int(getattr(user, "lifespan", 100) or 100))
    total += speed * 2 + defense * 2 + lifespan // 2

    # مسیر تذهیب
    try:
        from services.cult_paths import mults
        m = mults(tg_id)
        total = int(total * float(m.get("power", 1.0)))
    except Exception:
        pass

    # تیغ جهان
    try:
        from services.world_blade import penetration_bonus
        pen_p = int(pen_p) + int(penetration_bonus(tg_id) or 0)
    except Exception:
        pass

    total = max(1, int(total))

    return {
        "total": total,
        "base": base,
        "rank": rank_bonus,
        "realm": realm_p,
        "root": root_p,
        "weapon": weapon_p,
        "admin": admin_p,
        "spirit": spirit_p,
        "job": job_p,
        "body": body_p,
        "char": char_p,
        "race": race_p,
        "root_name": root_name,
        "realm_name": realm_name,
        "speed": speed,
        "defense": defense,
        "lifespan": lifespan,
        "dodge": dodge,
        "block": block,
        "penetration": pen_p,
    }


def win_chance(power_a: int, power_b: int) -> float:
    """شانس برد بر اساس قدرت با کمی واریانس برای هیجان بیشتر.
    قوی‌تر هنوز برتری واضح دارد اما شانس کامل ۱/۰ نیست مگر اختلاف خیلی زیاد باشد.
    """
    a = max(0, int(power_a or 0))
    b = max(0, int(power_b or 0))
    if a + b <= 0:
        return 0.5
    ratio = a / (a + b)
    # منحنی نرم‌تر از مکعب برای حفظ هیجان در اختلاف‌های متوسط
    curved = ratio ** 2.2
    return max(0.08, min(0.92, curved))


def win_chance_legacy_unused(power_a: int, power_b: int) -> float:
    try:
        from bot.config import DUEL_MIN_WIN_CHANCE, DUEL_MAX_WIN_CHANCE
        lo, hi = DUEL_MIN_WIN_CHANCE, DUEL_MAX_WIN_CHANCE
    except Exception:
        lo, hi = 0.02, 0.60
    if power_a + power_b <= 0:
        return 0.5
    raw = power_a / (power_a + power_b)
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
