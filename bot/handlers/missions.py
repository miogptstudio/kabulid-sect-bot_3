from datetime import datetime, date
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func

from database.engine import async_session
from database.crud import get_or_create_user
from database.models import Mission, UserMission, User
from services.death import erase_existence
from services.i18n import tr

router = Router()


EXTRA_MISSIONS = [
    {"title": "مأموریت شهری: گشت بازار", "description": "در شهر فعلی /explorecity بزن.", "mission_type": "city", "target_type": "explore", "target_value": 1, "reward_xp": 2, "reward_medal": None},
    {"title": "مأموریت شهری: سفر", "description": "با /travel به شهر دیگر برو.", "mission_type": "city", "target_type": "travel", "target_value": 1, "reward_xp": 2, "reward_medal": None},
    {"title": "مأموریت جهانی: جنگ فرقه", "description": "در حمله/دفاع فرقه‌ای شرکت کن یا /sectwar.", "mission_type": "global", "target_type": "sectwar", "target_value": 1, "reward_xp": 5, "reward_medal": "فاتح جهانی"},
    {"title": "مأموریت جهانی: لیدربورد", "description": "در /ranking بین ۱۰ نفر اول باش یا ۲ دوئل ببر.", "mission_type": "global", "target_type": "wins", "target_value": 2, "reward_xp": 4, "reward_medal": None},
    {"title": "مأموریت فرعی: تکنیک", "description": "/learntech بزن یا تکنیک فعال کن.", "mission_type": "side", "target_type": "tech", "target_value": 1, "reward_xp": 1, "reward_medal": None},
    {"title": "مأموریت فرعی: ساخت", "description": "۱ بار /craft یا استفاده از مواد.", "mission_type": "side", "target_type": "craft", "target_value": 1, "reward_xp": 1, "reward_medal": None},
    {"title": "مأموریت چندنفره: دوئل گروهی", "description": "در /lootarena یا آرنای باز شرکت کن.", "mission_type": "multi", "target_type": "arena", "target_value": 1, "reward_xp": 3, "reward_medal": None},
    {"title": "مأموریت چندنفره: دوئل دو نفره", "description": "با یک نفر /duel کن.", "mission_type": "multi", "target_type": "duels", "target_value": 1, "reward_xp": 2, "reward_medal": None},
    {"title": "مأموریت فرقه‌ای: عضوگیری", "description": "عضو فرقه شو یا دعوت کن /sects.", "mission_type": "sect", "target_type": "sect", "target_value": 1, "reward_xp": 2, "reward_medal": None},
    {"title": "مأموریت فرقه‌ای: مشارکت", "description": "امتیاز مشارکت فرقه بگیر (دوئل/تذهیب).", "mission_type": "sect", "target_type": "contrib", "target_value": 1, "reward_xp": 2, "reward_medal": None},
    {"title": "حمله به فرقه دشمن", "description": "هدف جهانی: در جنگ قلمرو فرقه شرکت کن.", "mission_type": "global", "target_type": "sectwar", "target_value": 1, "reward_xp": 6, "reward_medal": "تهاجم"},
]


DAILY_MISSIONS = [
    {
        "title": "دوئل روزانه",
        "description": "امروز حداقل ۱ دوئل انجام بده (برد یا باخت).",
        "mission_type": "daily",
        "target_type": "duels",
        "target_value": 1,
        "reward_xp": 1,
        "reward_medal": None,
    },
    {
        "title": "جمع‌آوری چی",
        "description": "۳ بار «تذهیب کردن» یا «جمع آوری چی» بگو.",
        "mission_type": "daily",
        "target_type": "gather",
        "target_value": 3,
        "reward_xp": 1,
        "reward_medal": None,
    },
    {
        "title": "نگهبان",
        "description": "۱ بار /guardian بزن و جواب بده.",
        "mission_type": "daily",
        "target_type": "guardian",
        "target_value": 1,
        "reward_xp": 1,
        "reward_medal": None,
    },
    {
        "title": "سفر شهری",
        "description": "با /travel به یک شهر دیگر برو.",
        "mission_type": "daily",
        "target_type": "travel",
        "target_value": 1,
        "reward_xp": 1,
        "reward_medal": None,
    },
    {
        "title": "شکار",
        "description": "۱ بار /hunt بزن (زنده بمان).",
        "mission_type": "daily",
        "target_type": "hunt",
        "target_value": 1,
        "reward_xp": 1,
        "reward_medal": None,
    },
    {
        "title": "کیف پول",
        "description": "۱ بار /dailycoin بگیر.",
        "mission_type": "daily",
        "target_type": "dailycoin",
        "target_value": 1,
        "reward_xp": 1,
        "reward_medal": None,
    },
]


