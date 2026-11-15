"""ارسال پول، بازار آزاد، خدمتکار، RPS دو نفره، لیدربوردها"""
from services import servants as servmod

import random
from datetime import datetime
from aiogram import Router, F
from bot.utils.safe_telegram import safe_edit_text
from aiogram.types import Message, CallbackQuery, URLInputFile, FSInputFile
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy import select, func, desc

from database.engine import async_session
from database.crud import get_or_create_user, get_user_by_telegram_id
from services.economy import get_or_create_wallet
from database.models import User
from database.models_v2 import Sect, SectMember, Cultivation
from database.models_v3 import Marriage
from services.i18n import tr

from services.portraits import panel_url

router = Router()


BIGINT_MAX = 9_223_372_036_854_775_807


def _parse_transfer_amount(tokens, start=0):
    """Parse large transfer amounts: 1000000000000, 1,000,000,000, 1B, 1T, 1 میلیارد, 1 تریلیون."""
    if start >= len(tokens):
        raise ValueError("missing amount")
    raw = str(tokens[start]).strip().replace(",", "").replace("٬", "").replace(" ", "")
    persian = str.maketrans("۰۱۲۳۴۵۶۷۸۹", "0123456789")
    raw = raw.translate(persian)
    multipliers = {
        "k": 10**3, "m": 10**6, "b": 10**9, "t": 10**12,
        "هزار": 10**3, "میلیون": 10**6, "میلیارد": 10**9,
        "تریلیون": 10**12, "کوادریلیون": 10**15,
    }
    low = raw.lower()
    if low in multipliers:
        raise ValueError("amount needs a number")
    for suffix, mult in sorted(multipliers.items(), key=lambda x: -len(x[0])):
        if low.endswith(suffix) and low[:-len(suffix)]:
            num = float(low[:-len(suffix)])
            if not num.is_integer():
                # allow e.g. 1.5T without floating-point rounding in normal ranges
                value = int(round(num * mult))
            else:
                value = int(num) * mult
            if value <= 0 or value > BIGINT_MAX:
                raise ValueError("amount out of range")
            return value, 1
    # Support the two-token Persian form: 1 میلیارد / 1 تریلیون
    if start + 1 < len(tokens):
        unit = str(tokens[start + 1]).strip().translate(persian)
        unit = unit.replace("٬", "")
        if unit in multipliers:
            num = int(raw)
            value = num * multipliers[unit]
            if value <= 0 or value > BIGINT_MAX:
                raise ValueError("amount out of range")
            return value, 2
    value = int(raw)
    if value <= 0 or value > BIGINT_MAX:
        raise ValueError("amount out of range")
    return value, 1

# بازار آزاد حافظه
_market: list[dict] = []
# خدمتکارها — منبع واحد
SERVANTS = servmod.MARKET
from services.persist import get_dict as _sg, save as _ss
def _servants_map():
    return _sg("servants")

from services.persist import PersistentMap
_servant_children = PersistentMap("social_servant_children_legacy")
_dual_servant_cd = PersistentMap("social_dual_servant_cd_legacy")
_rps_challenges = PersistentMap("social_rps_challenges")


