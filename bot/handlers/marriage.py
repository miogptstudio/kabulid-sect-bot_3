from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user
from database.models import User
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
            "💍 <b>سیستم ازدواج و نامزدی</b>\n\n"
            "روی پیام طرف مقابل ریپلای کن و /marry بزن.\n\n"
            "قوانین:\n"
            f"• نامزدی با مهلت {ENGAGE_HOURS} ساعت — فقط با قبول زن نهایی می‌شود\n"
            "• اگر اختلاف سطح ≥ ۲ باشد فقط <b>هشدار</b> می‌دهد (اجبار نیست)\n"
            "• ازدواج بین‌فرقه‌ای با هشدار ممکن است\n"
            "• فقط مرد درخواست می‌دهد؛ زن قبول یا رد می‌کند\n"
            "• مرد می‌تواند چند زن داشته باشد؛ هر زن یک شوهر\n"
            "• /divorce برای فسخ با رضایت\n"
            "• /wives وضعیت خانواده\n"
            "• /invitewedding دعوت مهمان"
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

        marriage, err, warnings = await propose(session, proposer, target)
        if err:
            await message.answer(err)
            return

        warn_text = "\n".join(warnings) if warnings else ""
        expires = marriage.engage_expires_at.strftime("%Y-%m-%d %H:%M") if marriage.engage_expires_at else "?"

        builder = InlineKeyboardBuilder()
        builder.button(text="قبول نامزدی / ازدواج 💍", callback_data=f"marryaccept:{marriage.id}")
        builder.button(text="رد", callback_data=f"marryreject:{marriage.id}")
        builder.adjust(1)

        await message.answer(
            f"💍 <b>درخواست نامزدی</b>\n\n"
            f"از: {proposer.full_name} (سطح {proposer.level})\n"
            f"به: {target.full_name} (سطح {target.level})\n"
            f"مهلت قبول: تا {expires} UTC ({ENGAGE_HOURS} ساعت)\n\n"
            f"{warn_text}\n\n"
            f"⚠️ ازدواج فقط با رضایت {target.full_name} انجام می‌شود.\n"
            f"در صورت رد، هیچ اجبار یا ربایشی وجود ندارد.",
            reply_markup=builder.as_markup()
        )


@router.callback_query(F.data.startswith("marryaccept:"))
async def marry_accept(callback: CallbackQuery):
    mid = int(callback.data.split(":")[1])
    async with async_session() as session:
        await expire_old_engagements(session)
        m = await session.get(Marriage, mid)
        if not m:
            await callback.answer("پیدا نشد.", show_alert=True)
            return
        msg = await accept_marriage(session, m, callback.from_user.id)
    await callback.message.edit_text(msg)
    await callback.answer()


@router.callback_query(F.data.startswith("marryreject:"))
async def marry_reject(callback: CallbackQuery):
    mid = int(callback.data.split(":")[1])
    async with async_session() as session:
        m = await session.get(Marriage, mid)
        if not m:
            await callback.answer("پیدا نشد.", show_alert=True)
            return
        msg = await reject_marriage(session, m, callback.from_user.id)
    await callback.message.edit_text(msg)
    await callback.answer()


@router.message(Command("divorce", "طلاق", "فسخ"))
async def cmd_divorce(message: Message):
    if not message.reply_to_message:
        await message.answer(
            "💔 برای فسخ ازدواج:\n"
            "روی پیام همسرت ریپلای کن و /divorce بزن.\n"
            "فسخ با اراده یکی از طرفین ثبت می‌شود (بدون زور برای ماندن)."
        )
        return

    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        partner_tg = message.reply_to_message.from_user
        partner = await get_or_create_user(
            session, partner_tg.id, partner_tg.full_name, partner_tg.username
        )
        msg = await divorce(session, user, partner.id)
        await message.answer(msg)


@router.message(Command("invitewedding", "دعوت‌عروسی", "دعوت"))
async def cmd_invite(message: Message):
    if not message.reply_to_message:
        await message.answer(
            "برای دعوت مهمان:\nروی پیام مهمان ریپلای کن و /invitewedding بزن.\nباید نامزد یا متاهل باشی."
        )
        return

    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        wives = await get_wives(session, user.id)
        as_wife = await get_husband(session, user.id)
        marriage = wives[0] if wives else as_wife
        if not marriage:
            # نامزدی فعال
            from sqlalchemy import select, or_
            result = await session.execute(
                select(Marriage).where(
                    or_(Marriage.husband_id == user.id, Marriage.wife_id == user.id),
                    Marriage.status == "engaged"
                )
            )
            marriage = result.scalars().first()
        if not marriage:
            await message.answer("اول باید نامزد یا متاهل باشی.")
            return
        guest = message.reply_to_message.from_user
        msg = await add_guest(session, marriage, guest.id)
        await message.answer(f"{msg}\nمهمان: {guest.full_name}")


@router.message(Command("wives", "همسران", "خانواده"))
async def cmd_wives(message: Message):
    async with async_session() as session:
        await expire_old_engagements(session)
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        text = "👨‍👩‍👧 <b>وضعیت خانوادگی</b>\n\n"
        wives = await get_wives(session, user.id)
        if wives:
            text += f"همسران ({len(wives)} نفر):\n"
            for w in wives:
                wife = await session.get(User, w.wife_id)
                if wife:
                    text += f"• {wife.full_name}\n"
        husband_rel = await get_husband(session, user.id)
        if husband_rel:
            husband = await session.get(User, husband_rel.husband_id)
            if husband:
                text += f"شوهر: {husband.full_name}\n"

        from sqlalchemy import select, or_
        eng = await session.execute(
            select(Marriage).where(
                or_(Marriage.husband_id == user.id, Marriage.wife_id == user.id),
                Marriage.status == "engaged"
            )
        )
        for e in eng.scalars().all():
            other_id = e.wife_id if e.husband_id == user.id else e.husband_id
            other = await session.get(User, other_id)
            exp = e.engage_expires_at.strftime("%m-%d %H:%M") if e.engage_expires_at else "?"
            text += f"💝 نامزدی با {other.full_name if other else '?'} (مهلت تا {exp})\n"

        if not wives and not husband_rel and not text.count("نامزدی"):
            text += "هنوز متاهل یا نامزد نیستی.\n/marry برای درخواست"
        await message.answer(text)
