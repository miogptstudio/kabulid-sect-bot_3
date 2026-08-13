from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user
from services.shop import (
    ensure_default_buildings_and_items,
    get_buildings,
    get_items_of_building,
    buy_item,
)
from database.models_v3 import ShopItem, Building
from bot.utils.panels import ensure_owner, parse_owner_data
from services.i18n import tr

router = Router()


@router.message(Command("buildings", "ساختمون", "shop", "فروشگاه", "مغازه"))
async def cmd_buildings(message: Message):
    uid = message.from_user.id
    async with async_session() as session:
        await ensure_default_buildings_and_items(session)
        buildings = await get_buildings(session)

    if not buildings:
        await message.answer(tr(message.from_user.id, "هنوز ساختمونی وجود نداره."))
        return

    builder = InlineKeyboardBuilder()
    text = (
        "🏘️ <b>مغازه / ساختمان‌ها</b>\n"
        f"(این پنل فقط برای تو کار می‌کند)\n\n"
    )
    for b in buildings:
        text += f"• {b.name}\n"
        builder.button(text=b.name, callback_data=f"building:{uid}:{b.id}")
    builder.adjust(1)

    text += "\nروی ساختمان کلیک کن. خرید با <b>همه ارزها</b> ممکن است (سکه، روحی، بهشتی، آسمانی، خدا).\nاگر سکه کم باشد از ارز بالاتر کسر می‌شود.\n/wallet"
    await message.answer(text, reply_markup=builder.as_markup())





@router.message(Command("teahouse", "چایخانه", "چای‌خانه"))
async def cmd_teahouse(message: Message):
    """ورود مستقیم به چای‌خانه با صفحه‌بندی"""
    from sqlalchemy import select as sel
    uid = message.from_user.id
    async with async_session() as session:
        await ensure_default_buildings_and_items(session)
        result = await session.execute(sel(Building).where(Building.building_type == "چای‌خانه"))
        b = result.scalar_one_or_none()
        if not b:
            b = Building(name="چای‌خانه", building_type="چای‌خانه", description="انواع چای")
            session.add(b)
            await session.commit()
            await session.refresh(b)
            await ensure_default_buildings_and_items(session)
        items = list(await get_items_of_building(session, b.id))
        bid = b.id

    if not items:
        await message.answer(tr(message.from_user.id, "چای‌خانه خالی است. /buildings را یک‌بار بزن و دوباره /teahouse"))
        return

    PER = 8
    total_pages = max(1, (len(items) + PER - 1) // PER)
    chunk = items[:PER]
    builder = InlineKeyboardBuilder()
    text = f"🍵 <b>چای‌خانه</b>" + chr(10) + f"صفحه 1/{total_pages} — {len(items)} نوع چای" + chr(10) + chr(10)
    for item in chunk:
        desc = (item.description or "")[:50]
        text += f"• <b>{item.name}</b>" + chr(10) + f"  {desc}" + chr(10) + f"  قیمت: <b>{item.price}</b> سکه" + chr(10) + chr(10)
        btn = item.name if len(item.name) <= 28 else item.name[:26] + "…"
        builder.button(text=f"خرید {btn}", callback_data=f"buyq:{uid}:{item.id}")
    builder.adjust(1)
    if total_pages > 1:
        builder.button(text="بعدی ➡️", callback_data=f"bpage:{uid}:{bid}:1")
    builder.button(text="همه ساختمان‌ها", callback_data=f"shopback:{uid}")
    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup())

@router.callback_query(F.data.startswith("building:"))
async def show_building_items(callback: CallbackQuery):
    owner_id, rest = parse_owner_data(callback.data, "building:")
    if owner_id is None:
        await callback.answer(tr(callback.from_user.id, "داده نامعتبر"), show_alert=True)
        return
    if not await ensure_owner(callback, owner_id, "مغازه"):
        return
    try:
        building_id = int(rest)
    except ValueError:
        await callback.answer(tr(callback.from_user.id, "خطا"), show_alert=True)
        return
    await _render_building(callback, owner_id, building_id, 0)


@router.callback_query(F.data.startswith("bpage:"))
async def building_page(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) < 4:
        await callback.answer()
        return
    try:
        owner_id, building_id, page = int(parts[1]), int(parts[2]), int(parts[3])
    except ValueError:
        await callback.answer()
        return
    if not await ensure_owner(callback, owner_id, "مغازه"):
        return
    await _render_building(callback, owner_id, building_id, page)


