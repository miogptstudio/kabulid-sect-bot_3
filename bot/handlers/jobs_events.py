"""شغل، جنگ قبایل، فروش کوروش، تاس شانس، رویداد"""
import random
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, FSInputFile, CallbackQuery, URLInputFile
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user
from services.economy import get_or_create_wallet
from services import jobs as jobs_svc
from services import tribe_war as tw
from services import cyrus_sale as cs
from services.i18n import get_lang, tr
from services.portraits import panel_url
from bot.utils.media import safe_answer_photo

router = Router()
_last_luck: dict[int, datetime] = {}
_last_daily: dict[int, datetime] = {}


@router.message(Command("work", "کار", "کارشغل"))
async def cmd_work(message: Message):
    try:
        res = jobs_svc.work(message.from_user.id)
        if isinstance(res, str):
            await message.answer(res)
            return
        if not isinstance(res, dict):
            await message.answer("⚠️ نتیجه شغل نامعتبر بود. دوباره /work را بزن.")
            return
        async with async_session() as session:
            user = await get_or_create_user(
                session, message.from_user.id,
                message.from_user.full_name, message.from_user.username
            )
            w = await get_or_create_wallet(session, user.id)
            w.coins = int(w.coins or 0) + int(res.get("coins") or 0)
            if res.get("spirit_stones"):
                w.spirit_stones = int(w.spirit_stones or 0) + int(res["spirit_stones"])
            await session.commit()
        await message.answer(str(res.get("msg") or "✅ کار انجام شد."))
    except Exception as e:
        await message.answer(f"⚠️ خطا در شغل: {type(e).__name__}: {str(e)[:180]}")


@router.message(Command("jobs", "شغلها", "اشغال"))
async def cmd_jobs(message: Message):

    await safe_answer_photo(message, panel_url("job", name=str(message.from_user.id)), caption=jobs_svc.list_jobs())


@router.message(Command("job", "انتخابشغل"))
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
    parts = callback.data.split(":", 2)
    if len(parts) < 3:
        await callback.answer("دادهٔ شغل نامعتبره.", show_alert=True)
        return
    try:
        owner, job = int(parts[1]), parts[2]
    except (ValueError, TypeError):
        await callback.answer("دادهٔ شغل نامعتبره.", show_alert=True)
        return
    if callback.from_user.id != owner:
        await callback.answer()
        return
    msg = jobs_svc.set_job(owner, job)
    await callback.message.edit_text(msg)
    await callback.answer()


@router.message(Command("myjob", "شغلمن"))
async def cmd_myjob(message: Message):
    j = jobs_svc.get_job(message.from_user.id)
    if not j:
        await message.answer(tr(message.from_user.id, "شغلی نداری. /jobs"))
        return
    info = jobs_svc.JOBS[j]
    await message.answer(f"💼 شغل: <b>{j}</b>\n{info['desc']} (×{info['mult']})")


@router.message(Command("changejob", "تعویضشغل"))
async def cmd_change_job(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "/changejob نامشغل"))
        return
    await message.answer(jobs_svc.change_job(message.from_user.id, parts[1].strip()))


@router.message(Command("declarewar", "اعلامجنگ", "جنگقبیله"))
async def cmd_declare_war(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "/declarewar نامقبیلههدف"))
        return
    await message.answer(tw.declare(message.from_user.id, parts[1]))


@router.message(Command("tribewar", "وضعیتجنگ"))
async def cmd_tribe_war(message: Message):
    await message.answer(tw.status(message.from_user.id))


@router.message(Command("tribewarfight", "نبردقبیله", "جنگنبرد"))
async def cmd_tribe_fight(message: Message):
    await message.answer(tw.fight(message.from_user.id))


@router.message(Command("cyrussale", "فروشکوروش"))
async def cmd_cyrus_sale(message: Message):
    await message.answer("⚔️ ایونت فروش شمشیر کوروش پایان یافته و حذف شده است.")




@router.message(Command("buycyrus", "خریدکوروش"))
async def cmd_buy_cyrus(message: Message):
    await message.answer("⚔️ ایونت کوروش حذف شده؛ خرید عمومی ممکن نیست.")




@router.message(Command("luckdice", "تاسشانس", "شانس"))
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