@router.message(Command("pay", "ارسالپول", "بفرستپول", "انتقالارز", "transfer"))
async def cmd_pay(message: Message):
    """انتقال همه ارزها به دیگران"""
    CURRENCY = {
        "coins": ("coins", "سکه"), "سکه": ("coins", "سکه"), "coin": ("coins", "سکه"),
        "spirit": ("spirit_stones", "سنگ روحی"), "روحی": ("spirit_stones", "سنگ روحی"),
        "heavenly": ("heavenly_stones", "سنگ بهشتی"), "بهشتی": ("heavenly_stones", "سنگ بهشتی"),
        "celestial": ("celestial_stones", "سنگ آسمانی"), "آسمانی": ("celestial_stones", "سنگ آسمانی"),
        "god": ("god_stones", "سنگ خدا"), "خدا": ("god_stones", "سنگ خدا"),
        "chaos": ("chaos_stones", "سنگ هرجومرج"), "هرجومرج": ("chaos_stones", "سنگ هرجومرج"),
        "void": ("void_stones", "سنگ پوچی"), "پوچی": ("void_stones", "سنگ پوچی"),
        "origin": ("origin_stones", "سنگ ازلی"), "ازلی": ("origin_stones", "سنگ ازلی"),
        "destiny": ("destiny_stones", "سنگ تقدیر"), "تقدیر": ("destiny_stones", "سنگ تقدیر"),
        "immortal": ("immortal_stones", "سنگ جاودان"), "جاودان": ("immortal_stones", "سنگ جاودان"),
        "creation": ("creation_stones", "سنگ خلقت"), "خلقت": ("creation_stones", "سنگ خلقت"),
        "absolute": ("absolute_stones", "سنگ مطلق"), "مطلق": ("absolute_stones", "سنگ مطلق"),
        "faith": ("faith_stones", "سنگ ایمان"), "ایمان": ("faith_stones", "سنگ ایمان"),
        "dragon": ("dragon_coins", "سکه اژدها"), "اژدها": ("dragon_coins", "سکه اژدها"),
        "karma": ("karma_points", "کارما"), "کارما": ("karma_points", "کارما"),
    }
    HELP = (
        "💸 <b>انتقال ارز</b>" + chr(10) + chr(10)
        + "ریپلای + /pay نوع مقدار" + chr(10)
        + "یا /pay آیدیعددی نوع مقدار" + chr(10) + chr(10)
        + "<b>انواع:</b>" + chr(10)
        + "• coins / سکه" + chr(10)
        + "• spirit / روحی" + chr(10)
        + "• heavenly / بهشتی" + chr(10)
        + "• celestial / آسمانی" + chr(10)
        + "• god / خدا" + chr(10) + chr(10)
        + "مقادیر خیلی بزرگ هم مجازند:" + chr(10)
        + "مثال: /pay بهشتی 1000000000000" + chr(10)
        + "یا /pay بهشتی 1 تریلیون" + chr(10)
        + "یا /pay بهشتی 1T" + chr(10) + chr(10)
        + "چند ارز با هم:" + chr(10)
        + "/payall coins 10 spirit 2" + chr(10)
        + "/payall coins 1 تریلیون god 5 میلیارد" + chr(10)
    )
    parts = (message.text or "").split()
    async with async_session() as session:
        sender = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if message.reply_to_message and message.reply_to_message.from_user:
            tu = message.reply_to_message.from_user
            target = await get_or_create_user(session, tu.id, tu.full_name, tu.username)
            args = parts[1:]
        elif len(parts) >= 4:
            try:
                tg = int(parts[1])
            except ValueError:
                await message.answer(HELP)
                return
            target = await get_user_by_telegram_id(session, tg)
            if not target:
                await message.answer(tr(message.from_user.id, "کاربر پیدا نشد."))
                return
            args = parts[2:]
        else:
            await message.answer(HELP)
            return
        if len(args) < 2:
            await message.answer(HELP)
            return
        kind_raw = args[0]
        try:
            amount, consumed = _parse_transfer_amount(args, 1)
        except (ValueError, OverflowError):
            await message.answer("مقدار نامعتبر است. مثال: 1000000000000 یا 1,000,000,000,000 یا 1 تریلیون")
            return
        # جلوگیری از ارسال به اکانت ربات
        try:
            from bot.config import ADMIN_IDS
            # اگر target همان ربات باشد (از طریق getMe ذخیره نشده) — چک username bot
            if getattr(target, "telegram_id", None) and message.bot:
                me = await message.bot.get_me()
                if target.telegram_id == me.id:
                    await message.answer("🤖 ربات چیزی از بازیکنها دریافت نمیکند (ارز/آیتم).")
                    return
        except Exception:
            pass
        if sender.id == target.id:
            await message.answer(tr(message.from_user.id, "به خودت نه."))
            return
        if kind_raw not in CURRENCY:
            await message.answer(HELP)
            return
        field, label = CURRENCY[kind_raw]
        sw = await get_or_create_wallet(session, sender.id)
        tw = await get_or_create_wallet(session, target.id)
        have = int(getattr(sw, field, 0) or 0)
        if have < amount:
            await message.answer(f"{label} کافی نیست (داری: {have}).")
            return
        setattr(sw, field, have - amount)
        setattr(tw, field, int(getattr(tw, field, 0) or 0) + amount)
        await session.commit()
    await message.answer(
        f"✅ انتقال انجام شد" + chr(10)
        + f"{amount} {label} → <b>{target.full_name}</b>"
    )