async def _render_building(callback: CallbackQuery, owner_id: int, building_id: int, page: int = 0):
    PER = 8
    async with async_session() as session:
        items = list(await get_items_of_building(session, building_id))
        building = await session.get(Building, building_id)

    if not items:
        await callback.answer(tr(callback.from_user.id, "آیتمی در این ساختمان نیست."), show_alert=True)
        return

    bname = building.name if building else "ساختمان"
    total_pages = max(1, (len(items) + PER - 1) // PER)
    page = max(0, min(page, total_pages - 1))
    chunk = items[page * PER:(page + 1) * PER]

    builder = InlineKeyboardBuilder()
    text = f"🛒 <b>{bname}</b>\nصفحه {page + 1}/{total_pages} — {len(items)} آیتم\n\n"
    for item in chunk:
        desc = (item.description or "")[:50]
        text += f"• <b>{item.name}</b>\n  {desc}\n  قیمت: <b>{item.price}</b> سکه\n\n"
        btn = item.name if len(item.name) <= 28 else item.name[:26] + "…"
        builder.button(text=f"خرید {btn}", callback_data=f"buyq:{owner_id}:{item.id}")
    builder.adjust(1)
    if page > 0:
        builder.button(text="⬅️ قبلی", callback_data=f"bpage:{owner_id}:{building_id}:{page - 1}")
    if page < total_pages - 1:
        builder.button(text="بعدی ➡️", callback_data=f"bpage:{owner_id}:{building_id}:{page + 1}")
    builder.button(text="⬅️ برگشت ساختمان‌ها", callback_data=f"shopback:{owner_id}")
    builder.adjust(2)

    try:
        await callback.message.edit_text(text, reply_markup=builder.as_markup())
    except Exception:
        try:
            await callback.message.answer(text, reply_markup=builder.as_markup())
        except Exception as e:
            await callback.answer(str(e)[:100], show_alert=True)
            return
    await callback.answer()


@router.callback_query(F.data.startswith("shopback:"))
async def shop_back(callback: CallbackQuery):
    try:
        owner_id = int(callback.data.split(":")[1])
    except (IndexError, ValueError):
        await callback.answer(tr(callback.from_user.id, "خطا"), show_alert=True)
        return
    if not await ensure_owner(callback, owner_id, "مغازه"):
        return

    async with async_session() as session:
        await ensure_default_buildings_and_items(session)
        buildings = await get_buildings(session)

    builder = InlineKeyboardBuilder()
    text = "🏘️ <b>مغازه / ساختمان‌ها</b>\n\n"
    for b in buildings:
        text += f"• {b.name}\n"
        builder.button(text=b.name, callback_data=f"building:{owner_id}:{b.id}")
    builder.adjust(1)

    await callback.message.edit_text(text, reply_markup=builder.as_markup())
    await callback.answer()



@router.callback_query(F.data.startswith("buyq:"))
async def process_buy_qty_menu(callback: CallbackQuery):
    """منوی انتخاب تعداد خرید"""
    owner_id, rest = parse_owner_data(callback.data, "buyq:")
    if owner_id is None:
        await callback.answer("داده نامعتبر", show_alert=True)
        return
    if not await ensure_owner(callback, owner_id, "مغازه"):
        return
    try:
        item_id = int(rest)
    except ValueError:
        await callback.answer("خطا", show_alert=True)
        return
    async with async_session() as session:
        item = await session.get(ShopItem, item_id)
        if not item:
            await callback.answer("آیتم پیدا نشد", show_alert=True)
            return
        name = item.name
        price = int(item.price or 0)
    builder = InlineKeyboardBuilder()
    for q in (1, 2, 3, 5, 10, 20, 50):
        builder.button(
            text=f"×{q} ({price * q:,})",
            callback_data=f"buy:{owner_id}:{item_id}:{q}",
        )
    builder.adjust(3)
    builder.button(text="انصراف", callback_data=f"shopback:{owner_id}")
    await callback.message.answer(
        f"🛒 <b>{name}</b>\nقیمت واحد: <b>{price:,}</b>\nچند تا می‌خری؟\n"
        f"(یا دستور: <code>/buyitem {item_id} تعداد</code>)",
        reply_markup=builder.as_markup(),
    )
    await callback.answer()


@router.callback_query(F.data.startswith("buy:"))
async def process_buy(callback: CallbackQuery):
    owner_id, rest = parse_owner_data(callback.data, "buy:")
    if owner_id is None:
        await callback.answer(tr(callback.from_user.id, "داده نامعتبر"), show_alert=True)
        return
    if not await ensure_owner(callback, owner_id, "مغازه"):
        return

    try:
        parts_r = rest.split(":")
        item_id = int(parts_r[0])
        qty = int(parts_r[1]) if len(parts_r) > 1 else 1
        qty = max(1, min(qty, 100))
    except ValueError:
        await callback.answer(tr(callback.from_user.id, "خطا"), show_alert=True)
        return

    try:
        async with async_session() as session:
            user = await get_or_create_user(
                session,
                callback.from_user.id,
                callback.from_user.full_name,
                callback.from_user.username,
            )
            item = await session.get(ShopItem, item_id)
            if not item:
                await callback.answer(tr(callback.from_user.id, "آیتم پیدا نشد."), show_alert=True)
                return
            msg = await buy_item(session, user, item, qty=qty)
    except Exception as e:
        msg = f"❌ خطا در خرید: {type(e).__name__}: {e}"

    # تلگرام برای alert حداکثر حدود ۲۰۰ کاراکتر
    short = msg if len(msg) <= 180 else (msg[:177] + "…")
    try:
        await callback.answer(short, show_alert=True)
    except Exception:
        await callback.answer("نتیجه خرید ارسال شد")
    try:
        await callback.message.answer(msg)
    except Exception:
        pass


@router.message(Command("inventory", "کیف", "اینونتوری"))
async def cmd_inventory(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session,
            message.from_user.id,
            message.from_user.full_name,
            message.from_user.username,
        )
        from sqlalchemy import select
        from database.models_v3 import UserInventory

        result = await session.execute(
            select(UserInventory, ShopItem)
            .join(ShopItem, UserInventory.item_id == ShopItem.id)
            .where(UserInventory.user_id == user.id)
        )
        rows = result.all()

    if not rows:
        await message.answer(tr(message.from_user.id, "کیفت خالیه. از /buildings خرید کن."))
        return

    text = "🎒 <b>کیف تو</b>\n\n"
    for i, (inv, item) in enumerate(rows, 1):
        text += f"{i}. {item.name} ×{inv.quantity}\n"
    text += "\n/use شماره [تعداد] — استفاده (مثلاً /use 1 4)\n/drop شماره [تعداد] — دور انداختن\n/buyitem نام تعداد — خرید دسته‌ای"
    await message.answer(text)


@router.message(Command("use", "استفاده"))
async def cmd_use_item(message: Message):
    """استفاده از آیتم: /use شماره [تعداد]"""
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(
            "فرمت: /use شماره [تعداد]\n"
            "اول /inventory بزن؛ شماره ردیف آیتم را ببین.\n"
            "مثال: /use 1\n"
            "مثال دسته‌ای: /use 1 4  ← چهارتا با هم"
        )
        return
    try:
        idx = int(parts[1]) - 1
    except ValueError:
        await message.answer(tr(message.from_user.id, "شماره نامعتبر"))
        return
    use_qty = 1
    if len(parts) >= 3:
        try:
            use_qty = max(1, min(int(parts[2]), 50))
        except ValueError:
            use_qty = 1

    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        from services.forbidden_lock import is_consume_locked, lock_consume, lock_message, is_forbidden_item, FORBIDDEN_TEA_NAME
        if is_consume_locked(message.from_user.id):
            await message.answer(lock_message())
            return
        from sqlalchemy import select
        from database.models_v3 import UserInventory

        result = await session.execute(
            select(UserInventory, ShopItem)
            .join(ShopItem, UserInventory.item_id == ShopItem.id)
            .where(UserInventory.user_id == user.id)
        )
        rows = result.all()
        if idx < 0 or idx >= len(rows):
            await message.answer(tr(message.from_user.id, "آیتم پیدا نشد. /inventory"))
            return
        inv, item = rows[idx]
        if inv.quantity < use_qty:
            await message.answer(f"فقط {inv.quantity} عدد داری.")
            return
        effect = item.effect or {}
        if isinstance(effect, str):
            import json
            try:
                effect = json.loads(effect)
            except Exception:
                effect = {}
        if not isinstance(effect, dict):
            effect = {}
        msg_parts = [f"✅ از «{item.name}» استفاده کردی."]
        # چای/آیتم ممنوعه → قفل مصرف ابدی
        msg_parts = []
        if (item.item_type or "") == "pill" or "قرص" in (item.name or ""):
            from services.pill_limit import register_pill
            from services.cultivation import get_or_create_cultivation as _goc
            _cult = await _goc(session, user.id)
            _okp, _pillmsg, _pill_died = register_pill(message.from_user.id, _cult.realm or "بیداری")
            if _pill_died:
                user.is_dead = True
                user.blood = 0
                inv.quantity = max(0, (inv.quantity or 1) - 1)
                if inv.quantity <= 0:
                    await session.delete(inv)
                await session.commit()
                await message.answer(_pillmsg + chr(10) + "💀 /afterdeath")
                return
            # ادامه با هشدار
            _pill_warn = _pillmsg
        else:
            _pill_warn = ""
        if is_forbidden_item(item.name, effect):
            lock_consume(message.from_user.id)
            msg_parts.append("☠️ قفل مصرف ابدی فعال شد — دیگر هیچ چیز مصرف نمی‌کنی.")

        if isinstance(effect, dict):
            if effect.get("knowledge"):
                from services.knowledge import add_knowledge
                tot, tier = add_knowledge(message.from_user.id, int(effect["knowledge"]))
                msg_parts.append(f"📚 دانش +{effect['knowledge']} (کل {tot} — {tier})")
            if effect.get("xp"):
                user.xp += int(effect["xp"])
                msg_parts.append(f"+{effect['xp']} XP")
            # عمر
            if effect.get("lifespan_full"):
                user.lifespan = 100
                msg_parts.append(f"❤️ عمر کامل شد (۱۰۰)")
            if effect.get("lifespan") or effect.get("life") or effect.get("age"):
                add_life = int(effect.get("lifespan") or effect.get("life") or effect.get("age") or 0)
                cur = int(getattr(user, "lifespan", 100) or 100)
                user.lifespan = min(500, cur + add_life)
                msg_parts.append(f"+{add_life} عمر (الان: {user.lifespan})")
            # انرژی مستقیم (قرص و غیره — غیر از چای که پایین‌تر هندل می‌شود)
            if effect.get("energy") and not (
                item.item_type == "tea" or effect.get("cooldown_min") or "چای" in (item.name or "")
            ):
                from services.cultivation import add_energy as _ae
                _gain = int(effect["energy"])
                _res = await _ae(session, user.id, _gain)
                msg_parts.append(f"+{_gain} انرژی تذهیب")
                if _res.get("messages"):
                    msg_parts.extend(_res["messages"])
            # خون
            if effect.get("blood"):
                b = int(effect["blood"])
                cur_b = int(getattr(user, "blood", 100) or 100)
                user.blood = min(500, cur_b + b * use_qty)
                msg_parts.append(f"+{b} خون (الان: {user.blood})")
            # محافظ
            if effect.get("protect"):
                msg_parts.append("سپر محافظ فعال شد (۱ بار).")
            if effect.get("combat_power") or effect.get("power_stat"):
                from services.knowledge import add_combat_stat
                amt = int(effect.get("combat_power") or effect.get("power_stat") or 5)
                msg_parts.append(add_combat_stat(message.from_user.id, "power", amt))
            if effect.get("combat_speed") or effect.get("speed_stat"):
                from services.knowledge import add_combat_stat
                amt = int(effect.get("combat_speed") or effect.get("speed_stat") or 5)
                msg_parts.append(add_combat_stat(message.from_user.id, "speed", amt))
            if effect.get("combat_defense") or effect.get("defense_stat"):
                from services.knowledge import add_combat_stat
                amt = int(effect.get("combat_defense") or effect.get("defense_stat") or 5)
                msg_parts.append(add_combat_stat(message.from_user.id, "defense", amt))
            if effect.get("duel_power"):
                msg_parts.append(f"قدرت دوئل (از آیتم): {effect['duel_power']}")
            if effect.get("learn_tech"):
                msg_parts.append(f"تکنیک مرتبط: {effect['learn_tech']} — /learntech")
            # چای تذهیب + انرژی با کول‌داون ۱۰ دقیقه
            if item.item_type == "tea" or effect.get("cooldown_min") or "چای" in item.name:
                from datetime import datetime, timedelta
                global _tea_cd
                try:
                    _tea_cd
                except NameError:
                    _tea_cd = {}
                uid = message.from_user.id
                wait = int(effect.get("cooldown_min") or 10)
                last = _tea_cd.get(uid)
                now = datetime.utcnow()
                if last and now < last:
                    left = int((last - now).total_seconds() // 60) + 1
                    await message.answer(f"⏳ چای هنوز اثر دارد. {left} دقیقه صبر کن.")
                    return
                from services.cultivation import add_energy
                gain = int(effect.get("energy") or 8000) * use_qty
                res = await add_energy(session, user.id, gain)
                _tea_cd[uid] = now + timedelta(minutes=wait)
                msg_parts.append(f"🍵 +{gain} انرژی تذهیب")
                if res.get("messages"):
                    msg_parts.extend(res["messages"])
                msg_parts.append(f"📊 انرژی فعلی: {res.get('energy', '?')}")
            elif effect.get("energy") and item.item_type in ("pill", "tea"):
                from services.cultivation import add_energy
                gain = int(effect["energy"]) * use_qty
                res = await add_energy(session, user.id, gain)
                msg_parts.append(f"+{gain} انرژی (×{use_qty})")
                if res.get("messages"):
                    msg_parts.extend(res["messages"])
            if effect.get("heal"):
                from services.combat_blood import heal_poison
                msg_parts.append(await heal_poison(session, user))

        # fallback نام‌محور اگر effect خالی بود
        if not effect or (isinstance(effect, dict) and not effect):
            nm = item.name or ""
            if "عمر" in nm:
                cur = int(getattr(user, "lifespan", 100) or 100)
                user.lifespan = min(500, cur + 10)
                msg_parts.append(f"+۱۰ عمر (الان: {user.lifespan})")
            elif "انرژی" in nm or "چی" in nm:
                from services.cultivation import add_energy as _ae2
                _r = await _ae2(session, user.id, 5000)
                msg_parts.append("+۵۰۰۰ انرژی")
            elif "سلامت" in nm or "پادزهر" in nm:
                try:
                    from services.combat_blood import heal_poison
                    msg_parts.append(await heal_poison(session, user))
                except Exception:
                    msg_parts.append("درمان اعمال شد.")

        # منابع از مواد
        if getattr(item, "item_type", "") in ("material", "herb_normal", "herb_spiritual"):
            from services.economy import get_or_create_wallet as _gw
            _w = await _gw(session, user.id)
            _gain = 15
            _w.coins += _gain
            msg_parts.append(f"منابع: +{_gain} سکه")
        inv.quantity -= use_qty
        if inv.quantity <= 0:
            await session.delete(inv)
        await session.commit()

    head = f"📦 استفاده ×{use_qty} از «{item.name if 'item' in dir() else 'آیتم'}»\n"
    await message.answer(head + "\n".join(msg_parts))


@router.message(Command("drop", "دورریختن", "حذف‌آیتم"))
async def cmd_drop_item(message: Message):
    """دور انداختن آیتم: /drop شماره [تعداد]"""
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "فرمت: /drop شماره\nیا /drop شماره تعداد\nمثال: /drop 1"))
        return
    try:
        idx = int(parts[1]) - 1
        qty = int(parts[2]) if len(parts) >= 3 else 1
    except ValueError:
        await message.answer(tr(message.from_user.id, "عدد نامعتبر"))
        return

    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        from services.forbidden_lock import is_consume_locked, lock_consume, lock_message, is_forbidden_item, FORBIDDEN_TEA_NAME
        if is_consume_locked(message.from_user.id):
            await message.answer(lock_message())
            return
        from sqlalchemy import select
        from database.models_v3 import UserInventory

        result = await session.execute(
            select(UserInventory, ShopItem)
            .join(ShopItem, UserInventory.item_id == ShopItem.id)
            .where(UserInventory.user_id == user.id)
        )
        rows = result.all()
        if idx < 0 or idx >= len(rows):
            await message.answer(tr(message.from_user.id, "آیتم پیدا نشد. /inventory"))
            return
        inv, item = rows[idx]
        if qty < 1 or qty > inv.quantity:
            await message.answer(f"تعداد نامعتبر (داری: {inv.quantity})")
            return
        inv.quantity -= qty
        name = item.name
        if inv.quantity <= 0:
            await session.delete(inv)
        await session.commit()

    await message.answer(f"🗑 «{name}» ×{qty} از کیف حذف شد.")


