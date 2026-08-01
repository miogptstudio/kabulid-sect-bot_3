from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user
from services.shop import (
    ensure_default_buildings_and_items,
    get_buildings,
    get_items_of_building,
    buy_item,
)
from database.models_v3 import ShopItem, Building
from bot.utils.panels import ensure_owner, parse_owner_data

router = Router()


@router.message(Command("buildings", "ساختمون", "shop", "فروشگاه", "مغازه"))
async def cmd_buildings(message: Message):
    uid = message.from_user.id
    async with async_session() as session:
        await ensure_default_buildings_and_items(session)
        buildings = await get_buildings(session)

    if not buildings:
        await message.answer("هنوز ساختمونی وجود نداره.")
        return

    builder = InlineKeyboardBuilder()
    text = (
        "🏘️ <b>مغازه / ساختمان‌ها</b>\n"
        f"(این پنل فقط برای تو کار می‌کند)\n\n"
    )
    for b in buildings:
        text += f"• {b.name}\n"
        builder.button(text=b.name, callback_data=f"building:{uid}:{b.id}")
    builder.adjust(1)

    text += "\nروی ساختمان کلیک کن. خرید با <b>سکه</b> است.\nسکه را با /wallet ببین."
    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("building:"))
async def show_building_items(callback: CallbackQuery):
    owner_id, rest = parse_owner_data(callback.data, "building:")
    if owner_id is None:
        await callback.answer("داده نامعتبر", show_alert=True)
        return
    if not await ensure_owner(callback, owner_id, "مغازه"):
        return

    try:
        building_id = int(rest)
    except ValueError:
        await callback.answer("خطا", show_alert=True)
        return

    async with async_session() as session:
        items = await get_items_of_building(session, building_id)
        building = await session.get(Building, building_id)

    if not items:
        await callback.answer("آیتمی در این ساختمان نیست.", show_alert=True)
        return

    bname = building.name if building else "ساختمان"
    builder = InlineKeyboardBuilder()
    text = f"🛒 <b>{bname}</b>\n\n"
    for item in items:
        text += (
            f"• <b>{item.name}</b>\n"
            f"  {item.description or ''}\n"
            f"  قیمت: <b>{item.price} سکه</b>\n\n"
        )
        builder.button(
            text=f"خرید {item.name}",
            callback_data=f"buy:{owner_id}:{item.id}",
        )
    builder.button(text="⬅️ برگشت به لیست ساختمان‌ها", callback_data=f"shopback:{owner_id}")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("shopback:"))
async def shop_back(callback: CallbackQuery):
    try:
        owner_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer("خطا", show_alert=True)
        return
    if not await ensure_owner(callback, owner_id, "مغازه"):
        return

    async with async_session() as session:
        await ensure_default_buildings_and_items(session)
        buildings = await get_buildings(session)

    builder = InlineKeyboardBuilder()
    text = "🏘️ <b>مغازه / ساختمان‌ها</b>\n\n"
    for b in buildings:
        text += f"• {b.name}\n"
        builder.button(text=b.name, callback_data=f"building:{owner_id}:{b.id}")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()


@router.callback_query(F.data.startswith("buy:"))
async def process_buy(callback: CallbackQuery):
    owner_id, rest = parse_owner_data(callback.data, "buy:")
    if owner_id is None:
        await callback.answer("داده نامعتبر", show_alert=True)
        return
    if not await ensure_owner(callback, owner_id, "مغازه"):
        return

    try:
        item_id = int(rest)
    except ValueError:
        await callback.answer("خطا", show_alert=True)
        return

    async with async_session() as session:
        user = await get_or_create_user(
            session,
            callback.from_user.id,
            callback.from_user.full_name,
            callback.from_user.username,
        )
        item = await session.get(ShopItem, item_id)
        if not item:
            await callback.answer("آیتم پیدا نشد.", show_alert=True)
            return
        msg = await buy_item(session, user, item)

    await callback.answer(msg, show_alert=True)