@router.message(Command("payall", "انتقالچندارز", "بفرستهمه"))
async def cmd_payall(message: Message):
    """چند ارز در یک دستور: /payall coins 10 spirit 2 heavenly 1 god 1 chaos 1 void 1 origin 1"""
    CURRENCY = {
        "coins": ("coins", "سکه"), "سکه": ("coins", "سکه"),
        "spirit": ("spirit_stones", "سنگ روحی"), "روحی": ("spirit_stones", "سنگ روحی"),
        "heavenly": ("heavenly_stones", "سنگ بهشتی"), "بهشتی": ("heavenly_stones", "سنگ بهشتی"),
        "celestial": ("celestial_stones", "سنگ آسمانی"), "آسمانی": ("celestial_stones", "سنگ آسمانی"),
        "god": ("god_stones", "سنگ خدا"), "خدا": ("god_stones", "سنگ خدا"),
        "chaos": ("chaos_stones", "سنگ هرجومرج"), "هرجومرج": ("chaos_stones", "سنگ هرجومرج"),
        "void": ("void_stones", "سنگ پوچی"), "پوچی": ("void_stones", "سنگ پوچی"),
        "origin": ("origin_stones", "سنگ ازلی"), "ازلی": ("origin_stones", "سنگ ازلی"),
        "destiny": ("destiny_stones", "سنگ تقدیر"), "تقدیر": ("destiny_stones", "سنگ تقدیر"),
        "immortal": ("immortal_stones", "سنگ جاودان"), "جاودان": ("immortal_stones", "سنگ جاودان"),
        "creation": ("creation_stones", "سنگ خلقت"), "خلقت": ("creation_stones", "سنگ خلقت"),
        "absolute": ("absolute_stones", "سنگ مطلق"), "مطلق": ("absolute_stones", "سنگ مطلق"),
        "faith": ("faith_stones", "سنگ ایمان"), "ایمان": ("faith_stones", "سنگ ایمان"),
        "dragon": ("dragon_coins", "سکه اژدها"), "اژدها": ("dragon_coins", "سکه اژدها"),
        "karma": ("karma_points", "کارما"), "کارما": ("karma_points", "کارما"),
    }
    parts = (message.text or "").split()
    async with async_session() as session:
        sender = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if message.reply_to_message and message.reply_to_message.from_user:
            tu = message.reply_to_message.from_user
            target = await get_or_create_user(session, tu.id, tu.full_name, tu.username)
            args = parts[1:]
        elif len(parts) >= 2:
            try:
                tg = int(parts[1])
                target = await get_user_by_telegram_id(session, tg)
                if not target:
                    await message.answer("کاربر پیدا نشد.")
                    return
                args = parts[2:]
            except ValueError:
                await message.answer(
                    "فرمت: ریپلای + /payall coins 10 spirit 2" + chr(10)
                    + "یا /payall آیدی coins 10 heavenly 1"
                )
                return
        else:
            await message.answer("ریپلای کن یا آیدی بده. مثال: /payall coins 10 spirit 5")
            return
        if sender.id == target.id:
            await message.answer("به خودت نه.")
            return
        if len(args) < 2 or len(args) % 2 != 0:
            await message.answer("جفت نوع+مقدار لازم است. مثال: coins 10 spirit 2")
            return
        pairs = []
        i = 0
        while i < len(args):
            k = args[i]
            if k not in CURRENCY or i + 1 >= len(args):
                await message.answer(f"نوع/فرمت نامعتبر: {k}")
                return
            try:
                amt, consumed = _parse_transfer_amount(args, i + 1)
            except (ValueError, OverflowError):
                await message.answer(f"مقدار نامعتبر برای {k}. مثال: 1000000000000 یا 1 تریلیون")
                return
            pairs.append((CURRENCY[k][0], CURRENCY[k][1], amt))
            i += 1 + consumed
        sw = await get_or_create_wallet(session, sender.id)
        tw = await get_or_create_wallet(session, target.id)
        for field, label, amt in pairs:
            have = int(getattr(sw, field, 0) or 0)
            if have < amt:
                await message.answer(f"{label} کافی نیست (داری: {have}، نیاز: {amt}).")
                return
        lines = []
        for field, label, amt in pairs:
            setattr(sw, field, int(getattr(sw, field, 0) or 0) - amt)
            setattr(tw, field, int(getattr(tw, field, 0) or 0) + amt)
            lines.append(f"• {amt} {label}")
        await session.commit()
    await message.answer(
        f"✅ انتقال چندارزی به <b>{target.full_name}</b>" + chr(10)
        + chr(10).join(lines)
    )



