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

router = Router()

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
    for m in DAILY_MISSIONS:
        result = await session.execute(
            select(Mission).where(Mission.title == m["title"], Mission.mission_type == "daily")
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
            select(Mission).where(Mission.is_active == True, Mission.mission_type == "daily")
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
            await callback.answer("این پنل مال تو نیست!", show_alert=True)
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
            await callback.answer("اکانت پاک شد.", show_alert=True)
            return

        existing = await session.execute(
            select(UserMission).where(
                UserMission.user_id == user.id,
                UserMission.mission_id == mission_id,
                UserMission.is_completed == False,
            )
        )
        if existing.scalar_one_or_none():
            await callback.answer("این مأموریت را قبلاً گرفتی!", show_alert=True)
            return

        mission = await session.get(Mission, mission_id)
        if not mission or not mission.is_active:
            await callback.answer("مأموریت پیدا نشد.", show_alert=True)
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
            await message.answer("مأموریت فعالی نداری. /missions")
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
