"""نژاد و هستههای نژادی"""
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user
from services.cultivation import RACES, RACE_CULT, ADMIN_RACES, ALL_RACES
from bot.config import ADMIN_IDS
from services import cores as cores_svc
from services.i18n import t_user, tr

router = Router()


@router.message(Command("race", "نژاد", "نژادها"))
async def cmd_race(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        current = getattr(user, "race", None) or "انسان"
        info = RACE_CULT.get(current, {})
        text = (
            f"🧬 نژاد فعلی: <b>{current}</b>" + chr(10)
            + f"سبک: {info.get('style', '—')}" + chr(10)
            + f"{info.get('desc', '')}" + chr(10)
            + f"ضریب: ×{info.get('bonus', 1)}" + chr(10) + chr(10)
            + "تغییر نژاد با هسته: /cores · /findcore · /usecore" + chr(10)
            + "انتخاب اولیه (اگر هنوز انسان ساده هستی):"
        )
        if current != "انسان" and current in ALL_RACES:
            # still allow showing cores path
            await message.answer(
                text + chr(10) + "برای تبدیل دوباره باید هسته پیدا کنی."
            )
            return

    is_admin = message.from_user.id in ADMIN_IDS
    choices = list(RACES) + (list(ADMIN_RACES) if is_admin else [])
    builder = InlineKeyboardBuilder()
    # فقط چند نژاد پایه در دکمه؛ بقیه با هسته
    basic = ["انسان", "جن", "غول", "پری", "سایهرو", "فرشته", "اهریمن", "نامیرا"]
    if is_admin:
        basic = basic + list(ADMIN_RACES)
    for r in basic:
        if r not in ALL_RACES:
            continue
        info = RACE_CULT.get(r, {})
        label = f"{r} (×{info.get('bonus', 1)})"
        if r in ADMIN_RACES:
            label = "👑 " + label
        builder.button(text=label[:40], callback_data=f"setrace:{message.from_user.id}:{r}")
    builder.adjust(2)
    text2 = "🧬 <b>نژاد پایه</b> (یکبار رایگان)" + chr(10)
    text2 += "نژادهای قویتر و ایرانی با <b>هسته</b>:" + chr(10)
    text2 += "/cores · /findcore · /usecore نامهسته" + chr(10)
    if is_admin:
        text2 += chr(10) + "👑 خدایان و قادر مطلق فقط ادمین" + chr(10) + "⚠️ نامیرا: قدرت بالا، بدون تولیدمثل"
    await message.answer(text2, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("setrace:"))
async def cb_set_race(callback: CallbackQuery):
    parts = callback.data.split(":")
    owner, race = int(parts[1]), parts[2]
    if callback.from_user.id != owner:
        await callback.answer()
        return
    if race not in ALL_RACES:
        await callback.answer()
        return
    if race in ADMIN_RACES and callback.from_user.id not in ADMIN_IDS:
        await callback.answer(tr(callback.from_user.id, "این نژاد فقط برای ادمین/سازنده است"), show_alert=True)
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, callback.from_user.id,
            callback.from_user.full_name, callback.from_user.username
        )
        cur = getattr(user, "race", None) or "انسان"
        if cur != "انسان" and cur in ALL_RACES:
            await callback.answer(tr(callback.from_user.id, "نژاد پایه قبلاً انتخاب شده — از هسته استفاده کن: /findcore"), show_alert=True)
            return
        user.race = race
        await session.commit()
        info = RACE_CULT[race]
    await callback.message.edit_text(
        f"✅ نژاد «<b>{race}</b>» ثبت شد." + chr(10)
        + f"سبک: {info['style']}" + chr(10)
        + f"{info['desc']}" + chr(10)
        + f"ضریب: ×{info['bonus']}" + chr(10)
        + (("⚠️ این نژاد نمیتواند تولیدمثل کند." + chr(10)) if race in ("نامیرا", "قادر مطلق", "خدایان") else "")
        + chr(10) + "برای نژادهای دیگر: /cores"
    )
    await callback.answer()


@router.message(Command("cores", "هسته", "هستهها", "core"))
async def cmd_cores(message: Message):
    await message.answer(cores_svc.list_cores_text())


@router.message(Command("findcore", "جستجویهسته", "پیداهسته"))
async def cmd_find_core(message: Message):
    name, msg = cores_svc.find_core(message.from_user.id)
    await message.answer(msg)


@router.message(Command("mycore", "هستهمن", "هستههامن"))
async def cmd_my_core(message: Message):
    bag = cores_svc.get_user_cores(message.from_user.id)
    if not bag:
        await message.answer(tr(message.from_user.id, "هستهای نداری. /findcore"))
        return
    text = "💎 <b>هستههای تو</b>" + chr(10) + chr(10)
    for n, q in bag.items():
        race = cores_svc.CORES.get(n, {}).get("race", "?")
        text += f"• {n} ×{q} → {race}" + chr(10)
    text += chr(10) + "/usecore نامهسته"
    await message.answer(text)


@router.message(Command("usecore", "استفادههسته", "جذبهسته"))
async def cmd_use_core(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("/usecore نامهسته" + chr(10) + "مثال: /usecore هسته سیمرغ" + chr(10) + "/mycore")
        return
    core_name = parts[1].strip()
    race, msg = cores_svc.use_core(message.from_user.id, core_name)
    if not race:
        await message.answer(msg)
        return
    if race in ADMIN_RACES and message.from_user.id not in ADMIN_IDS:
        # refund
        cores_svc.add_core(message.from_user.id, core_name if core_name in cores_svc.CORES else "هسته انسان", 1)
        await message.answer(tr(message.from_user.id, "نژاد خدایان با هسته عمومی ممکن نیست."))
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        old = getattr(user, "race", None) or "انسان"
        user.race = race
        await session.commit()
        info = RACE_CULT.get(race, {})
    await message.answer(
        msg + chr(10)
        + f"قبل: {old} → بعد: <b>{race}</b>" + chr(10)
        + f"سبک: {info.get('style')} | ضریب ×{info.get('bonus')}" + chr(10)
        + f"{info.get('desc', '')}"
    )