@router.message(Command("market", "بازار"))
async def cmd_market(message: Message):
    parts = (message.text or "").split(maxsplit=3)
    if len(parts) >= 2 and parts[1].lower() in ("sell", "فروش"):
        if len(parts) < 4:
            await message.answer("فرمت: /market sell نام_آیتم قیمت\nمثال: /market sell سنگ_روحی 500")
            return
        item = parts[2].strip()
        try:
            price = int(parts[3].strip())
        except ValueError:
            await message.answer("❌ قیمت باید عدد باشه.")
            return
        if not item:
            await message.answer("❌ اسم آیتم خالیه.")
            return
        if price <= 0:
            await message.answer("❌ قیمت باید بیشتر از صفر باشه.")
            return
        _market.append({
            "seller": message.from_user.id,
            "seller_name": message.from_user.full_name,
            "item": item,
            "price": price,
        })
        await message.answer(f"📦 «{item}» با قیمت {price} سکه در بازار قرار گرفت.")
        return
    text = "🏪 <b>بازار آزاد</b>\n\n"
    if not _market:
        text += "خالی است.\nفروش: /market sell نام قیمت\nخرید: /marketbuy شماره"
    else:
        for i, m in enumerate(_market[:30], 1):
            text += f"{i}. {m['item']} — {m['price']} سکه (@{m['seller_name']})\n"
        text += "\n/marketbuy شماره"
    await message.answer(text)


@router.message(Command("marketbuy", "خریدبازار"))
async def cmd_market_buy(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "/marketbuy شماره"))
        return
    try:
        idx = int(parts[1]) - 1
    except ValueError:
        await message.answer(tr(message.from_user.id, "عدد نامعتبر"))
        return
    if idx < 0 or idx >= len(_market):
        await message.answer(tr(message.from_user.id, "پیدا نشد."))
        return
    listing = _market[idx]
    if listing["seller"] == message.from_user.id:
        await message.answer(tr(message.from_user.id, "مال خودت است."))
        return
    async with async_session() as session:
        buyer = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        seller = await get_user_by_telegram_id(session, listing["seller"])
        bw = await get_or_create_wallet(session, buyer.id)
        if bw.coins < listing["price"]:
            await message.answer(tr(message.from_user.id, "سکه کافی نیست."))
            return
        bw.coins -= listing["price"]
        if seller:
            sw = await get_or_create_wallet(session, seller.id)
            sw.coins += listing["price"]
        await session.commit()
    fee = 0
    try:
        from services.retention import market_fee
        fee = int(market_fee(int(listing.get("price") or 0)) or 0)
        if fee:
            async with async_session() as session:
                buyer = await get_or_create_user(
                    session, message.from_user.id,
                    message.from_user.full_name, message.from_user.username
                )
                bw = await get_or_create_wallet(session, buyer.id)
                bw.coins = max(0, int(bw.coins or 0) - fee)
                await session.commit()
    except Exception:
        fee = 0
    _market.pop(idx)
    suffix = f"\n💸 کارمزد: {fee} سکه" if fee else ""
    await message.answer(f"✅ «{listing['item']}» خریداری شد.{suffix}")