@router.message(Command("gift", "هدیه", "بده"))
async def cmd_gift_item(message: Message):
    """هدیه آیتم: ریپلای + /gift شماره"""
    if not message.reply_to_message:
        await message.answer("روی پیام گیرنده ریپلای کن و /gift شماره بزن." + chr(10) + "شماره از /inventory")
        return
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "/gift شماره"))
        return
    try:
        idx = int(parts[1]) - 1
    except ValueError:
        await message.answer(tr(message.from_user.id, "شماره نامعتبر"))
        return
    async with async_session() as session:
        giver = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        tu = message.reply_to_message.from_user
        recv = await get_or_create_user(session, tu.id, tu.full_name, tu.username)
        if giver.id == recv.id:
            await message.answer(tr(message.from_user.id, "به خودت نه."))
            return
        from sqlalchemy import select
        from database.models_v3 import UserInventory
        result = await session.execute(
            select(UserInventory, ShopItem)
            .join(ShopItem, UserInventory.item_id == ShopItem.id)
            .where(UserInventory.user_id == giver.id)
        )
        rows = result.all()
        if idx < 0 or idx >= len(rows):
            await message.answer(tr(message.from_user.id, "آیتم پیدا نشد."))
            return
        inv, item = rows[idx]
        if item.item_type == "weapon_unique" or (isinstance(item.effect, dict) and item.effect.get("unique")):
            await message.answer(tr(message.from_user.id, "آیتم یکتا قابل هدیه نیست."))
            return
        # transfer 1
        inv.quantity -= 1
        if inv.quantity <= 0:
            await session.delete(inv)
        # add to recv
        r2 = await session.execute(
            select(UserInventory).where(
                UserInventory.user_id == recv.id,
                UserInventory.item_id == item.id
            )
        )
        rinv = r2.scalar_one_or_none()
        if rinv:
            rinv.quantity += 1
        else:
            session.add(UserInventory(user_id=recv.id, item_id=item.id, quantity=1))
        await session.commit()
    await message.answer(f"🎁 «{item.name}» به {recv.full_name} هدیه شد.")


