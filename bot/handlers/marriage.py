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
    from aiogram.types import FSInputFile
    from services.portraits import panel_url
    await message.answer_photo(FSInputFile(panel_url("marriage")), caption="💍 <b>ازدواج و خانواده</b>")
    # /marry servant N must be handled before the player-to-player marriage flow.
    parts = (message.text or "").split()
    if len(parts) >= 3 and parts[1].lower() in ("servant", "خدمتکار"):
        from services import servants as servmod
        try:
            selector = int(parts[2])
        except ValueError:
            await message.answer("شمارهٔ خدمتکار نامعتبره.")
            return
        ok, msg, servant = servmod.marry_servant(message.from_user.id, selector)
        await message.answer(msg)
        return

    if not message.reply_to_message:
        await message.answer(
            "💍 <b>ازدواج و نامزدی</b>\n\n"
            "روی پیام طرف ریپلای + /marry\n\n"
            f"• نامزدی تا {ENGAGE_HOURS} ساعت\n"
            "• مرد یا زن میتوانند خواستگاری کنند؛ طرف مقابل قبول/رد میکند\n"
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
        from aiogram.types import FSInputFile
        from services.portraits import panel_url
        caption=(
            f"💍 <b>پنل ازدواج بین دو بازیکن</b>\n\n"
            f"👤 نفر اول: <b>{proposer.full_name}</b> | Lv.{proposer.level} | {proposer.gender}\n"
            f"👤 نفر دوم: <b>{target.full_name}</b> | Lv.{target.level} | {target.gender}\n"
            f"⏳ مهلت نامزدی: {expires} UTC\n"
            f"{warn_text}\n\n"
            f"🤝 تصمیم نهایی فقط با رضایت طرف مقابل انجام میشود."
        )
        await message.answer_photo(FSInputFile(panel_url("marriage")),caption=caption,reply_markup=builder.as_markup())


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
        await callback.message.edit_caption(caption=msg)
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
        await callback.message.edit_caption(caption=msg)
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
        text = "💍 <b>خانواده / همسران</b>" + chr(10) + chr(10)
        n = 0
        if wives:
            text += f"👥 همسران بازیکن ({len(wives)} نفر):" + chr(10)
            for w in wives:
                n += 1
                wu = await session.get(
                    __import__("database.models", fromlist=["User"]).User, w.wife_id
                )
                g = getattr(wu, "gender", "") if wu else ""
                name = wu.full_name if wu else str(w.wife_id)
                text += f"{n}. {name} ({g})" + chr(10)
        if hus:
            n += 1
            hu = await session.get(
                __import__("database.models", fromlist=["User"]).User, hus.husband_id
            )
            g = getattr(hu, "gender", "") if hu else ""
            name = hu.full_name if hu else str(hus.husband_id)
            text += f"{n}. همسر اصلی: {name} ({g})" + chr(10)
        # خدمتکارهای ازدواج‌کرده
        try:
            from services import servants as servmod
            bag = servmod.list_owned(message.from_user.id)
            married_servs = [s for s in bag if servmod.is_married(message.from_user.id, s)]
            if married_servs:
                text += chr(10) + f"🧑🤝🧑 همسران خدمتکار ({len(married_servs)} نفر):" + chr(10)
                for s in married_servs:
                    n += 1
                    text += (
                        f"{n}. {s.get('name','—')} | {s.get('gender','—')} | {s.get('race','—')}"
                        + f" | ❤️{s.get('loyalty',0)}% | 🧘{s.get('cult',1)}" + chr(10)
                    )
        except Exception as e:
            text += chr(10) + f"(خطا در خواندن همسر خدمتکار: {type(e).__name__})" + chr(10)
        if n == 0:
            text += (
                "همسری نداری." + chr(10)
                + "ریپلای + /marry برای خواستگاری" + chr(10)
                + "/marryservant شماره — ازدواج با خدمتکار"
            )
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


@router.message(Command("invitewedding", "دعوتعروسی"))
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