# LEGACY disabled
async def cmd_servants_legacy(message: Message):
    text = "👤 <b>بازار خدمتکار</b>\n\n"
    text += "⚠️ آسیب به خدمتکار = مرگ و حذف اکانت تو\n\n"
    for s in SERVANTS:
        text += f"{s['id']}. {s['name']} ({s['gender']}) — {s['price']} سکه\n  {s['desc']}\n"
    text += ("\n/buyservant شماره\n/myservants\n/marryservant شماره\n/dualservant شماره — تذهیب دوگانه با خدمتکار\n/childservant شماره — تلاش برای بچه با خدمتکار همسر\n/mychildren — لیست فرزندان")
    await message.answer(text)


# LEGACY - shadowed buy removed
async def cmd_buy_servant_legacy(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "/buyservant شماره"))
        return
    sid = int(parts[1])
    s = next((x for x in SERVANTS if x["id"] == sid), None)
    if not s:
        await message.answer(tr(message.from_user.id, "پیدا نشد."))
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
        if w.coins < s["price"]:
            await message.answer(tr(message.from_user.id, "سکه کافی نیست."))
            return
        w.coins -= s["price"]
        await session.commit()
    (_servants_map().setdefault(str(message.from_user.id), []).append(s["id"]), _ss("servants"))
    await message.answer(
        f"✅ {s['name']} را خریدی.\n"
        f"⚠️ آسیب زدن به خدمتکار ممنوع است و باعث مرگ و حذف اکانت میشود."
    )


async def cmd_my_servants_legacy(message: Message):
    ids = _servants_map().get(str(message.from_user.id), [])
    if not ids:
        await message.answer(
            "خدمتکاری نداری." + chr(10)
            + "/servants — بازار" + chr(10)
            + "/buyservant شماره — خرید"
        )
        return
    married = set(servmod.married_uids(message.from_user.id))
    text = "👤 <b>خدمتکارهای تو</b>" + chr(10) + chr(10)
    for i in ids:
        s = next((x for x in SERVANTS if x["id"] == i), None)
        if s:
            tag = " 💍 همسر" if any(str(x.get("base_id")) == str(i) and str(x.get("uid")) in married for x in servmod.list_owned(message.from_user.id)) else ""
            text += f"• #{s['id']} {s['name']} ({s['gender']}){tag}" + chr(10)
    text += (
        chr(10) + "/marryservant شماره — ازدواج با خدمتکار زن"
        + chr(10) + "/servants — بازار دوباره"
    )
    await message.answer(text)


@router.message(Command("marryservant", "ازدواجخدمتکار"))
async def cmd_marry_servant(message: Message):
    """ازدواج با خدمتکار؛ شمارهٔ /myservants یا شمارهٔ بازار را میپذیرد."""
    parts = (message.text or "").split()
    selector = None

    if len(parts) >= 3 and parts[1].lower() in ("servant", "خدمتکار"):
        try:
            selector = int(parts[2])
        except ValueError:
            pass
    elif len(parts) >= 2:
        try:
            selector = int(parts[1])
        except ValueError:
            pass

    if selector is None:
        await message.answer(
            "💍 فرمت ازدواج با خدمتکار:\n"
            "/marryservant شماره\n"
            "یا /marry servant شماره\n\n"
            "شماره را از /myservants بردار."
        )
        return

    ok, msg, servant = servmod.marry_servant(message.from_user.id, selector)
    await message.answer(msg)





@router.message(F.text.regexp(r"(?i)^/marry\s+servant\s+\d+"))
async def cmd_marry_servant_text(message: Message):
    parts = (message.text or "").split()
    if len(parts) >= 3:
        try:
            selector = int(parts[2])
        except ValueError:
            await message.answer("شمارهٔ خدمتکار نامعتبره.")
            return
        ok, msg, servant = servmod.marry_servant(message.from_user.id, selector)
        await message.answer(msg)



