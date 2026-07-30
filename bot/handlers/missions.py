from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from database.engine import async_session
from database.crud import get_or_create_user
from database.models import Mission, UserMission, User

router = Router()


@router.message(Command("missions", "مأموریت", "ماموریت"))
async def cmd_missions(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=message.from_user.id,
            full_name=message.from_user.full_name,
            username=message.from_user.username
        )

        # مأموریت‌های فعال
        result = await session.execute(
            select(Mission).where(Mission.is_active == True)
        )
        missions = result.scalars().all()

    if not missions:
        await message.answer("فعلاً مأموریت فعالی وجود نداره.")
        return

    text = "🎯 <b>مأموریت‌های فعال</b>\n\n"
    builder = InlineKeyboardBuilder()

    for m in missions:
        type_emoji = {
            "global": "🌍",
            "section": "🏛️",
            "level": "📶"
        }.get(m.mission_type, "📋")

        text += (
            f"{type_emoji} <b>{m.title}</b>\n"
            f"{m.description}\n"
            f"هدف: {m.target_value} {m.target_type}\n"
            f"جایزه: {m.reward_xp} XP"
        )
        if m.reward_medal:
            text += f" + مدال «{m.reward_medal}»"
        text += "\n\n"

        builder.button(
            text=f"انتخاب: {m.title}",
            callback_data=f"take_mission:{m.id}"
        )

    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("take_mission:"))
async def take_mission(callback: CallbackQuery):
    mission_id = int(callback.data.split(":")[1])

    async with async_session() as session:
        user = await get_or_create_user(
            session,
            telegram_id=callback.from_user.id,
            full_name=callback.from_user.full_name,
            username=callback.from_user.username
        )

        # چک کن قبلاً نگرفته باشه
        existing = await session.execute(
            select(UserMission).where(
                UserMission.user_id == user.id,
                UserMission.mission_id == mission_id,
                UserMission.is_completed == False
            )
        )
        if existing.scalar_one_or_none():
            await callback.answer("این مأموریت رو قبلاً گرفتی!", show_alert=True)
            return

        mission = await session.get(Mission, mission_id)
        if not mission or not mission.is_active:
            await callback.answer("مأموریت پیدا نشد.", show_alert=True)
            return

        # بررسی شرایط
        if mission.mission_type == "section" and mission.target_rank:
            if user.rank != mission.target_rank:
                await callback.answer("این مأموریت برای رتبه تو نیست.", show_alert=True)
                return

        if mission.mission_type == "level":
            if mission.min_level and user.level < mission.min_level:
                await callback.answer("سطح تو برای این مأموریت کمه.", show_alert=True)
                return
            if mission.max_level and user.level > mission.max_level:
                await callback.answer("سطح تو برای این مأموریت بالاست.", show_alert=True)
                return

        user_mission = UserMission(user_id=user.id, mission_id=mission_id)
        session.add(user_mission)
        await session.commit()

        await callback.message.edit_text(
            f"✅ مأموریت «{mission.title}» برات فعال شد!\n"
            f"پیشرفت: 0 / {mission.target_value}"
        )
        await callback.answer()
