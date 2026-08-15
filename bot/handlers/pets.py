import random
from datetime import datetime, timedelta
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user
from database.models_v3 import Pet
from services.pets import (
    spawn_wild, get_user_pets, tame_pet, buy_domestic, feed_pet, train_pet,
    pet_capacity, DEFAULT_PET_SLOTS, MAX_PET_SLOTS, PALACE_UPGRADE_SLOTS,
    PALACE_UPGRADE_COST, HUNT_COOLDOWN_HOURS,
)
from services.i18n import tr
from services.economy import (
    get_or_create_wallet, exchange_to_stones, exchange_to_coins,
    exchange_up, exchange_down, wallet_text, pay_any_currency,
)

router = Router()


@router.message(Command("pets", "حیوانات", "پت", "حیوان"))
async def cmd_pets(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if not getattr(user, "pet_slots", None):
            user.pet_slots = DEFAULT_PET_SLOTS
            await session.commit()
        pets = await get_user_pets(session, user.id)
        slots = pet_capacity(user)
        last_hunt = getattr(user, "last_hunt_at", None)

    text = (
        "🐾 <b>حیوانات تو</b>\n"
        f"🏰 کاخ رامشدگان: <b>{len(pets)}</b> / <b>{slots}</b> (سقف {MAX_PET_SLOTS})\n"
    )
    if last_hunt:
        nxt = last_hunt + timedelta(hours=HUNT_COOLDOWN_HOURS)
        now = datetime.utcnow()
        if now < nxt:
            left = int((nxt - now).total_seconds())
            m = left // 60
            text += f"⏰ شکار بعدی تا {m} دقیقه دیگر\n"
        else:
            text += "✅ میتوانی شکار کنی\n"
    else:
        text += "✅ میتوانی شکار کنی\n"
    text += "\n"

    if not pets:
        text += "حیوانی نداری.\n"
    else:
        for i, p in enumerate(pets, 1):
            kind = "وحشی" if p.is_wild else "خونگی"
            text += (
                f"<b>{i}.</b> {p.name} ({p.species}) — {kind}\n"
                f"   AT:{p.attack} | DEF:{p.defense} | وفاداری:{p.loyalty}\n"
            )

    text += (
        "\n<b>دستورات:</b>\n"
        "/hunt — شکار (هر ۱ ساعت یکبار)\n"
        "/buypet — خرید خونگی (۱۰۰ سکه یا معادل)\n"
        "/petpalace — وضعیت و ارتقای کاخ رامشدگان\n"
        "/upgradepetpalace — ارتقای ظرفیت (+5)\n"
        "/petinfo شماره | /feedpet | /trainpet | /renamepet\n"
        "/sellpet | /giftpet | /releasepet"
    )
    await message.answer(text)


@router.message(Command("petpalace", "کاخرام", "کاخرامشدگان"))
async def cmd_pet_palace(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if not getattr(user, "pet_slots", None):
            user.pet_slots = DEFAULT_PET_SLOTS
            await session.commit()
        pets = await get_user_pets(session, user.id)
        slots = pet_capacity(user)
    await message.answer(
        "🏰 <b>کاخ رامشدگان</b>\n\n"
        f"ظرفیت فعلی: <b>{slots}</b>\n"
        f"اشغالشده: <b>{len(pets)}</b>\n"
        f"سقف نهایی: <b>{MAX_PET_SLOTS}</b>\n\n"
        f"هر ارتقا: +{PALACE_UPGRADE_SLOTS} ظرفیت\n"
        f"هزینه هر ارتقا: {PALACE_UPGRADE_COST} سکه (یا معادل ارز بالاتر)\n\n"
        "/upgradepetpalace — ارتقا\n"
        "شکار: هر ساعت فقط یکبار (/hunt)"
    )


@router.message(Command("upgradepetpalace", "ارتقایکاخ", "ارتقاءکاخ"))
async def cmd_upgrade_palace(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        slots = pet_capacity(user)
        if slots >= MAX_PET_SLOTS:
            await message.answer(f"کاخ در حداکثر ظرفیت است ({MAX_PET_SLOTS}).")
            return
        w = await get_or_create_wallet(session, user.id)
        ok, pay_msg = pay_any_currency(w, PALACE_UPGRADE_COST)
        if not ok:
            await message.answer(pay_msg)
            return
        user.pet_slots = min(MAX_PET_SLOTS, slots + PALACE_UPGRADE_SLOTS)
        await session.commit()
        new_s = user.pet_slots
    await message.answer(
        f"✅ کاخ رامشدگان ارتقا یافت!\n"
        f"ظرفیت: <b>{new_s}</b> / {MAX_PET_SLOTS}\n"
        f"{pay_msg}"
    )


@router.message(Command("petinfo", "اطلاعاتپت"))
async def cmd_petinfo(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "فرمت: /petinfo شماره"))
        return
    try:
        idx = int(parts[1]) - 1
    except ValueError:
        await message.answer(tr(message.from_user.id, "شماره نامعتبر"))
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        pets = await get_user_pets(session, user.id)
        if idx < 0 or idx >= len(pets):
            await message.answer(tr(message.from_user.id, "حیوان پیدا نشد. /pets"))
            return
        p = pets[idx]
    await message.answer(
        f"🐾 <b>{p.name}</b>\n"
        f"گونه: {p.species}\n"
        f"نوع: {'وحشی' if p.is_wild else 'خونگی'}\n"
        f"حمله: {p.attack}\n"
        f"دفاع: {p.defense}\n"
        f"وفاداری: {p.loyalty}/100\n"
        f"{p.description or ''}"
    )



@router.message(Command("hunt", "شکار"))
async def cmd_hunt(message: Message):
    """شکار حیوان وحشی — کولداون ۱ ساعت"""
    now = datetime.utcnow()
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if getattr(user, "is_dead", False):
            await message.answer(tr(message.from_user.id, "مردهای. /afterdeath"))
            return

        last = getattr(user, "last_hunt_at", None)
        try:
            if last is not None and getattr(last, "tzinfo", None) is not None:
                last = last.replace(tzinfo=None)
        except Exception:
            pass
        if last and now < last + timedelta(hours=HUNT_COOLDOWN_HOURS):
            left = max(0, int((last + timedelta(hours=HUNT_COOLDOWN_HOURS) - now).total_seconds()))
            mnt, sec = left // 60, left % 60
            await message.answer("⏳ هر ساعت فقط یک شکار." + chr(10) + f"مانده: {mnt} دقیقه و {sec} ثانیه")
            return

        world = getattr(user, "world", "فانی") or "فانی"
        risk = 0.35 if world != "زیرین" else 0.7
        try:
            from bot.config import HUNT_RISK_NORMAL, HUNT_RISK_UNDERWORLD
            risk = HUNT_RISK_NORMAL if world != "زیرین" else HUNT_RISK_UNDERWORLD
        except Exception:
            pass

        user.last_hunt_at = now
        roll = random.random()

        if roll < risk * 0.15:
            if getattr(user, "race", None) not in ("نامیرا", "خدایان", "قادر مطلق"):
                user.is_dead = True
                user.world = "زیرین"
                await session.commit()
                await message.answer("💀 در شکار کشته شدی. /afterdeath")
                return
        if roll < risk * 0.5:
            dmg = random.randint(3, 12)
            if hasattr(user, "blood"):
                user.blood = max(1, int(user.blood or 100) - dmg)
            await session.commit()
            await message.answer(f"🩸 زخمی شدی (−{dmg} خون). شکار فرار کرد." + chr(10) + "/pets")
            return

        try:
            pet = await spawn_wild(session)
        except Exception as e:
            await session.commit()
            await message.answer(f"❌ خطا در اسپان شکار: {type(e).__name__}: {str(e)[:180]}")
            return

        msg_a = None
        try:
            from services.achievements import check_and_award
            msg_a = await check_and_award(session, user, "first_hunt")
        except Exception:
            pass

        await session.commit()
        builder = InlineKeyboardBuilder()
        builder.button(text="رام کردن 🐺", callback_data=f"tame:{message.from_user.id}:{pet.id}")
        builder.button(text="رها کردن", callback_data=f"release:{message.from_user.id}:{pet.id}")
        builder.adjust(2)
        text_out = (
            "🌲 حیوان وحشی پیدا شد!" + chr(10) + chr(10)
            + f"<b>{pet.species}</b>" + chr(10)
            + f"حمله: {pet.attack} | دفاع: {pet.defense}" + chr(10)
            + "رام کن یا رها کن."
        )
        if msg_a:
            text_out += chr(10) + msg_a
        await message.answer(text_out, reply_markup=builder.as_markup())



@router.callback_query(F.data.startswith("tame:"))
async def cb_tame(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer()
        return
    owner_id, pet_id = int(parts[1]), int(parts[2])
    if callback.from_user.id != owner_id:
        await callback.answer()
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        pet = await session.get(Pet, pet_id)
        if not pet:
            await callback.answer(tr(callback.from_user.id, "دیگر اینجا نیست."), show_alert=True)
            return
        msg = await tame_pet(session, user, pet)
        try:
            if msg.startswith("✅"):
                from services.achievements import check_and_award
                a = await check_and_award(session, user, "first_tame")
                if a:
                    msg = msg + chr(10) + a
        except Exception:
            pass
    try:
        await callback.message.edit_text(msg)
    except Exception:
        await callback.message.answer(msg)
    await callback.answer()


@router.callback_query(F.data.startswith("release:"))
async def cb_release(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer()
        return
    owner_id, pet_id = int(parts[1]), int(parts[2])
    if callback.from_user.id != owner_id:
        await callback.answer()
        return
    async with async_session() as session:
        pet = await session.get(Pet, pet_id)
        if pet and pet.is_wild and pet.owner_id is None:
            await session.delete(pet)
            await session.commit()
    try:
        await callback.message.edit_text(tr(callback.from_user.id, "حیوان رها شد."))
    except Exception:
        pass
    await callback.answer()


@router.message(Command("buypet", "خریدپت", "خریدحیوان"))
async def cmd_buy_pet(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        msg = await buy_domestic(session, user, cost_coins=100)
    await message.answer(msg)


@router.message(Command("feedpet", "غذایپت", "غذاپت"))
async def cmd_feed_pet(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "فرمت: /feedpet شماره"))
        return
    try:
        idx = int(parts[1]) - 1
    except ValueError:
        await message.answer(tr(message.from_user.id, "شماره نامعتبر"))
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        pets = await get_user_pets(session, user.id)
        if idx < 0 or idx >= len(pets):
            await message.answer(tr(message.from_user.id, "حیوان پیدا نشد. /pets"))
            return
        msg = await feed_pet(session, pets[idx], cost=20)
    await message.answer(msg)


@router.message(Command("trainpet", "آموزشپت", "آموزشپت"))
async def cmd_train_pet(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "فرمت: /trainpet شماره"))
        return
    try:
        idx = int(parts[1]) - 1
    except ValueError:
        await message.answer(tr(message.from_user.id, "شماره نامعتبر"))
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        pets = await get_user_pets(session, user.id)
        if idx < 0 or idx >= len(pets):
            await message.answer(tr(message.from_user.id, "حیوان پیدا نشد. /pets"))
            return
        msg = await train_pet(session, pets[idx], cost=50)
    await message.answer(msg)


@router.message(Command("renamepet", "نامپت"))
async def cmd_rename_pet(message: Message):
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(tr(message.from_user.id, "فرمت: /renamepet شماره نامجدید"))
        return
    try:
        idx = int(parts[1]) - 1
    except ValueError:
        await message.answer(tr(message.from_user.id, "شماره نامعتبر"))
        return
    new_name = parts[2].strip()[:32]
    if not new_name:
        await message.answer(tr(message.from_user.id, "نام خالی است."))
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        pets = await get_user_pets(session, user.id)
        if idx < 0 or idx >= len(pets):
            await message.answer(tr(message.from_user.id, "حیوان پیدا نشد."))
            return
        pets[idx].name = new_name
        await session.commit()
    await message.answer(f"✅ نام تغییر کرد: <b>{new_name}</b>")


@router.message(Command("sellpet", "فروشحیوان", "فروشپت"))
async def cmd_sell_pet(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "فرمت: /sellpet شماره"))
        return
    try:
        idx = int(parts[1]) - 1
    except ValueError:
        await message.answer(tr(message.from_user.id, "شماره نامعتبر"))
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        pets = await get_user_pets(session, user.id)
        if idx < 0 or idx >= len(pets):
            await message.answer(tr(message.from_user.id, "حیوان پیدا نشد."))
            return
        pet = pets[idx]
        price = 50 + (pet.attack or 0) * 5 + (pet.defense or 0) * 3
        w = await get_or_create_wallet(session, user.id)
        w.coins = (w.coins or 0) + price
        name = pet.name
        await session.delete(pet)
        await session.commit()
    await message.answer(f"💰 «{name}» فروخته شد! +{price} سکه")


@router.message(Command("giftpet", "هدیهحیوان", "هدیهپت"))
async def cmd_gift_pet(message: Message):
    if not message.reply_to_message:
        await message.answer(tr(message.from_user.id, "روی پیام گیرنده ریپلای کن:\n/giftpet شماره"))
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "فرمت: /giftpet شماره"))
        return
    try:
        idx = int(parts[1]) - 1
    except ValueError:
        await message.answer(tr(message.from_user.id, "شماره نامعتبر"))
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        t = message.reply_to_message.from_user
        target = await get_or_create_user(session, t.id, t.full_name, t.username)
        pets = await get_user_pets(session, user.id)
        if idx < 0 or idx >= len(pets):
            await message.answer(tr(message.from_user.id, "حیوان پیدا نشد."))
            return
        # capacity of target
        from services.pets import can_own_more
        ok, msg = await can_own_more(session, target)
        if not ok:
            await message.answer("کاخ گیرنده پر است.\n" + msg)
            return
        pet = pets[idx]
        pet.owner_id = target.id
        name = pet.name
        await session.commit()
    await message.answer(f"🎁 «{name}» به {target.full_name} هدیه شد.")