@router.message(Command("dualservant", "تذهیبخدمتکار", "دوگانهخدمتکار"))
async def cmd_dual_servant(message: Message):
    import random
    from datetime import datetime
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(
            "☯️ <b>تذهیب دوگانه با خدمتکار</b>\n"
            "فرمت: /dualservant شماره\n"
            "شماره = شماره لیست /myservants\n\n"
            "نیاز: خرید + ازدواج + جنسیت مخالف\n"
            "پاداش: +۵۰ انرژی | شانس فرزند | کولداون ۳۰ دقیقه"
        )
        return
    try:
        selector = int(parts[1])
    except ValueError:
        await message.answer("شماره نامعتبر. از /myservants شماره را بردار.")
        return

    servant, idx = servmod._servant_by_selector(message.from_user.id, selector)
    if not servant:
        await message.answer("خدمتکار پیدا نشد. اول /buyservant و /myservants")
        return
    if not servmod.is_married(message.from_user.id, servant):
        await message.answer(f"اول ازدواج کن: /marryservant {(idx or 0)+1}")
        return

    busy, left = servmod.check_cd("servant_dual_cd", str(message.from_user.id), 30)
    if busy:
        await message.answer(f"⏳ کولداون تذهیب دوگانه: {left} دقیقه")
        return

    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if user.gender not in ("مرد", "زن"):
            await message.answer("اول /gender بزن.")
            return
        sg = servant.get("gender") or ""
        if user.gender == sg:
            await message.answer(
                f"باید جنسیت مخالف باشد.\nتو: {user.gender} | خدمتکار: {sg}"
            )
            return
        from services.cultivation import get_or_create_cultivation, add_energy, get_active_technique
        cult = await get_or_create_cultivation(session, user.id)
        if getattr(cult, "spiritual_root", None) == "بدون ریشه":
            await message.answer("هنوز ریشه معنوی نداری.")
            return
        tech = await get_active_technique(session, user.id)
        if not tech:
            await message.answer("تکنیک فعال نداری. /learntech")
            return
        user.is_virgin = False
        res = await add_energy(session, user.id, 50)
        await session.commit()

    servmod.set_cd("servant_dual_cd", str(message.from_user.id))
    name = servant.get("name", "خدمتکار")
    msg = f"☯️ تذهیب دوگانه با «{name}» انجام شد.\n+۵۰ انرژی\n"
    if res.get("messages"):
        msg += "\n".join(res["messages"]) + "\n"
    from services.dual import CHILD_CHANCE
    if random.random() < CHILD_CHANCE:
        child = {
            "name": f"فرزند {message.from_user.full_name[:10]} و {name}",
            "techs": [],
            "gender": random.choice(["مرد", "زن"]),
            "servant": name,
            "servant_uid": servant.get("uid"),
            "base_id": servant.get("base_id"),
            "at": datetime.utcnow().isoformat(),
        }
        child = servmod.add_child(message.from_user.id, child)
        msg += f"\n👶✨ معجزه! فرزند: {child['name']} ({child['gender']})\n/mychildren"
    else:
        msg += f"\nفرزندی نبود. بعداً: /childservant {(idx or 0)+1}"
    await message.answer(msg)


@router.message(Command("childservant", "بچهخدمتکار", "فرزندخدمتکار"))
async def cmd_child_servant(message: Message):
    import random
    from datetime import datetime
    from services.dual import CHILD_CHANCE
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(
            "👶 <b>فرزند با خدمتکار</b>\n"
            "فرمت: /childservant شماره\n"
            "شماره از /myservants (همسر شده)\n"
            f"شانس: {int(CHILD_CHANCE*100)}٪ | کولداون ۶۰ دقیقه"
        )
        return
    try:
        selector = int(parts[1])
    except ValueError:
        await message.answer("شماره نامعتبر.")
        return
    servant, idx = servmod._servant_by_selector(message.from_user.id, selector)
    if not servant:
        await message.answer("خدمتکار پیدا نشد. /myservants")
        return
    if not servmod.is_married(message.from_user.id, servant):
        await message.answer(f"باید اول ازدواج کنی: /marryservant {(idx or 0)+1}")
        return

    cd_key = f"child_{message.from_user.id}"
    busy, left = servmod.check_cd("servant_child_cd", cd_key, 60)
    if busy:
        await message.answer(f"⏳ کولداون فرزند: {left} دقیقه")
        return

    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if user.gender not in ("مرد", "زن"):
            await message.answer("اول /gender بزن.")
            return
        sg = servant.get("gender") or ""
        if user.gender == sg:
            await message.answer(
                f"برای فرزند باید جنسیت مخالف باشد.\nتو: {user.gender} | خدمتکار: {sg}"
            )
            return

    servmod.set_cd("servant_child_cd", cd_key)
    name = servant.get("name", "خدمتکار")
    if random.random() < CHILD_CHANCE:
        child = {
            "name": f"فرزند {message.from_user.full_name[:10]} و {name}",
            "techs": [],
            "gender": random.choice(["مرد", "زن"]),
            "servant": name,
            "servant_uid": servant.get("uid"),
            "base_id": servant.get("base_id"),
            "at": datetime.utcnow().isoformat(),
        }
        child = servmod.add_child(message.from_user.id, child)
        await message.answer(
            f"👶✨ فرزند به دنیا آمد!\n{child['name']} ({child['gender']})\n/mychildren"
        )
    else:
        await message.answer(
            f"این بار فرزندی نشد.\nشانس حدود {int(CHILD_CHANCE*100)}٪ است. یک ساعت دیگر دوباره تلاش کن."
        )