async def ensure_daily_missions(session):
    # حذف مأموریت‌های منسوخ
    for bad in ("نابودی نوادگان ضحاک", "عکس‌های سیاه‌وسفید منظره"):
        try:
            r = await session.execute(select(Mission).where(Mission.title == bad))
            for row in r.scalars().all():
                row.is_active = False
        except Exception:
            pass

    for m in DAILY_MISSIONS + EXTRA_MISSIONS:
        result = await session.execute(
            select(Mission).where(Mission.title == m["title"], Mission.mission_type == m["mission_type"])
        )
        if not result.scalar_one_or_none():
            session.add(Mission(
                title=m["title"],
                description=m["description"],
                mission_type=m["mission_type"],
                target_type=m["target_type"],
                target_value=m["target_value"],
                reward_xp=m["reward_xp"],
                reward_medal=m["reward_medal"],
                is_active=True,
            ))
    await session.commit()




async def auto_accept_dailies(session, user: User) -> list[str]:
    """مأموریت‌های روزانه را خودکار فعال کن"""
    msgs = []
    await ensure_daily_missions(session)
    result = await session.execute(
        select(Mission).where(Mission.is_active == True, Mission.mission_type == "daily")
    )
    for mission in result.scalars().all():
        existing = await session.execute(
            select(UserMission).where(
                UserMission.user_id == user.id,
                UserMission.mission_id == mission.id,
            )
        )
        um = existing.scalar_one_or_none()
        if not um:
            session.add(UserMission(user_id=user.id, mission_id=mission.id, progress=0))
            msgs.append(f"📌 فعال شد: {mission.title}")
    await session.commit()
    return msgs


async def auto_finish_ready(session, user: User) -> list[str]:
    """مأموریت‌هایی که پیشرفت‌شان کامل است را خودکار تمام کن و پاداش بده"""
    msgs = []
    result = await session.execute(
        select(UserMission).where(
            UserMission.user_id == user.id,
            UserMission.is_completed == False,
        )
    )
    for um in result.scalars().all():
        mission = await session.get(Mission, um.mission_id)
        if not mission:
            continue
        if (um.progress or 0) >= (mission.target_value or 1):
            um.is_completed = True
            um.completed_at = datetime.utcnow()
            um.reward_claimed = True
            user.xp = int(user.xp or 0) + int(mission.reward_xp or 0)
            try:
                from services.economy import get_or_create_wallet
                w = await get_or_create_wallet(session, user.id)
                w.coins = int(w.coins or 0) + 50
                w.spirit_stones = int(getattr(w, "spirit_stones", 0) or 0) + 1
            except Exception:
                pass
            msgs.append(f"✅ «{mission.title}» خودکار تمام شد! +{mission.reward_xp or 0} XP")
    await session.commit()
    return msgs



async def count_completed_today(session, user_id: int) -> int:
    """تعداد مأموریت‌های تکمیل‌شده امروز"""
    today_start = datetime.combine(date.today(), datetime.min.time())
    result = await session.execute(
        select(func.count()).select_from(UserMission).where(
            UserMission.user_id == user_id,
            UserMission.is_completed == True,
            UserMission.completed_at >= today_start,
        )
    )
    return int(result.scalar() or 0)


async def count_taken_today(session, user_id: int) -> int:
    """تعداد مأموریت‌هایی که امروز گرفته (فعال یا کامل)"""
    today_start = datetime.combine(date.today(), datetime.min.time())
    # UserMission may not have started_at - use completed or all active taken
    # Fallback: count all user missions created conceptually via completed_at or id
    result = await session.execute(
        select(UserMission).where(UserMission.user_id == user_id)
    )
    rows = result.scalars().all()
    # count completed today + active incomplete (assume taken today if incomplete)
    n = 0
    for um in rows:
        if um.is_completed and um.completed_at and um.completed_at >= today_start:
            n += 1
        elif not um.is_completed:
            n += 1
    return n


@router.message(Command("missions", "مأموریت", "ماموریت"))
async def cmd_missions(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session,
            message.from_user.id,
            message.from_user.full_name,
            message.from_user.username,
        )
        await ensure_daily_missions(session)
        result = await session.execute(
            select(Mission).where(Mission.is_active == True)
        )
        missions = result.scalars().all()
        done = await count_completed_today(session, user.id)
        taken = await count_taken_today(session, user.id)

    text = (
        "🎯 <b>مأموریت‌های روزانه</b>\n\n"
        f"امروز تکمیل‌شده: <b>{done}/3</b>\n"
        f"⚠️ حداکثر ۳ مأموریت در روز.\n"
        f"اگر بعد از ۳ تا، مأموریت چهارمی بگیری…\n\n"
    )
    builder = InlineKeyboardBuilder()
    for m in missions:
        text += (
            f"📋 <b>{m.title}</b>\n"
            f"{m.description}\n"
            f"هدف: {m.target_value} | جایزه: {m.reward_xp} XP\n\n"
        )
        builder.button(
            text=f"انتخاب: {m.title}",
            callback_data=f"take_mission:{message.from_user.id}:{m.id}",
        )
    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("take_mission:"))