@router.message(Command("adshop", "فروشگاه‌ادمین"))
async def cmd_admin_shop(message: Message):
    from bot.config import ADMIN_IDS
    from sqlalchemy import select
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(tr(message.from_user.id, "فقط ادمین."))
        return
    async with async_session() as session:
        from services.shop import ensure_default_buildings_and_items, get_buildings, get_items_of_building
        await ensure_default_buildings_and_items(session)
        # تضمین وجود شمشیر کوروش
        r = await session.execute(select(ShopItem).where(ShopItem.name == "شمشیر کوروش بزرگ"))
        if not r.scalar_one_or_none():
            from services.shop import DEFAULT_ITEMS
            cyrus = next((x for x in DEFAULT_ITEMS if "کوروش" in x.get("name", "")), None)
            if cyrus:
                # پیدا کردن آهنگری
                buildings0 = await get_buildings(session)
                forge = next((b for b in buildings0 if "آهن" in (b.name or "") or "آهنگری" in (b.name or "")), buildings0[0] if buildings0 else None)
                if forge:
                    session.add(ShopItem(
                        building_id=forge.id,
                        name=cyrus["name"],
                        item_type=cyrus.get("item_type", "weapon_unique"),
                        description=cyrus.get("description", ""),
                        price=cyrus.get("price", 0),
                        effect=cyrus.get("effect") or {},
                    ))
                    await session.commit()
        buildings = await get_buildings(session)
        text = "🛠 <b>فروشگاه ادمین (رایگان)</b>" + chr(10)
        text += "/adget نام‌دقیق‌آیتم" + chr(10) + chr(10)
        text += "⚔️ <b>خاص / یکتا</b>" + chr(10)
        text += "• شمشیر کوروش بزرگ" + chr(10)
        text += "• شمشیر ذوالفقار" + chr(10) + chr(10)
        for b in buildings:
            items = await get_items_of_building(session, b.id)
            text += f"<b>{b.name}</b>" + chr(10)
            # اول یکتاها، بعد بقیه تا سقف
            uniques = [it for it in items if (it.item_type == "weapon_unique") or ("کوروش" in (it.name or "")) or ("ذوالفقار" in (it.name or ""))]
            rest = [it for it in items if it not in uniques]
            shown = uniques + rest
            for it in shown[:20]:
                mark = " ⭐" if it in uniques else ""
                text += f"• {it.name}{mark}" + chr(10)
            text += chr(10)
        # چند پیام اگر طولانی
        if len(text) <= 4000:
            await message.answer(text)
        else:
            await message.answer(text[:4000])
            await message.answer(text[4000:8000] if len(text) > 4000 else "")


