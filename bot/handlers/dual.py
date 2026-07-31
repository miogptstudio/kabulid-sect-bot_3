from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user
from services.dual import request_dual, accept_dual, reject_dual

router = Router()

LOCKED_GENDERS = ("مرد", "زن")


@router.message(Command("gender", "جنسیت"))
async def cmd_gender(message: Message, state: FSMContext):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if user.gender in LOCKED_GENDERS:
            await message.answer(
                f"جنسیت تو «<b>{user.gender}</b>» است و <b>قابل تغییر نیست</b>."
            )
            return

    builder = InlineKeyboardBuilder()
    builder.button(text="مرد 👨", callback_data=f"setgender:{message.from_user.id}:مرد")
    builder.button(text="زن 👩", callback_data=f"setgender:{message.from_user.id}:زن")
    builder.adjust(1)
    await message.answer(
        "⚧ <b>انتخاب جنسیت (فقط یک‌بار)</b>\n\n"
        "قبل از تذهیب باید جنسیت را مشخص کنی.\n"
        "⚠️ بعد از انتخاب، <b>دیگر قابل تغییر نیست</b>.",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("setgender:"))
async def set_gender(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) == 3:
        owner_id, gender = int(parts[1]), parts[2]
        if callback.from_user.id != owner_id:
            await callback.answer("این دکمه مال تو نیست!", show_alert=True)
            return
    else:
        gender = parts[1]

    if gender not in LOCKED_GENDERS:
        await callback.answer("فقط مرد یا زن", show_alert=True)
        return

    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        if user.gender in LOCKED_GENDERS:
            await callback.message.edit_text(
                f"جنسیت قبلاً «{user.gender}» ثبت شده و قابل تغییر نیست."
            )
            await callback.answer()
            return
        user.gender = gender
        await session.commit()

    await callback.message.edit_text(
        f"✅ جنسیت «<b>{gender}</b>» ثبت شد.\n"
        f"دیگر قابل تغییر نیست. حالا می‌توانی تذهیب کنی."
    )
    await callback.answer()


@router.message(Command("dual", "تذهیب‌دوگانه", "دوگانه"))
async def cmd_dual(message: Message):
    if not message.reply_to_message:
        await message.answer(
            "☯️ برای تذهیب دوگانه:\n"
            "روی پیام طرف مقابل ریپلای کن و بنویس /dual\n\n"
            "شرایط:\n"
            "• یکی مرد و یکی زن باشن\n"
            "• هر دو ریشه معنوی داشته باشن\n"
            "• هر دو تکنیک تذهیب فعال داشته باشن"
        )
        return

    async with async_session() as session:
        user1 = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if user1.gender not in LOCKED_GENDERS:
            await message.answer("اول با /gender جنسیت دائمی خودت را مشخص کن.")
            return
        u2 = message.reply_to_message.from_user
        user2 = await get_or_create_user(
            session, u2.id, u2.full_name, u2.username
        )
        if user2.gender not in LOCKED_GENDERS:
            await message.answer("طرف مقابل هنوز جنسیت ثبت نکرده.")
            return

        try:
            dual = await request_dual(session, user1, user2)
        except ValueError as e:
            await message.answer(str(e))
            return

        builder = InlineKeyboardBuilder()
        builder.button(text="قبول ✅", callback_data=f"dualaccept:{dual.id}")
        builder.button(text="رد ❌", callback_data=f"dualreject:{dual.id}")
        builder.adjust(1)
        await message.answer(
            f"☯️ <b>درخواست تذهیب دوگانه</b>\n\n"
            f"از: {user1.full_name} ({user1.gender})\n"
            f"به: {user2.full_name} ({user2.gender})\n\n"
            f"{user2.full_name} باید قبول یا رد کنه.",
            reply_markup=builder.as_markup(),
        )


@router.callback_query(F.data.startswith("dualaccept:"))
async def dual_accept(callback: CallbackQuery):
    dual_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        try:
            msg = await accept_dual(session, dual_id, user)
        except ValueError as e:
            await callback.answer(str(e), show_alert=True)
            return
    await callback.message.edit_text(msg)
    await callback.answer()


@router.callback_query(F.data.startswith("dualreject:"))
async def dual_reject(callback: CallbackQuery):
    dual_id = int(callback.data.split(":")[1])
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        try:
            msg = await reject_dual(session, dual_id, user)
        except ValueError as e:
            await callback.answer(str(e), show_alert=True)
            return
    await callback.message.edit_text(msg)
    await callback.answer()
