from datetime import datetime, date, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from database.engine import async_session
from database.crud import get_or_create_user
from services.economy import get_or_create_wallet
from services.i18n import tr

router = Router()

# in-memory streak store (با دیتابیس پایدار بهتر است؛ فعلاً همراه user.xp)
_streaks: dict[int, dict] = {}


@router.message(Command("daily", "روزانه", "استریک"))
async def cmd_daily_streak(message: Message):
    uid = message.from_user.id
    today = date.today().isoformat()
    info = _streaks.get(uid, {"last": None, "count": 0})
    if info["last"] == today:
        await message.answer(f"امروز جایزه را گرفتی. استریک: {info['count']} روز")
        return
    yesterday = (date.today() - timedelta(days=1)).isoformat()
    if info["last"] == yesterday:
        info["count"] += 1
    else:
        info["count"] = 1
    info["last"] = today
    _streaks[uid] = info
    reward_coins = 30 + info["count"] * 10
    reward_stones = 1 if info["count"] % 7 == 0 else 0
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
        w.coins += reward_coins
        w.spirit_stones += reward_stones
        await session.commit()
        coins = w.coins
    text = (
        f"🔥 ورود روزانه!\n"
        f"استریک: <b>{info['count']}</b> روز\n"
        f"🪙 +{reward_coins} سکه"
    )
    if reward_stones:
        text += f"\n💎 +{reward_stones} سنگ روحی (پاداش ۷ روز)"
    text += f"\nموجودی: {coins}"
    await message.answer(text)


# مزایده ساده
_auctions: list[dict] = []


@router.message(Command("auction", "مزایده"))
async def cmd_auction(message: Message):
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        text = "🏛️ <b>مزایده‌ها</b>\n\n"
        if not _auctions:
            text += "مزایده فعالی نیست.\nساخت: /auction نام‌آیتم قیمت‌شروع"
        else:
            for i, a in enumerate(_auctions):
                text += f"{i+1}. {a['item']} — بالاترین: {a['bid']} سکه (@{a.get('bidder_name','—')})\n"
            text += "\nپیشنهاد: /bid شماره مبلغ"
        await message.answer(text)
        return
    item, try_price = parts[1], parts[2]
    try:
        price = int(try_price)
    except ValueError:
        await message.answer(tr(message.from_user.id, "قیمت باید عدد باشد."))
        return
    if price < 100:
        await message.answer(tr(message.from_user.id, "حداقل شروع مزایده ۱۰۰ سکه."))
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
        # ورود به مزایده: پرداخت ورودی ۱۰٪
        fee = max(50, price // 10)
        if w.coins < fee:
            await message.answer(f"برای ثبت مزایده {fee} سکه ورودی لازم است.")
            return
        w.coins -= fee
        await session.commit()
    _auctions.append({
        "item": item,
        "bid": price,
        "owner": message.from_user.id,
        "bidder": None,
        "bidder_name": None,
        "owner_name": message.from_user.full_name,
    })
    await message.answer(f"مزایده «{item}» با شروع {price} ثبت شد. (ورودی {fee} سکه)")


@router.message(Command("bid", "پیشنهاد"))
async def cmd_bid(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer(tr(message.from_user.id, "فرمت: /bid شماره مبلغ"))
        return
    try:
        idx, amount = int(parts[1]) - 1, int(parts[2])
    except ValueError:
        await message.answer(tr(message.from_user.id, "عدد نامعتبر"))
        return
    if idx < 0 or idx >= len(_auctions):
        await message.answer(tr(message.from_user.id, "مزایده پیدا نشد."))
        return
    a = _auctions[idx]
    if amount <= a["bid"]:
        await message.answer(f"باید بیشتر از {a['bid']} پیشنهاد بدهی.")
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
        if w.coins < amount:
            await message.answer(tr(message.from_user.id, "سکه کافی نیست."))
            return
        w.coins -= amount
        await session.commit()
    a["bid"] = amount
    a["bidder"] = message.from_user.id
    a["bidder_name"] = message.from_user.full_name
    await message.answer(f"پیشنهاد {amount} سکه برای «{a['item']}» ثبت شد.")