@router.message(Command("adget", "ادمین‌بگیر"))
async def cmd_admin_get(message: Message):
    from bot.config import ADMIN_IDS
    if message.from_user.id not in ADMIN_IDS:
        await message.answer(tr(message.from_user.id, "فقط ادمین."))
        return
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "/adget نام دقیق آیتم"))
        return
    name = parts[1].strip()
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        from sqlalchemy import select
        from database.models_v3 import UserInventory
        r = await session.execute(select(ShopItem).where(ShopItem.name == name))
        item = r.scalar_one_or_none()
        if not item:
            r = await session.execute(select(ShopItem).where(ShopItem.name.contains(name)))
            item = r.scalars().first()
        if not item and "کوروش" in name:
            r = await session.execute(select(ShopItem).where(ShopItem.name.contains("کوروش")))
            item = r.scalars().first()
        if not item:
            await message.answer(tr(message.from_user.id, "آیتم پیدا نشد. /adshop"))
            return
        name = item.name
        r2 = await session.execute(
            select(UserInventory).where(
                UserInventory.user_id == user.id,
                UserInventory.item_id == item.id
            )
        )
        inv = r2.scalar_one_or_none()
        if inv:
            inv.quantity += 1
        else:
            session.add(UserInventory(user_id=user.id, item_id=item.id, quantity=1))
        if item.item_type == "weapon_unique" or (isinstance(item.effect, dict) and item.effect.get("unique") == "cyrus"):
            user.has_cyrus_sword = True
        await session.commit()
    await message.answer(f"✅ رایگان: «{name}» به کیف اضافه شد.")



