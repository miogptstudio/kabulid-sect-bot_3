"""روح رزمی"""
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services import martial_spirit as ms
from services.i18n import t_user, tr

router = Router()


@router.message(Command("spirit", "روح‌رزمی", "martialspirit"))
async def cmd_spirit(message: Message):
    await message.answer(ms.status_text(message.from_user.id))


@router.message(Command("awaken", "بیدار‌روح", "بیدارسازی"))
async def cmd_awaken(message: Message):
    builder = InlineKeyboardBuilder()
    for name in list(ms.SPIRIT_TYPES.keys())[:8]:
        builder.button(text=name, callback_data=f"awaken:{message.from_user.id}:{name}")
    builder.button(text="🎲 تصادفی", callback_data=f"awaken:{message.from_user.id}:random")
    builder.adjust(2)
    await message.answer(
        t_user(message.from_user.id, "spirit_awaken_pick"),
        reply_markup=builder.as_markup(),
    )


from aiogram import F
from aiogram.types import CallbackQuery


@router.callback_query(F.data.startswith("awaken:"))
async def cb_awaken(callback: CallbackQuery):
    parts = callback.data.split(":")
    owner, choice = int(parts[1]), parts[2]
    if callback.from_user.id != owner:
        await callback.answer()
        return
    preferred = None if choice == "random" else choice
    ok, msg = ms.awaken(owner, preferred)
    await callback.message.edit_text(msg)
    await callback.answer()


@router.message(Command("trainspirit", "تمرین‌روح", "روح‌تمرین"))
async def cmd_train_spirit(message: Message):
    await message.answer(ms.train(message.from_user.id))


@router.message(Command("spiritmode", "حالت‌روح"))
async def cmd_spirit_mode(message: Message):
    await message.answer(ms.toggle(message.from_user.id))
