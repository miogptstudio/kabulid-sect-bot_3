from services.cultivation import is_immortal_race
from sqlalchemy import select, delete, or_
from sqlalchemy.ext.asyncio import AsyncSession
from database.models import User, Medal, UserAchievement, Duel, UserMission, Mission
from database.models_v2 import SectMember, Cultivation, MasterDisciple, ArenaProfile, GameAccount
from database.models_v3 import (
    UserInventory, UserTechnique, CraftingSkill, UserWallet, Pet,
    Marriage, DualCultivation, BetrayalLog
)


async def become_spirit_raiser(session: AsyncSession, user: User) -> str:
    if is_immortal_race(getattr(user, 'race', None)):
        return "نژاد خدایان نامیراست."
    if not user.is_dead:
        return "تو نمرده‌ای."
    if user.is_spirit_raiser:
        return "قبلاً پرورش‌دهنده روح شده‌ای."

    user.is_dead = False
    user.is_spirit_raiser = True
    user.yang = 50
    user.yin = 0
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


async def _delete_related(session: AsyncSession, uid: int, tg_id: int):
    """حذف همه وابستگی‌های کاربر"""
    models_uid = [
        Medal, UserAchievement, UserInventory, UserTechnique,
        CraftingSkill, UserWallet, Pet, BetrayalLog, SectMember,
        Cultivation, ArenaProfile, UserMission,
    ]
    for model in models_uid:
        try:
            await session.execute(delete(model).where(model.user_id == uid))
        except Exception:
            pass

    try:
        await session.execute(
            delete(MasterDisciple).where(
                or_(MasterDisciple.master_id == uid, MasterDisciple.disciple_id == uid)
            )
        )
    except Exception:
        pass

    try:
        await session.execute(
            delete(Marriage).where(
                or_(Marriage.husband_id == uid, Marriage.wife_id == uid)
            )
        )
    except Exception:
        pass

    try:
        await session.execute(
            delete(DualCultivation).where(
                or_(DualCultivation.user1_id == uid, DualCultivation.user2_id == uid)
            )
        )
    except Exception:
        pass

    try:
        await session.execute(
            delete(Duel).where(
                or_(
                    Duel.challenger_id == uid,
                    Duel.opponent_id == uid,
                    Duel.winner_id == uid,
                )
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


async def erase_existence(session: AsyncSession, user: User) -> str:
    """
    پاک‌سازی کامل و شروع از صفر.
    حذف ردیف User گاهی به خاطر FK شکست می‌خورد؛
    پس همیشه داده‌ها را پاک و فیلدها را ریست می‌کنیم.
    """
    if not user.is_dead:
        return "فقط بعد از مرگ می‌توانی وجودت را محو کنی."

    uid = user.id
    tg_id = user.telegram_id
    name = user.full_name
    username = user.username

    await _delete_related(session, uid, tg_id)

    # برداشتن قفل مصرف ممنوعه و تکنیک مخفی (بر اساس telegram_id)
    try:
        from services.forbidden_lock import unlock_consume
        unlock_consume(int(tg_id))
    except Exception:
        pass
    try:
        from services.persist import get_dict, save as _psave
        for ns, key in (("void_owners", "ids"),):
            d = get_dict(ns)
            ids = [int(x) for x in d.get("ids", []) if int(x) != int(tg_id)]
            d["ids"] = ids
            _psave(ns)
        d2 = get_dict("void_learned")
        d2["ids"] = [int(x) for x in d2.get("ids", []) if int(x) != int(tg_id)]
        _psave("void_learned")
        get_dict("void_text").pop(str(int(tg_id)), None)
        _psave("void_text")
    except Exception:
        pass

    # ریست کامل فیلدهای کاربر = اکانت نو
    user.is_dead = False
    user.is_spirit_raiser = False
    user.rank = "عضو دسته‌های پایین‌تر"
    user.level = 1
    user.xp = 0
    user.wins = 0
    user.losses = 0
    user.total_duels = 0
    user.win_streak = 0
    user.loss_streak = 0
    user.same_rank_wins = 0
    user.gender = "نامشخص"
    user.yang = 100
    user.yin = 0
    user.is_virgin = True
    user.solo_count = 0
    user.blood = 100
    user.poisoned_until = None
    user.equipped_weapon_id = None
    user.has_cyrus_sword = False
    user.first_cities = None
    user.city = "tehran"
    user.world = "فانی"
    user.lifespan = 100
    user.is_banned = False
    user.is_active = True
    user.restricted_until = None
    user.restriction_reason = None
    if hasattr(user, "race"):
        user.race = "انسان"
    # role را برای ادمین نگه نمی‌داریم مگر ADMIN — ساده: عضو
    from bot.config import ADMIN_IDS
    from database.models import ROLE_LEADER, ROLE_MEMBER
    if tg_id in ADMIN_IDS:
        user.role = ROLE_LEADER
    else:
        user.role = ROLE_MEMBER

    # ریست تذهیب
    try:
        from database.models_v2 import Cultivation
        from sqlalchemy import select
        r = await session.execute(select(Cultivation).where(Cultivation.user_id == uid))
        cult = r.scalar_one_or_none()
        if cult:
            cult.energy = 0
            cult.stage = 1
            cult.realm = "بیداری"
            cult.spiritual_root = "بدون ریشه"
            cult.talent = None
            if hasattr(cult, "body_type"):
                cult.body_type = "بدن معمولی"
    except Exception:
        pass

    await session.commit()

    return (
        "🌑 وجودت به <b>پوچی</b> بازگشت و اکانت از صفر شد.\n"
        f"شناسه تلگرام همان است ({tg_id}).\n"
        "دوباره /start بزن، /gender و /race را انتخاب کن و از اول شروع کن."
    )
