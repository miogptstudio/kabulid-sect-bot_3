from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from database.engine import async_session
from database.crud import get_or_create_user
from services.power import calc_power
from services.cities import (
    CITIES, ensure_user_city, get_city, list_cities_text, NAME_TO_ID
)

router = Router()


@router.message(Command("power", "قدرت"))
async def cmd_power(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        p = await calc_power(session, user)
    await message.answer(
        f"⚔️ <b>قدرت رزمی</b>\n\n"
        f"مجموع: <b>{p['total']}</b>\n"
        f"├ پایه/سطح: {p['base']}\n"
        f"├ رتبه: {p['rank']}\n"
        f"├ تذهیب ({p['realm_name']}): {p['realm']}\n"
        f"├ ریشه ({p['root_name']}): {p['root']}\n"
        f"└ سلاح/آیتم: {p['weapon']}\n\n"
        f"این عدد در دوئل شانس برد را تغییر می‌دهد."
    )


@router.message(Command("cities", "شهرها", "شهر"))
async def cmd_cities(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        cid = await ensure_user_city(session, user)
        cid = user.city or "kabul"
    await message.answer(list_cities_text(cid))


@router.message(Command("travel", "سفر"))
async def cmd_travel(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("فرمت: /travel نام‌شهر\nمثال: /travel هرات\nلیست: /cities")
        return
    name = parts[1].strip()
    city_id = NAME_TO_ID.get(name) or NAME_TO_ID.get(name.lower())
    if not city_id:
        await message.answer("شهر پیدا نشد. /cities")
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        user.city = city_id
        await session.commit()
    c = get_city(city_id)
    await message.answer(f"🗺️ به <b>{c['name']}</b> سفر کردی.\n{c['desc']}")


@router.message(Command("mate", "جفت‌گیری", "جفتگیری"))
async def cmd_mate_help(message: Message):
    await message.answer(
        "💞 <b>جفت‌گیری و خانواده</b>\n\n"
        "۱) اول هر دو /gender بزنید (مرد / زن)\n"
        "۲) تذهیب دوگانه: ریپلای + /dual\n"
        "   (فقط مرد و زن، هر دو ریشه و تکنیک)\n"
        "۳) ازدواج: ریپلای + /marry → نامزدی ۴۸س → قبول زن\n"
        "۴) شانس بسیار نادر فرزند بعد از تذهیب دوگانه\n"
        "۵) /wives وضعیت خانواده | /divorce طلاق\n\n"
        "ازدواج اجباری وجود ندارد."
    )


WORLDS = ["فانی", "بهشتی", "زیرین"]


@router.message(Command("worlds", "دنیاها", "دنیا"))
async def cmd_worlds(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = getattr(user, "world", None) or "فانی"
    await message.answer(
        f"🌌 <b>دنیاها</b>\n\n"
        f"دنیای فعلی تو: <b>{w}</b>\n\n"
        f"• فانی — دنیای عادی انسان‌ها و فرقه‌ها\n"
        f"• بهشتی — انرژی بیشتر، خطر کمتر\n"
        f"• زیرین — خطر مرگ بالا، پاداش بیشتر\n\n"
        f"/goworld فانی|بهشتی|زیرین"
    )


@router.message(Command("goworld", "رفتن‌دنیا"))
async def cmd_go_world(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or parts[1].strip() not in WORLDS:
        await message.answer("فرمت: /goworld فانی|بهشتی|زیرین")
        return
    world = parts[1].strip()
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        user.world = world
        await session.commit()
    await message.answer(f"🌌 وارد دنیای <b>{world}</b> شدی.")


@router.message(Command("dimension", "بعد", "بُعد"))
async def cmd_dimension(message: Message):
    """بُعد این چت/گروه"""
    from services.dimension import get_or_create_group_dim
    chat = message.chat
    async with async_session() as session:
        g = await get_or_create_group_dim(
            session, chat.id, getattr(chat, "title", None) or "خصوصی"
        )
    await message.answer(
        f"🌀 <b>بُعد این مکان</b>\n\n"
        f"نام: {g.name}\n"
        f"نوع: <b>{g.dimension_type}</b>\n"
        f"Chat ID: <code>{g.chat_id}</code>\n\n"
        f"هر گروه تلگرام بُعد جدا دارد.\n"
        f"مدیر گروه (سازنده ربات): /setdimension فانی|بهشتی|زیرین"
    )


@router.message(Command("setdimension", "تنظیم‌بعد"))
async def cmd_set_dimension(message: Message):
    from bot.config import ADMIN_IDS
    from services.dimension import set_group_dimension, DIM_TYPES
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("فقط سازنده ربات می‌تواند بُعد گروه را عوض کند.")
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or parts[1].strip() not in DIM_TYPES:
        await message.answer("فرمت: /setdimension فانی|بهشتی|زیرین")
        return
    async with async_session() as session:
        g = await set_group_dimension(session, message.chat.id, parts[1].strip())
    await message.answer(f"✅ بُعد این گروه: <b>{g.dimension_type}</b>")