@router.message(Command("inventory", "کیف", "اینونتوری"))
async def cmd_inventory(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session,
            message.from_user.id,
            message.from_user.full_name,
            message.from_user.username,
        )
        from sqlalchemy import select
        from database.models_v3 import UserInventory

        result = await session.execute(
            select(UserInventory, ShopItem)
            .join(ShopItem, UserInventory.item_id == ShopItem.id)
            .where(UserInventory.user_id == user.id)
        )
        rows = result.all()

    if not rows:
        await message.answer("کیفت خالیه. از /buildings خرید کن.")
        return

    text = "🎒 <b>کیف تو</b>\n\n"
    for i, (inv, item) in enumerate(rows, 1):
        text += f"{i}. {item.name} ×{inv.quantity}\n"
    text += "\n/use شماره — استفاده\n/drop شماره — دور انداختن"
    await message.answer(text)


@router.message(Command("use", "استفاده"))
async def cmd_use_item(message: Message):
    """استفاده از آیتم: /use شماره"""
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(
            "فرمت: /use شماره\n"
            "اول /inventory بزن؛ شماره ردیف آیتم را ببین.\n"
            "مثال: /use 1"
        )
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
        from sqlalchemy import select
        from database.models_v3 import UserInventory

        result = await session.execute(
            select(UserInventory, ShopItem)
            .join(ShopItem, UserInventory.item_id == ShopItem.id)
            .where(UserInventory.user_id == user.id)
        )
        rows = result.all()
        if idx < 0 or idx >= len(rows):
            await message.answer("آیتم پیدا نشد. /inventory")
            return
        inv, item = rows[idx]
        effect = item.effect or {}
        msg_parts = [f"✅ از «{item.name}» استفاده کردی."]

        if isinstance(effect, dict):
            if effect.get("xp"):
                user.xp += int(effect["xp"])
                msg_parts.append(f"+{effect['xp']} XP")
            if effect.get("duel_power"):
                msg_parts.append(f"قدرت دوئل (از آیتم): {effect['duel_power']}")
            if effect.get("learn_tech"):
                msg_parts.append(f"تکنیک مرتبط: {effect['learn_tech']} — /learntech")

        # منابع از مواد
        if getattr(item, "item_type", "") in ("material", "herb_normal", "herb_spiritual", "pill"):
            from services.economy import get_or_create_wallet as _gw
            _w = await _gw(session, user.id)
            _gain = 15
            _w.coins += _gain
            msg_parts.append(f"منابع: +{_gain} سکه")
        inv.quantity -= 1
        if inv.quantity <= 0:
            await session.delete(inv)
        await session.commit()

    await message.answer("\n".join(msg_parts))


@router.message(Command("drop", "دورریختن", "حذف‌آیتم"))
async def cmd_drop_item(message: Message):
    """دور انداختن آیتم: /drop شماره [تعداد]"""
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("فرمت: /drop شماره\nیا /drop شماره تعداد\nمثال: /drop 1")
        return
    try:
        idx = int(parts[1]) - 1
        qty = int(parts[2]) if len(parts) >= 3 else 1
    except ValueError:
        await message.answer("عدد نامعتبر")
        return

    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        from sqlalchemy import select
        from database.models_v3 import UserInventory

        result = await session.execute(
            select(UserInventory, ShopItem)
            .join(ShopItem, UserInventory.item_id == ShopItem.id)
            .where(UserInventory.user_id == user.id)
        )
        rows = result.all()
        if idx < 0 or idx >= len(rows):
            await message.answer("آیتم پیدا نشد. /inventory")
            return
        inv, item = rows[idx]
        if qty < 1 or qty > inv.quantity:
            await message.answer(f"تعداد نامعتبر (داری: {inv.quantity})")
            return
        inv.quantity -= qty
        name = item.name
        if inv.quantity <= 0:
            await session.delete(inv)
        await session.commit()

    await message.answer(f"🗑 «{name}» ×{qty} از کیف حذف شد.")
