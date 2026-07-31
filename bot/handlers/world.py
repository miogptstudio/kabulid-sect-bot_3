from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from database.engine import async_session
from database.crud import get_or_create_user
from services.power import calc_power
from services.cities import (
    CITIES, ensure_user_city, get_city, list_cities_text, NAME_TO_ID, city_detail_text
)
from bot.config import ADMIN_IDS

router = Router()
WORLDS = ["فانی", "بهشتی", "زیرین"]


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
        f"در دوئل و /kill اثر دارد."
    )


@router.message(Command("cities", "شهرها", "کشورها"))
async def cmd_cities(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        await ensure_user_city(session, user)
        cid = user.city or "tehran"
    await message.answer(list_cities_text(cid))


@router.message(Command("mycity", "شهر‌من"))
async def cmd_mycity(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        await ensure_user_city(session, user)
        c = get_city(user.city or "tehran")
    await message.answer(city_detail_text(c))


@router.message(Command("travel", "سفر"))
async def cmd_travel(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("فرمت: /travel نام‌شهر\nمثال: /travel بندرعباس\nلیست: /cities")
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
        try:
            from services.missions_progress import bump_mission
            await bump_mission(session, user.id, "travel")
        except Exception:
            pass
    c = get_city(city_id)
    await message.answer(
        f"🗺️ به <b>{c['name']}</b> ({c['country']}) سفر کردی.\n"
        f"مرحله خاص: <b>{c['stage']}</b>\n{c['desc']}"
    )


@router.message(Command("worlds", "دنیاها", "دنیا"))
async def cmd_worlds(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = getattr(user, "world", None) or "فانی"
    await message.answer(
        f"🌌 <b>دنیاها</b>\n\nفعلی: <b>{w}</b>\n\n"
        f"• فانی — عادی\n• بهشتی — امن‌تر\n• زیرین — خطرناک‌تر\n\n"
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


@router.message(Command("mate", "جفت‌گیری", "جفتگیری"))
async def cmd_mate_help(message: Message):
    await message.answer(
        "💞 <b>جفت‌گیری و خانواده</b>\n\n"
        "۱) /gender (دائمی)\n"
        "۲) ریپلای + /dual\n"
        "۳) ریپلای + /marry\n"
        "۴) /wives · /divorce"
    )


@router.message(Command("dimension", "بعد", "بُعد"))
async def cmd_dimension(message: Message):
    from services.dimension import get_or_create_group_dim
    chat = message.chat
    async with async_session() as session:
        g = await get_or_create_group_dim(
            session, chat.id, getattr(chat, "title", None) or "خصوصی"
        )
    await message.answer(
        f"🌀 <b>بُعد این مکان</b>\nنام: {g.name}\nنوع: <b>{g.dimension_type}</b>\n"
        f"Chat: <code>{g.chat_id}</code>\n\n"
        f"ادمین: /setdimension فانی|بهشتی|زیرین"
    )


@router.message(Command("setdimension", "تنظیم‌بعد"))
async def cmd_set_dimension(message: Message):
    from services.dimension import set_group_dimension, DIM_TYPES
    if message.from_user.id not in ADMIN_IDS:
        await message.answer("فقط سازنده ربات.")
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or parts[1].strip() not in DIM_TYPES:
        await message.answer("فرمت: /setdimension فانی|بهشتی|زیرین")
        return
    async with async_session() as session:
        g = await set_group_dimension(session, message.chat.id, parts[1].strip())
    await message.answer(f"✅ بُعد گروه: <b>{g.dimension_type}</b>")
