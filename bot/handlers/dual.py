from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user
from database.models_v3 import DualCultivation
from services.dual import request_dual, accept_dual, reject_dual
from services.i18n import t_user, tr

router = Router()
LOCKED_GENDERS = ("مرد", "زن")


@router.message(Command("gender"))
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
        "⚧ <b>انتخاب جنسیت (فقط یکبار)</b>\n\n"
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
            await callback.answer()
            return
    else:
        gender = parts[1]

    if gender not in LOCKED_GENDERS:
        await callback.answer()
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
        f"دیگر قابل تغییر نیست. حالا میتوانی تذهیب کنی."
    )
    await callback.answer()


@router.message(Command("dual", "تذهیبدوگانه", "دوگانه"))
async def cmd_dual(message: Message):
    if not message.reply_to_message:
        await message.answer(
            "☯️ برای تذهیب دوگانه:\n"
            "روی پیام طرف مقابل ریپلای کن و بنویس /dual\n\n"
            "شرایط:\n"
            "• یکی مرد و یکی زن\n"
            "• هر دو ریشه معنوی\n"
            "• هر دو تکنیک تذهیب فعال (/learntech)"
        )
        return

    async with async_session() as session:
        user1 = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if user1.gender not in LOCKED_GENDERS:
            await message.answer(tr(message.from_user.id, "اول با /gender جنسیت دائمی خودت را مشخص کن."))
            return
        u2 = message.reply_to_message.from_user
        user2 = await get_or_create_user(
            session, u2.id, u2.full_name, u2.username
        )
        if user2.gender not in LOCKED_GENDERS:
            await message.answer(tr(message.from_user.id, "طرف مقابل هنوز /gender نزده."))
            return

        try:
            result = await request_dual(session, user1, user2)
        except Exception as e:
            import logging
            logging.getLogger(__name__).exception("dual request: %s", e)
            await message.answer(f"⚠️ خطا در تذهیب دوگانه: {type(e).__name__}\n{str(e)[:250]}")
            return
        if isinstance(result, str):
            await message.answer(result)
            return

        dual = result
        builder = InlineKeyboardBuilder()
        builder.button(text=t_user(message.from_user.id, "btn_accept"), callback_data=f"dualaccept:{dual.id}:{user2.id}")
        builder.button(text=t_user(message.from_user.id, "btn_reject"), callback_data=f"dualreject:{dual.id}:{user2.id}")
        builder.adjust(1)
        await message.answer(
            f"☯️ <b>درخواست تذهیب دوگانه</b>\n\n"
            f"از: {user1.full_name} ({user1.gender})\n"
            f"به: {user2.full_name} ({user2.gender})\n\n"
            f"فقط <b>{user2.full_name}</b> میتواند قبول/رد کند.",
            reply_markup=builder.as_markup(),
        )


@router.callback_query(F.data.startswith("dualaccept:"))
async def dual_accept(callback: CallbackQuery):
    parts = callback.data.split(":")
    dual_id = int(parts[1])
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        dual = await session.get(DualCultivation, dual_id)
        if not dual:
            await callback.answer()
            return
        if dual.user2_id != user.id:
            await callback.answer("این درخواست برای تو نیست.", show_alert=False)
            return
        if dual.status != "pending":
            await callback.answer("این درخواست دیگر معتبر نیست.", show_alert=True)
            return
        msg = await accept_dual(session, dual, user.id)
        try:
            await callback.message.edit_text(msg)
        except Exception:
            await callback.message.answer(msg)
    await callback.answer()


@router.callback_query(F.data.startswith("dualreject:"))
async def dual_reject(callback: CallbackQuery):
    parts = callback.data.split(":")
    dual_id = int(parts[1])
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        dual = await session.get(DualCultivation, dual_id)
        if not dual:
            await callback.answer()
            return
        if user.id not in (dual.user1_id, dual.user2_id):
            await callback.answer()
            return
        msg = await reject_dual(session, dual, user.id)
        try:
            await callback.message.edit_text(msg)
        except Exception:
            await callback.message.answer(msg)
    await callback.answer()


@router.message(Command("canceldual", "لغودوگانه"))
async def cmd_cancel_dual(message: Message):
    from services.dual import cancel_dual
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        msg = await cancel_dual(session, user.id)
    await message.answer(msg)


@router.message(F.text.in_({"مرد", "زن", "جنسیت مرد", "جنسیت زن"}))
async def text_gender(message: Message):
    """انتخاب جنسیت با نوشتن مرد / زن"""
    t = (message.text or "").strip()
    gender = "مرد" if "مرد" in t else ("زن" if "زن" in t else None)
    if not gender:
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if user.gender in LOCKED_GENDERS:
            await message.answer(f"جنسیت تو «{user.gender}» است و قابل تغییر نیست.")
            return
        user.gender = gender
        await session.commit()
    await message.answer(
        f"✅ جنسیت «<b>{gender}</b>» با نوشتن ثبت شد." + chr(10)
        + "دیگر قابل تغییر نیست."
    )
