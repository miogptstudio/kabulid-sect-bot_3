from datetime import datetime, timedelta
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select

from database.engine import async_session
from database.crud import get_or_create_user
from database.models_v3 import GardenPlot, UserInventory, ShopItem
from services.economy import get_or_create_wallet

router = Router()

PLANTS = {
    "بذر معمولی": {"grow_hours": 1, "reward_coins": 20, "reward_item": None},
    "بذر معنوی": {"grow_hours": 3, "reward_coins": 50, "reward_item": "گیاه معنوی - برگ روح"},
    "بذر روحی": {"grow_hours": 6, "reward_coins": 100, "reward_item": None},
}


@router.message(Command("garden", "باغ", "کشت"))
async def cmd_garden(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        result = await session.execute(
            select(GardenPlot).where(GardenPlot.user_id == user.id)
        )
        plots = result.scalars().all()
    text = "🌱 <b>باغ تذهیب</b>\n\n"
    if not plots:
        text += "زمینی نداری. /plant بذر معمولی\n"
    else:
        now = datetime.utcnow()
        for i, p in enumerate(plots, 1):
            ready = p.ready_at and now >= p.ready_at
            st = "✅ رسیده" if ready else f"در حال رشد (تا {p.ready_at})"
            text += f"{i}. {p.plant_name} — {st}\n"
    text += "\n/plant نام‌بذر — کاشت\n/harvest — برداشت همه رسیده‌ها\nبذرها: معمولی، معنوی، روحی"
    await message.answer(text)


@router.message(Command("plant", "کاشتن"))
async def cmd_plant(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    name = parts[1].strip() if len(parts) > 1 else "بذر معمولی"
    if name not in PLANTS and not name.startswith("بذر"):
        name = "بذر " + name if f"بذر {name}" in PLANTS else name
    if name not in PLANTS:
        await message.answer("بذر نامعتبر. معمولی / معنوی / روحی")
        return
    info = PLANTS[name]
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        result = await session.execute(
            select(GardenPlot).where(GardenPlot.user_id == user.id)
        )
        if len(result.scalars().all()) >= 5:
            await message.answer("حداکثر ۵ زمین.")
            return
        ready = datetime.utcnow() + timedelta(hours=info["grow_hours"])
        plot = GardenPlot(
            user_id=user.id, plant_name=name, stage=1, ready_at=ready
        )
        session.add(plot)
        await session.commit()
    await message.answer(f"🌱 {name} کاشته شد. آماده حدود {info['grow_hours']} ساعت دیگر.")


@router.message(Command("harvest", "برداشت"))
async def cmd_harvest(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        result = await session.execute(
            select(GardenPlot).where(GardenPlot.user_id == user.id)
        )
        plots = result.scalars().all()
        now = datetime.utcnow()
        w = await get_or_create_wallet(session, user.id)
        gained = 0
        for p in plots:
            if p.ready_at and now >= p.ready_at:
                info = PLANTS.get(p.plant_name, PLANTS["بذر معمولی"])
                w.coins += info["reward_coins"]
                gained += info["reward_coins"]
                await session.delete(p)
        await session.commit()
    if gained:
        await message.answer(f"🌾 برداشت شد! +{gained} سکه")
    else:
        await message.answer("چیزی آماده نیست.")
