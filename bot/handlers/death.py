from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user
from services.death import become_spirit_raiser, erase_existence

router = Router()


def death_keyboard():
    builder = InlineKeyboardBuilder()
    builder.button(text="👻 پرورش‌دهنده روح شو", callback_data="death:spirit")
    builder.button(text="🌑 وجودم به پوچی برگردد (حذف دائمی)", callback_data="death:void")
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
            await message.answer("تو هم‌اکنون پرورش‌دهنده روح هستی.")
            return

        if not user.is_dead:
            await message.answer("تو زنده هستی. این منو فقط بعد از مرگ فعال می‌شود.")
            return

        await message.answer(
            "💀 <b>مرگ</b>\n\n"
            "بدن فیزیکی‌ات از بین رفته. یکی را انتخاب کن:\n\n"
            "👻 <b>پرورش‌دهنده روح</b>\n"
            "دوباره به عنوان موجود روحی به وجود می‌آیی و تذهیب روح را از نو شروع می‌کنی.\n\n"
            "🌑 <b>بازگشت به پوچی</b>\n"
            "وجودت برای همیشه پاک می‌شود و این اکانت حذف می‌گردد.\n"
            "این کار برگشت‌ناپذیر است.",
            reply_markup=death_keyboard()
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


@router.callback_query(F.data == "death:void")
async def cb_void_confirm(callback: CallbackQuery):
    builder = InlineKeyboardBuilder()
    builder.button(text="بله، پاکم کن برای همیشه", callback_data="death:void_confirm")
    builder.button(text="انصراف", callback_data="death:cancel")
    builder.adjust(1)
    await callback.message.edit_text(
        "⚠️ مطمئنی؟\n"
        "با تأیید، تمام پیشرفت، فرقه، ازدواج، آیتم‌ها و این اکانت <b>برای همیشه حذف</b> می‌شود.",
        reply_markup=builder.as_markup()
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
            await callback.message.edit_text("دیگر مرده حساب نمی‌شوی.")
            await callback.answer()
            return
        msg = await erase_existence(session, user)
    await callback.message.edit_text(msg)
    await callback.answer()


@router.callback_query(F.data == "death:cancel")
async def cb_cancel(callback: CallbackQuery):
    await callback.message.edit_text(
        "انصراف دادی. هنوز می‌توانی با /afterdeath انتخاب کنی.",
        reply_markup=death_keyboard()
    )
    await callback.answer()
