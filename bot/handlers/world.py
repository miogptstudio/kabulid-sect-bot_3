from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from database.engine import async_session
from database.crud import get_or_create_user
from services.power import calc_power
from services.cities import (
    CITIES, ALL_CITIES, HEAVEN_CITIES, UNDER_CITIES,
    ensure_user_city, get_city, list_cities_text, NAME_TO_ID, city_detail_text,
    cities_for_world, CITY_HIDDEN_WEAPONS,
)
from bot.config import ADMIN_IDS

router = Router()
from services.cities import ALL_WORLDS, WORLD_DEFAULT_CITY
from services.i18n import tr
WORLDS = list(ALL_WORLDS)


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
        cid = await ensure_user_city(session, user)
        world = getattr(user, "world", None) or "فانی"
    text = list_cities_text(cid, world=world)
    text += f"\n\nدنیای فعلی: <b>{world}</b>\n/goworld برای تغییر دنیا\n/explorecity برای کاوش شهر فعلی"
    await message.answer(text[:4000])



@router.message(Command("mycity", "شهرمن"))
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
        await message.answer(
            "فرمت: /travel نامشهر\n"
            "مثال: /travel بندرعباس\n"
            "لیست: /cities\n"
            "شهرهای بهشتی و زیرین بعد از /goworld"
        )
        return
    name = parts[1].strip()
    city_id = NAME_TO_ID.get(name)
    if not city_id:
        # partial match
        for n, i in NAME_TO_ID.items():
            if name in n or n in name:
                city_id = i
                break
    if not city_id:
        await message.answer(tr(message.from_user.id, "شهر پیدا نشد. /cities"))
        return
    city = get_city(city_id)
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        world = getattr(user, "world", None) or "فانی"
        cworld = city.get("world") or "فانی"
        if cworld != world and city.get("world"):
            await message.answer(
                f"این شهر مال دنیای <b>{cworld}</b> است.\n"
                f"دنیای تو: <b>{world}</b>\n"
                f"اول /goworld {cworld}"
            )
            return
        user.city = city_id
        await session.commit()
        try:
            from services.missions_progress import bump_mission
            await bump_mission(session, user.id, "travel")
        except Exception:
            pass
    await message.answer(
        f"✈️ رسیدی به <b>{city['name']}</b>\n"
        + city_detail_text(city)
        + "\n\n/explorecity را بزن شاید چیزی پیدا کنی."
    )