# ========== ایونت آرش کمانگیر ==========
# روزانه حداکثر ۲ نفر می‌توانند کمان آرش را بخرند
_ARASH_BOW_PRICE = 50000  # سکه
_ARASH_DAILY_LIMIT = 2

def _arash_map():
    from services.persist import get_dict
    return get_dict("arash_event")

def _arash_day():
    from datetime import datetime
    return datetime.utcnow().strftime("%Y-%m-%d")

def _arash_bought_today() -> list:
    m = _arash_map()
    day = _arash_day()
    rec = m.get("day_buys") or {}
    if rec.get("day") != day:
        return []
    return list(rec.get("buyers") or [])

@router.message(Command("arash", "آرش", "کمانآرش", "ایونتآرش"))
async def cmd_arash_event(message: Message):
    """جزئیات ایونت آرش کمانگیر"""
    try:
        from services.martial_quests import progress
        progress(message.from_user.id, "arash_view", 1)
        from services.campaign import progress as camp_p
        camp_p(message.from_user.id, "arash_view", 1)
    except Exception:
        pass
    bought = _arash_bought_today()
    left = max(0, _ARASH_DAILY_LIMIT - len(bought))
    await message.answer(
        "🏹 <b>ایونت آرش کمانگیر</b>\n\n"
        "در افسانه‌های جهان رزمی، آرش کمانگیر با تیری مرزها را تعیین کرد.\n"
        "اکنون کمان افسانه‌ای او برای مدت محدود در دسترس است.\n\n"
        f"💰 قیمت کمان آرش: <b>{_ARASH_BOW_PRICE:,}</b> سکه\n"
        f"👥 سهمیه روزانه: <b>{_ARASH_DAILY_LIMIT}</b> نفر (باقی‌مانده امروز: <b>{left}</b>)\n\n"
        "✨ اثر کمان:\n"
        "• +۱۵٪ قدرت در دوئل\n"
        "• علامت ویژه «آرش» در پروفایل\n"
        "• یک‌بار در روز تیر ویژه (آسیب اضافه)\n\n"
        "برای خرید: /buyarash\n"
        "وضعیت: /arashstatus"
    )

@router.message(Command("buyarash", "خریدکمانآرش", "خریدآرش"))
async def cmd_buy_arash(message: Message):
    from services.persist import get_dict, save
    from database.engine import async_session
    from database.crud import get_or_create_user
    from services.economy import get_or_create_wallet
    tg = message.from_user.id
    bought = _arash_bought_today()
    if tg in bought:
        await message.answer("قبلاً امروز کمان آرش را خریده‌ای.")
        return
    if len(bought) >= _ARASH_DAILY_LIMIT:
        await message.answer(
            f"⛔ سهمیه امروز تمام شد ({_ARASH_DAILY_LIMIT} نفر). فردا دوباره تلاش کن.\n"
            "/arash برای جزئیات"
        )
        return
    async with async_session() as session:
        user = await get_or_create_user(session, tg, message.from_user.full_name, message.from_user.username)
        w = await get_or_create_wallet(session, user.id)
        if (w.coins or 0) < _ARASH_BOW_PRICE:
            await message.answer(f"سکه کافی نیست. نیاز: {_ARASH_BOW_PRICE:,} — موجودی: {w.coins or 0:,}")
            return
        w.coins = (w.coins or 0) - _ARASH_BOW_PRICE
        # ثبت خرید روزانه
        m = get_dict("arash_event")
        day = _arash_day()
        rec = m.get("day_buys") or {}
        if rec.get("day") != day:
            rec = {"day": day, "buyers": []}
        rec["buyers"] = list(rec.get("buyers") or []) + [tg]
        m["day_buys"] = rec
        # مالکیت دائمی کمان
        owners = m.get("owners") or {}
        owners[str(tg)] = {"at": __import__("datetime").datetime.utcnow().isoformat(), "name": message.from_user.full_name or str(tg)}
        m["owners"] = owners
        save("arash_event")
        # فلگ روی کاربر اگر فیلد مناسب هست
        try:
            if hasattr(user, "has_cyrus_sword"):
                # از فیلد موجود برای سلاح ویژه استفاده می‌کنیم یا first_cities
                pass
            # در اینونتوری یک آیتم مجازی ثبت نمی‌کنیم مگر مدل داشته باشد؛ در persist نگه می‌داریم
        except Exception:
            pass
        await session.commit()
    await message.answer(
        f"🏹 <b>کمان آرش به تو رسید!</b>" + chr(10)
        + f"−{_ARASH_BOW_PRICE:,} سکه" + chr(10)
        + f"سهمیه امروز: {len(bought)+1}/{_ARASH_DAILY_LIMIT}" + chr(10) + chr(10)
        + "قدرت دوئل +۱۵٪ فعال شد. /arashstatus"
    )

