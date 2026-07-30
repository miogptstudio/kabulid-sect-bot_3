from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select
import random

from database.engine import async_session
from database.crud import get_or_create_user
from database.models_v2 import Sect, SECT_TYPES
from database.models_v3 import Territory, LeadershipChallenge
from services.sects import (
    create_sect, join_sect, get_user_sect,
    challenge_leader, resolve_challenge, betray_sect,
    conquer_territory, get_rank_sword, can_create_sect
)
from services.cultivation import get_or_create_cultivation

router = Router()


@router.message(Command("sects", "فرقه‌ها", "فرقه"))
async def cmd_sects(message: Message):
    async with async_session() as session:
        result = await session.execute(select(Sect).where(Sect.is_active == True))
        sects = result.scalars().all()
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        my = await get_user_sect(session, user.id)
        cult = await get_or_create_cultivation(session, user.id)
        sword = await get_rank_sword(user, cult.spiritual_root)

    text = "🏛️ <b>لیست فرقه‌ها</b>\n\n"
    if not sects:
        text += "هنوز فرقه‌ای نیست.\n"
    else:
        for s in sects:
            text += f"• <b>{s.name}</b> ({s.sect_type}) — اعضا: {s.member_count} | امتیاز: {s.total_points}\n"
    
    if my:
        text += f"\n📍 تو عضو فرقه هستی (وضعیت: {my.status})"
    else:
        text += "\n📍 تذهیب‌کننده دوره‌گرد هستی (بدون فرقه — منابع خودت تامین کن)"
    
    if sword:
        text += f"\n⚔️ شمشیر رتبه تو: <b>{sword}</b>"
    
    text += (
        "\n\nدستورات:\n"
        "/createsect &lt;نام&gt; &lt;نوع&gt; — ساخت (نیاز قلمرو بالا+)\n"
        "/joinsect &lt;نام&gt;\n"
        "/mysect\n"
        "/challengeleader — چالش رهبری (ماهانه)\n"
        "/betray — خیانت و ترک فرقه\n"
        "/territories — قلمروها\n"
        "/conquer &lt;نام قلمرو&gt;"
    )
    await message.answer(text)


@router.message(Command("createsect"))
async def cmd_create_sect(message: Message):
    parts = message.text.split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            f"فرمت: /createsect &lt;نام&gt; &lt;نوع&gt;\n"
            f"انواع: {', '.join(SECT_TYPES)}\n"
            f"⚠️ نیاز به قلمرو تذهیب «بالا» یا بالاتر"
        )
        return
    
    name, sect_type = parts[1], parts[2]
    if sect_type not in SECT_TYPES:
        await message.answer(f"نوع نامعتبر. انواع: {', '.join(SECT_TYPES)}")
        return
    
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        try:
            sect = await create_sect(session, name, sect_type, user)
            await message.answer(
                f"✅ فرقه <b>{sect.name}</b> ({sect.sect_type}) ساخته شد.\n"
                f"تو رهبر و عضو داخلی هستی.\n"
                f"قلمرو اولیه هم ایجاد شد."
            )
        except ValueError as e:
            await message.answer(str(e))


@router.message(Command("joinsect"))
async def cmd_join_sect(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("فرمت: /joinsect &lt;نام فرقه&gt;")
        return
    name = parts[1].strip()
    
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        result = await session.execute(
            select(Sect).where(Sect.name == name, Sect.is_active == True)
        )
        sect = result.scalar_one_or_none()
        if not sect:
            await message.answer("فرقه پیدا نشد.")
            return
        try:
            member = await join_sect(session, user, sect)
            await message.answer(f"✅ به <b>{sect.name}</b> پیوستی. وضعیت: {member.status}")
        except ValueError as e:
            await message.answer(str(e))


@router.message(Command("mysect"))
async def cmd_my_sect(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        membership = await get_user_sect(session, user.id)
        if not membership:
            await message.answer("عضو فرقه‌ای نیستی. تذهیب‌کننده دوره‌گرد هستی.")
            return
        sect = await session.get(Sect, membership.sect_id)
        is_leader = sect and sect.leader_id == user.id
        text = (
            f"🏛️ <b>{sect.name}</b>\n"
            f"نوع: {sect.sect_type}\n"
            f"وضعیت تو: {membership.status}\n"
            f"امتیاز کمکی: {membership.contribution_points}\n"
            f"امتیاز فرقه: {sect.total_points}\n"
            f"اعضا: {sect.member_count}\n"
            f"{'👑 تو رهبر این فرقه هستی' if is_leader else ''}"
        )
        await message.answer(text)


@router.message(Command("challengeleader", "چالش‌رهبری"))
async def cmd_challenge(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        membership = await get_user_sect(session, user.id)
        if not membership:
            await message.answer("عضو فرقه نیستی.")
            return
        sect = await session.get(Sect, membership.sect_id)
        result = await challenge_leader(session, user, sect)
        if isinstance(result, str):
            await message.answer(result)
            return
        
        challenge = result
        # حل ساده: ۵۰٪ شانس (بعداً می‌تونه دوئل واقعی بشه)
        won = random.random() > 0.45
        msg = await resolve_challenge(session, challenge, won)
        await message.answer(
            f"⚔️ چالش رهبری فرقه <b>{sect.name}</b>\n\n{msg}\n\n"
            f"⚠️ فقط رهبری همین فرقه عوض می‌شود؛ کنترل کل ربات فقط مال صاحب ربات است."
        )


@router.message(Command("betray", "خیانت"))
async def cmd_betray(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        msg = await betray_sect(session, user, reason="خیانت داوطلبانه")
        await message.answer(msg)


@router.message(Command("territories", "قلمروها"))
async def cmd_territories(message: Message):
    async with async_session() as session:
        result = await session.execute(select(Territory))
        territories = result.scalars().all()
    
    if not territories:
        await message.answer("قلمرویی ثبت نشده. با ساخت فرقه، قلمرو اولیه ساخته می‌شود.")
        return
    
    text = "🗺️ <b>قلمروها</b>\n\n"
    for t in territories:
        owner = "آزاد"
        if t.owner_sect_id:
            async with async_session() as session:
                sect = await session.get(Sect, t.owner_sect_id)
                owner = sect.name if sect else "?"
        text += f"• <b>{t.name}</b> — مالک: {owner} | دفاع: {t.defense_points}\n"
    text += "\n/conquer &lt;نام قلمرو&gt; برای تصاحب"
    await message.answer(text)


@router.message(Command("conquer", "تصاحب"))
async def cmd_conquer(message: Message):
    parts = message.text.split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("فرمت: /conquer &lt;نام قلمرو&gt;")
        return
    name = parts[1].strip()
    
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        membership = await get_user_sect(session, user.id)
        if not membership:
            await message.answer("باید عضو فرقه باشی.")
            return
        sect = await session.get(Sect, membership.sect_id)
        result = await session.execute(select(Territory).where(Territory.name == name))
        territory = result.scalar_one_or_none()
        if not territory:
            await message.answer("قلمرو پیدا نشد. /territories")
            return
        msg = await conquer_territory(session, sect, territory)
        await message.answer(msg)
