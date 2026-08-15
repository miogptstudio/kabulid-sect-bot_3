"""خون، آسیب، سم، دفاع، نفوذ، جاخالی"""
from __future__ import annotations
import random
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User

POISON_HOURS = 3


def max_blood_for_user(user: User, power_total: int | None = None, realm: str | None = None, stage: int | None = None) -> int:
    """جان با سطح/قلمرو رشد میکند — سطح پایین به بالا آسیب جدی نمیزند"""
    base = 100
    lvl = int(getattr(user, "level", 1) or 1)
    # اگر realm/stage داده شد از آن استفاده کن
    ri = 0
    st = int(stage or 1)
    if realm:
        try:
            from database.models_v2 import CULTIVATION_REALMS
            if realm in CULTIVATION_REALMS:
                ri = CULTIVATION_REALMS.index(realm)
        except Exception:
            ri = 0
    # فرمول: پایه + سطح + قلمرو^2 + مرحله
    hp = base + lvl * 15 + (ri ** 2) * 40 + ri * 80 + st * 25
    if power_total:
        hp += int(power_total) // 8
    return max(100, int(hp))


async def ensure_blood(user: User, session: AsyncSession | None = None) -> int:
    """تنظیم سقف خون بر اساس قدرت تقریبی"""
    mx = max_blood_for_user(user)
    # try better estimate from cultivation if available on user object later
    if getattr(user, "blood", None) is None:
        user.blood = mx
    else:
        # اگر سقف جدید بزرگتر است، خون را به نسبت بالا نبر مگر خالی باشد
        if int(user.blood or 0) > mx:
            user.blood = mx
        if int(user.blood or 0) <= 0 and not getattr(user, "is_dead", False):
            user.blood = max(1, mx // 10)
    return int(user.blood or 0)


async def max_blood_async(session: AsyncSession, user: User) -> int:
    try:
        from services.cultivation import get_or_create_cultivation
        from services.power import calc_power
        cult = await get_or_create_cultivation(session, user.id)
        p = await calc_power(session, user)
        return max_blood_for_user(user, power_total=p.get("total"), realm=cult.realm, stage=cult.stage)
    except Exception:
        return max_blood_for_user(user)


def has_cyrus(user: User) -> bool:
    return bool(getattr(user, "has_cyrus_sword", False))


async def get_defense_stats(session: AsyncSession, user: User) -> dict:
    """دفاع، نفوذ، سرعت از قدرت + مسیر تذهیب + دانش"""
    from services.power import calc_power
    p = await calc_power(session, user)
    total = int(p.get("total") or 0)
    tg = int(getattr(user, "telegram_id", 0) or 0)
    # مسیر
    try:
        from services.cult_paths import mults
        m = mults(tg)
    except Exception:
        m = {"power": 1.0, "speed": 1.0, "defense": 1.0}
    # دانش
    try:
        from services.knowledge import get_defense, get_speed, get_power
        kdef, kspd, kpow = get_defense(tg), get_speed(tg), get_power(tg)
    except Exception:
        kdef, kspd, kpow = 10, 10, 10
    defense = int((total * 0.35 + kdef * 3) * float(m.get("defense", 1)))
    speed = int((total * 0.2 + kspd * 4) * float(m.get("speed", 1)))
    atk = int((total * 0.5 + kpow * 3) * float(m.get("power", 1)))
    # نفوذ از سلاح
    pen = int(p.get("penetration") or 0)
    return {
        "attack": max(1, atk),
        "defense": max(0, defense),
        "speed": max(0, speed),
        "penetration": max(0, pen),
        "total": total,
        "dodge_rate": min(65.0, speed * 0.12),  # درصد
    }


async def apply_damage(
    session: AsyncSession,
    attacker: User,
    defender: User,
    raw_damage: int,
    is_cyrus_strike: bool = False,
    is_death_duel: bool = False,
) -> dict:
    """آسیب با دفاع، نفوذ، جاخالی — سطح پایین به بالا کم آسیب میزند"""
    await ensure_blood(defender)
    atk_s = await get_defense_stats(session, attacker)
    def_s = await get_defense_stats(session, defender)

    # سپر پوچی: ایمنی کامل
    try:
        from sqlalchemy import select as _sel
        from database.models_v3 import UserInventory, ShopItem
        res = await session.execute(
            _sel(UserInventory, ShopItem)
            .join(ShopItem, UserInventory.item_id == ShopItem.id)
            .where(UserInventory.user_id == defender.id)
        )
        for inv, item in res.all():
            eff = item.effect if isinstance(item.effect, dict) else {}
            if eff.get("immune") or eff.get("shield") == "void" or eff.get("unique") == "void_shield":
                mx = await max_blood_async(session, defender)
                return {
                    "damage": 0,
                    "blood": int(defender.blood or mx),
                    "max_blood": mx,
                    "killed": False,
                    "dodged": False,
                    "immune": True,
                    "msg": f"🛡 سپر پوچی {defender.full_name}: هیچ حملهای اثر نکرد!",
                }
            # ضد نفوذ
            if eff.get("anti_pen"):
                # applied later via defense boost - store on def_s
                def_s["defense"] = int(def_s.get("defense") or 0) + int(eff.get("anti_pen") or 0)
            if eff.get("shield") and eff.get("armor"):
                def_s["defense"] = int(def_s.get("defense") or 0) + int(eff.get("armor") or 0)
    except Exception:
        pass



    # جاخالی قطعی فقط اگر سرعت مدافع خیلی بالاتر باشد (بدون تاس)
    spd_def = float(def_s.get("speed") or 0)
    spd_atk = float(atk_s.get("speed") or 0)
    if spd_def > spd_atk * 1.8 and def_s["total"] >= atk_s["total"] * 0.9:
        return {
            "damage": 0,
            "blood": int(defender.blood or 0),
            "max_blood": await max_blood_async(session, defender),
            "killed": False,
            "dodged": True,
            "msg": f"💨 {defender.full_name} با سرعت بالاتر جاخالی داد (قطعی).",
        }

    # تفاوت قدرت — سطح پایین تقریباً به سطح بالا آسیب نمیزند
    ratio = (atk_s["total"] + 1) / (def_s["total"] + 1)
    if ratio < 0.25:
        level_mult = 0.02   # تقریباً صفر
    elif ratio < 0.4:
        level_mult = 0.06
    elif ratio < 0.55:
        level_mult = 0.15
    elif ratio < 0.75:
        level_mult = 0.35
    elif ratio < 0.95:
        level_mult = 0.65
    elif ratio > 3.0:
        level_mult = 2.0
    elif ratio > 2.0:
        level_mult = 1.5
    else:
        level_mult = 1.0

    # دفاع مؤثر بعد از نفوذ
    pen = int(atk_s.get("penetration") or 0)
    # سلاح نابودکننده جهان: نفوذ اضافه از kill count
    try:
        from services.world_blade import penetration_bonus
        pen += penetration_bonus(int(getattr(attacker, "telegram_id", 0) or 0))
    except Exception:
        pass
    effective_def = max(0, int(def_s["defense"]) - pen)
    # کاهش آسیب
    mitigation = effective_def / (effective_def + 80)
    dmg = int(raw_damage * level_mult * (1.0 - mitigation * 0.85))
    dmg = max(0, dmg)
    # حداقل آسیب نمادین اگر نسبت قدرت نزدیک باشد
    if dmg < 1 and ratio >= 0.7:
        dmg = 1

    if is_cyrus_strike and has_cyrus(attacker):
        dmg = max(dmg, int((await max_blood_async(session, defender)) * 0.5))

    mx = await max_blood_async(session, defender)
    cur = int(defender.blood or mx)
    if cur > mx:
        cur = mx
    new_hp = max(0, cur - dmg)
    defender.blood = new_hp
    killed = new_hp <= 0
    if killed:
        defender.is_dead = True
        defender.blood = 0
        # ثبت کشتن برای شمشیر جهان
        try:
            from services.world_blade import on_kill
            on_kill(int(getattr(attacker, "telegram_id", 0) or 0))
        except Exception:
            pass
    await session.commit()
    return {
        "damage": dmg,
        "blood": new_hp,
        "max_blood": mx,
        "killed": killed,
        "dodged": False,
        "mitigation": int(mitigation * 100),
        "penetration": pen,
        "msg": f"آسیب {dmg} (دفاع {effective_def} | نفوذ {pen})",
    }


async def apply_poison(session: AsyncSession, target: User) -> str:
    target.poisoned_until = datetime.utcnow() + timedelta(hours=POISON_HOURS)
    mx = await max_blood_async(session, target)
    target.blood = max(10, int(target.blood or mx) - max(10, mx // 15))
    await session.commit()
    return f"☠️ مسموم شدی تا {POISON_HOURS} ساعت. خون: {target.blood}/{mx}"


async def check_poison_death(session: AsyncSession, user: User) -> bool:
    until = getattr(user, "poisoned_until", None)
    if not until:
        return False
    if datetime.utcnow() < until:
        return False
    # سم تمام شد بدون درمان → مرگ
    user.is_dead = True
    user.blood = 0
    user.poisoned_until = None
    await session.commit()
    return True


async def heal_poison(session: AsyncSession, user: User) -> str:
    user.poisoned_until = None
    mx = await max_blood_async(session, user)
    user.blood = min(mx, int(user.blood or 0) + mx // 5)
    await session.commit()
    return f"✅ سم پاک شد. خون: {user.blood}/{mx}"
