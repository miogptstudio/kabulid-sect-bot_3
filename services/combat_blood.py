"""سیستم خون، زخم، سم، شمشیر کوروش — آسیب پایدار تا درمان"""
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User

MAX_BLOOD_BASE = 100
POISON_HOURS = 3


def has_cyrus(user: User) -> bool:
    return bool(getattr(user, "has_cyrus_sword", False))


def max_blood_for_user(user: User, cult=None) -> int:
    """هرچه تذهیب بالاتر، خون بیشتر"""
    base = MAX_BLOOD_BASE
    level = int(getattr(user, "level", 1) or 1)
    bonus = (level - 1) * 5
    if cult is not None:
        stage = int(getattr(cult, "stage", 1) or 1)
        realm = getattr(cult, "realm", "") or ""
        realm_bonus = {
            "بیداری": 0, "پایه": 20, "هسته": 50, "روح": 100,
            "آسمانی": 200, "بهشتی": 300, "الهی": 500, "پوچی": 400,
            "ای‌تری": 250, "جاودانگی": 800, "وحدت": 1000,
        }
        # fuzzy match
        rb = 0
        for k, v in realm_bonus.items():
            if k in realm:
                rb = max(rb, v)
        bonus += stage * 3 + rb
    return max(100, base + bonus)


async def ensure_blood(user: User, cult=None):
    mx = max_blood_for_user(user, cult)
    if getattr(user, "blood", None) is None:
        user.blood = mx
    # اگر حداکثر جدید بیشتر است و خون پر بوده، پر نگه می‌داریم
    if user.blood > mx:
        user.blood = mx


async def apply_damage(
    session: AsyncSession,
    attacker: User,
    defender: User,
    base_damage: int,
    *,
    is_cyrus_strike: bool = False,
    is_death_duel: bool = False,
) -> dict:
    await ensure_blood(attacker)
    await ensure_blood(defender)
    msgs = []
    mx = max_blood_for_user(defender)

    if is_cyrus_strike or (has_cyrus(attacker) and is_death_duel):
        msgs.append("⚔️ ضربه شمشیر کوروش! روح نابود شد و اکانت پاک می‌شود.")
        defender.is_dead = True
        defender.blood = 0
        await session.commit()
        from services.death import erase_existence
        wipe = await erase_existence(session, defender)
        msgs.append(wipe)
        return {"killed": True, "wiped": True, "damage": 999, "blood": 0, "max_blood": mx, "messages": msgs}

    if has_cyrus(defender) and not has_cyrus(attacker):
        msgs.append("🛡 شمشیر کوروش از صاحبش محافظت کرد — بدون آسیب.")
        return {"killed": False, "wiped": False, "damage": 0, "blood": defender.blood, "max_blood": mx, "messages": msgs}

    dmg = max(5, min(45, int(base_damage)))
    before = int(defender.blood or mx)
    defender.blood = max(0, before - dmg)
    msgs.append(f"🩸 آسیب {dmg} | خون: {defender.blood}/{mx}")

    if defender.blood <= 0:
        defender.is_dead = True
        msgs.append("💀 خون تمام شد — مرگ.")
        await session.commit()
        return {"killed": True, "wiped": False, "damage": dmg, "blood": 0, "max_blood": mx, "messages": msgs}

    await session.commit()
    return {"killed": False, "wiped": False, "damage": dmg, "blood": defender.blood, "max_blood": mx, "messages": msgs}


async def apply_poison(session: AsyncSession, target: User) -> str:
    target.poisoned_until = datetime.utcnow() + timedelta(hours=POISON_HOURS)
    mx = max_blood_for_user(target)
    target.blood = max(10, int(target.blood or mx) - 15)
    await session.commit()
    return (
        f"☠️ زخمی و مسموم شدی! خون: {target.blood}/{mx}\n"
        f"تا ۳ ساعت فرصت /heal داری وگرنه می‌میری.\n"
        f"مهلت تا: {target.poisoned_until.strftime('%H:%M UTC')}"
    )


async def check_poison_death(session: AsyncSession, user: User) -> str | None:
    until = getattr(user, "poisoned_until", None)
    if not until:
        return None
    if datetime.utcnow() < until:
        return None
    # سم منقضی و درمان نشده
    user.is_dead = True
    user.blood = 0
    user.poisoned_until = None
    await session.commit()
    return "☠️ از سم مردی. /afterdeath"


async def heal_poison(session: AsyncSession, user: User) -> str:
    if not getattr(user, "poisoned_until", None):
        mx = max_blood_for_user(user)
        user.blood = mx
        await session.commit()
        return f"خون پر شد: {user.blood}/{mx}"
    user.poisoned_until = None
    mx = max_blood_for_user(user)
    user.blood = mx
    await session.commit()
    return f"✅ سم پاک شد و خون پر شد: {user.blood}/{mx}"
