"""شغل، جنگ قبایل، فروش کوروش، تاس شانس، رویداد"""
import random
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user
from services.economy import get_or_create_wallet
from services import jobs as jobs_svc
from services import tribe_war as tw
from services import cyrus_sale as cs
from services.i18n import get_lang

router = Router()
_last_luck: dict[int, datetime] = {}
_last_daily: dict[int, datetime] = {}


@router.message(Command("jobs", "شغل‌ها", "اشغال"))
async def cmd_jobs(message: Message):
    await message.answer(jobs_svc.list_jobs())


@router.message(Command("job", "انتخاب‌شغل"))
async def cmd_job(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        builder = InlineKeyboardBuilder()
        for name in jobs_svc.JOBS:
            builder.button(text=name, callback_data=f"setjob:{message.from_user.id}:{name}")
        builder.adjust(2)
        await message.answer("💼 شغل را انتخاب کن:", reply_markup=builder.as_markup())
        return
    await message.answer(jobs_svc.set_job(message.from_user.id, parts[1].strip()))


@router.callback_query(F.data.startswith("setjob:"))
async def cb_set_job(callback: CallbackQuery):
    parts = callback.data.split(":")
    owner, job = int(parts[1]), parts[2]
    if callback.from_user.id != owner:
        await callback.answer()
        return
    msg = jobs_svc.set_job(owner, job)
    await callback.message.edit_text(msg)
    await callback.answer()


@router.message(Command("myjob", "شغل‌من"))
async def cmd_myjob(message: Message):
    j = jobs_svc.get_job(message.from_user.id)
    if not j:
        await message.answer(tr(message.from_user.id, "شغلی نداری. /jobs"))
        return
    info = jobs_svc.JOBS[j]
    await message.answer(f"💼 شغل: <b>{j}</b>\n{info['desc']} (×{info['mult']})")


@router.message(Command("changejob", "تعویض‌شغل"))
async def cmd_change_job(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "/changejob نام‌شغل"))
        return
    await message.answer(jobs_svc.change_job(message.from_user.id, parts[1].strip()))


@router.message(Command("declarewar", "اعلام‌جنگ", "جنگ‌قبیله"))
async def cmd_declare_war(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "/declarewar نام‌قبیله‌هدف"))
        return
    await message.answer(tw.declare(message.from_user.id, parts[1]))


@router.message(Command("tribewar", "وضعیت‌جنگ"))
async def cmd_tribe_war(message: Message):
    await message.answer(tw.status(message.from_user.id))


@router.message(Command("tribewarfight", "نبرد‌قبیله", "جنگ‌نبرد"))
async def cmd_tribe_fight(message: Message):
    await message.answer(tw.fight(message.from_user.id))


@router.message(Command("cyrussale", "فروش‌کوروش"))
async def cmd_cyrus_sale(message: Message):
    await message.answer(cs.sale_info())


@router.message(Command("buycyrus", "خرید‌کوروش"))
async def cmd_buy_cyrus(message: Message):
    ok, msg = cs.can_buy(message.from_user.id)
    if not ok:
        await message.answer(msg)
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
        price = cs.PUBLIC_PRICE
        if (w.spirit_stones or 0) < price:
            await message.answer(f"نیاز به {price} سنگ روحی داری.")
            return
        from sqlalchemy import select
        from database.models_v3 import ShopItem, UserInventory
        from services.shop import ensure_default_buildings_and_items
        await ensure_default_buildings_and_items(session)
        r = await session.execute(select(ShopItem).where(ShopItem.name.contains("کوروش")))
        item = r.scalars().first()
        if not item:
            await message.answer(tr(message.from_user.id, "آیتم کوروش در دیتابیس نیست. یک‌بار /buildings بزن."))
            return
        w.spirit_stones -= price
        inv = await session.execute(
            select(UserInventory).where(
                UserInventory.user_id == user.id, UserInventory.item_id == item.id
            )
        )
        existing = inv.scalar_one_or_none()
        if existing:
            existing.quantity += 1
        else:
            session.add(UserInventory(user_id=user.id, item_id=item.id, quantity=1))
        user.has_cyrus_sword = True
        await session.commit()
    cs._bought.add(message.from_user.id)
    await message.answer(
        f"✅ شمشیر کوروش بزرگ خریداری شد (−{cs.PUBLIC_PRICE} سنگ روحی).\n/equip برای تجهیز"
    )


