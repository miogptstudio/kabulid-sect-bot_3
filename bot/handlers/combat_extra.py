from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select

from database.engine import async_session
from database.crud import get_or_create_user
from database.models import User
from database.models_v3 import UserInventory, ShopItem
from services.combat_blood import (
    apply_damage, apply_poison, check_poison_death, heal_poison, has_cyrus, ensure_blood
)
from services.power import calc_power
from services.economy import get_or_create_wallet

router = Router()

# شهرهایی که سلاح گرم مخفی دارند
CITY_GUNS = {
    "tehran": ("کلت پنهان", 25),
    "mashhad": ("تفنگ شکاری", 30),
    "isfahan": ("تپانچه قدیمی", 22),
    "shiraz": ("اسلحه قاچاق", 28),
    "tabriz": ("تفنگ کوهستان", 27),
    "newyork": ("برتا", 35),
    "moscow": ("کلاشنیکف کهنه", 40),
}


@router.message(Command("equip", "تجهیز", "مسلح"))
async def cmd_equip(message: Message):
    """تجهیز سلاح از کیف: /equip شماره"""
    parts = (message.text or "").split()
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        result = await session.execute(
            select(UserInventory, ShopItem)
            .join(ShopItem, UserInventory.item_id == ShopItem.id)
            .where(UserInventory.user_id == user.id)
        )
        rows = result.all()
        if len(parts) < 2:
            text = "⚔️ سلاح‌های قابل تجهیز:\n"
            for i, (inv, item) in enumerate(rows, 1):
                if item.item_type in ("weapon", "weapon_unique") or (
                    isinstance(item.effect, dict) and item.effect.get("duel_power")
                ):
                    mark = " ✅مجهز" if user.equipped_weapon_id == item.id else ""
                    text += f"{i}. {item.name}{mark}\n"
            text += "\n/equip شماره — تجهیز\n/unequip — برداشتن سلاح"
            await message.answer(text)
            return
        try:
            idx = int(parts[1]) - 1
        except ValueError:
            await message.answer("شماره نامعتبر")
            return
        if idx < 0 or idx >= len(rows):
            await message.answer("پیدا نشد")
            return
        inv, item = rows[idx]
        user.equipped_weapon_id = item.id
        if "ذوالفقار" in item.name or "کوروش" in item.name or (
            isinstance(item.effect, dict) and item.effect.get("unique") == "cyrus"
        ):
            user.has_cyrus_sword = True
        await session.commit()
        await message.answer(f"✅ «{item.name}» مجهز شد. در دوئل استفاده می‌شود.")