@router.message(Command("mychildren", "فرزندانمن", "بچهها", "فرزندان"))
async def cmd_my_children(message: Message):
    kids = servmod.list_children(message.from_user.id)
    if not kids:
        await message.answer(
            "هنوز فرزندی نداری.\n"
            "۱) خدمتکار بخر /buyservant\n"
            "۲) ازدواج /marryservant شماره\n"
            "۳) /dualservant یا /childservant"
        )
        return
    text = "👶 <b>فرزندان تو</b>\n\n"
    for i, c in enumerate(kids, 1):
        techs = c.get("techs") or []
        text += f"{i}. <b>{c.get('name','—')}</b> ({c.get('gender','—')})\n"
        if c.get("servant"):
            text += f"   والد خدمتکار: {c['servant']}\n"
        text += f"   تکنیک‌ها: {', '.join(techs) if techs else '—'}\n"
    text += "\n/namechild شماره نام_جدید\n/teachchild شماره نام_تکنیک"
    await message.answer(text)


@router.message(Command("namechild", "نامفرزند", "اسمبچه"))
async def cmd_name_child(message: Message):
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await message.answer("فرمت: /namechild شماره نام_جدید\nمثال: /namechild 1 آرش")
        return
    ok, msg = servmod.rename_child(message.from_user.id, int(parts[1]), parts[2])
    await message.answer(msg)


@router.message(Command("teachchild", "آموزشبچه", "تکنیکفرزند"))
async def cmd_teach_child(message: Message):
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3 or not parts[1].isdigit():
        await message.answer("فرمت: /teachchild شماره نام_تکنیک\nمثال: /teachchild 1 شعله درونی")
        return
    ok, msg = servmod.teach_child(message.from_user.id, int(parts[1]), parts[2])
    await message.answer(msg)


@router.message(Command("transformservant", "دگرگونیخدمتکار"))
async def cmd_transform_servant(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("فرمت: /transformservant شماره")
        return
    await message.answer(servmod.transform(message.from_user.id, int(parts[1])))


@router.message(Command("feedloyalty", "وفاداری", "loyalty"))
async def cmd_feed_loyalty(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("فرمت: /feedloyalty شماره  (۵۰ سکه)")
        return
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        from services.economy import get_or_create_wallet
        w = await get_or_create_wallet(session, user.id)
        msg, left = servmod.feed_loyalty(message.from_user.id, int(parts[1]), int(w.coins or 0))
        if left != int(w.coins or 0):
            w.coins = left
            await session.commit()
        await message.answer(msg)


@router.message(Command("checkbetray", "بررسیخیانت"))
async def cmd_check_betray(message: Message):
    await message.answer(servmod.check_betrayal(message.from_user.id))


@router.callback_query(F.data.startswith("servduelguide:"))
async def cb_servant_duel_guide(callback: CallbackQuery):
    await callback.answer()
    idx = callback.data.split(":", 2)[2]
    await callback.message.answer(
        "⚔️ <b>دوئل خدمتکاران</b>\n\n"
        f"خدمتکار شماره {idx} را انتخاب کردهای. برای مبارزه با خدمتکار حریف، "
        "روی پیام او ریپلای کن و بنویس:\n"
        f"<code>/servantduel {idx} شماره_خدمتکار_حریف</code>\n\n"
        "این دوئل فقط آمار خود خدمتکارها را مقایسه میکند."
    )
