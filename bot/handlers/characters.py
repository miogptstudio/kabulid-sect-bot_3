"""هندلر کاراکتر شانسی"""
from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from database.engine import async_session
from database.crud import get_or_create_user
from services.economy import get_or_create_wallet
from services import characters as chars
from services.i18n import tr

router = Router()


@router.message(Command("charrates", "رتبه‌کاراکتر", "charinfo"))
async def cmd_rates(message: Message):
    await message.answer(chars.rarity_guide())


@router.message(Command("pullchar", "کاراکتر", "کاراکترشانسی", "gacha", "شانسی"))
async def cmd_pull(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username,
        )
        w = await get_or_create_wallet(session, user.id)
        cost = chars.PULL_COST_COINS
        if (w.coins or 0) < cost:
            await message.answer(f"سکه کافی نیست (نیاز {cost}). /dailycoin یا دوئل")
            return
        ok, msg, _card = chars.pull(message.from_user.id)
        if not ok:
            await message.answer(msg)
            return
        w.coins -= cost
        await session.commit()
    await message.answer(msg)


@router.message(Command("mychars", "کاراکترها", "لیست‌کاراکتر"))
async def cmd_list(message: Message):
    await message.answer(chars.list_chars(message.from_user.id))


@router.message(Command("bestchar", "بهترین‌کاراکتر"))
async def cmd_best(message: Message):
    await message.answer(chars.best_char(message.from_user.id))