@router.message(Command("unequip", "خلع‌سلاح", "برداشتن‌سلاح"))
async def cmd_unequip(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if not user.equipped_weapon_id:
            await message.answer("سلاحی مجهز نیست. /equip برای دیدن لیست.")
            return
        from sqlalchemy import select
        from database.models_v3 import ShopItem
        item = await session.get(ShopItem, user.equipped_weapon_id)
        name = item.name if item else "سلاح"
        user.equipped_weapon_id = None
        # اگر کوروش بود، فلگ را فقط وقتی هنوز در کیف است نگه دار
        if item and ("کوروش" in (item.name or "") or (isinstance(item.effect, dict) and item.effect.get("unique") == "cyrus")):
            # چک کیف
            from database.models_v3 import UserInventory
            inv = await session.execute(
                select(UserInventory).where(
                    UserInventory.user_id == user.id,
                    UserInventory.item_id == item.id
                )
            )
            if not inv.scalar_one_or_none():
                user.has_cyrus_sword = False
        await session.commit()
        await message.answer(
            f"✅ «{name}» برداشته شد و در /inventory است."
            + chr(10) + "/equip شماره — تجهیز دوباره"
        )


@router.message(Command("heal", "درمان", "قرص‌سلامتی"))
async def cmd_heal(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        # مصرف قرص سلامتی از کیف
        result = await session.execute(
            select(UserInventory, ShopItem)
            .join(ShopItem, UserInventory.item_id == ShopItem.id)
            .where(UserInventory.user_id == user.id)
        )
        pill = None
        inv = None
        for i, it in result.all():
            if "سلامت" in it.name or (it.item_type == "pill" and "سم" in (it.description or "")):
                inv, pill = i, it
                break
            if it.name in ("قرص سلامتی", "پادزهر", "قرص عمر"):
                inv, pill = i, it
                break
        if not pill:
            await message.answer("قرص سلامتی/پادزهر در کیف نداری. از /buildings بخر.")
            return
        inv.quantity -= 1
        if inv.quantity <= 0:
            await session.delete(inv)
        msg = await heal_poison(session, user)
        await ensure_blood(user)
        user.blood = min(100, (user.blood or 0) + 20)
        await session.commit()
        await message.answer(msg + f"\nخون الان: {user.blood}%")


@router.message(Command("blood", "خون", "وضعیت‌رزمی"))
async def cmd_blood(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        await ensure_blood(user)
        poison = getattr(user, "poisoned_until", None)
        msg = await check_poison_death(session, user)
        if msg:
            await message.answer(msg)
            return
        text = f"🩸 خون: <b>{user.blood}%</b>\n"
        if poison and poison > datetime.utcnow():
            text += f"☠️ مسموم تا {poison.strftime('%H:%M')} — /heal\n"
        if has_cyrus(user):
            text += "⚔️ شمشیر کوروش: فعال (محافظت از مرگ عادی)\n"
        pw = await calc_power(session, user)
        text += f"قدرت: {pw['total']} (سلاح مجهز: {pw.get('weapon', 0)})"
        await message.answer(text)


@router.message(Command("deathduel", "دوئل‌مرگ"))
async def cmd_death_duel(message: Message):
    if not message.reply_to_message:
        await message.answer("ریپلای + /deathduel — تا مرگ یکی ادامه دارد.")
        return
    async with async_session() as session:
        a = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        ou = message.reply_to_message.from_user
        if ou.id == message.from_user.id:
            await message.answer("با خودت نه.")
            return
        b = await get_or_create_user(session, ou.id, ou.full_name, ou.username)
        if a.is_dead or b.is_dead:
            await message.answer("یکی مرده است.")
            return
        pa = await calc_power(session, a)
        pb = await calc_power(session, b)

    builder = InlineKeyboardBuilder()
    builder.button(text="قبول دوئل مرگ ☠️", callback_data=f"dduel:{a.id}:{b.id}")
    builder.button(text="رد", callback_data=f"dduelrej:{a.id}:{b.id}")
    builder.adjust(1)
    await message.answer(
        f"☠️ <b>دوئل تا مرگ</b>\n"
        f"{a.full_name} ({pa['total']}) vs {b.full_name} ({pb['total']})\n"
        f"فقط قدرت — تا خون یکی صفر شود.\n"
        f"اگر شمشیر کوروش باشد، بازنده برای همیشه پاک می‌شود.",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("dduel:"))
async def cb_death_duel(callback: CallbackQuery):
    parts = callback.data.split(":")
    a_id, b_id = int(parts[1]), int(parts[2])
    async with async_session() as session:
        me = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        if me.id != b_id:
            await callback.answer()
            return
        a = await session.get(User, a_id)
        b = me
        logs = []
        for round_n in range(1, 30):
            pa = await calc_power(session, a)
            pb = await calc_power(session, b)
            # نوبت بر اساس قدرت — قوی‌تر بیشتر آسیب
            if pa["total"] >= pb["total"]:
                atk, dfn = a, b
                dmg = 10 + (pa["total"] - pb["total"]) // 20
            else:
                atk, dfn = b, a
                dmg = 10 + (pb["total"] - pa["total"]) // 20
            cyrus = has_cyrus(atk)
            res = await apply_damage(
                session, atk, dfn, dmg,
                is_cyrus_strike=cyrus,
                is_death_duel=True,
            )
            logs.append(f"راند {round_n}: {atk.full_name} → {dfn.full_name}\n" + "\n".join(res["messages"]))
            if res.get("killed") or res.get("wiped"):
                break
            # تازه‌سازی
            await session.refresh(a)
            await session.refresh(b)
            if a.is_dead or b.is_dead:
                break
        await callback.message.edit_text("☠️ <b>دوئل مرگ</b>\n\n" + "\n\n".join(logs[-8:]))
    await callback.answer()


@router.callback_query(F.data.startswith("dduelrej:"))
async def cb_dduel_rej(callback: CallbackQuery):
    parts = callback.data.split(":")
    if callback.from_user.id:
        async with async_session() as session:
            me = await get_or_create_user(
                session, callback.from_user.id,
                callback.from_user.full_name, callback.from_user.username
            )
            if me.id != int(parts[2]):
                await callback.answer()
                return
    await callback.message.edit_text("دوئل مرگ رد شد.")
    await callback.answer()
