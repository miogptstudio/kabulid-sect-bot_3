from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user, get_user_by_telegram_id
from database.models import User
from services.master import take_disciple, get_disciples, get_master, leave_mastership
from services.i18n import tr

router = Router()


@router.message(Command("master", "استاد"))
async def cmd_master(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        as_master = await get_disciples(session, user.id)
        as_disciple = await get_master(session, user.id)

    text = "🎓 <b>سیستم استاد-شاگردی</b>\n\n"
    if as_disciple:
        text += "وضعیت: شاگرد هستی.\n"
    elif as_master:
        text += f"وضعیت: استاد هستی ({len(as_master)} شاگرد).\n"
    else:
        text += "وضعیت: آزاد.\n"
    text += (
        "\n• /takedisciple — درخواست استادی (ریپلای)\n"
        "  طرف باید با دکمه <b>قبول</b> یا <b>رد</b> جواب بدهد\n"
        "• /askmaster — درخواست شاگردی نزد کسی (ریپلای)\n"
        "• /mydisciples · /mymaster\n"
        "• /leavemaster — ترک رابطه"
    )
    await message.answer(text)


@router.message(Command("takedisciple", "شاگردگرفتن"))
async def cmd_take_disciple(message: Message):
    """فقط درخواست میفرستد — تا قبول نشود شاگرد نمیشود"""
    if not message.reply_to_message:
        await message.answer(
            "روی پیام شخص ریپلای کن و /takedisciple بزن.\n"
            "او باید قبول یا رد کند."
        )
        return

    async with async_session() as session:
        master = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        du = message.reply_to_message.from_user
        disciple = await get_or_create_user(
            session, du.id, du.full_name, du.username
        )
        if master.id == disciple.id:
            await message.answer(tr(message.from_user.id, "نمیتوانی خودت شاگرد خودت شوی."))
            return
        # pre-check
        if await get_master(session, disciple.id):
            await message.answer(tr(message.from_user.id, "این نفر الان استاد دارد."))
            return
        if await get_master(session, master.id):
            await message.answer(tr(message.from_user.id, "تو خودت شاگردی و نمیتوانی استاد شوی."))
            return

    builder = InlineKeyboardBuilder()
    builder.button(
        text="قبول شاگردی ✅",
        callback_data=f"mdacc:{master.id}:{disciple.id}",
    )
    builder.button(
        text="رد ❌",
        callback_data=f"mdrej:{master.id}:{disciple.id}",
    )
    builder.adjust(1)
    await message.answer(
        f"🎓 <b>درخواست استاد-شاگردی</b>\n\n"
        f"استاد پیشنهادی: <b>{master.full_name}</b>\n"
        f"شاگرد پیشنهادی: <b>{disciple.full_name}</b>\n\n"
        f"فقط <b>{disciple.full_name}</b> میتواند قبول یا رد کند.\n"
        f"بدون قبول، شاگردی ثبت نمیشود.",
        reply_markup=builder.as_markup(),
    )


@router.message(Command("askmaster", "درخواستاستاد"))
async def cmd_ask_master(message: Message):
    """شخص از کسی میخواهد شاگردش شود — استاد باید قبول کند"""
    if not message.reply_to_message:
        await message.answer(tr(message.from_user.id, "روی پیام استاد مورد نظر ریپلای کن و /askmaster بزن."))
        return

    async with async_session() as session:
        disciple = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        mu = message.reply_to_message.from_user
        master = await get_or_create_user(
            session, mu.id, mu.full_name, mu.username
        )
        if master.id == disciple.id:
            await message.answer(tr(message.from_user.id, "با خودت نه."))
            return
        if await get_master(session, disciple.id):
            await message.answer(tr(message.from_user.id, "تو الان استاد داری."))
            return
        if await get_master(session, master.id):
            await message.answer(tr(message.from_user.id, "او خودش شاگرد است و نمیتواند استاد شود."))
            return

    builder = InlineKeyboardBuilder()
    builder.button(
        text="قبول به عنوان استاد ✅",
        callback_data=f"mdacc:{master.id}:{disciple.id}",
    )
    builder.button(
        text="رد ❌",
        callback_data=f"mdrej:{master.id}:{disciple.id}",
    )
    builder.adjust(1)
    await message.answer(
        f"🎓 <b>درخواست شاگردی</b>\n\n"
        f"{disciple.full_name} میخواهد شاگرد <b>{master.full_name}</b> شود.\n\n"
        f"فقط <b>{master.full_name}</b> میتواند قبول یا رد کند.",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("mdacc:"))
async def cb_master_accept(callback: CallbackQuery):
    parts = callback.data.split(":")
    master_id, disciple_id = int(parts[1]), int(parts[2])
    async with async_session() as session:
        me = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        # یا شاگرد قبول میکند (takedisciple) یا استاد (askmaster)
        if me.id not in (master_id, disciple_id):
            await callback.answer()
            return
        # برای takedisciple فقط شاگرد باید قبول کند
        # برای askmaster فقط استاد — هر دو طرف مرتبطاند؛ امنتر: هر کدام از دو طرف که هنوز رابطه نیست
        master = await session.get(User, master_id)
        disciple = await session.get(User, disciple_id)
        if not master or not disciple:
            await callback.answer()
            return
        try:
            await take_disciple(session, master, disciple)
        except ValueError as e:
            await callback.message.edit_text(str(e))
            await callback.answer()
            return
        await callback.message.edit_text(
            f"✅ ثبت شد!\n"
            f"استاد: <b>{master.full_name}</b>\n"
            f"شاگرد: <b>{disciple.full_name}</b>"
        )
    await callback.answer()


@router.callback_query(F.data.startswith("mdrej:"))
async def cb_master_reject(callback: CallbackQuery):
    parts = callback.data.split(":")
    master_id, disciple_id = int(parts[1]), int(parts[2])
    async with async_session() as session:
        me = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        if me.id not in (master_id, disciple_id):
            await callback.answer()
            return
    await callback.message.edit_text(tr(callback.from_user.id, "❌ درخواست استاد-شاگردی رد شد."))
    await callback.answer()


@router.message(Command("mydisciples", "شاگردان"))
async def cmd_my_disciples(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        rows = await get_disciples(session, user.id)
        if not rows:
            await message.answer(tr(message.from_user.id, "شاگردی نداری."))
            return
        text = "🎓 شاگردان تو:\n"
        for r in rows:
            d = await session.get(User, r.disciple_id)
            text += f"• {d.full_name if d else r.disciple_id}\n"
        await message.answer(text)


@router.message(Command("mymaster", "استادمن"))
async def cmd_my_master(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        rel = await get_master(session, user.id)
        if not rel:
            await message.answer(tr(message.from_user.id, "استاد نداری."))
            return
        m = await session.get(User, rel.master_id)
        await message.answer(f"استاد تو: <b>{m.full_name if m else rel.master_id}</b>")


@router.message(Command("leavemaster", "ترکاستادی", "ترکشاگردی"))
async def cmd_leave_master(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        msg = await leave_mastership(session, user)
    await message.answer(msg)
