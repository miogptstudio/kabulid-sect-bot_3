from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from database.engine import async_session
from database.crud import get_or_create_user
from database.models_v3 import Recipe
from services.crafting import ensure_default_recipes, craft, get_or_create_skill

router = Router()


@router.message(Command("craft", "ساخت", "کیمیاگری", "طلسم"))
async def cmd_craft(message: Message):
    async with async_session() as session:
        await ensure_default_recipes(session)
        result = await session.execute(select(Recipe).where(Recipe.is_active == True))
        recipes = result.scalars().all()
        
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
    
    if not recipes:
        await message.answer("هنوز دستوری برای ساخت وجود نداره.")
        return
    
    builder = InlineKeyboardBuilder()
    text = "⚗️ <b>ساخت معجون و طلسم</b>\n\n"
    
    for r in recipes:
        mats = ", ".join([f"{k}×{v}" for k, v in r.required_materials.items()])
        text += (
            f"• <b>{r.name}</b> ({r.recipe_type})\n"
            f"  مواد: {mats}\n"
            f"  شانس: {r.success_rate}% | نیاز قلمرو: {r.min_cultivation_realm}\n\n"
        )
        builder.button(text=f"ساخت {r.name}", callback_data=f"craft:{r.id}")
    
    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("craft:"))
async def process_craft(callback: CallbackQuery):
    recipe_id = int(callback.data.split(":")[1])
    
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        recipe = await session.get(Recipe, recipe_id)
        if not recipe:
            await callback.answer("دستور پیدا نشد.", show_alert=True)
            return
        
        result = await craft(session, user, recipe)
    
    await callback.answer(result["message"], show_alert=True)
    
    if result["success"]:
        try:
            await callback.message.answer(result["message"])
        except Exception:
            pass