@router.message(Command("releasepet", "آزادپت", "رهاپت"))
async def cmd_release_pet(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "فرمت: /releasepet شماره"))
        return
    try:
        idx = int(parts[1]) - 1
    except ValueError:
        await message.answer(tr(message.from_user.id, "شماره نامعتبر"))
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        pets = await get_user_pets(session, user.id)
        if idx < 0 or idx >= len(pets):
            await message.answer(tr(message.from_user.id, "حیوان پیدا نشد."))
            return
        pet = pets[idx]
        name = pet.name
        await session.delete(pet)
        await session.commit()
    await message.answer(f"🕊️ «{name}» آزاد شد.")


@router.message(Command("wallet", "کیفپول", "سکه"))
async def cmd_wallet(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
        text = wallet_text(w)
    await message.answer(text)


@router.message(Command("exchangestone"))
async def cmd_ex_stone(message: Message):
    parts = (message.text or "").split()
    n = 1
    if len(parts) >= 2:
        try:
            n = max(1, int(parts[1]))
        except ValueError:
            await message.answer("تعداد نامعتبر")
            return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        from services.economy import exchange_to_stones
        msg = await exchange_to_stones(session, user.id, n)
    await message.answer(msg)


@router.message(Command("exchangecoin"))
async def cmd_ex_coin(message: Message):
    parts = (message.text or "").split()
    n = 1
    if len(parts) >= 2:
        try:
            n = max(1, int(parts[1]))
        except ValueError:
            await message.answer("تعداد نامعتبر")
            return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        from services.economy import exchange_to_coins
        msg = await exchange_to_coins(session, user.id, n)
    await message.answer(msg)


@router.message(Command("dailycoin", "سکهروزانه", "سکه_روزانه"))
async def cmd_daily_coin(message: Message):
    from datetime import date, datetime as _dt
    uid = message.from_user.id
    today = date.today().isoformat()
    # حافظه کمکی در صورت مشکل DB
    if not hasattr(cmd_daily_coin, "_mem"):
        cmd_daily_coin._mem = {}
    if cmd_daily_coin._mem.get(uid) == today:
        await message.answer(tr(message.from_user.id, "امروز سکه روزانه را گرفتی."))
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
        last = getattr(w, "last_daily_coin", None)
        if last is not None:
            try:
                ld = last.date() if hasattr(last, "date") else last
                if str(ld)[:10] == today:
                    cmd_daily_coin._mem[uid] = today
                    await message.answer(tr(message.from_user.id, "امروز سکه روزانه را گرفتی."))
                    return
            except Exception:
                pass
        w.coins = (w.coins or 0) + 30
        try:
            w.last_daily_coin = _dt.utcnow()
        except Exception:
            pass
        await session.commit()
        total = w.coins or 0
    cmd_daily_coin._mem[uid] = today
    await message.answer(f"🪙 +۳۰ سکه روزانه!" + chr(10) + f"موجودی: {total}")



@router.message(Command("exchangeup", "ارتقایارز"))
async def cmd_exchange_up(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "فرمت: /exchangeup heavenly | celestial | god [تعداد]"))
        return
    kind = parts[1]
    try:
        amount = int(parts[2]) if len(parts) > 2 else 1
    except ValueError:
        amount = 1
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        msg = await exchange_up(session, user.id, kind, amount)
    await message.answer(msg)


@router.message(Command("exchangedown", "تبدیلپایین", "تبدیل_پایین", "نزولارز"))
async def cmd_exchange_down(message: Message):
    """تبدیل ارز بالاتر به پایینتر"""
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(
            "⬇️ <b>تبدیل به ارز پایینتر</b>" + chr(10)
            + "/exchangedown spirit [n] — روحی → سکه (×1000)" + chr(10)
            + "/exchangedown heavenly [n] — بهشتی → روحی (×1000)" + chr(10)
            + "/exchangedown celestial [n] — آسمانی → بهشتی (×1000)" + chr(10)
            + "/exchangedown god [n] — خدا → آسمانی (×1e9)" + chr(10)
            + "مثال: /exchangedown heavenly 2"
        )
        return
    kind = parts[1]
    amount = 1
    if len(parts) >= 3:
        try:
            amount = max(1, int(parts[2]))
        except ValueError:
            await message.answer("تعداد نامعتبر")
            return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        from services.economy import exchange_down
        msg = await exchange_down(session, user.id, kind, amount)
    await message.answer(msg)
