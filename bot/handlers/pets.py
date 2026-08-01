from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from database.engine import async_session
from database.crud import get_or_create_user
from database.models_v3 import Pet
from services.pets import spawn_wild, get_user_pets, tame_pet, buy_domestic
from services.economy import get_or_create_wallet, add_coins, exchange_to_stones, exchange_to_coins, COINS_PER_STONE

router = Router()


@router.message(Command("pets", "حیوانات", "پت"))
async def cmd_pets(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        pets = await get_user_pets(session, user.id)
    
    text = "🐾 <b>حیوانات تو</b>\n\n"
    if not pets:
        text += "حیوانی نداری.\n"
    else:
        for p in pets:
            kind = "خونگی" if not p.is_wild else "وحشی"
            text += f"• {p.name} ({p.species}) — {kind}\n  AT:{p.attack} DEF:{p.defense} وفاداری:{p.loyalty}\n"
    
    text += (
        "\nدستورات:\n"
        "/hunt — شکار حیوان وحشی\n"
        "/buypet — خرید حیوان خونگی (۱۰۰ سکه)\n"
        "/wallet — کیف پول"
    )
    await message.answer(text)


@router.message(Command("hunt", "شکار"))
async def cmd_hunt(message: Message):
    import random
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if user.is_dead:
            await message.answer("مرده‌ای. /afterdeath")
            return
        # خطر شکار
        roll = random.random()
        world = getattr(user, "world", "فانی") or "فانی"
        try:
            from bot.config import HUNT_RISK_NORMAL, HUNT_RISK_UNDERWORLD
            risk = HUNT_RISK_NORMAL if world != "زیرین" else HUNT_RISK_UNDERWORLD
        except Exception:
            risk = 0.45 if world != "زیرین" else 0.85
        if roll < risk * 0.3:
            user.is_dead = True
            user.world = "زیرین"
            await session.commit()
            await message.answer("💀 در شکار کشته شدی و به دنیای زیرین افتادی. /afterdeath")
            return
        if roll < risk:
            dmg = random.randint(5, 15)
            if hasattr(user, "lifespan"):
                user.lifespan = max(0, (user.lifespan or 100) - dmg)
                if user.lifespan <= 0:
                    user.is_dead = True
            await session.commit()
            await message.answer(f"🩸 زخمی شدی! -{dmg} عمر. شکار فرار کرد.")
            return
        pet = await spawn_wild(session)
        
        builder = InlineKeyboardBuilder()
        builder.button(text="رام کردن 🐺", callback_data=f"tame:{message.from_user.id}:{pet.id}")
        builder.button(text="رها کردن", callback_data=f"release:{message.from_user.id}:{pet.id}")
        builder.adjust(2)
        
        await message.answer(
            f"🌲 حیوان وحشی پیدا شد!\n\n"
            f"<b>{pet.species}</b>\n"
            f"حمله: {pet.attack} | دفاع: {pet.defense}\n\n"
            f"می‌خوای رامش کنی؟",
            reply_markup=builder.as_markup()
        )


@router.callback_query(F.data.startswith("tame:"))
async def cb_tame(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) >= 3:
        owner_id, pet_id = int(parts[1]), int(parts[2])
        if callback.from_user.id != owner_id:
            await callback.answer()
            return
    else:
        pet_id = int(parts[1])
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        pet = await session.get(Pet, pet_id)
        if not pet:
            await callback.answer("دیگر اینجا نیست.", show_alert=True)
            return
        msg = await tame_pet(session, user, pet)
    await callback.message.edit_text(msg)
    await callback.answer()


@router.callback_query(F.data.startswith("release:"))
async def cb_release(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) >= 3:
        owner_id, pet_id = int(parts[1]), int(parts[2])
        if callback.from_user.id != owner_id:
            await callback.answer()
            return
    else:
        pet_id = int(parts[1])
    async with async_session() as session:
        pet = await session.get(Pet, pet_id)
        if pet and pet.is_wild:
            await session.delete(pet)
            await session.commit()
    await callback.message.edit_text("حیوان رها شد.")
    await callback.answer()


@router.message(Command("buypet", "خریدپت"))
async def cmd_buy_pet(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        msg = await buy_domestic(session, user, cost_coins=100)
    await message.answer(msg)


@router.message(Command("wallet", "کیف‌پول", "سکه"))
async def cmd_wallet(message: Message):
    from services.economy import get_or_create_wallet, wallet_text
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
        text = wallet_text(w)
    await message.answer(text)


@router.message(Command("exchangestone"))
async def cmd_ex_stone(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        msg = await exchange_to_stones(session, user.id, 1)
    await message.answer(msg)


@router.message(Command("exchangecoin"))
async def cmd_ex_coin(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        msg = await exchange_to_coins(session, user.id, 1)
    await message.answer(msg)


@router.message(Command("dailycoin", "سکهروزانه"))
async def cmd_daily_coin(message: Message):
    """پاداش روزانه سکه — فقط یک‌بار در هر روز"""
    from datetime import datetime, date
    from services.economy import get_or_create_wallet
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
        today = date.today()
        last = w.last_daily_coin
        if last is not None and last.date() == today:
            await message.answer(
                "امروز سکه روزانه را گرفتی.\n"
                "فردا دوباره /dailycoin بزن."
            )
            return
        w.coins += 30
        w.last_daily_coin = datetime.utcnow()
        await session.commit()
        total = w.coins
    await message.answer(f"🪙 +۳۰ سکه روزانه!\nموجودی: {total}")


@router.message(Command("sellpet", "فروش‌حیوان"))
async def cmd_sell_pet(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("فرمت: /sellpet شماره\nلیست را با /pets ببین (شماره از ۱)")
        return
    try:
        idx = int(parts[1]) - 1
    except ValueError:
        await message.answer("شماره نامعتبر")
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        pets = await get_user_pets(session, user.id)
        if idx < 0 or idx >= len(pets):
            await message.answer("حیوان پیدا نشد.")
            return
        pet = pets[idx]
        price = 50 + pet.attack * 5 + pet.defense * 3
        from services.economy import get_or_create_wallet
        w = await get_or_create_wallet(session, user.id)
        w.coins += price
        await session.delete(pet)
        await session.commit()
    await message.answer(f"فروخته شد! +{price} سکه")


@router.message(Command("giftpet", "هدیه‌حیوان"))
async def cmd_gift_pet(message: Message):
    if not message.reply_to_message:
        await message.answer("روی پیام گیرنده ریپلای کن:\n/giftpet شماره")
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("فرمت: /giftpet شماره")
        return
    try:
        idx = int(parts[1]) - 1
    except ValueError:
        await message.answer("شماره نامعتبر")
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        target = await get_or_create_user(
            session, message.reply_to_message.from_user.id,
            message.reply_to_message.from_user.full_name,
            message.reply_to_message.from_user.username
        )
        pets = await get_user_pets(session, user.id)
        if idx < 0 or idx >= len(pets):
            await message.answer("حیوان پیدا نشد.")
            return
        pet = pets[idx]
        pet.owner_id = target.id
        await session.commit()
    await message.answer(f"🎁 {pet.name} به {target.full_name} هدیه شد.")


@router.message(Command("exchangeup", "ارتقای‌ارز"))
async def cmd_exchange_up(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("فرمت: /exchangeup heavenly|celestial|god [تعداد]")
        return
    kind = parts[1]
    amount = int(parts[2]) if len(parts) > 2 else 1
    from services.economy import exchange_up
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        msg = await exchange_up(session, user.id, kind, amount)
    await message.answer(msg)
