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
    await message.answer("⚔️ ایونت فروش شمشیر کوروش پایان یافته و حذف شده است.")




@router.message(Command("buycyrus", "خرید‌کوروش"))
async def cmd_buy_cyrus(message: Message):
    await message.answer("⚔️ ایونت کوروش حذف شده؛ خرید عمومی ممکن نیست.")




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


# ——— معدن سنگ روح ———
@router.message(Command("mine", "معدن"))
async def cmd_mine(message: Message):
    from services import spirit_mine as sm
    await message.answer(sm.status(message.from_user.id))


@router.message(Command("buymine", "خرید‌معدن"))
async def cmd_buy_mine(message: Message):
    from services import spirit_mine as sm
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
        ok, msg, new_sp = sm.buy_mine(message.from_user.id, w.spirit_stones or 0)
        if ok:
            w.spirit_stones = new_sp
            await session.commit()
        await message.answer(msg)


@router.message(Command("claimmine", "برداشت‌معدن"))
async def cmd_claim_mine(message: Message):
    from services import spirit_mine as sm
    ok, msg, amount = sm.claim(message.from_user.id)
    if ok and amount:
        async with async_session() as session:
            user = await get_or_create_user(
                session, message.from_user.id,
                message.from_user.full_name, message.from_user.username
            )
            w = await get_or_create_wallet(session, user.id)
            w.spirit_stones = (w.spirit_stones or 0) + amount
            await session.commit()
    await message.answer(msg)


@router.message(Command("upgrademine", "ارتقا‌معدن"))
async def cmd_upgrade_mine(message: Message):
    from services import spirit_mine as sm
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
        ok, msg, new_sp = sm.upgrade(message.from_user.id, w.spirit_stones or 0)
        if ok:
            w.spirit_stones = new_sp
            await session.commit()
        await message.answer(msg)


from aiogram import Router as _R
from aiogram.filters import Command
from aiogram.types import Message
from database.engine import async_session
from database.crud import get_or_create_user
from bot.config import ADMIN_IDS

# reuse router if exists
try:
    router
except NameError:
    router = _R()


@router.message(Command("cultbuilding", "ساختمان‌تزکیه", "تزکیه‌خانه"))
async def cmd_cult_building(message: Message):
    from services.cult_building import status
    await message.answer(status(message.from_user.id))