@router.message(Command("arashstatus", "وضعیتآرش"))
async def cmd_arash_status(message: Message):
    from services.persist import get_dict
    m = get_dict("arash_event")
    bought = _arash_bought_today()
    owners = m.get("owners") or {}
    has = str(message.from_user.id) in owners
    await message.answer(
        "🏹 <b>وضعیت ایونت آرش</b>\n\n"
        f"خرید امروز: {len(bought)}/{_ARASH_DAILY_LIMIT}\n"
        f"تو کمان داری: {'✅ بله' if has else '❌ خیر'}\n"
        f"کل مالکان ثبت‌شده: {len(owners)}\n\n"
        "/arash | /buyarash"
    )


@router.message(Command("events", "رویدادها"))
async def cmd_events(message: Message):
    nl = chr(10)
    await message.answer(
        "🌍 <b>رویدادها و سیستم‌های جهان رزمی</b>" + nl + nl
        + "🏹 آرش کمانگیر: /arash | /buyarash" + nl
        + "📖 کمپین: /campaign | /claimcampaign" + nl
        + "🏰 سیاه‌چال: /dungeon | /dungeonrun" + nl
        + "🏆 لیگ فصلی: /league" + nl
        + "⚔️ کمبو: /combos | 💎 آرتیفکت: /artifacts" + nl
        + "🗡️ مأموریت: /quests | /claimquest" + nl
        + "🏅 القاب: /titles" + nl
        + "🏕 جنگ قبایل: /declarewar | /tribewar" + nl
        + "🎲 تاس شانس: /luckdice" + nl
        + "🎁 /dailycoin | 💱 /convert | 💼 /jobs"
    )


@router.message(Command("statuscard", "وضعیت", "کارتوضعیت"))
async def cmd_status_card(message: Message):
    """کارت وضعیت شبیه رباتهای تزکیه"""
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


@router.message(Command("buymine", "خریدمعدن"))
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


@router.message(Command("claimmine", "برداشتمعدن"))
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


@router.message(Command("upgrademine", "ارتقامعدن"))
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
from aiogram.types import Message, FSInputFile
from database.engine import async_session
from database.crud import get_or_create_user
from bot.config import ADMIN_IDS

# reuse router if exists
try:
    router
except NameError:
    router = _R()


@router.message(Command("cultbuilding", "ساختمانتزکیه", "تزکیهخانه"))
async def cmd_cult_building(message: Message):
    from services.cult_building import status
    await message.answer(status(message.from_user.id))


