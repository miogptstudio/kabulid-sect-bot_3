from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from database.engine import async_session
from database.crud import get_or_create_user
from services.prison import try_bail, check_prison_block, kills_today, BAIL_HEAVENLY
from services.economy import get_or_create_wallet, pay_any_currency
from services.season import season_text
from services.i18n import tr

router = Router()

BLACK_MARKET = [
    {"name": "خنجر سیاه", "price": 2000, "desc": "سلاح غیرقانونی +۱۵ قدرت"},
    {"name": "قرص سم‌زدا فوری", "price": 1500, "desc": "پاک کردن سم فوری"},
    {"name": "نقشه زندان", "price": 5000, "desc": "اطلاعات فرار (نمایشی)"},
    {"name": "سنگ روحی دزدی", "price": 3000, "desc": "+3 سنگ روحی"},
    {"name": "چای قاچاق", "price": 8000, "desc": "+20000 انرژی"},
]


@router.message(Command("bail", "آزادی‌زندان", "وثیقه"))
async def cmd_bail(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        msg = await try_bail(session, user)
    await message.answer(msg)


@router.message(Command("prison", "زندان"))
async def cmd_prison(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        block = await check_prison_block(session, user)
        if block:
            await message.answer(block)
            return
    await message.answer(
        f"آزاد هستی." + chr(10)
        + f"قتل امروز: {kills_today(message.from_user.id)}/3" + chr(10)
        + f"با بیش از ۳ قتل در روز → {5} ساعت زندان." + chr(10)
        + f"وثیقه: /bail ({BAIL_HEAVENLY} سنگ بهشتی)"
    )


@router.message(Command("blackmarket", "بازار‌سیاه", "بازارسیاه"))
async def cmd_black_market(message: Message):
    text = "🕶 <b>بازار سیاه</b>" + chr(10) + "خرید پرریسک — فقط نقد." + chr(10) + chr(10)
    for i, it in enumerate(BLACK_MARKET, 1):
        text += f"{i}. {it['name']} — {it['price']} سکه" + chr(10) + f"   {it['desc']}" + chr(10)
    text += chr(10) + "/buyblack شماره"
    await message.answer(text)


@router.message(Command("buyblack", "خرید‌سیاه"))
async def cmd_buy_black(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "/buyblack شماره"))
        return
    try:
        idx = int(parts[1]) - 1
    except ValueError:
        await message.answer(tr(message.from_user.id, "شماره نامعتبر"))
        return
    if idx < 0 or idx >= len(BLACK_MARKET):
        await message.answer(tr(message.from_user.id, "نامعتبر"))
        return
    it = BLACK_MARKET[idx]
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        block = await check_prison_block(session, user)
        if block:
            await message.answer(block)
            return
        w = await get_or_create_wallet(session, user.id)
        ok, pay_msg = pay_any_currency(w, it["price"])
        if not ok:
            await message.answer(pay_msg)
            return
        extra = ""
        if "سنگ روحی" in it["name"]:
            w.spirit_stones = (w.spirit_stones or 0) + 3
            extra = "+3 سنگ روحی"
        elif "چای" in it["name"]:
            from services.cultivation import add_energy
            res = await add_energy(session, user.id, 20000)
            extra = f"انرژی: {res.get('energy')}"
        await session.commit()
    await message.answer(f"✅ {it['name']} خریدی." + chr(10) + pay_msg + chr(10) + extra)


@router.message(Command("season", "فصل"))
async def cmd_season(message: Message):
    await message.answer(season_text())


@router.message(Command("train", "تمرین", "زمین‌تمرین", "training"))
async def cmd_train(message: Message):
    parts = (message.text or "").split()
    minutes = 60
    if len(parts) >= 2:
        try:
            minutes = int(parts[1])
        except ValueError:
            minutes = 60
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        from services.training import start_training
        msg = await start_training(session, user, minutes)
    await message.answer(msg)


@router.message(Command("trainstatus", "وضعیت‌تمرین"))
async def cmd_train_status(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        from services.training import train_status
        msg = await train_status(session, user)
    await message.answer(msg)


@router.message(Command("trainclaim", "پایان‌تمرین", "دریافت‌تمرین"))
async def cmd_train_claim(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        from services.training import claim_training
        msg = await claim_training(session, user)
    await message.answer(msg)