@router.message(Command("worlds", "دنیاها", "دنیا"))
async def cmd_worlds(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        cur = getattr(user, "world", None) or "فانی"
    lines = ["🌌 <b>دنیاها</b>", "", f"فعلی: <b>{cur}</b>", ""]
    for name in WORLDS:
        lines.append("• " + name)
    lines += ["", "/goworld نامدنیا", "/cities — شهرهای دنیای فعلی", "/cave — غار شهر"]
    await message.answer(chr(10).join(lines))


@router.message(Command("goworld", "رفتندنیا"))
async def cmd_go_world(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or parts[1].strip() not in WORLDS:
        await message.answer(
            "فرمت: /goworld نامدنیا" + chr(10) + " | ".join(WORLDS)
        )
        return
    world = parts[1].strip()
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        user.world = world
        user.city = WORLD_DEFAULT_CITY.get(world, "tehran")
        await session.commit()
    await message.answer(
        f"🌌 وارد دنیای <b>{world}</b> شدی." + chr(10)
        + "/cities — شهرها | /cave — غار | /travel نامشهر"
    )


@router.message(Command("mate", "جفتگیری", "جفتگیری"))
async def cmd_mate_help(message: Message):
    await message.answer(
        "💞 <b>جفتگیری و خانواده</b>\n\n"
        "۱) /gender (دائمی)\n"
        "۲) ریپلای + /dual\n"
        "۳) ریپلای + /marry\n"
        "۴) /wives · /divorce\n\n""با خدمتکار:\n""/dualservant شماره · /childservant شماره · /mychildren"
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


@router.message(Command("setdimension", "تنظیمبعد"))
async def cmd_set_dimension(message: Message):
    from services.dimension import set_group_dimension, DIM_TYPES
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(tr(message.from_user.id, "فقط سازنده ربات."))
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2 or parts[1].strip() not in DIM_TYPES:
        await message.answer(tr(message.from_user.id, "فرمت: /setdimension فانی|بهشتی|زیرین"))
        return
    async with async_session() as session:
        g = await set_group_dimension(session, message.chat.id, parts[1].strip())
    await message.answer(f"✅ بُعد گروه: <b>{g.dimension_type}</b>")


@router.message(Command("explorecity", "کاوششهر", "کاوش"))
async def cmd_explore_city(message: Message):
    """کاوش شهر فعلی — سلاح مخفی فقط بار اول"""
    import json
    import random
    from sqlalchemy import select
    from database.models_v3 import ShopItem, UserInventory, Building
    from services.economy import get_or_create_wallet

    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        cid = await ensure_user_city(session, user)
        city = get_city(cid)
        world = getattr(user, "world", None) or "فانی"

        visited = []
        raw = getattr(user, "first_cities", None)
        if raw:
            try:
                visited = json.loads(raw) if isinstance(raw, str) else list(raw)
            except Exception:
                visited = []

        already = cid in visited
        lines = [
            f"🔍 <b>کاوش: {city['name']}</b>",
            f"دنیا: {world}",
            city_detail_text(city),
            "",
        ]

        if not already:
            visited.append(cid)
            user.first_cities = json.dumps(visited, ensure_ascii=False)
            w = await get_or_create_wallet(session, user.id)
            coins = random.randint(10, 40)
            w.coins = (w.coins or 0) + coins
            reward_parts = [f"+{coins} سکه"]

            gun = CITY_HIDDEN_WEAPONS.get(cid)
            if gun:
                gname, gpower = gun
                r = await session.execute(select(ShopItem).where(ShopItem.name == gname))
                item = r.scalar_one_or_none()
                if not item:
                    br = await session.execute(
                        select(Building).where(Building.building_type == "آهنگری")
                    )
                    b = br.scalar_one_or_none()
                    if not b:
                        b = Building(name="آهنگری", building_type="آهنگری", description="اسلحه")
                        session.add(b)
                        await session.flush()
                    item = ShopItem(
                        name=gname,
                        item_type="weapon",
                        description=f"سلاح مخفی شهر {city['name']}",
                        price=0,
                        effect={"duel_power": gpower, "hidden_gun": True},
                        is_active=True,
                        building_id=b.id,
                    )
                    session.add(item)
                    await session.flush()
                inv_r = await session.execute(
                    select(UserInventory).where(
                        UserInventory.user_id == user.id,
                        UserInventory.item_id == item.id,
                    )
                )
                inv = inv_r.scalar_one_or_none()
                if inv:
                    inv.quantity = (inv.quantity or 1) + 1
                else:
                    session.add(UserInventory(user_id=user.id, item_id=item.id, quantity=1))
                reward_parts.append(f"🔫 سلاح مخفی: <b>{gname}</b> (قدرت {gpower})")

            if random.random() < 0.25:
                w.coins = (w.coins or 0) + 15
                reward_parts.append("+۱۵ سکه اضافی (شانسی)")

            await session.commit()
            try:
                from services.missions_progress import bump_mission
                await bump_mission(session, user.id, "explore")
            except Exception:
                pass

            lines.append("🎁 <b>اولین بازدید این شهر!</b>")
            lines.extend(reward_parts)
        else:
            if random.random() < 0.3:
                w = await get_or_create_wallet(session, user.id)
                c = random.randint(1, 8)
                w.coins = (w.coins or 0) + c
                await session.commit()
                lines.append(f"بازدید تکراری. +{c} سکه ناچیز.")
            else:
                lines.append("قبلاً اینجا را کاویدهای. چیز تازهای نیست.")

        lines.append("")
        lines.append("/travel نامشهر — رفتن به شهر دیگر")
        lines.append("/cities — لیست شهرهای دنیای فعلی")
        await message.answer(chr(10).join(lines))


@router.message(Command("region8", "هشتجهان", "جهاناولیه"))
async def cmd_region8(message: Message):
    from services.eight_worlds import status_text
    await message.answer(status_text(message.from_user.id))


@router.message(Command("enter8", "ورودهشتجهان"))
async def cmd_enter8(message: Message):
    from services.eight_worlds import enter
    await message.answer(enter(message.from_user.id))


@router.message(Command("goregion", "منطقهبعد", "regiongo"))
async def cmd_goregion(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(
            "فرمت: /goregion ناممنطقه" + chr(10)
            + "منطقه ۱ نامش نیک است." + chr(10)
            + "منطقه ۳: والا مقام | منطقه ۴: بلند مرتبه" + chr(10)
            + "بقیه: بینام" + chr(10)
            + "⚠️ نام اشتباه = حذف دائمی اکانت"
        )
        return
    name = parts[1].strip()
    from services.eight_worlds import try_advance
    msg, wipe = try_advance(message.from_user.id, name)
    if wipe:
        async with async_session() as session:
            user = await get_or_create_user(
                session, message.from_user.id,
                message.from_user.full_name, message.from_user.username
            )
            try:
                from services.death import erase_existence
                await erase_existence(session, user)
            except Exception:
                user.is_dead = True
                await session.commit()
        await message.answer(
            "💀 نام اشتباه بود." + chr(10)
            + "اکانت برای همیشه پاک شد. از /start دوباره شروع کن."
        )
        return
    await message.answer(msg)
