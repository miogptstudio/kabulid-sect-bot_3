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
        builder.button(text=f"خرید {btn}", callback_data=f"buy:{uid}:{item.id}")
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
        builder.button(text=f"خرید {btn}", callback_data=f"buy:{owner_id}:{item.id}")
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


@router.callback_query(F.data.startswith("buy:"))
async def process_buy(callback: CallbackQuery):
    owner_id, rest = parse_owner_data(callback.data, "buy:")
    if owner_id is None:
        await callback.answer(tr(callback.from_user.id, "داده نامعتبر"), show_alert=True)
        return
    if not await ensure_owner(callback, owner_id, "مغازه"):
        return

    try:
        item_id = int(rest)
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
            msg = await buy_item(session, user, item)
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
    text += "\n/use شماره — استفاده\n/drop شماره — دور انداختن"
    await message.answer(text)


@router.message(Command("use", "استفاده"))
async def cmd_use_item(message: Message):
    """استفاده از آیتم: /use شماره"""
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(
            "فرمت: /use شماره\n"
            "اول /inventory بزن؛ شماره ردیف آیتم را ببین.\n"
            "مثال: /use 1"
        )
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
        from services.forbidden_lock import is_consume_locked, lock_consume, lock_message, FORBIDDEN_TEA_NAME
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
        if item.name == FORBIDDEN_TEA_NAME or effect.get("forbidden") or "ممنوعه" in (item.name or ""):
            lock_consume(message.from_user.id)
            msg_parts.append("☠️ قفل مصرف ابدی فعال شد — دیگر هیچ چیز مصرف نمی‌کنی.")

        if isinstance(effect, dict):
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
                user.blood = min(500, cur_b + b)
                msg_parts.append(f"+{b} خون (الان: {user.blood})")
            # محافظ
            if effect.get("protect"):
                msg_parts.append("سپر محافظ فعال شد (۱ بار).")
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
                gain = int(effect.get("energy") or 8000)
                res = await add_energy(session, user.id, gain)
                _tea_cd[uid] = now + timedelta(minutes=wait)
                msg_parts.append(f"🍵 +{gain} انرژی تذهیب")
                if res.get("messages"):
                    msg_parts.extend(res["messages"])
                msg_parts.append(f"📊 انرژی فعلی: {res.get('energy', '?')}")
            elif effect.get("energy") and item.item_type in ("pill", "tea"):
                from services.cultivation import add_energy
                gain = int(effect["energy"])
                res = await add_energy(session, user.id, gain)
                msg_parts.append(f"+{gain} انرژی")
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
        inv.quantity -= 1
        if inv.quantity <= 0:
            await session.delete(inv)
        await session.commit()

    await message.answer("\n".join(msg_parts))


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
        from services.forbidden_lock import is_consume_locked, lock_consume, lock_message, FORBIDDEN_TEA_NAME
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
