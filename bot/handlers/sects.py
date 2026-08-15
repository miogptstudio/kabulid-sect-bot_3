from services.retention import war_is_open, territory_war_window
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
from services.i18n import tr

router = Router()


@router.message(Command("sects", "فرقهها", "فرقه"))
async def cmd_sects(message: Message):
    from aiogram.types import FSInputFile
    from services.portraits import panel_url
    await message.answer_photo(FSInputFile(panel_url("sect")), caption="🏛️ <b>فرقهها</b>")
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

    text = "🏛️ <b>لیست فرقهها</b>\n\n"
    if not sects:
        text += "هنوز فرقهای نیست.\n"
    else:
        for s in sects:
            text += f"• <b>{s.name}</b> ({s.sect_type}) — اعضا: {s.member_count} | امتیاز: {s.total_points}\n"
    
    if my:
        text += f"\n📍 تو عضو فرقه هستی (وضعیت: {my.status})"
    else:
        text += "\n📍 تذهیبکننده دورهگرد هستی (بدون فرقه — منابع خودت تامین کن)"
    
    if sword:
        text += f"\n⚔️ شمشیر رتبه تو: <b>{sword}</b>"
    
    text += (
        "\n\n<b>دستورات فرقه:</b>\n"
        "/createsect نام نوع — ساخت فرقه (تذهیب بالا+)\n"
        "  انواع: ارتدوکس / بیطرف / شیطانی\n"
        "/joinsect نام — <b>عضو شدن</b> در فرقه\n"
        "/mysect — وضعیت فرقه و امتیاز مشارکت تو\n"
        "/challengeleader — چالش صندلی رهبر (ماهی یکبار)\n"
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
            f"⚠️ نیاز به قلمرو بالاتر از «بالا» (حداقل پیشرفته)"
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
            try:
                from services.dao_path import set_dao
                if sect_type in ("ارتدوکس", "شیطانی", "بیطرف"):
                    set_dao(message.from_user.id, sect_type)
            except Exception:
                pass
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
        await message.answer(tr(message.from_user.id, "فرمت: /joinsect &lt;نام فرقه&gt;"))
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
            await message.answer(tr(message.from_user.id, "فرقه پیدا نشد."))
            return
        try:
            member = await join_sect(session, user, sect, tg_id=message.from_user.id)
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
            await message.answer(tr(message.from_user.id, "عضو فرقهای نیستی. تذهیبکننده دورهگرد هستی."))
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


@router.message(Command("challengeleader", "چالشرهبری"))
async def cmd_challenge(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        membership = await get_user_sect(session, user.id)
        if not membership:
            await message.answer(tr(message.from_user.id, "عضو فرقه نیستی."))
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
        # بدون شانس — فقط قدرت خالص
        t1 = int(p1.get("total") or 0)
        t2 = int(p2.get("total") or 0)
        if t1 == t2:
            won = False  # تساوی = رهبر میماند
        else:
            won = t1 > t2
        msg = await resolve_challenge(session, challenge, won)
        power_line = f"قدرت چالشگر: <b>{t1}</b> | قدرت رهبر: <b>{t2}</b>" + chr(10)
        if msg == "LOST_NEED_PARDON":
            user.is_dead = True
            await session.commit()
            from aiogram.utils.keyboard import InlineKeyboardBuilder
            builder = InlineKeyboardBuilder()
            builder.button(
                text="بخشیدن چالشگر 🙏",
                callback_data=f"pardon:{sect.leader_id}:{user.id}"
            )
            builder.button(
                text="رها کردن به مرگ",
                callback_data=f"nopardon:{sect.leader_id}:{user.id}"
            )
            builder.adjust(1)
            await message.answer(
                power_line + f"⚔️ چالش رهبری <b>{sect.name}</b> شکست خورد.\n"
                f"{user.full_name} در آستانه مرگ است.\n"
                f"فقط رهبر میتواند ببخشد یا رها کند.",
                reply_markup=builder.as_markup(),
            )
        else:
            await message.answer(
                power_line + f"⚔️ چالش رهبری فرقه <b>{sect.name}</b>\n\n{msg}"
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
            await callback.answer()
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
            await callback.answer()
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
        await message.answer(tr(message.from_user.id, "قلمرویی ثبت نشده. با ساخت فرقه، قلمرو اولیه ساخته میشود."))
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
        await message.answer(tr(message.from_user.id, "فرمت: /conquer &lt;نام قلمرو&gt;"))
        return
    name = parts[1].strip()
    
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        membership = await get_user_sect(session, user.id)
        if not membership:
            await message.answer(tr(message.from_user.id, "باید عضو فرقه باشی."))
            return
        sect = await session.get(Sect, membership.sect_id)
        result = await session.execute(select(Territory).where(Territory.name == name))
        territory = result.scalar_one_or_none()
        if not territory:
            await message.answer(tr(message.from_user.id, "قلمرو پیدا نشد. /territories"))
            return
        msg = await conquer_territory(session, sect, territory)
        await message.answer(msg)


@router.message(Command("transferleader", "واگذاریرهبری"))
async def cmd_transfer(message: Message):
    if not message.reply_to_message:
        await message.answer(tr(message.from_user.id, "روی پیام عضو فرقه ریپلای کن و /transferleader بزن."))
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
        await message.answer(tr(message.from_user.id, "فرمت: /newsect نامفرقه\nبعد نوع را با دکمه انتخاب کن."))
        return
    name = parts[1].strip()[:32]
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    for t in ["ارتدوکس", "بیطرف", "شیطانی"]:
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
        await callback.answer()
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


@router.message(Command("sectsettings", "تنظیماتفرقه"))
async def cmd_sect_settings(message: Message):
    parts = (message.text or "").split(maxsplit=2)
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        membership = await get_user_sect(session, user.id)
        if not membership:
            await message.answer(tr(message.from_user.id, "عضو فرقه نیستی."))
            return
        sect = await session.get(Sect, membership.sect_id)
        if not sect or sect.leader_id != user.id:
            await message.answer(tr(message.from_user.id, "فقط رهبر فرقه میتواند تنظیمات را عوض کند."))
            return
        if len(parts) < 3:
            await message.answer(
                f"⚙️ تنظیمات فرقه <b>{sect.name}</b>\n"
                f"نوع: {sect.sect_type}\n"
                f"اعضا: {sect.member_count}\n\n"
                f"/sectsettings name نامجدید\n"
                f"/sectsettings desc توضیح"
            )
            return
        key, val = parts[1], parts[2]
        if key == "name":
            sect.name = val[:64]
            await session.commit()
            await message.answer(f"نام فرقه: {sect.name}")
        elif key == "desc":
            if hasattr(sect, "description"):
                sect.description = val[:256]
                await session.commit()
            await message.answer(tr(message.from_user.id, "توضیح بهروز شد."))
        else:
            await message.answer(tr(message.from_user.id, "کلید: name یا desc"))



# ===== سیستمهای فرقه: خزانه، برج، کتابخانه، مأموریت =====
from services import sect_systems as ssys


async def _require_sect(session, user):
    from services.sects import get_user_sect
    mem = await get_user_sect(session, user.id)
    return mem


def _is_officer(status: str) -> bool:
    s = status or ""
    return any(x in s for x in ("رهبر", "ارجمند", "ارشد", "معاون"))


@router.message(Command("secttreasury", "خزانهفرقه", "خزانه"))
async def cmd_sect_treasury(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        mem = await _require_sect(session, user)
        if not mem:
            await message.answer("عضو فرقه نیستی.")
            return
        from database.models_v2 import Sect
        sect = await session.get(Sect, mem.sect_id)
        await message.answer(ssys.treasury_text(mem.sect_id, sect.name if sect else ""))


@router.message(Command("sectdeposit", "واریزفرقه"))
async def cmd_sect_deposit(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer("فرمت: /sectdeposit coins|spirit|heavenly|materials مقدار")
        return
    cur, amt = parts[1], int(parts[2])
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        mem = await _require_sect(session, user)
        if not mem:
            await message.answer("عضو فرقه نیستی.")
            return
        from services.economy import get_or_create_wallet
        w = await get_or_create_wallet(session, user.id)
        field = {"coins": "coins", "سکه": "coins", "spirit": "spirit_stones", "روحی": "spirit_stones",
                 "heavenly": "heavenly_stones", "بهشتی": "heavenly_stones", "materials": None, "مواد": None}.get(cur.lower())
        if field is None and cur.lower() in ("materials", "مواد"):
            # مواد از خزانه مستقیم بدون کیف
            await message.answer(ssys.deposit(mem.sect_id, "materials", amt))
            return
        if not field:
            await message.answer("ارز: coins spirit heavenly materials")
            return
        have = int(getattr(w, field, 0) or 0)
        if have < amt:
            await message.answer("موجودی کافی نیست.")
            return
        setattr(w, field, have - amt)
        await session.commit()
        await message.answer(ssys.deposit(mem.sect_id, "coins" if field=="coins" else ("spirit" if "spirit" in field else "heavenly"), amt))


@router.message(Command("sectwithdraw", "برداشتفرقه"))
async def cmd_sect_withdraw(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer("فرمت: /sectwithdraw coins|spirit|heavenly|materials مقدار")
        return
    cur, amt = parts[1], int(parts[2])
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        mem = await _require_sect(session, user)
        if not mem or not _is_officer(mem.status):
            await message.answer("فقط رهبر/ارجمند/ارشد.")
            return
        ok, msg = ssys.withdraw(mem.sect_id, cur, amt)
        if not ok:
            await message.answer(msg)
            return
        from services.economy import get_or_create_wallet
        w = await get_or_create_wallet(session, user.id)
        if cur.lower() in ("coins", "سکه"):
            w.coins = int(w.coins or 0) + amt
        elif cur.lower() in ("spirit", "روحی"):
            w.spirit_stones = int(getattr(w, "spirit_stones", 0) or 0) + amt
        elif cur.lower() in ("heavenly", "بهشتی"):
            w.heavenly_stones = int(getattr(w, "heavenly_stones", 0) or 0) + amt
        await session.commit()
        await message.answer(msg + " به کیف تو واریز شد.")


@router.message(Command("sectbuildings", "ساختمانفرقه", "برجفرقه"))
async def cmd_sect_buildings(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        mem = await _require_sect(session, user)
        if not mem:
            await message.answer("عضو فرقه نیستی.")
            return
        await message.answer(ssys.buildings_text(mem.sect_id))


@router.message(Command("sectupgrade", "ارتقابرج", "ارتقاساختمان"))
async def cmd_sect_upgrade(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("فرمت: /sectupgrade tower|library|forge")
        return
    aliases = {
        "برج": "tower", "برج تهذیب": "tower", "tower": "tower",
        "کتابخانه": "library", "کتابخانه تکنیک": "library", "library": "library",
        "آهنگری": "forge", "آهنگری فرقه": "forge", "forge": "forge",
    }
    key = aliases.get(parts[1].strip().lower(), parts[1].strip().lower())
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        mem = await _require_sect(session, user)
        if not mem or not _is_officer(mem.status):
            await message.answer("فقط رهبر/ارجمند.")
            return
        await message.answer(ssys.upgrade_building(mem.sect_id, key))


@router.message(Command("sectlibrary", "کتابخانهفرقه"))
async def cmd_sect_library(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        mem = await _require_sect(session, user)
        if not mem:
            await message.answer("عضو فرقه نیستی.")
            return
        await message.answer(ssys.list_library_techs(mem.sect_id))


@router.message(Command("learnsecttech", "یادگیریتکنیکفرقه"))
async def cmd_learn_sect_tech(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("فرمت: /learnsecttech نامتکنیک")
        return
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        mem = await _require_sect(session, user)
        if not mem:
            await message.answer("عضو فرقه نیستی.")
            return
        await message.answer(ssys.learn_sect_tech(message.from_user.id, mem.sect_id, parts[1].strip(), ssys.get_contrib(message.from_user.id)))


@router.message(Command("leaderpromotion", "مقامرهبر", "ارتقاع رهبری"))
async def cmd_leader_rank(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        mem = await _require_sect(session, user)
        if not mem:
            await message.answer("عضو فرقه نیستی.")
            return
        await message.answer(ssys.leader_rank_text(mem.sect_id))


@router.message(Command("sectmissions", "مأموریتفرقه", "ماموریتفرقه"))
async def cmd_sect_missions(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        mem = await _require_sect(session, user)
        if not mem:
            await message.answer("عضو فرقه نیستی.")
            return
        text = ssys.list_open_missions(mem.sect_id)
        text = text.replace("امتیاز مشارکت تو: 0 (با /mysectmission ببین)", f"امتیاز مشارکت تو: {ssys.get_contrib(message.from_user.id)}")
        await message.answer(text)


@router.message(Command("assignsectmission", "صدورمأموریت"))
async def cmd_assign_mission(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        mem = await _require_sect(session, user)
        if not mem or not _is_officer(mem.status):
            await message.answer("فقط رهبر یا ارجمند میتواند مأموریت بدهد.")
            return
        await message.answer(ssys.assign_missions(mem.sect_id, 3))


@router.message(Command("dosectmission", "انجاممأموریتفرقه"))
async def cmd_do_sect_mission(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("فرمت: /dosectmission شماره")
        return
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        mem = await _require_sect(session, user)
        if not mem:
            await message.answer("عضو فرقه نیستی.")
            return
        msg = ssys.do_mission(message.from_user.id, mem.sect_id, int(parts[1]))
        # personal coin reward
        if "انجام شد" in msg:
            from services.economy import get_or_create_wallet
            w = await get_or_create_wallet(session, user.id)
            # extract half coins roughly 20
            w.coins = int(w.coins or 0) + 25
            await session.commit()
        await message.answer(msg)


@router.message(Command("mysectmission", "مشارکتمن"))
async def cmd_my_contrib(message: Message):
    c = ssys.get_contrib(message.from_user.id)
    await message.answer(f"🏅 امتیاز مشارکت فرقه تو: <b>{c}</b>\nبا مأموریت فرقه (/sectmissions) افزایش مییابد.")



# ===== قوانین، آزمون عضویت، مسابقه ارتقا =====
from services import sect_exam as sexam


@router.message(Command("sectrules", "قوانینفرقه", "قوانینفرقه"))
async def cmd_sect_rules(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        if len(parts) >= 2:
            name = parts[1].strip()
            result = await session.execute(select(Sect).where(Sect.name == name, Sect.is_active == True))
            sect = result.scalar_one_or_none()
            if not sect:
                await message.answer("فرقه پیدا نشد.")
                return
            await message.answer(sexam.rules_text(sect.id, sect.name))
            return
        mem = await get_user_sect(session, user.id)
        if not mem:
            await message.answer("نام فرقه را بنویس: /sectrules نام")
            return
        sect = await session.get(Sect, mem.sect_id)
        await message.answer(sexam.rules_text(mem.sect_id, sect.name if sect else ""))


@router.message(Command("setsectrules", "تنظیمقوانین"))
async def cmd_set_rules(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("فرمت: /setsectrules قانون1 | قانون2 | قانون3")
        return
    rules = [r.strip() for r in parts[1].split("|")]
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        mem = await get_user_sect(session, user.id)
        if not mem:
            await message.answer("عضو فرقه نیستی.")
            return
        sect = await session.get(Sect, mem.sect_id)
        if not sect or sect.leader_id != user.id:
            await message.answer("فقط رهبر.")
            return
        await message.answer(sexam.set_rules(mem.sect_id, rules))


@router.message(Command("sectexam", "آزمونفرقه", "آزمونفرقه"))
async def cmd_sect_exam(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("فرمت: /sectexam نامفرقه\nقبلش /sectrules نامفرقه")
        return
    name = parts[1].strip()
    async with async_session() as session:
        result = await session.execute(select(Sect).where(Sect.name == name, Sect.is_active == True))
        sect = result.scalar_one_or_none()
        if not sect:
            await message.answer("فرقه پیدا نشد.")
            return
        await message.answer(sexam.start_exam(message.from_user.id, sect.id, sect.name))


@router.message(Command("examanswer", "پاسخآزمون"))
async def cmd_exam_answer(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("فرمت: /examanswer شماره")
        return
    await message.answer(sexam.answer_exam(message.from_user.id, int(parts[1])))


@router.message(Command("startpromocomp", "مسابقهارتقا"))
async def cmd_start_promo(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "فرمت: /startpromocomp مقصد\n"
            "مقصدها: عضو بیرونی | عضو داخلی | ارشد | ارجمند"
        )
        return
    target = parts[1].strip()
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        mem = await get_user_sect(session, user.id)
        if not mem:
            await message.answer("عضو فرقه نیستی.")
            return
        sect = await session.get(Sect, mem.sect_id)
        if not sect or sect.leader_id != user.id:
            # ارجمند هم بتواند
            if not mem.status or "ارجمند" not in mem.status:
                await message.answer("فقط رهبر یا ارجمند.")
                return
        await message.answer(sexam.start_promo_comp(mem.sect_id, target, hours=24))


@router.message(Command("promocompete", "شرکتمسابقه"))
async def cmd_promo_compete(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        mem = await get_user_sect(session, user.id)
        if not mem:
            await message.answer("عضو فرقه نیستی.")
            return
        # امتیاز بر اساس مشارکت ذخیرهشده + امتیاز مسابقه
        from services.sect_systems import get_contrib
        base = max(1, get_contrib(message.from_user.id) // 10)
        sexam.add_promo_score(mem.sect_id, message.from_user.id, base)
        await message.answer(
            f"🏅 +{base} امتیاز مسابقه ثبت شد." + chr(10) + sexam.promo_status(mem.sect_id)
        )


@router.message(Command("promostatus", "وضعیتمسابقه"))
async def cmd_promo_status(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        mem = await get_user_sect(session, user.id)
        if not mem:
            await message.answer("عضو فرقه نیستی.")
            return
        await message.answer(sexam.promo_status(mem.sect_id))


@router.message(Command("endpromocomp", "پایانمسابقه"))
async def cmd_end_promo(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        mem = await get_user_sect(session, user.id)
        if not mem:
            await message.answer("عضو فرقه نیستی.")
            return
        sect = await session.get(Sect, mem.sect_id)
        if not sect or sect.leader_id != user.id:
            await message.answer("فقط رهبر.")
            return
        winner_tg, msg = sexam.end_promo_comp(mem.sect_id)
        await message.answer(msg)


@router.message(Command("promotewinner", "ارتقابرنده"))
async def cmd_promote_winner(message: Message):
    """اعمال ارتقای برنده مسابقه"""
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        mem = await get_user_sect(session, user.id)
        if not mem:
            await message.answer("عضو فرقه نیستی.")
            return
        sect = await session.get(Sect, mem.sect_id)
        if not sect or sect.leader_id != user.id:
            await message.answer("فقط رهبر.")
            return
        data = sexam._promo().get(str(int(mem.sect_id))) or {}
        scores = data.get("scores") or {}
        if not scores:
            await message.answer("برندهای نیست.")
            return
        winner_tg = max(scores.items(), key=lambda x: int(x[1]))[0]
        target = data.get("target") or "عضو بیرونی"
        # پیدا کردن user برنده در همین فرقه
        from sqlalchemy import select as sq
        from database.models import User as U
        res = await session.execute(sq(U).where(U.telegram_id == int(winner_tg)))
        wuser = res.scalar_one_or_none()
        if not wuser:
            await message.answer("کاربر برنده پیدا نشد.")
            return
        wmem = await get_user_sect(session, wuser.id)
        if not wmem or wmem.sect_id != mem.sect_id:
            await message.answer("برنده عضو این فرقه نیست.")
            return
        wmem.status = target
        await session.commit()
        await message.answer(f"✅ `{winner_tg}` به مقام <b>{target}</b> ارتقا یافت.")
