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
    if _card:
        try:
            from services.portraits import character_url
            await message.answer_photo(
                photo=character_url(_card.get("name", "?"), _card.get("rarity", "معمولی")),
                caption=msg,
            )
        except Exception:
            await message.answer(msg)
    else:
        await message.answer(msg)


@router.message(Command("mychars", "کاراکترها", "لیست‌کاراکتر"))
async def cmd_list(message: Message):
    await message.answer(chars.list_chars(message.from_user.id))


@router.message(Command("bestchar", "بهترین‌کاراکتر"))
async def cmd_best(message: Message):
    await message.answer(chars.best_char(message.from_user.id))



@router.message(Command("mychars", "کاراکترها", "لیست‌کاراکتر"))
async def cmd_mychars(message: Message):
    await message.answer(chars.list_owned_indexed(message.from_user.id))


@router.message(Command("tradechar", "معاوضه‌کاراکتر"))
async def cmd_trade_char(message: Message):
    parts = (message.text or "").split()
    # /tradechar target_tg idx_me idx_them  OR reply + idx_me idx_them
    target = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.id
        if len(parts) < 3:
            await message.answer("ریپلای + /tradechar شماره_من شماره_او")
            return
        idx_a, idx_b = int(parts[1]), int(parts[2])
    else:
        if len(parts) < 4:
            await message.answer("فرمت: /tradechar آیدی_عددی شماره_من شماره_او\nیا ریپلای + /tradechar شماره_من شماره_او")
            return
        target, idx_a, idx_b = int(parts[1]), int(parts[2]), int(parts[3])
    ok, msg, key = chars.propose_trade(message.from_user.id, target, idx_a, idx_b)
    await message.answer(msg)


@router.message(Command("accepttrade", "قبول‌معاوضه"))
async def cmd_accept_trade(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("/accepttrade کلید")
        return
    await message.answer(chars.accept_trade(parts[1].strip(), message.from_user.id))


@router.message(Command("charduel", "دوئل‌کاراکتر"))
async def cmd_char_duel(message: Message):
    parts = (message.text or "").split()
    target = None
    if message.reply_to_message and message.reply_to_message.from_user:
        target = message.reply_to_message.from_user.id
        if len(parts) < 3:
            await message.answer("ریپلای + /charduel شماره_من شماره_او")
            return
        idx_a, idx_b = int(parts[1]), int(parts[2])
    else:
        if len(parts) < 4:
            await message.answer("فرمت: /charduel آیدی شماره_من شماره_او")
            return
        target, idx_a, idx_b = int(parts[1]), int(parts[2]), int(parts[3])
    ok, msg, key = chars.propose_char_duel(message.from_user.id, target, idx_a, idx_b)
    await message.answer(msg)


@router.message(Command("acceptcharduel", "قبول‌دوئل‌کاراکتر"))
async def cmd_accept_cduel(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("/acceptcharduel کلید")
        return
    await message.answer(chars.accept_char_duel(parts[1].strip(), message.from_user.id))


@router.message(Command("mergechar", "ترکیب‌کاراکتر", "ادغام‌کاراکتر"))
async def cmd_merge_char(message: Message):
    await message.answer(chars.merge_duplicates(message.from_user.id))
