"""سیستم خون، زخم، سم، شمشیر کوروش"""
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User
from services.death import erase_existence

MAX_BLOOD = 100
POISON_HOURS = 3


def has_cyrus(user: User) -> bool:
    return bool(getattr(user, "has_cyrus_sword", False))


async def ensure_blood(user: User):
    if getattr(user, "blood", None) is None:
        user.blood = MAX_BLOOD


async def apply_damage(
    session: AsyncSession,
    attacker: User,
    defender: User,
    base_damage: int,
    *,
    is_cyrus_strike: bool = False,
    is_death_duel: bool = False,
) -> dict:
    """
    آسیب خون. شمشیر کوروش = نابودی کامل اکانت.
    دارنده‌ی کوروش معمولاً آسیب نمی‌بیند مگر در برابر خود کوروش.
    """
    await ensure_blood(attacker)
    await ensure_blood(defender)
    msgs = []

    # ضربه کوروش: همیشه نابود می‌کند
    if is_cyrus_strike or (has_cyrus(attacker) and is_death_duel):
        msgs.append("⚔️ ضربه شمشیر کوروش! روح نابود شد و اکانت پاک می‌شود.")
        defender.is_dead = True
        defender.blood = 0
        await session.commit()
        wipe = await erase_existence(session, defender)
        msgs.append(wipe)
        return {"killed": True, "wiped": True, "blood": 0, "messages": msgs}

    # دارنده‌ی کوروش آسیب نمی‌بیند (مگر با کوروش دشمن)
    if has_cyrus(defender) and not has_cyrus(attacker):
        msgs.append("🛡 شمشیر کوروش از صاحبش محافظت کرد — بدون آسیب.")
        return {"killed": False, "wiped": False, "blood": defender.blood, "messages": msgs}

    dmg = max(5, min(40, base_damage))  # هیچ‌وقت یک‌ضرب ۱۰۰٪ نه
    defender.blood = max(0, (defender.blood or MAX_BLOOD) - dmg)
    msgs.append(f"🩸 −{dmg} خون (باقی: {defender.blood}%)")

    if defender.blood <= 0:
        defender.is_dead = True
        msgs.append("💀 خون تمام شد — مرگ.")
        await session.commit()
        return {"killed": True, "wiped": False, "blood": 0, "messages": msgs}

    await session.commit()
    return {"killed": False, "wiped": False, "blood": defender.blood, "messages": msgs}


async def apply_poison(session: AsyncSession, target: User) -> str:
    target.poisoned_until = datetime.utcnow() + timedelta(hours=POISON_HOURS)
    target.blood = max(10, (target.blood or MAX_BLOOD) - 15)
    await session.commit()
    return (
        f"☠️ زخمی و مسموم شدی! خون: {target.blood}%\n"
        f"تا ۳ ساعت فرصت داری /heal با قرص سلامتی استفاده کنی وگرنه می‌میری.\n"
        f"مهلت تا: {target.poisoned_until.strftime('%H:%M UTC')}"
    )


async def check_poison_death(session: AsyncSession, user: User) -> str | None:
    until = getattr(user, "poisoned_until", None)
    if not until:
        return None
    if datetime.utcnow() < until:
        return None
    if has_cyrus(user):
        user.poisoned_until = None
        await session.commit()
        return "🛡 کوروش سم را خنثی کرد."
    user.is_dead = True
    user.blood = 0
    user.poisoned_until = None
    await session.commit()
    return "☠️ سم کار خودش را کرد. مردی. /afterdeath"


async def heal_poison(session: AsyncSession, user: User) -> str:
    if not getattr(user, "poisoned_until", None):
        return "مسموم نیستی."
    user.poisoned_until = None
    user.blood = min(MAX_BLOOD, (user.blood or 0) + 30)
    await session.commit()
    return f"✅ سم پاک شد. خون: {user.blood}%"
