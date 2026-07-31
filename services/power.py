"""محاسبه قدرت رزمی برای دوئل و نمایش پروفایل"""
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database.models import User
from database.models_v3 import UserInventory, ShopItem
from services.cultivation import get_or_create_cultivation

REALM_POWER = {
    "پایه": 10,
    "متوسط": 25,
    "بالا": 45,
    "پیشرفته": 70,
    "خدا": 100,
}

ROOT_BONUS = {
    "بدون ریشه": 0,
    "ریشه پنج‌عنصر": 5,
    "ریشه آتش": 8,
    "ریشه آب": 8,
    "ریشه چوب": 8,
    "ریشه فلز": 8,
    "ریشه خاک": 8,
    "ریشه روح": 12,
}


async def calc_power(session: AsyncSession, user: User) -> dict:
    base = 20 + (user.level or 1) * 3
    rank_bonus = {"عضو دسته‌های پایین‌تر": 0, "عضو بیرونی": 5, "عضو داخلی": 12, "ارشد": 25, "ارجمند": 40}.get(user.rank, 0)

    cult = await get_or_create_cultivation(session, user.id)
    realm_p = REALM_POWER.get(cult.realm, 10) + (cult.stage or 1) * 8 + min(int(cult.energy or 0) // 10000, 50)
    root_p = ROOT_BONUS.get(cult.spiritual_root or "بدون ریشه", 0)

    # سلاح‌ها از اینونتوری
    weapon_p = 0
    result = await session.execute(
        select(UserInventory, ShopItem)
        .join(ShopItem, UserInventory.item_id == ShopItem.id)
        .where(UserInventory.user_id == user.id)
    )
    for inv, item in result.all():
        effect = item.effect or {}
        if isinstance(effect, dict) and effect.get("duel_power"):
            weapon_p += int(effect["duel_power"]) * max(inv.quantity, 1)

    total = base + rank_bonus + realm_p + root_p + weapon_p
    if getattr(user, "is_spirit_raiser", False):
        total += 15

    return {
        "total": total,
        "base": base,
        "rank": rank_bonus,
        "realm": realm_p,
        "root": root_p,
        "weapon": weapon_p,
        "root_name": cult.spiritual_root,
        "realm_name": cult.realm,
    }


def win_chance(power_a: int, power_b: int) -> float:
    """شانس برد A — در سختی بالا بازیکن ضعیف‌تر شانس بسیار کمی دارد"""
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
