from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command
from database.engine import async_session
from database.crud import get_or_create_user
from services.open_world import ALIASES, migrate_player_position, move, location_text, spawn_event, spawn_boss, create_city, create_country, feed, drink, hit_boss, world_state, boss_attack_text, current_sky, sky_info, challenge_heaven_stair, forced_sky_ascension, SKIES

router = Router()

async def ensure_world_user(session, message):
    user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
    migrate_player_position(user)
    return user

@router.message(Command("world", "جهان", "موقعیت", "مختصات", "نقشهجدید"))
async def cmd_world(message: Message):
    async with async_session() as session:
        user = await ensure_world_user(session, message)
        await session.commit()
        text = location_text(user)
    await message.answer(text)

@router.message(Command("north", "شمال", "move_north"))
@router.message(Command("south", "جنوب", "move_south"))
@router.message(Command("east", "شرق", "move_east"))
@router.message(Command("west", "غرب", "move_west"))
async def cmd_move(message: Message):
    raw = (message.text or "").split()[0].lstrip("/").lower()
    direction = {"north":"north","شمال":"north","move_north":"north","south":"south","جنوب":"south","move_south":"south","east":"east","شرق":"east","move_east":"east","west":"west","غرب":"west","move_west":"west"}.get(raw)
    if not direction:
        return
    async with async_session() as session:
        user = await ensure_world_user(session, message)
        result = move(user, direction)
        await session.commit()
        if result.get("cooldown"):
            await message.answer(f"⏳ برای حرکت بعدی {result['cooldown']} ثانیه صبر کن."); return
        text = f"🧭 به <b>{result['direction']}</b> رفتی.\n📍 مختصات جدید: <b>({result['x']}, {result['y']})</b>\n🍖 {user.hunger}% | 💧 {user.thirst}%"
        if result.get("encounter"):
            text += f"\n\n✨ اتفاق: {result['encounter']}"
        if user.hunger == 0 or user.thirst == 0:
            text += "\n\n⚠️ نیاز بقا به صفر رسید؛ این وضعیت به‌تنهایی تو را نمی‌کشد. غذا/آب مصرف کن."
    await message.answer(text)

