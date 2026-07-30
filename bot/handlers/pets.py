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
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        pet = await spawn_wild(session)
        
        builder = InlineKeyboardBuilder()
        builder.button(text="رام کردن 🐺", callback_data=f"tame:{pet.id}")
        builder.button(text="رها کردن", callback_data=f"release:{pet.id}")
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
    pet_id = int(callback.data.split(":")[1])
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
    pet_id = int(callback.data.split(":")[1])
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
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
    
    await message.answer(
        f"💰 <b>کیف پول</b>\n\n"
        f"🪙 سکه: {w.coins}\n"
        f"💎 سنگ روحی: {w.spirit_stones}\n\n"
        f"نرخ: {COINS_PER_STONE} سکه = ۱ سنگ روحی\n\n"
        f"/exchangestone — تبدیل سکه به سنگ\n"
        f"/exchangecoin — تبدیل سنگ به سکه\n"
        f"(فروشگاه‌های خارج فرقه با سکه کار می‌کنند)"
    )


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
    """پاداش ساده روزانه سکه"""
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        total = await add_coins(session, user.id, 30)
    await message.answer(f"🪙 +۳۰ سکه روزانه!\nموجودی: {total}")
