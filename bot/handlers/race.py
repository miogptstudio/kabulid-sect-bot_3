from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user
from services.cultivation import RACES, RACE_CULT

router = Router()


@router.message(Command("race", "نژاد", "نژادها"))
async def cmd_race(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        current = getattr(user, "race", None) or "انسان"
        if current != "انسان" and current in RACES:
            info = RACE_CULT.get(current, {})
            await message.answer(
                f"نژاد فعلی: <b>{current}</b>" + chr(10)
                + f"سبک تذهیب: {info.get('style')}" + chr(10)
                + f"{info.get('desc')}" + chr(10)
                + f"ضریب: ×{info.get('bonus')}" + chr(10) + chr(10)
                + "نژاد فقط یک‌بار قابل انتخاب است."
            )
            return
    builder = InlineKeyboardBuilder()
    for r in RACES:
        info = RACE_CULT.get(r, {})
        builder.button(
            text=f"{r} (×{info.get('bonus', 1)})",
            callback_data=f"setrace:{message.from_user.id}:{r}"
        )
    builder.adjust(2)
    text = "🧬 <b>انتخاب نژاد</b> (یک‌بار)" + chr(10) + chr(10)
    for r in RACES:
        info = RACE_CULT[r]
        text += f"• <b>{r}</b>: {info['style']} — {info['desc']}" + chr(10)
    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("setrace:"))
async def cb_set_race(callback: CallbackQuery):
    parts = callback.data.split(":")
    owner, race = int(parts[1]), parts[2]
    if callback.from_user.id != owner:
        await callback.answer()
        return
    if race not in RACES:
        await callback.answer()
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        cur = getattr(user, "race", None) or "انسان"
        if cur != "انسان" and cur in RACES:
            await callback.answer("نژاد قبلاً انتخاب شده", show_alert=True)
            return
        user.race = race
        await session.commit()
        info = RACE_CULT[race]
    await callback.message.edit_text(
        f"✅ نژاد «<b>{race}</b>» ثبت شد." + chr(10)
        + f"سبک: {info['style']}" + chr(10)
        + f"{info['desc']}" + chr(10)
        + f"ضریب تذهیب: ×{info['bonus']}"
    )
    await callback.answer()
