from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Medal, UserAchievement, Duel
from database.models_v2 import SectMember, Cultivation, MasterDisciple, ArenaProfile, GameAccount
from database.models_v3 import (
    UserInventory, UserTechnique, CraftingSkill, UserWallet, Pet,
    Marriage, DualCultivation, BetrayalLog
)


async def become_spirit_raiser(session: AsyncSession, user: User) -> str:
    if not user.is_dead:
        return "تو نمرده‌ای."
    if user.is_spirit_raiser:
        return "قبلاً پرورش‌دهنده روح شده‌ای."

    user.is_dead = False
    user.is_spirit_raiser = True
    user.yang = 50
    user.yin = 0
    # شروع دوباره تذهیب روحی
    try:
        cult = await session.execute(
            select(Cultivation).where(Cultivation.user_id == user.id)
        )
        c = cult.scalar_one_or_none()
        if c:
            c.realm = "پایه"
            c.stage = 1
            c.energy = 0
            c.spiritual_root = "ریشه روح"
    except Exception:
        pass

    await session.commit()
    return (
        "👻 به عنوان <b>پرورش‌دهنده روح</b> دوباره به وجود آمدی.\n"
        "بدن فیزیکی از بین رفته؛ حالا مسیر روح را طی می‌کنی.\n"
        "ریشه: ریشه روح | تذهیب از پایه از نو."
    )


async def erase_existence(session: AsyncSession, user: User) -> str:
    """پاک کردن کامل اکانت — وجود به پوچی برمی‌گردد"""
    if not user.is_dead:
        return "فقط بعد از مرگ می‌توانی وجودت را محو کنی."

    uid = user.id
    tg_id = user.telegram_id

    # حذف وابستگی‌ها (به ترتیب برای جلوگیری از خطای FK)
    tables_user_id = [
        Medal, UserAchievement, UserInventory, UserTechnique,
        CraftingSkill, UserWallet, Pet, BetrayalLog, SectMember,
        Cultivation, ArenaProfile,
    ]
    for model in tables_user_id:
        try:
            await session.execute(delete(model).where(model.user_id == uid))
        except Exception:
            pass

    try:
        await session.execute(
            delete(MasterDisciple).where(
                (MasterDisciple.master_id == uid) | (MasterDisciple.disciple_id == uid)
            )
        )
    except Exception:
        pass

    try:
        await session.execute(
            delete(Marriage).where(
                (Marriage.husband_id == uid) | (Marriage.wife_id == uid)
            )
        )
    except Exception:
        pass

    try:
        await session.execute(
            delete(DualCultivation).where(
                (DualCultivation.user1_id == uid) | (DualCultivation.user2_id == uid)
            )
        )
    except Exception:
        pass

    try:
        await session.execute(
            delete(Duel).where(
                (Duel.challenger_id == uid) | (Duel.opponent_id == uid) | (Duel.winner_id == uid)
            )
        )
    except Exception:
        pass

    try:
        await session.execute(
            delete(GameAccount).where(GameAccount.owner_telegram_id == tg_id)
        )
    except Exception:
        pass

    await session.delete(user)
    await session.commit()
    return (
        "🌑 وجودت به <b>پوچی</b> بازگشت.\n"
        "این اکانت برای همیشه پاک شد. اگر دوباره /start بزنی، از صفر شروع می‌کنی."
    )