@router.message(Command("luckdice", "تاس‌شانس", "شانس"))
async def cmd_luck_dice(message: Message):
    now = datetime.utcnow()
    last = _last_luck.get(message.from_user.id)
    if last and now - last < timedelta(hours=3):
        left = int((timedelta(hours=3) - (now - last)).total_seconds() // 60) + 1
        await message.answer(f"⏳ تاس شانس هر ۳ ساعت — حدود {left} دقیقه دیگر")
        return
    _last_luck[message.from_user.id] = now
    roll = random.randint(1, 6)
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
        if roll == 1:
            w.coins = (w.coins or 0) + 50
            reward = "+۵۰ سکه"
        elif roll == 2:
            w.coins = (w.coins or 0) + 120
            reward = "+۱۲۰ سکه"
        elif roll == 3:
            w.spirit_stones = (w.spirit_stones or 0) + 1
            reward = "+۱ سنگ روحی"
        elif roll == 4:
            from services.cultivation import add_energy
            await add_energy(session, user.id, 500)
            reward = "+۵۰۰ انرژی"
        elif roll == 5:
            w.coins = (w.coins or 0) + 300
            reward = "+۳۰۰ سکه"
        else:
            w.spirit_stones = (w.spirit_stones or 0) + 2
            reward = "+۲ سنگ روحی (شانس بزرگ!)"
        await session.commit()
    await message.answer(f"🎲 تاس: <b>{roll}</b>\n🎁 {reward}")


@router.message(Command("events", "رویدادها"))
async def cmd_events(message: Message):
    sale = "فعال ✅" if cs.sale_active() else "پایان ❌"
    await message.answer(
        "🌍 <b>رویدادها</b>\n\n"
        f"⚔️ فروش عمومی شمشیر کوروش: {sale}\n"
        "   /cyrussale | /buycyrus\n\n"
        "🏕 جنگ قبایل: /declarewar | /tribewar | /tribewarfight\n\n"
        "🎲 تاس شانس: /luckdice (هر ۳س)\n"
        "🎁 پاداش روزانه: /dailycoin\n"
        "💼 شغل: /jobs"
    )


@router.message(Command("statuscard", "وضعیت", "کارت‌وضعیت"))
async def cmd_status_card(message: Message):
    """کارت وضعیت شبیه ربات‌های تزکیه"""
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        from services.cultivation import get_or_create_cultivation
        from services.power import calc_power
        from services.economy import get_or_create_wallet
        from services.cities import get_city, ensure_user_city
        cult = await get_or_create_cultivation(session, user.id)
        w = await get_or_create_wallet(session, user.id)
        pw = await calc_power(session, user)
        cid = await ensure_user_city(session, user)
        city = get_city(cid)
        job = jobs_svc.get_job(message.from_user.id) or "—"
        blood = getattr(user, "blood", 100) or 100
        text = (
            f"<b>{user.full_name}</b>\n"
            f"🏷 {user.rank} — {getattr(user, 'race', 'انسان')}\n"
            f"💼 شغل: {job}\n"
            f"━━━━━━━━━━━━\n"
            f"🔮 قلمرو: {cult.realm} (مرحله {cult.stage})\n"
            f"🌱 ریشه: {cult.spiritual_root or '—'}\n"
            f"❤️ خون: {blood}/100\n"
            f"⚡ قدرت: {pw['total']}\n"
            f"🌀 چی/انرژی: {int(cult.energy or 0)}\n"
            f"━━━━━━━━━━━━\n"
            f"🪙 سکه: {w.coins or 0} | 💎 روحی: {w.spirit_stones or 0}\n"
            f"🏙️ {city.get('name')} | 🌌 {getattr(user, 'world', 'فانی')}\n"
            f"⏳ عمر: {getattr(user, 'lifespan', 100)}%"
        )
    await message.answer(text)