@router.message(Command("upgradecultbuilding", "ارتقا‌تزکیه"))
async def cmd_up_cult_building(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        from services.cult_building import upgrade
        msg = await upgrade(session, user.id, message.from_user.id)
    await message.answer(msg)


@router.message(Command("calamitystatus", "وضعیت‌مصیبت"))
async def cmd_calamity(message: Message):
    from services.sect_calamity import status_text, tick_calamity
    async with async_session() as session:
        msgs = await tick_calamity(session)
    text = status_text()
    if msgs:
        text += chr(10) + chr(10) + chr(10).join(msgs)
    await message.answer(text)


@router.message(Command("protectsect", "محافظت‌فرقه"))
async def cmd_protect_sect(message: Message):
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("فقط ادمین.")
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("فرمت: /protectsect sect_id")
        return
    from services.sect_calamity import protect_sect
    await message.answer(protect_sect(int(parts[1])))



@router.message(Command("knowledge", "دانش", "statscombat", "نرخ‌نبرد"))
async def cmd_knowledge(message: Message):
    from services.knowledge import status
    await message.answer(status(message.from_user.id))


@router.message(Command("readbook", "کتاب‌خواندن", "خواندن‌کتاب"))
async def cmd_readbook(message: Message):
    from services.knowledge import read_book
    await message.answer(read_book(message.from_user.id))


@router.message(Command("wanderworld", "گردش‌جهان", "جهانگردی"))
async def cmd_wander(message: Message):
    from services.knowledge import wander_world
    await message.answer(wander_world(message.from_user.id))


@router.message(Command("talkmaster", "گفتگو‌استاد", "صحبت‌استاد"))
async def cmd_talk_master(message: Message):
    from services.knowledge import talk_master
    has = False
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        try:
            from services.master import get_master
            rel = await get_master(session, user.id)
            has = rel is not None
        except Exception:
            has = False
    await message.answer(talk_master(message.from_user.id, has))


@router.message(Command("trainbody", "تمرین‌بدن", "لول‌بدن"))
async def cmd_train_body(message: Message):
    from services.knowledge import train_body
    await message.answer(train_body(message.from_user.id))


@router.message(Command("trainspirit", "تمرین‌روح", "لول‌روح"))
async def cmd_train_spirit(message: Message):
    from services.knowledge import train_spirit
    await message.answer(train_spirit(message.from_user.id))


@router.message(Command("knights", "شوالیه", "شوالیه‌ها"))
async def cmd_knights(message: Message):
    from services.knights import list_text
    await message.answer(list_text())


@router.message(Command("buyknight", "خرید‌شوالیه"))
async def cmd_buy_knight(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("فرمت: /buyknight شماره")
        return
    try:
        kid = int(parts[1])
    except ValueError:
        await message.answer("شماره نامعتبر")
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
        from services.knights import buy
        ok, msg, left = buy(message.from_user.id, kid, int(w.coins or 0))
        if ok:
            w.coins = left
            await session.commit()
    await message.answer(msg)


@router.message(Command("myknights", "شوالیه‌های‌من"))
async def cmd_my_knights(message: Message):
    from services.knights import my_knights
    await message.answer(my_knights(message.from_user.id))



@router.message(Command("myhome", "خانه", "خونه"))
async def cmd_myhome(message: Message):
    from services.housing import status
    await message.answer(status(message.from_user.id))


@router.message(Command("upgradehome", "ارتقا‌خانه"))
async def cmd_upgrade_home(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        from services.housing import upgrade
        msg = await upgrade(session, user.id, message.from_user.id)
    await message.answer(msg)


@router.message(Command("buyfurniture", "خرید‌وسیله"))
async def cmd_buy_furn(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        from services.housing import FURNITURE_SHOP
        await message.answer("فرمت: /buyfurniture نام\n" + "، ".join(FURNITURE_SHOP.keys()))
        return
    from services.housing import buy_furniture
    ok, cost, msg = buy_furniture(message.from_user.id, parts[1].strip())
    if not ok:
        await message.answer(msg)
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        from services.economy import get_or_create_wallet, pay_any_currency
        w = await get_or_create_wallet(session, user.id)
        paid, pmsg = pay_any_currency(w, cost)
        if not paid:
            # rollback furniture
            from services.housing import get_home
            h = get_home(message.from_user.id)
            if h.get("furniture"):
                h["furniture"].pop()
            await message.answer(pmsg)
            return
        await session.commit()
    await message.answer(msg + chr(10) + pmsg)



@router.message(Command("bodyrealms", "قلمرو‌بدن", "قلمروبدن"))
async def cmd_body_realms(message: Message):
    from services.body_spirit_realms import body_realm_status
    await message.answer(body_realm_status(message.from_user.id))


@router.message(Command("spiritrealms", "قلمرو‌روح", "قلمروروح"))
async def cmd_spirit_realms(message: Message):
    from services.body_spirit_realms import spirit_realm_status
    await message.answer(spirit_realm_status(message.from_user.id))



@router.message(Command("cultpath", "مسیر‌تذهیب", "مسیرتذهیب"))
async def cmd_cult_path(message: Message):
    from services.cult_paths import list_paths, set_path, get_path
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        cur = get_path(message.from_user.id)
        await message.answer(list_paths() + chr(10) + f"مسیر فعلی: <b>{cur}</b>")
        return
    await message.answer(set_path(message.from_user.id, parts[1].strip()))


@router.message(Command("worldblade", "نابودکننده", "شمشیر‌جهان"))
async def cmd_world_blade(message: Message):
    from services.world_blade import status, ITEM_NAME, PRICE
    await message.answer(
        status(message.from_user.id) + chr(10) + chr(10)
        + f"خرید از آهنگری: <b>{ITEM_NAME}</b>" + chr(10)
        + f"قیمت: {PRICE:,} سکه"
    )
