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
        "\n\n<b>دستورات فرقه:</b>\n"
        "/createsect نام نوع — ساخت فرقه (تذهیب بالا+)\n"
        "  انواع: ارتدوکس / بی‌طرف / شیطانی\n"
        "/joinsect نام — <b>عضو شدن</b> در فرقه\n"
        "/mysect — وضعیت فرقه و امتیاز مشارکت تو\n"
        "/challengeleader — چالش صندلی رهبر (ماهی یک‌بار)\n"
        "/betray — خیانت و ترک فرقه\n"
        "/territories — لیست قلمروها\n"
        "/conquer نام — تصاحب قلمرو\n\n"
        "<b>عضوگیری:</b> بقیه را دعوت کن /joinsect را بزنند."
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
        from services.power import calc_power
        leader = await session.get(__import__("database.models", fromlist=["User"]).User, sect.leader_id)
        p1 = await calc_power(session, user)
        p2 = await calc_power(session, leader) if leader else {"total": 50}
        # شانس بر اساس قدرت
        ratio = p1["total"] / max(p1["total"] + p2["total"], 1)
        won = random.random() < max(0.2, min(0.8, ratio))
        msg = await resolve_challenge(session, challenge, won)
        if msg == "LOST_NEED_PARDON":
            user.is_dead = True
            await session.commit()
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(
                text="بخشیدن چالش‌گر 🙏",
                callback_data=f"pardon:{sect.leader_id}:{user.id}"
            )
            builder.button(
                text="رها کردن به مرگ",
                callback_data=f"nopardon:{sect.leader_id}:{user.id}"
            )
            builder.adjust(1)
            await message.answer(
                f"⚔️ چالش رهبری <b>{sect.name}</b> شکست خورد.\n"
                f"{user.full_name} در آستانه مرگ است.\n"
                f"فقط رهبر می‌تواند ببخشد یا رها کند.",
                reply_markup=builder.as_markup(),
            )
        else:
            await message.answer(
                f"⚔️ چالش رهبری فرقه <b>{sect.name}</b>\n\n{msg}"
            )


@router.callback_query(F.data.startswith("pardon:"))
async def cb_pardon(callback: CallbackQuery):
    parts = callback.data.split(":")
    leader_id, target_id = int(parts[1]), int(parts[2])
    async with async_session() as session:
        from database.models import User
        actor = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        if actor.id != leader_id:
            await callback.answer("فقط رهبر!", show_alert=True)
            return
        target = await session.get(User, target_id)
        if target:
            target.is_dead = False
            if hasattr(target, "lifespan"):
                target.lifespan = max(target.lifespan or 0, 20)
            await session.commit()
        await callback.message.edit_text(f"🙏 {target.full_name if target else 'فرد'} بخشیده شد و زنده ماند.")
    await callback.answer()


@router.callback_query(F.data.startswith("nopardon:"))
async def cb_nopardon(callback: CallbackQuery):
    parts = callback.data.split(":")
    leader_id, target_id = int(parts[1]), int(parts[2])
    async with async_session() as session:
        from database.models import User
        actor = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        if actor.id != leader_id:
            await callback.answer("فقط رهبر!", show_alert=True)
            return
        target = await session.get(User, target_id)
        if target:
            target.is_dead = True
            target.world = "زیرین"
            await session.commit()
        await callback.message.edit_text(
            f"💀 {target.full_name if target else 'فرد'} بخشیده نشد. /afterdeath برای انتخاب سرنوشت."
        )
    await callback.answer()


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


@router.message(Command("transferleader", "واگذاری‌رهبری"))
async def cmd_transfer(message: Message):
    if not message.reply_to_message:
        await message.answer("روی پیام عضو فرقه ریپلای کن و /transferleader بزن.")
        return
    from services.sects import transfer_leadership
    async with async_session() as session:
        leader = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        t = message.reply_to_message.from_user
        new_l = await get_or_create_user(session, t.id, t.full_name, t.username)
        msg = await transfer_leadership(session, leader, new_l)
    await message.answer(msg)


@router.message(Command("newsect"))
async def cmd_newsect_buttons(message: Message):
    """ساخت فرقه با دکمه نوع"""
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("فرمت: /newsect نام‌فرقه\nبعد نوع را با دکمه انتخاب کن.")
        return
    name = parts[1].strip()[:32]
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for t in ["ارتدوکس", "بی‌طرف", "شیطانی"]:
        builder.button(text=t, callback_data=f"secttype:{message.from_user.id}:{t}:{name}")
    builder.adjust(1)
    await message.answer(
        f"فرقه «{name}» — نوع را انتخاب کن:",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("secttype:"))
async def cb_sect_type(callback: CallbackQuery):
    # secttype:uid:type:name — type and name may have issues; use split max 3
    parts = callback.data.split(":", 3)
    if len(parts) < 4:
        await callback.answer("خطا")
        return
    owner = int(parts[1])
    if callback.from_user.id != owner:
        await callback.answer("مال تو نیست!", show_alert=True)
        return
    sect_type, name = parts[2], parts[3]
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        try:
            sect = await create_sect(session, name, sect_type, user)
            await callback.message.edit_text(
                f"✅ فرقه <b>{sect.name}</b> ({sect_type}) ساخته شد.\nتو رهبر هستی."
            )
        except ValueError as e:
            await callback.message.edit_text(str(e))
    await callback.answer()