@router.message(Command("newcity", "ساختشهر", "شهرسازی"))
async def cmd_new_city(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("فرمت: /newcity نام شهر")
        return
    async with async_session() as session:
        user = await ensure_world_user(session, message)
        _, text = create_city(user, parts[1])
        await session.commit()
    await message.answer(text)

@router.message(Command("newcountry", "ساختکشور", "کشورسازی"))
async def cmd_new_country(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("فرمت: /newcountry نام کشور")
        return
    async with async_session() as session:
        user = await ensure_world_user(session, message)
        _, text = create_country(user, parts[1])
        await session.commit()
    await message.answer(text)

@router.message(Command("eat", "غذا", "گرسنه"))
async def cmd_eat(message: Message):
    async with async_session() as session:
        user = await ensure_world_user(session, message)
        feed(user); await session.commit()
    await message.answer(f"🍖 غذا خوردی. گرسنگی: {user.hunger}%")

@router.message(Command("drink", "آب", "تشنگی"))
async def cmd_drink(message: Message):
    async with async_session() as session:
        user = await ensure_world_user(session, message)
        drink(user); await session.commit()
    await message.answer(f"💧 آب نوشیدی. تشنگی: {user.thirst}%")

@router.message(Command("skies", "۹آسمان", "نهآسمان", "آسمانها", "آسمان"))
async def cmd_skies(message: Message):
    async with async_session() as session:
        user = await ensure_world_user(session, message)
        info = sky_info(user)
        await session.commit()
    lines = [f"☁️ <b>۹ آسمان — آسمان {info['number']}</b>", f"🌌 {info['name']}", f"📍 مختصات: ({user.world_x}, {user.world_y})", "", f"📜 {info['lore']}", "", "🏙️ مکان‌های شاخص:"]
    lines.extend(f"• {x}" for x in info['landmarks'])
    lines.append("\n⬆️ برای صعود: «پلکان بهشت» را به چالش بکش یا وقتی تذهیبت از پیشرفته عبور کرد، صعود اجباری انجام می‌شود.")
    await message.answer("\n".join(lines))

@router.message(Command("heavenstair", "پلکانبهشت", "پلکان", "صعود"))
async def cmd_heaven_stair(message: Message):
    async with async_session() as session:
        user = await ensure_world_user(session, message)
        from services.power import calc_power
        power = int((await calc_power(session, user)).get("total", 1))
        result = challenge_heaven_stair(user, power)
        await session.commit()
    await message.answer(result["message"])

@router.message(Command("worldcities", "شهرهایجهان", "شهرها", "قلمروهایجهان"))
async def cmd_world_cities(message: Message):
    async with async_session() as session:
        user = await ensure_world_user(session, message)
        d = world_state()
        info = sky_info(user)
        cities = d.get("cities", {})
        rows = [v for v in cities.values() if int(v.get("sky", 1) or 1) == current_sky(user)]
        await session.commit()
    text = [f"🏙️ <b>شهرها و قلمروهای {info['name']}</b>", "", "شهرهای شناخته‌شده:"]
    if rows:
        text.extend(f"• {v['name']} — ({v.get('x',0)}, {v.get('y',0)})" for v in rows[:30])
    else:
        text.append("• هنوز شهر بازیکنی در این آسمان ثبت نشده است.")
    text += ["", "مکان‌های بزرگ:"] + [f"• {x}" for x in info['landmarks']]
    text.append("\nهر بازیکن می‌تواند دور از شهر آغازین شهر بسازد و بعد آن را هسته یک قلمرو یا کشور قرار دهد.")
    await message.answer("\n".join(text))

@router.message(Command("landmarks", "مکانها", "مکانهایآسمان", "مکانهایجدید"))
async def cmd_landmarks(message: Message):
    async with async_session() as session:
        user = await ensure_world_user(session, message)
        info = sky_info(user)
        await session.commit()
    await message.answer("🗺️ <b>مکان‌های مهم این آسمان</b>\n\n" + "\n".join(f"📍 {x}" for x in info['landmarks']) + "\n\nحرکت کن تا نقاط ناشناخته و شهرهای قابل کشف پیدا شوند.")

@router.message(Command("worldevent", "رویدادجهان", "رویدادجدید"))
async def cmd_world_event(message: Message):
    e = spawn_event(force=True)
    await message.answer(f"⚠️ <b>{e['name']}</b>\n{e['desc']}\n📍 مختصات: ({e['x']}, {e['y']})")

@router.message(Command("worldboss", "باسجهان", "باسجدید"))
async def cmd_world_boss(message: Message):
    b = spawn_boss()
    await message.answer(f"👑 <b>{b['name']}</b>\n{b['subtitle']}\n❤️ HP: {b['hp']:,}/{b['max_hp']:,}\n📍 مختصات: ({b['x']}, {b['y']})\n\nبه مختصات باس برو؛ نبرد مکان‌محور است.")

@router.message(Command("bossattack", "حملهبهباس", "ضربهباس"))
async def cmd_boss_attack(message: Message):
    async with async_session() as session:
        user = await ensure_world_user(session, message)
        b = world_state().get("boss")
        if not b or b.get("hp", 0) <= 0:
            await message.answer("باسی فعال نیست. /worldboss"); return
        if (user.world_x, user.world_y) != (b.get("x"), b.get("y")):
            await message.answer(f"📍 تو ({user.world_x},{user.world_y}) هستی؛ باس در ({b['x']},{b['y']}) است."); return
        from services.power import calc_power
        p = await calc_power(session, user)
        b, dmg = hit_boss(user.telegram_id, max(100, int(p.get("total", 100)) // 3))
        await session.commit()
    if b.get("hp", 0) <= 0:
        async with async_session() as reward_session:
            u=await get_or_create_user(reward_session,message.from_user.id,message.from_user.full_name,message.from_user.username)
            from services.economy import get_or_create_wallet
            w=await get_or_create_wallet(reward_session,u.id)
            w.eternal_ink=int(getattr(w,"eternal_ink",0) or 0)+1
            await reward_session.commit()
        await message.answer("🏆 <b>ختمِ کلام شکست!</b>\nسیمرغِ خطوطِ غبارآلود فروپاشید.\n🪶 +۱ جوهر ازلی\n📜 دانش فراموش‌شده به یادگار ماند.")
    else:
        await message.answer(f"⚔️ ضربه زدی: {dmg:,}\n❤️ باس: {b['hp']:,}/{b['max_hp']:,}\n\n{boss_attack_text(b)}")

@router.message(F.text.func(lambda t: bool(t) and not t.strip().startswith("/") and t.strip().lower() in ALIASES))
async def text_move(message: Message):
    raw = (message.text or "").strip().lower()
    direction = ALIASES.get(raw)
    if not direction or raw.startswith("/"):
        return
    async with async_session() as session:
        user = await ensure_world_user(session, message)
        result = move(user, direction)
        await session.commit()
    if result.get("cooldown"):
        await message.answer(f"⏳ برای حرکت بعدی {result['cooldown']} ثانیه صبر کن."); return
    text = f"🧭 {result['direction']} → ({result['x']}, {result['y']})\n🍖 {user.hunger}% | 💧 {user.thirst}%"
    if result.get("encounter"):
        text += f"\n✨ {result['encounter']}"
    await message.answer(text)
