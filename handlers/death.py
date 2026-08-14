from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user
from services.death import become_spirit_raiser, erase_existence
from services.dimension import become_vengeful, release_spirit
from services.i18n import tr

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
            await message.answer(tr(message.from_user.id, "روح هستی. /releasespirit برای ترک انتقام (اگر انتقام‌جو باشی)."))
            return
        if not user.is_dead:
            await message.answer(tr(message.from_user.id, "زنده‌ای. این منو فقط بعد از مرگ است."))
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
            await callback.answer(tr(callback.from_user.id, "مرده نیستی"), show_alert=True)
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
            await callback.message.edit_text(tr(callback.from_user.id, "دیگر مرده نیستی."))
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


# تسخیر بدن — فقط پرورش‌دهنده روح، یک‌بار
_possessed_once: set[int] = set()  # telegram ids that already possessed


@router.message(Command("possess", "تسخیر"))
async def cmd_possess(message: Message):
    if not message.reply_to_message:
        await message.answer(
            "👻 تسخیر بدن:\n"
            "فقط پرورش‌دهنده روح · فقط یک‌بار در عمر\n"
            "روی پیام هدف ریپلای کن و /possess بزن.\n"
            "هدف باید زنده باشد."
        )
        return
    async with async_session() as session:
        spirit = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if not getattr(spirit, "is_spirit_raiser", False):
            await message.answer(tr(message.from_user.id, "فقط پرورش‌دهنده روح می‌تواند تسخیر کند."))
            return
        if message.from_user.id in _possessed_once:
            await message.answer(tr(message.from_user.id, "قبلاً یک‌بار تسخیر کرده‌ای. دیگر ممکن نیست."))
            return
        tu = message.reply_to_message.from_user
        if tu.id == message.from_user.id:
            await message.answer(tr(message.from_user.id, "خودت را نه."))
            return
        target = await get_or_create_user(
            session, tu.id, tu.full_name, tu.username
        )
        if target.is_dead:
            await message.answer(tr(message.from_user.id, "هدف مرده است."))
            return
        # تسخیر: روح وارد بدن می‌شود — روح زنده می‌شود روی هویت هدف؟ ساده: انرژی و سطح از هدف می‌گیرد و هدف موقتاً ضعیف
        from services.cultivation import get_or_create_cultivation
        sc = await get_or_create_cultivation(session, spirit.id)
        tc = await get_or_create_cultivation(session, target.id)
        # روح انرژی هدف را می‌دزدد و زنده می‌شود
        steal = max(100, tc.energy // 2)
        sc.energy += steal
        tc.energy = max(0, tc.energy - steal)
        spirit.is_dead = False
        spirit.is_spirit_raiser = True  # هنوز روح‌گونه
        if not sc.spiritual_root or sc.spiritual_root == "بدون ریشه":
            sc.spiritual_root = "ریشه روح"
        _possessed_once.add(message.from_user.id)
        await session.commit()
    await message.answer(
        f"👻 تسخیر موفق!\n"
        f"بدن {target.full_name} را تسخیر کردی.\n"
        f"+{steal} انرژی از او گرفتی.\n"
        f"⚠️ این تنها تسخیر مجاز تو بود."
    )


@router.message(Command("suicide", "خودکشی", "انتحار"))
async def cmd_suicide(message: Message):
    """خودکشی درون‌بازی — مرگ کاراکتر و رفتن به منوی بعد از مرگ"""
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if user.is_dead:
            await message.answer(
                "💀 همین حالا مرده‌ای." + chr(10) + "سرنوشتت را انتخاب کن: /afterdeath"
            )
            return
        if getattr(user, "is_spirit_raiser", False):
            await message.answer("روح هستی؛ خودکشی معنا ندارد. /releasespirit")
            return
    builder = InlineKeyboardBuilder()
    builder.button(text="تأیید خودکشی ☠️", callback_data=f"suicide:yes:{message.from_user.id}")
    builder.button(text="انصراف", callback_data=f"suicide:no:{message.from_user.id}")
    builder.adjust(1)
    await message.answer(
        "☠️ <b>خودکشی (درون‌بازی)</b>" + chr(10) + chr(10)
        + "کاراکترت می‌میرد و به منوی بعد از مرگ می‌روی." + chr(10)
        + "می‌توانی پرورش‌دهنده روح، روح انتقام‌جو یا پوچی (حذف) را انتخاب کنی." + chr(10) + chr(10)
        + "این عمل فقط روی <b>کاراکتر بازی</b> است." + chr(10)
        + "مطمئنی؟",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("suicide:"))
async def cb_suicide(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer()
        return
    action, owner = parts[1], int(parts[2])
    if callback.from_user.id != owner:
        await callback.answer()
        return
    if action == "no":
        await callback.message.edit_text("انصراف از خودکشی.")
        await callback.answer()
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        if user.is_dead:
            await callback.message.edit_text("قبلاً مرده‌ای. /afterdeath")
            await callback.answer()
            return
        user.is_dead = True
        if hasattr(user, "blood"):
            user.blood = 0
        if hasattr(user, "restriction_reason"):
            # خروج از تمرین/قفل‌های سبک
            if user.restriction_reason == "تمرین":
                user.restriction_reason = None
                user.restricted_until = None
        await session.commit()
    await callback.message.edit_text(
        "☠️ خودکشی انجام شد. کاراکتر مرد." + chr(10) + chr(10)
        + "حالا سرنوشتت را انتخاب کن:" + chr(10)
        + "/afterdeath" + chr(10) + chr(10)
        + "👻 پرورش‌دهنده روح" + chr(10)
        + "😈 روح انتقام‌جو" + chr(10)
        + "🌑 پوچی (حذف دائمی اکانت)",
        reply_markup=death_keyboard(),
    )
    await callback.answer()

