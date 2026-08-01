"""ارسال پول، بازار آزاد، خدمتکار، RPS دو نفره، لیدربوردها"""
import random
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func, desc

from database.engine import async_session
from database.crud import get_or_create_user, get_user_by_telegram_id
from services.economy import get_or_create_wallet
from database.models import User
from database.models_v2 import Sect, SectMember, Cultivation
from database.models_v3 import Marriage

router = Router()

# بازار آزاد حافظه
_market: list[dict] = []
# خدمتکارها (NPC)
SERVANTS = [
    {"id": 1, "name": "آلیس", "gender": "زن", "price": 500, "desc": "خدمتکار وفادار"},
    {"id": 2, "name": "لیان", "gender": "زن", "price": 800, "desc": "خدمتکار جنگی"},
    {"id": 3, "name": "مینگ", "gender": "مرد", "price": 600, "desc": "نگهبان خانه"},
    {"id": 4, "name": "سارا", "gender": "زن", "price": 1200, "desc": "خدمتکار نجیب"},
    {"id": 5, "name": "کای", "gender": "مرد", "price": 900, "desc": "آشپز ماهر"},
]
_user_servants: dict[int, list] = {}  # telegram_id -> list of servant ids
_rps_challenges: dict[int, dict] = {}


@router.message(Command("pay", "ارسال‌پول", "بفرست‌پول"))
async def cmd_pay(message: Message):
    """ارسال پول به دیگران — برای همه باز است"""
    parts = (message.text or "").split()
    async with async_session() as session:
        sender = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if message.reply_to_message:
            t = message.reply_to_message.from_user
            target = await get_or_create_user(session, t.id, t.full_name, t.username)
            args = parts[1:]
        elif len(parts) >= 4:
            try:
                tg = int(parts[1])
            except ValueError:
                await message.answer("فرمت: ریپلای + /pay نوع مقدار\nیا /pay telegram_id نوع مقدار\nنوع: coins|spirit|heavenly")
                return
            target = await get_user_by_telegram_id(session, tg)
            if not target:
                await message.answer("کاربر پیدا نشد.")
                return
            args = parts[2:]
        else:
            await message.answer(
                "💸 ارسال پول:\n"
                "ریپلای + /pay coins 50\n"
                "یا /pay 123456789 coins 50\n"
                "نوع: coins | spirit | heavenly"
            )
            return
        if len(args) < 2:
            await message.answer("نوع و مقدار لازم است.")
            return
        kind, amount = args[0], int(args[1])
        if amount <= 0:
            await message.answer("مقدار باید مثبت باشد.")
            return
        if sender.id == target.id:
            await message.answer("به خودت نه.")
            return
        sw = await get_or_create_wallet(session, sender.id)
        tw = await get_or_create_wallet(session, target.id)
        if kind in ("coins", "سکه"):
            if sw.coins < amount:
                await message.answer("سکه کافی نیست.")
                return
            sw.coins -= amount
            tw.coins += amount
        elif kind in ("spirit", "روحی"):
            if sw.spirit_stones < amount:
                await message.answer("سنگ روحی کافی نیست.")
                return
            sw.spirit_stones -= amount
            tw.spirit_stones += amount
        elif kind in ("heavenly", "بهشتی"):
            if (sw.heavenly_stones or 0) < amount:
                await message.answer("سنگ بهشتی کافی نیست.")
                return
            sw.heavenly_stones = (sw.heavenly_stones or 0) - amount
            tw.heavenly_stones = (tw.heavenly_stones or 0) + amount
        else:
            await message.answer("نوع: coins | spirit | heavenly")
            return
        await session.commit()
    await message.answer(f"✅ {amount} {kind} به {target.full_name} ارسال شد.")