# --- انتخاب با نوشتن ---
BUILDING_ALIASES = {
    "داروخانه": "داروخانه",
    "دارو": "داروخانه",
    "کیمیاگری": "کیمیاگری",
    "کیمیا": "کیمیاگری",
    "طلسم‌خانه": "طلسم‌خانه",
    "طلسم خانه": "طلسم‌خانه",
    "طلسمخانه": "طلسم‌خانه",
    "آهنگری": "آهنگری",
    "آهنگر": "آهنگری",
    "کتابخانه": "کتابخانه",
    "کتاب": "کتابخانه",
    "چای‌خانه": "چای‌خانه",
    "چایخانه": "چای‌خانه",
    "چای": "چای‌خانه",
}


@router.message(F.text.func(lambda t: bool(t) and t.strip() in BUILDING_ALIASES))
async def text_open_building(message: Message):
    """باز کردن ساختمان با نوشتن نام: داروخانه، آهنگری، ..."""
    key = BUILDING_ALIASES.get((message.text or "").strip())
    if not key:
        return
    uid = message.from_user.id
    from sqlalchemy import select as sel
    async with async_session() as session:
        await ensure_default_buildings_and_items(session)
        result = await session.execute(sel(Building).where(Building.building_type == key))
        b = result.scalar_one_or_none()
        if not b:
            result = await session.execute(sel(Building).where(Building.name.contains(key)))
            b = result.scalar_one_or_none()
        if not b:
            await message.answer(f"ساختمان «{key}» پیدا نشد. /buildings")
            return
        items = list(await get_items_of_building(session, b.id))
        bid = b.id
    if not items:
        await message.answer(f"«{key}» خالی است.")
        return
    PER = 8
    total_pages = max(1, (len(items) + PER - 1) // PER)
    chunk = items[:PER]
    builder = InlineKeyboardBuilder()
    text = f"🏪 <b>{b.name}</b>" + chr(10) + f"صفحه 1/{total_pages}" + chr(10) + chr(10)
    text += "خرید با دکمه یا بنویس: <code>خرید نام‌آیتم</code>" + chr(10) + chr(10)
    for item in chunk:
        desc = (item.description or "")[:50]
        text += f"• <b>{item.name}</b> — {item.price} سکه" + chr(10)
        if desc:
            text += f"  {desc}" + chr(10)
        btn = item.name if len(item.name) <= 28 else item.name[:26] + "…"
        builder.button(text=f"خرید {btn}", callback_data=f"buyq:{uid}:{item.id}")
    builder.adjust(1)
    if total_pages > 1:
        builder.button(text="بعدی ➡️", callback_data=f"bpage:{uid}:{bid}:1")
    builder.button(text="همه ساختمان‌ها", callback_data=f"shopback:{uid}")
    builder.adjust(1)
    await message.answer(text, reply_markup=builder.as_markup())


@router.message(F.text.regexp(r"^(?:خرید|بخر)\s+.+$"))
async def text_buy_item(message: Message):
    """خرید با نوشتن: خرید قرص طول عمر"""
    t = (message.text or "").strip()
    for prefix in ("خرید ", "بخر "):
        if t.startswith(prefix):
            name = t[len(prefix):].strip()
            break
    else:
        return
    if not name:
        await message.answer("مثال: خرید قرص طول عمر")
        return
    from sqlalchemy import select as sel
    async with async_session() as session:
        await ensure_default_buildings_and_items(session)
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        result = await session.execute(sel(ShopItem))
        items = list(result.scalars().all())
        # match exact or contains
        item = next((i for i in items if (i.name or "") == name), None)
        if not item:
            item = next((i for i in items if name in (i.name or "")), None)
        if not item:
            await message.answer(f"آیتم «{name}» پیدا نشد. اول داروخانه یا /buildings را باز کن.")
            return
        # reuse buy logic via price
        from services.economy import get_or_create_wallet, pay_any_currency
        from database.models_v3 import UserInventory
        w = await get_or_create_wallet(session, user.id)
        ok, pmsg = pay_any_currency(w, int(item.price or 0))
        if not ok:
            await message.answer(pmsg)
            return
        r = await session.execute(
            sel(UserInventory).where(
                UserInventory.user_id == user.id,
                UserInventory.item_id == item.id,
            )
        )
        inv = r.scalar_one_or_none()
        if inv:
            inv.quantity = int(inv.quantity or 0) + 1
        else:
            session.add(UserInventory(user_id=user.id, item_id=item.id, quantity=1))
        await session.commit()
        await message.answer(
            f"✅ «<b>{item.name}</b>» خریده شد." + chr(10) + pmsg + chr(10)
            + "/inventory — کیف"
        )


@router.message(Command("pillstatus", "وضعیت‌قرص", "سقف‌قرص"))
async def cmd_pill_status(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        from services.cultivation import get_or_create_cultivation
        from services.pill_limit import status, max_pills
        cult = await get_or_create_cultivation(session, user.id)
        lim = max_pills(cult.realm or "بیداری")
        await message.answer(
            status(message.from_user.id, cult.realm or "بیداری") + chr(10)
            + f"هر قلمرو بالاتر سقف را افزایش می‌دهد." + chr(10)
            + "بیش از سقف = ۶۰٪ احتمال انفجار و مرگ."
        )


@router.message(Command("buyitem", "خریدآیتم", "بخر"))
async def cmd_buyitem(message: Message):
    """خرید تعدادی: /buyitem شماره_یا_نام تعداد"""
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 2:
        await message.answer(
            "🛒 خرید دسته‌ای\n"
            "فرمت: /buyitem شماره تعداد\n"
            "یا: /buyitem نام‌آیتم تعداد\n"
            "مثال: /buyitem 3 10\n"
            "اول از /buildings لیست را ببین."
        )
        return
    qty = 1
    key = parts[1]
    if len(parts) >= 3:
        try:
            qty = max(1, min(int(parts[2]), 100))
        except ValueError:
            qty = 1
    async with async_session() as session:
        await ensure_default_buildings_and_items(session)
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        item = None
        try:
            iid = int(key)
            item = await session.get(ShopItem, iid)
        except ValueError:
            from sqlalchemy import select as sel
            r = await session.execute(sel(ShopItem).where(ShopItem.name.contains(key)))
            item = r.scalars().first()
        if not item:
            await message.answer("آیتم پیدا نشد.")
            return
        msg = await buy_item(session, user, item, qty=qty)
    await message.answer(msg)