async def take_mission(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) == 3:
        owner_id, mission_id = int(parts[1]), int(parts[2])
        if callback.from_user.id != owner_id:
            await callback.answer()
            return
    else:
        mission_id = int(parts[1])

    async with async_session() as session:
        user = await get_or_create_user(
            session,
            callback.from_user.id,
            callback.from_user.full_name,
            callback.from_user.username,
        )

        completed = await count_completed_today(session, user.id)
        taken = await count_taken_today(session, user.id)

        # قانون: بعد از ۳ مأموریت (تکمیل‌شده)، انتخاب چهارمی = مرگ و پاکی
        if completed >= 3 or taken >= 3:
            user.is_dead = True
            await session.commit()
            kill_msg = (
                "💀 <b>شماها زیادی ضعیف بودید برا همین ادمین کشتتون</b>\n\n"
                "اکانت شما برای همیشه پاک می‌شود.\n"
                "از اول شروع کنید.\n\n"
                "در حال حذف دائمی اکانت…"
            )
            await callback.message.edit_text(kill_msg)
            # پاک کردن کامل
            final = await erase_existence(session, user)
            try:
                await callback.message.answer(final)
            except Exception:
                pass
            await callback.answer(tr(callback.from_user.id, "اکانت پاک شد."), show_alert=True)
            return

        # هر مأموریت فقط یک‌بار در روز
        from datetime import date, datetime
        today_start = datetime.combine(date.today(), datetime.min.time())
        done_today = await session.execute(
            select(UserMission).where(
                UserMission.user_id == user.id,
                UserMission.mission_id == mission_id,
                UserMission.is_completed == True,
                UserMission.completed_at >= today_start,
            )
        )
        if done_today.scalar_one_or_none():
            await callback.answer(tr(callback.from_user.id, "این مأموریت را امروز تمام کردی. فردا."), show_alert=True)
            return

        existing = await session.execute(
            select(UserMission).where(
                UserMission.user_id == user.id,
                UserMission.mission_id == mission_id,
                UserMission.is_completed == False,
            )
        )
        if existing.scalar_one_or_none():
            await callback.answer(tr(callback.from_user.id, "این مأموریت را قبلاً گرفتی!"), show_alert=True)
            return

        mission = await session.get(Mission, mission_id)
        if not mission or not mission.is_active:
            await callback.answer(tr(callback.from_user.id, "مأموریت پیدا نشد."), show_alert=True)
            return

        user_mission = UserMission(user_id=user.id, mission_id=mission_id)
        session.add(user_mission)
        await session.commit()

        await callback.message.edit_text(
            f"✅ مأموریت «{mission.title}» فعال شد!\n"
            f"پیشرفت: 0 / {mission.target_value}\n"
            f"امروز: {completed}/3 تکمیل‌شده"
        )
        await callback.answer()


@router.message(Command("completemission", "تموم‌ماموریت"))
async def cmd_complete_mission(message: Message):
    """تکمیل دستی مأموریت فعال اول (برای تست و سادگی)"""
    async with async_session() as session:
        user = await get_or_create_user(
            session,
            message.from_user.id,
            message.from_user.full_name,
            message.from_user.username,
        )
        result = await session.execute(
            select(UserMission).where(
                UserMission.user_id == user.id,
                UserMission.is_completed == False,
            )
        )
        um = result.scalars().first()
        if not um:
            await message.answer(tr(message.from_user.id, "مأموریت فعالی نداری. /missions"))
            return
        mission = await session.get(Mission, um.mission_id)
        um.progress = mission.target_value if mission else 1
        um.is_completed = True
        um.completed_at = datetime.utcnow()
        if mission:
            user.xp += mission.reward_xp or 0
        await session.commit()
        done = await count_completed_today(session, user.id)
        await message.answer(
            f"✅ مأموریت «{mission.title if mission else '?'}» تمام شد!\n"
            f"امروز: {done}/3\n"
            f"{'⚠️ یک مأموریت دیگر نگیر وگرنه…' if done >= 3 else ''}"
        )