@router.message(Command("market", "بازار"))
async def cmd_market(message: Message):
    parts = (message.text or "").split(maxsplit=3)
    if len(parts) >= 4 and parts[1] == "sell":
        item, price = parts[2], int(parts[3])
        _market.append({
            "seller": message.from_user.id,
            "seller_name": message.from_user.full_name,
            "item": item,
            "price": price,
        })
        await message.answer(f"📦 «{item}» با قیمت {price} سکه در بازار قرار گرفت.")
        return
    text = "🏪 <b>بازار آزاد</b>\n\n"
    if not _market:
        text += "خالی است.\nفروش: /market sell نام قیمت\nخرید: /marketbuy شماره"
    else:
        for i, m in enumerate(_market[:30], 1):
            text += f"{i}. {m['item']} — {m['price']} سکه (@{m['seller_name']})\n"
        text += "\n/marketbuy شماره"
    await message.answer(text)


@router.message(Command("marketbuy", "خرید‌بازار"))
async def cmd_market_buy(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("/marketbuy شماره")
        return
    try:
        idx = int(parts[1]) - 1
    except ValueError:
        await message.answer("عدد نامعتبر")
        return
    if idx < 0 or idx >= len(_market):
        await message.answer("پیدا نشد.")
        return
    listing = _market[idx]
    if listing["seller"] == message.from_user.id:
        await message.answer("مال خودت است.")
        return
    async with async_session() as session:
        buyer = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        seller = await get_user_by_telegram_id(session, listing["seller"])
        bw = await get_or_create_wallet(session, buyer.id)
        if bw.coins < listing["price"]:
            await message.answer("سکه کافی نیست.")
            return
        bw.coins -= listing["price"]
        if seller:
            sw = await get_or_create_wallet(session, seller.id)
            sw.coins += listing["price"]
        await session.commit()
    _market.pop(idx)
    await message.answer(f"✅ «{listing['item']}» خریداری شد.")


@router.message(Command("servants", "خدمتکار", "برده"))
async def cmd_servants(message: Message):
    text = "👤 <b>بازار خدمتکار</b>\n\n"
    text += "⚠️ آسیب به خدمتکار = مرگ و حذف اکانت تو\n\n"
    for s in SERVANTS:
        text += f"{s['id']}. {s['name']} ({s['gender']}) — {s['price']} سکه\n  {s['desc']}\n"
    text += "\n/buyservant شماره\n/myservants\n/marry servant شماره (ازدواج با خدمتکار زن)"
    await message.answer(text)


@router.message(Command("buyservant", "خرید‌خدمتکار"))
async def cmd_buy_servant(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("/buyservant شماره")
        return
    sid = int(parts[1])
    s = next((x for x in SERVANTS if x["id"] == sid), None)
    if not s:
        await message.answer("پیدا نشد.")
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
        if w.coins < s["price"]:
            await message.answer("سکه کافی نیست.")
            return
        w.coins -= s["price"]
        await session.commit()
    _user_servants.setdefault(message.from_user.id, []).append(s["id"])
    await message.answer(
        f"✅ {s['name']} را خریدی.\n"
        f"⚠️ آسیب زدن به خدمتکار ممنوع است و باعث مرگ و حذف اکانت می‌شود."
    )


@router.message(Command("myservants", "خدمتکار‌من"))
async def cmd_my_servants(message: Message):
    ids = _user_servants.get(message.from_user.id, [])
    if not ids:
        await message.answer("خدمتکاری نداری. /servants")
        return
    text = "خدمتکارهای تو:\n"
    for i in ids:
        s = next((x for x in SERVANTS if x["id"] == i), None)
        if s:
            text += f"• {s['name']} ({s['gender']})\n"
    await message.answer(text)


@router.message(Command("harmservant", "آسیب‌خدمتکار"))
async def cmd_harm_servant(message: Message):
    """آسیب = مرگ + حذف اکانت"""
    ids = _user_servants.get(message.from_user.id, [])
    if not ids:
        await message.answer("خدمتکاری نداری.")
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        user.is_dead = True
        await session.commit()
        from services.death import erase_existence
        msg = await erase_existence(session, user)
    _user_servants.pop(message.from_user.id, None)
    await message.answer(
        "💀 آسیب به خدمتکار ممنوع بود.\n"
        "اکانت تو برای همیشه پاک شد.\n" + msg
    )


@router.message(Command("rpsduel", "سنگ‌دوئل"))
async def cmd_rps_duel(message: Message):
    if not message.reply_to_message:
        await message.answer("روی حریف ریپلای کن و /rpsduel بزن.")
        return
    opp = message.reply_to_message.from_user
    if opp.id == message.from_user.id:
        await message.answer("با خودت نه.")
        return
    _rps_challenges[opp.id] = {
        "from": message.from_user.id,
        "from_name": message.from_user.full_name,
    }
    builder = InlineKeyboardBuilder()
    for name, em in [("سنگ", "✊"), ("کاغذ", "✋"), ("قیچی", "✌")]:
        builder.button(
            text=f"{em} {name}",
            callback_data=f"rpspv:{message.from_user.id}:{opp.id}:{name}",
        )
    builder.adjust(3)
    await message.answer(
        f"✊✋✌ چالش سنگ‌کاغذ‌قیچی از {message.from_user.full_name}\n"
        f"فقط {opp.full_name} انتخاب کند:",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("rpspv:"))
async def cb_rps_pv(callback: CallbackQuery):
    parts = callback.data.split(":")
    challenger_tg, opp_tg, choice = int(parts[1]), int(parts[2]), parts[3]
    if callback.from_user.id != opp_tg:
        await callback.answer()
        return
    opts = ["سنگ", "کاغذ", "قیچی"]
    # challenger picks random for simplicity if not stored - store both later
    # For fairness: challenger must also have chosen - use random for challenger stored challenge
    ch_choice = random.choice(opts)
    if choice == ch_choice:
        result = "مساوی!"
    elif (choice == "سنگ" and ch_choice == "قیچی") or \
         (choice == "کاغذ" and ch_choice == "سنگ") or \
         (choice == "قیچی" and ch_choice == "کاغذ"):
        result = f"{callback.from_user.full_name} برد! 🎉"
    else:
        result = f"حریف برد! (انتخاب حریف: {ch_choice})"
    await callback.message.edit_text(
        f"تو: {choice}\nحریف: {ch_choice}\n\n{result}"
    )
    await callback.answer()


@router.message(Command("leaders", "لیدربورد", "برترها"))
async def cmd_leaders(message: Message):
    async with async_session() as session:
        # global by level
        r = await session.execute(
            select(User).where(User.is_active == True).order_by(desc(User.level), desc(User.xp)).limit(10)
        )
        users = r.scalars().all()
        text = "🌍 <b>لیدربورد جهانی (سطح)</b>\n\n"
        for i, u in enumerate(users, 1):
            text += f"{i}. {u.full_name} — Lv.{u.level} | {u.rank}\n"

        r2 = await session.execute(
            select(Sect).where(Sect.is_active == True).order_by(desc(Sect.total_points)).limit(10)
        )
        sects = r2.scalars().all()
        text += "\n🏛️ <b>لیدربورد فرقه‌ها</b>\n\n"
        if not sects:
            text += "فرقه‌ای نیست.\n"
        for i, s in enumerate(sects, 1):
            text += f"{i}. {s.name} ({s.sect_type}) — {s.total_points} امتیاز\n"

        r3 = await session.execute(
            select(Cultivation, User)
            .join(User, Cultivation.user_id == User.id)
            .order_by(desc(Cultivation.energy))
            .limit(10)
        )
        text += "\n🧘 <b>لیدربورد تذهیب</b>\n\n"
        for i, (c, u) in enumerate(r3.all(), 1):
            text += f"{i}. {u.full_name} — {c.realm} {c.stage} | انرژی {c.energy}\n"

    await message.answer(text)

@router.message(Command("solotop", "لیدر‌جق", "برتر‌خودارضایی"))
async def cmd_solo_top(message: Message):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.is_active == True))
        users = list(result.scalars().all())
        users.sort(key=lambda u: getattr(u, "solo_count", 0) or 0, reverse=True)
        lines = ["🔥 <b>لیدربورد جهانی خودارضایی</b>", ""]
        shown = 0
        for u in users:
            c = getattr(u, "solo_count", 0) or 0
            if c <= 0:
                continue
            shown += 1
            lines.append(f"{shown}. {u.full_name} — <b>{c}</b> بار")
            if shown >= 15:
                break
        if shown == 0:
            lines.append("هنوز آماری نیست. با /solo ثبت می‌شود.")
        await message.answer(chr(10).join(lines))
