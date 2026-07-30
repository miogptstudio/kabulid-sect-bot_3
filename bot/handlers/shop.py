from aiogram import Router, F
from sqlalchemy import select
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user
from services.shop import (
    ensure_default_buildings_and_items,
    get_buildings,
    get_items_of_building,
    buy_item
)
from database.models_v3 import ShopItem

router = Router()


@router.message(Command("buildings", "ساختمون", "shop", "فروشگاه"))
async def cmd_buildings(message: Message):
    async with async_session() as session:
        await ensure_default_buildings_and_items(session)
        buildings = await get_buildings(session)
    
    if not buildings:
        await message.answer("هنوز ساختمونی وجود نداره.")
        return
    
    builder = InlineKeyboardBuilder()
    text = "🏘️ <b>ساختمان‌های موجود</b>\n\n"
    for b in buildings:
        text += f"• {b.name}\n"
        builder.button(text=b.name, callback_data=f"building:{b.id}")
    builder.adjust(1)
    
    text += "\nروی ساختمان مورد نظر کلیک کن تا آیتم‌هاش رو ببینی."
    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("building:"))
async def show_building_items(callback: CallbackQuery):
    building_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        items = await get_items_of_building(session, building_id)
    
    if not items:
        await callback.answer("آیتمی در این ساختمان نیست.", show_alert=True)
        return
    
    builder = InlineKeyboardBuilder()
    text = "🛒 <b>آیتم‌های موجود</b>\n\n"
    for item in items:
        text += (
            f"• <b>{item.name}</b>\n"
            f"  {item.description or ''}\n"
            f"  قیمت: {item.price} XP\n\n"
        )
        builder.button(text=f"خرید {item.name}", callback_data=f"buy:{item.id}")
    builder.adjust(1)
    
    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("buy:"))
async def process_buy(callback: CallbackQuery):
    item_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        item = await session.get(ShopItem, item_id)
        if not item:
            await callback.answer("آیتم پیدا نشد.", show_alert=True)
            return
        
        msg = await buy_item(session, user, item)
    
    await callback.answer(msg, show_alert=True)


@router.message(Command("inventory", "اینونتوری", "کیف", "items"))
async def cmd_inventory(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        from database.models_v3 import UserInventory, ShopItem
        result = await session.execute(
            select(UserInventory, ShopItem)
            .join(ShopItem, UserInventory.item_id == ShopItem.id)
            .where(UserInventory.user_id == user.id)
        )
        rows = result.all()
    
    if not rows:
        await message.answer("کیفت خالیه. از /buildings خرید کن.")
        return
    
    text = "🎒 <b>کیف / اینونتوری تو</b>\n\n"
    type_emoji = {
        "pill": "💊",
        "talisman": "📜",
        "material": "🧪",
        "herb_normal": "🌿",
        "herb_spiritual": "✨",
        "weapon": "⚔️",
    }
    for inv, item in rows:
        emoji = type_emoji.get(item.item_type, "📦")
        text += f"{emoji} {item.name} ×{inv.quantity}\n"
    
    await message.answer(text)
