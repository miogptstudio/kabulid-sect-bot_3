from datetime import datetime, timedelta
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from sqlalchemy import select

from database.engine import async_session
from database.crud import get_or_create_user
from database.models_v3 import GardenPlot
from services.economy import get_or_create_wallet, pay_any_currency

router = Router()

DEFAULT_SLOTS = 10
PLANT_COOLDOWN = timedelta(hours=5)
LAND_PRICE_COINS = 5000  # قیمت هر بسته زمین (معادل سکه)
LAND_SLOTS_PER_BUY = 5
MAX_SLOTS = 50

PLANTS = {
    "بذر معمولی": {"grow_hours": 1, "reward_coins": 20, "reward_item": None},
    "بذر معنوی": {"grow_hours": 3, "reward_coins": 50, "reward_item": "گیاه معنوی - برگ روح"},
    "بذر روحی": {"grow_hours": 6, "reward_coins": 100, "reward_item": None},
}


def _slots(user) -> int:
    return int(getattr(user, "garden_slots", None) or DEFAULT_SLOTS)


@router.message(Command("garden", "باغ", "کشت"))
async def cmd_garden(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if not getattr(user, "garden_slots", None):
            user.garden_slots = DEFAULT_SLOTS
            await session.commit()
        result = await session.execute(
            select(GardenPlot).where(GardenPlot.user_id == user.id)
        )
        plots = list(result.scalars().all())
        slots = _slots(user)
        last = getattr(user, "last_plant_at", None)

    text = (
        "🌱 <b>باغ تذهیب</b>" + chr(10) + chr(10)
        + f"زمین اشغال: <b>{len(plots)}</b> / <b>{slots}</b>" + chr(10)
    )
    if last:
        nxt = last + PLANT_COOLDOWN
        now = datetime.utcnow()
        if now < nxt:
            left = int((nxt - now).total_seconds())
            h, m = left // 3600, (left % 3600) // 60
            text += f"⏰ کاشت بعدی تا {h}س {m}د دیگر" + chr(10)
        else:
            text += "✅ می‌توانی الان بکاری" + chr(10)
    else:
        text += "✅ می‌توانی الان بکاری" + chr(10)

    text += chr(10)
    if not plots:
        text += "هنوز چیزی نکاشته‌ای." + chr(10)
    else:
        now = datetime.utcnow()
        for i, p in enumerate(plots, 1):
            ready = p.ready_at and now >= p.ready_at
            st = "✅ رسیده" if ready else f"⏳ تا {p.ready_at}"
            text += f"{i}. {p.plant_name} — {st}" + chr(10)

    text += (
        chr(10)
        + "دستورات:" + chr(10)
        + "/plant نام‌بذر — کاشت (هر ۵ ساعت یک گیاه)" + chr(10)
        + "/harvest — برداشت رسیده‌ها" + chr(10)
        + f"/buyland — خرید زمین (+{LAND_SLOTS_PER_BUY} ظرفیت، {LAND_PRICE_COINS} سکه یا معادل)" + chr(10)
        + "بذرها: معمولی | معنوی | روحی"
    )
    await message.answer(text)


@router.message(Command("plant", "کاشتن"))
async def cmd_plant(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    name = parts[1].strip() if len(parts) > 1 else "بذر معمولی"
    if name not in PLANTS and not name.startswith("بذر"):
        alt = "بذر " + name
        if alt in PLANTS:
            name = alt
    if name not in PLANTS:
        await message.answer("بذر نامعتبر. معمولی | معنوی | روحی")
        return
    info = PLANTS[name]
    now = datetime.utcnow()

    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if not getattr(user, "garden_slots", None):
            user.garden_slots = DEFAULT_SLOTS

        # کول‌داون ۵ ساعت
        last = getattr(user, "last_plant_at", None)
        if last and now < last + PLANT_COOLDOWN:
            left = int((last + PLANT_COOLDOWN - now).total_seconds())
            h, m = left // 3600, (left % 3600) // 60
            await message.answer(
                f"⏳ هر ۵ ساعت فقط یک گیاه می‌توانی بکاری." + chr(10)
                + f"مانده: {h} ساعت و {m} دقیقه"
            )
            return

        result = await session.execute(
            select(GardenPlot).where(GardenPlot.user_id == user.id)
        )
        plots = list(result.scalars().all())
        slots = _slots(user)
        if len(plots) >= slots:
            await message.answer(
                f"زمین پر است ({len(plots)}/{slots})." + chr(10)
                + f"با /buyland ظرفیت را زیاد کن ({LAND_PRICE_COINS} سکه برای +{LAND_SLOTS_PER_BUY})."
            )
            return

        ready = now + timedelta(hours=info["grow_hours"])
        plot = GardenPlot(
            user_id=user.id, plant_name=name, stage=1, ready_at=ready
        )
        session.add(plot)
        user.last_plant_at = now
        await session.commit()

    await message.answer(
        f"🌱 «{name}» کاشته شد." + chr(10)
        + f"آماده حدود {info['grow_hours']} ساعت دیگر." + chr(10)
        + "کاشت بعدی: ۵ ساعت دیگر."
    )


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
        plots = list(result.scalars().all())
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


@router.message(Command("buyland", "خرید‌زمین", "خریدزمین"))
async def cmd_buy_land(message: Message):
    """خرید ظرفیت بیشتر زمین"""
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        slots = _slots(user)
        if slots >= MAX_SLOTS:
            await message.answer(f"حداکثر ظرفیت ({MAX_SLOTS}) را داری.")
            return
        w = await get_or_create_wallet(session, user.id)
        ok, pay_msg = pay_any_currency(w, LAND_PRICE_COINS)
        if not ok:
            await message.answer(pay_msg)
            return
        user.garden_slots = min(MAX_SLOTS, slots + LAND_SLOTS_PER_BUY)
        await session.commit()
        new_slots = user.garden_slots
    await message.answer(
        f"✅ +{LAND_SLOTS_PER_BUY} ظرفیت زمین خریدی." + chr(10)
        + f"ظرفیت فعلی: <b>{new_slots}</b> / {MAX_SLOTS}" + chr(10)
        + pay_msg
    )
