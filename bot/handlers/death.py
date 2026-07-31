from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user
from services.death import become_spirit_raiser, erase_existence
from services.dimension import become_vengeful, release_spirit

router = Router()


def death_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="👻 پرورش‌دهنده روح", callback_data="death:spirit")
    builder.button(text="😈 روح انتقام‌جو", callback_data="death:vengeful")
    builder.button(text="🌑 پوچی (حذف دائمی)", callback_data="death:void")
    builder.adjust(1)
    return builder.as_markup()


@router.message(Command("afterdeath", "بعدازمرگ", "مرگ"))
async def cmd_afterdeath(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if user.is_spirit_raiser and not user.is_dead:
            await message.answer(
                "روح هستی. /releasespirit برای ترک انتقام (اگر انتقام‌جو باشی)."
            )
            return
        if not user.is_dead:
            await message.answer("زنده‌ای. این منو فقط بعد از مرگ است.")
            return
        await message.answer(
            "💀 <b>مرگ — انتخاب سرنوشت</b>\n\n"
            "👻 پرورش‌دهنده روح — تذهیب روحی از نو\n"
            "😈 روح انتقام‌جو — در دنیای زیرین با قدرت انتقام\n"
            "🌑 پوچی — حذف دائمی اکانت",
            reply_markup=death_keyboard(),
        )


@router.callback_query(F.data == "death:spirit")
async def cb_spirit(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        msg = await become_spirit_raiser(session, user)
    await callback.message.edit_text(msg)
    await callback.answer()


@router.callback_query(F.data == "death:vengeful")
async def cb_vengeful(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        if not user.is_dead:
            await callback.answer("مرده نیستی", show_alert=True)
            return
        spirit = await become_vengeful(session, user, reason="انتخاب بعد از مرگ")
    await callback.message.edit_text(
        f"😈 روح انتقام‌جو شدی!\n"
        f"قدرت روح: {spirit.power}\n"
        f"دنیا: زیرین\n"
        f"/releasespirit برای رها کردن انتقام"
    )
    await callback.answer()


@router.callback_query(F.data == "death:void")
async def cb_void_confirm(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="بله، پاکم کن", callback_data="death:void_confirm")
    builder.button(text="انصراف", callback_data="death:cancel")
    builder.adjust(1)
    await callback.message.edit_text(
        "⚠️ مطمئنی؟ اکانت برای همیشه حذف می‌شود.",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data == "death:void_confirm")
async def cb_void_do(callback: CallbackQuery):
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        if not user.is_dead:
            await callback.message.edit_text("دیگر مرده نیستی.")
            await callback.answer()
            return
        msg = await erase_existence(session, user)
    await callback.message.edit_text(msg)
    await callback.answer()


@router.callback_query(F.data == "death:cancel")
async def cb_cancel(callback: CallbackQuery):
    await callback.message.edit_text("انصراف. /afterdeath", reply_markup=death_keyboard())
    await callback.answer()


@router.message(Command("releasespirit", "رها‌روح"))
async def cmd_release_spirit(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        msg = await release_spirit(session, user)
    await message.answer(msg)