@router.message(Command("upgradecultbuilding", "ارتقاتزکیه"))
async def cmd_up_cult_building(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        from services.cult_building import upgrade, upgrade_cost, level
        from services.economy import get_or_create_wallet, pay_any_currency
        tg_id = message.from_user.id
        current = level(tg_id)
        cost = upgrade_cost(tg_id)
        if current >= 20:
            msg = "ساختمان تذهیب در حداکثر سطح است."
        else:
            w = await get_or_create_wallet(session, user.id)
            ok, pay_msg = pay_any_currency(w, cost)
            if not ok:
                msg = pay_msg
            else:
                new_level, _ = upgrade(tg_id)
                await session.commit()
                msg = f"✅ ساختمان تذهیب → سطح <b>{new_level}</b>" + chr(10) + pay_msg
    await message.answer(msg)


@router.message(Command("calamitystatus", "وضعیتمصیبت"))
async def cmd_calamity(message: Message):
    from services.sect_calamity import status_text, tick_calamity
    async with async_session() as session:
        msgs = await tick_calamity(session)
    text = status_text()
    if msgs:
        text += chr(10) + chr(10) + chr(10).join(msgs)
    await message.answer(text)


@router.message(Command("protectsect", "محافظتفرقه"))
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



@router.message(Command("knowledge", "دانش", "statscombat", "نرخنبرد"))
async def cmd_knowledge(message: Message):
    from services.knowledge import status
    await message.answer(status(message.from_user.id))


@router.message(Command("readbook", "کتابخواندن", "خواندنکتاب"))
async def cmd_readbook(message: Message):
    from services.knowledge import read_book
    await message.answer(read_book(message.from_user.id))


@router.message(Command("wanderworld", "گردشجهان", "جهانگردی"))
async def cmd_wander(message: Message):
    from services.knowledge import wander_world
    await message.answer(wander_world(message.from_user.id))


@router.message(Command("talkmaster", "گفتگواستاد", "صحبتاستاد"))
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


@router.message(Command("trainbody", "تمرینبدن", "لولبدن"))
async def cmd_train_body(message: Message):
    from services.knowledge import train_body
    await message.answer(train_body(message.from_user.id))


@router.message(Command("knights", "شوالیه", "شوالیهها"))
async def cmd_knights(message: Message):
    from services.knights import list_text
    await message.answer(list_text())


@router.message(Command("buyknight", "خریدشوالیه"))
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


@router.message(Command("myknights", "شوالیههایمن"))
async def cmd_my_knights(message: Message):
    from services.knights import my_knights
    await message.answer(my_knights(message.from_user.id))



@router.message(Command("myhome", "خانه", "خونه"))
async def cmd_myhome(message: Message):
    from services.housing import status
    await message.answer(status(message.from_user.id))


@router.message(Command("upgradehome", "ارتقاخانه"))
async def cmd_upgrade_home(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        from services.housing import upgrade
        msg = await upgrade(session, user.id, message.from_user.id)
    await message.answer(msg)


@router.message(Command("buyfurniture", "خریدوسیله"))
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



@router.message(Command("bodyrealms", "قلمروبدن", "قلمروبدن"))
async def cmd_body_realms(message: Message):
    from services.body_spirit_realms import body_realm_status
    await message.answer(body_realm_status(message.from_user.id))


@router.message(Command("spiritrealms", "قلمروروح", "قلمروروح"))
async def cmd_spirit_realms(message: Message):
    from services.body_spirit_realms import spirit_realm_status
    await message.answer(spirit_realm_status(message.from_user.id))



@router.message(Command("cultpath", "مسیرتذهیب", "مسیرتذهیب"))
async def cmd_cult_path(message: Message):
    from services.cult_paths import list_paths, set_path, get_path
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        cur = get_path(message.from_user.id)
        await message.answer(list_paths() + chr(10) + f"مسیر فعلی: <b>{cur}</b>")
        return
    await message.answer(set_path(message.from_user.id, parts[1].strip()))


@router.message(Command("worldblade", "نابودکننده", "شمشیرجهان"))
async def cmd_world_blade(message: Message):
    from services.world_blade import status, ITEM_NAME, PRICE
    await message.answer(
        status(message.from_user.id) + chr(10) + chr(10)
        + f"خرید از آهنگری: <b>{ITEM_NAME}</b>" + chr(10)
        + f"قیمت: {PRICE:,} سکه"
    )


@router.message(Command("quests", "مأموریت", "ماموریت", "مأموریتها", "dailyquest"))
async def cmd_quests(message: Message):
    from services.martial_quests import status_text, progress
    try:
        progress(message.from_user.id, "arash_view", 0)  # ensure day init
    except Exception:
        pass
    await message.answer(status_text(message.from_user.id))


@router.message(Command("claimquest", "دریافتمأموریت", "جایزهمأموریت"))
async def cmd_claim_quest(message: Message):
    from services.martial_quests import claim
    msg, coins, xp = claim(message.from_user.id)
    if coins or xp:
        async with async_session() as session:
            user = await get_or_create_user(
                session, message.from_user.id,
                message.from_user.full_name, message.from_user.username
            )
            w = await get_or_create_wallet(session, user.id)
            w.coins = int(w.coins or 0) + int(coins)
            user.xp = int(user.xp or 0) + int(xp)
            await session.commit()
    await message.answer(msg)


@router.message(Command("titles", "القاب", "لقب"))
async def cmd_titles(message: Message):
    from services.titles import status_text, auto_check
    try:
        from services.persist import get_dict
        has_arash = str(message.from_user.id) in ((get_dict("arash_event") or {}).get("owners") or {})
        auto_check(message.from_user.id, has_arash=has_arash)
    except Exception:
        pass
    await message.answer(status_text(message.from_user.id))


@router.message(Command("settitle", "انتخابلقب"))
async def cmd_set_title(message: Message):
    from services.titles import set_active
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("فرمت: /settitle شناسه\nمثال: /settitle duelist\n/titles")
        return
    await message.answer(set_active(message.from_user.id, parts[1].strip()))


# ========== سیستم‌های پیشرفته جهان رزمی ==========

@router.message(Command("campaign", "کمپین", "داستان"))
async def cmd_campaign(message: Message):
    from services.campaign import status_text, progress
    try:
        progress(message.from_user.id, "view_city", 0)
    except Exception:
        pass
    await message.answer(status_text(message.from_user.id))


@router.message(Command("claimcampaign", "دریافتکمپین", "جایزهکمپین"))
async def cmd_claim_campaign(message: Message):
    from services.campaign import claim
    from services.cultivation import add_energy
    msg, rewards = claim(message.from_user.id)
    if rewards:
        async with async_session() as session:
            user = await get_or_create_user(
                session, message.from_user.id,
                message.from_user.full_name, message.from_user.username
            )
            w = await get_or_create_wallet(session, user.id)
            w.coins = int(w.coins or 0) + int(rewards.get("coins") or 0)
            user.xp = int(user.xp or 0) + int(rewards.get("xp") or 0)
            if rewards.get("energy"):
                await add_energy(session, user.id, int(rewards["energy"]))
            await session.commit()
        try:
            from services.season_league import add_score
            add_score(message.from_user.id, 25, "campaign")
        except Exception:
            pass
    await message.answer(msg)


@router.message(Command("dungeon", "سیاهچال", "سیاه‌چال", "دنجن"))
async def cmd_dungeon(message: Message):
    from services.dungeon import status_text
    from services.power import calc_power
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        p = await calc_power(session, user)
    await message.answer(status_text(message.from_user.id, int(p.get("total") or 0)))


@router.message(Command("dungeonrun", "حملهسیاهچال", "ورودسیاهچال"))
async def cmd_dungeon_run(message: Message):
    from services.dungeon import run
    from services.power import calc_power
    from services.artifacts import try_drop
    from services.combo_combat import unlock_by_progress
    from services.season_league import add_score
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        p = await calc_power(session, user)
        power = int(p.get("total") or 0)
        result = run(message.from_user.id, power)
        if not result.get("ok"):
            await message.answer(result.get("msg", "خطا"))
            return
        if result.get("coins") or result.get("xp"):
            w = await get_or_create_wallet(session, user.id)
            w.coins = int(w.coins or 0) + int(result.get("coins") or 0)
            user.xp = int(user.xp or 0) + int(result.get("xp") or 0)
            await session.commit()
        msg = result.get("msg", "")
        if result.get("won"):
            floor = int(result.get("floor") or 0)
            add_score(message.from_user.id, 10 * floor, "dungeon")
            unlock_by_progress(message.from_user.id, dungeon_floor=floor)
            drop = try_drop(message.from_user.id, luck=1.0 + floor * 0.1)
            if drop:
                msg += "\n\n" + drop
        await message.answer(msg[:4000])


@router.message(Command("artifacts", "آرتیفکت", "آرتیفکتها", "artifact"))
async def cmd_artifacts(message: Message):
    from services.artifacts import status_text
    await message.answer(status_text(message.from_user.id))


@router.message(Command("equipartifact", "تجهیزآرتیفکت", "equipart"))
async def cmd_equip_artifact(message: Message):
    from services.artifacts import equip
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("فرمت: /equipartifact شناسه\n/artifacts")
        return
    await message.answer(equip(message.from_user.id, parts[1].strip()))


@router.message(Command("league", "لیگ", "فصل", "seasonleague"))
async def cmd_league(message: Message):
    from services.season_league import status_text
    await message.answer(status_text(message.from_user.id))


@router.message(Command("combos", "کمبو", "کمبوها", "combo"))
async def cmd_combos(message: Message):
    from services.combo_combat import status_text
    await message.answer(status_text(message.from_user.id))
