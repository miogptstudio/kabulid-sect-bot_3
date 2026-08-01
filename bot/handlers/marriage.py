from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user
from database.models_v3 import Marriage
from services.marriage import (
    propose, accept_marriage, reject_marriage, add_guest,
    get_wives, get_husband, divorce, expire_old_engagements, ENGAGE_HOURS
)

router = Router()


@router.message(Command("marry", "ازدواج", "عروسی", "نامزدی"))
async def cmd_marry(message: Message):
    if not message.reply_to_message:
        await message.answer(
            "💍 <b>ازدواج و نامزدی</b>\n\n"
            "روی پیام طرف ریپلای + /marry\n\n"
            f"• نامزدی تا {ENGAGE_HOURS} ساعت\n"
            "• مرد یا زن می‌توانند خواستگاری کنند؛ طرف مقابل قبول/رد می‌کند\n"
            "• هر دو باید /gender زده باشند\n"
            "• /divorce · /wives · /invitewedding"
        )
        return

    async with async_session() as session:
        await expire_old_engagements(session)
        proposer = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        t = message.reply_to_message.from_user
        target = await get_or_create_user(session, t.id, t.full_name, t.username)

        if proposer.gender not in ("مرد", "زن") or target.gender not in ("مرد", "زن"):
            await message.answer("هر دو باید با /gender جنسیت دائمی ثبت کرده باشند.")
            return

        marriage, err, warnings = await propose(session, proposer, target)
        if err:
            await message.answer(err)
            return

        warn_text = "\n".join(warnings) if warnings else ""
        expires = marriage.engage_expires_at.strftime("%Y-%m-%d %H:%M") if marriage.engage_expires_at else "?"
        builder = InlineKeyboardBuilder()
        builder.button(text="قبول 💍", callback_data=f"marryaccept:{marriage.id}:{target.id}")
        builder.button(text="رد ❌", callback_data=f"marryreject:{marriage.id}:{target.id}")
        builder.adjust(1)
        await message.answer(
            f"💍 <b>درخواست نامزدی</b>\n\n"
            f"از: {proposer.full_name} (Lv.{proposer.level})\n"
            f"به: {target.full_name} (Lv.{target.level})\n"
            f"مهلت: تا {expires} UTC\n"
            f"{warn_text}\n\n"
            f"فقط <b>{target.full_name}</b> می‌تواند قبول/رد کند.",
            reply_markup=builder.as_markup(),
        )


@router.callback_query(F.data.startswith("marryaccept:"))
async def cb_accept(callback: CallbackQuery):
    parts = callback.data.split(":")
    mid = int(parts[1])
    if len(parts) >= 3:
        only = int(parts[2])
        if callback.from_user.id != only:
            # check by telegram - need user id mapping
            async with async_session() as session:
                u = await get_or_create_user(
                    session, callback.from_user.id,
                    callback.from_user.full_name, callback.from_user.username
                )
                if u.id != only and u.telegram_id != only:
                    # only might be user.id or telegram - check marriage
                    m = await session.get(Marriage, mid)
                    if not m or m.wife_id != u.id:
                        await callback.answer()
                        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        m = await session.get(Marriage, mid)
        if not m:
            await callback.answer("پیدا نشد", show_alert=True)
            return
        msg = await accept_marriage(session, m, user.id)
        await callback.message.edit_text(msg)
    await callback.answer()


@router.callback_query(F.data.startswith("marryreject:"))
async def cb_reject(callback: CallbackQuery):
    parts = callback.data.split(":")
    mid = int(parts[1])
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        m = await session.get(Marriage, mid)
        if not m:
            await callback.answer("پیدا نشد", show_alert=True)
            return
        msg = await reject_marriage(session, m, user.id)
        await callback.message.edit_text(msg)
    await callback.answer()


@router.message(Command("wives", "همسران", "خانواده"))
async def cmd_wives(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        wives = await get_wives(session, user.id)
        hus = await get_husband(session, user.id)
        text = "👨‍👩‍👧‍👦 <b>خانواده</b>\n\n"
        if wives:
            text += "همسران:\n"
            for w in wives:
                wu = await session.get(__import__("database.models", fromlist=["User"]).User, w.wife_id)
                text += f"• {wu.full_name if wu else w.wife_id}\n"
        if hus:
            hu = await session.get(__import__("database.models", fromlist=["User"]).User, hus.husband_id)
            text += f"شوهر: {hu.full_name if hu else hus.husband_id}\n"
        if not wives and not hus:
            text += "مجرد هستی."
        await message.answer(text)


@router.message(Command("divorce", "طلاق"))
async def cmd_divorce(message: Message):
    if not message.reply_to_message:
        await message.answer("روی پیام همسر ریپلای کن و /divorce بزن.")
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        t = message.reply_to_message.from_user
        partner = await get_or_create_user(session, t.id, t.full_name, t.username)
        msg = await divorce(session, user, partner.id)
        await message.answer(msg)


@router.message(Command("invitewedding", "دعوت‌عروسی"))
async def cmd_invite(message: Message):
    if not message.reply_to_message:
        await message.answer("روی پیام مهمان ریپلای کن.")
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        from sqlalchemy import select, or_
        result = await session.execute(
            select(Marriage).where(
                or_(Marriage.husband_id == user.id, Marriage.wife_id == user.id),
                Marriage.status.in_(["engaged", "married"])
            )
        )
        m = result.scalars().first()
        if not m:
            await message.answer("ازدواج/نامزدی فعالی نداری.")
            return
        msg = await add_guest(session, m, message.reply_to_message.from_user.id)
        await message.answer(msg)
