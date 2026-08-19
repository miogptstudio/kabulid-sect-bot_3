"""ارسال پول، بازار آزاد، خدمتکار، RPS دو نفره، لیدربوردها"""
from services import servants as servmod

import random
from datetime import datetime
from aiogram import Router, F
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

_servant_children: dict = {}  # telegram_id -> list of child dicts
_dual_servant_cd: dict = {}  # telegram_id -> last dual datetime
_rps_challenges: dict[int, dict] = {}


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
    from datetime import datetime, timedelta
    import random
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(
            "☯️ /dualservant شماره" + chr(10)
            + "نیاز: خرید + ازدواج با خدمتکار + /gender مخالف" + chr(10)
            + "پاداش: +۵۰ انرژی | شانس نادر بچه | کولداون ۳۰ دقیقه"
        )
        return
    try:
        sid = int(parts[1])
    except ValueError:
        await message.answer(tr(message.from_user.id, "شماره نامعتبر."))
        return
    s = next((x for x in SERVANTS if x["id"] == sid), None)
    if not s:
        await message.answer(tr(message.from_user.id, "خدمتکار پیدا نشد. /servants"))
        return
    servant = next(
        (x for x in servmod.list_owned(message.from_user.id)
         if int(x.get("base_id") or -1) == sid),
        None,
    )
    if not servant:
        await message.answer("اول بخر: /buyservant " + str(sid))
        return
    if not servmod.is_married(message.from_user.id, servant):
        await message.answer("اول ازدواج: /marryservant " + str(sid))
        return
    last = _dual_servant_cd.get(message.from_user.id)
    if last and datetime.utcnow() - last < timedelta(minutes=30):
        left = int((timedelta(minutes=30) - (datetime.utcnow() - last)).total_seconds() // 60) + 1
        await message.answer(f"⏳ کولداون تذهیب دوگانه خدمتکار: {left} دقیقه")
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if user.gender not in ("مرد", "زن"):
            await message.answer(tr(message.from_user.id, "اول /gender بزن."))
            return
        if user.gender == s["gender"]:
            await message.answer(
                f"باید جنسیت مخالف باشد. تو: {user.gender} | خدمتکار: {s['gender']}"
            )
            return
        from services.cultivation import get_or_create_cultivation, add_energy, get_active_technique
        cult = await get_or_create_cultivation(session, user.id)
        if getattr(cult, "spiritual_root", None) == "بدون ریشه":
            await message.answer(tr(message.from_user.id, "هنوز ریشه معنوی نداری."))
            return
        tech = await get_active_technique(session, user.id)
        if not tech:
            await message.answer(tr(message.from_user.id, "تکنیک فعال نداری. /learntech"))
            return
        user.is_virgin = False
        res = await add_energy(session, user.id, 50)
        await session.commit()
    _dual_servant_cd[message.from_user.id] = datetime.utcnow()
    msg = f"☯️ تذهیب دوگانه با «{s['name']}» انجام شد." + chr(10) + "+۵۰ انرژی" + chr(10)
    if res.get("messages"):
        msg += chr(10).join(res["messages"]) + chr(10)
    from services.dual import CHILD_CHANCE
    if random.random() < CHILD_CHANCE:
        child = {
            "name": f"فرزند {message.from_user.full_name[:10]} و {s['name']}",
            "techs": [],
            "gender": random.choice(["مرد", "زن"]),
            "servant": s["name"],
            "servant_id": sid,
        }
        _servant_children.setdefault(message.from_user.id, []).append(child)
        msg += chr(10) + "👶✨ معجزه! فرزند: " + child["name"] + f" ({child['gender']})"
    else:
        msg += chr(10) + "فرزندی نبود. /childservant " + str(sid)
    await message.answer(msg)


@router.message(Command("childservant", "بچهخدمتکار", "فرزندخدمتکار"))
async def cmd_child_servant(message: Message):
    import random
    from datetime import datetime, timedelta
    from services.dual import CHILD_CHANCE
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(
            "👶 /childservant شماره" + chr(10)
            + "با خدمتکار همسر و جنسیت مخالف" + chr(10)
            + f"شانس نادر ({CHILD_CHANCE}) | هر ۱ ساعت یکبار"
        )
        return
    try:
        sid = int(parts[1])
    except ValueError:
        await message.answer(tr(message.from_user.id, "شماره نامعتبر."))
        return
    s = next((x for x in SERVANTS if x["id"] == sid), None)
    if not s:
        await message.answer(tr(message.from_user.id, "پیدا نشد."))
        return
    owned_ids = [x.get("base_id") for x in servmod.list_owned(message.from_user.id)]
    owned = owned_ids
    servant = next((x for x in servmod.list_owned(message.from_user.id) if int(x.get("base_id") or -1) == sid), None)
    if not servant or not servmod.is_married(message.from_user.id, servant):
        await message.answer(tr(message.from_user.id, "باید /buyservant و /marryservant کرده باشی."))
        return
    key = f"child_{message.from_user.id}"
    last = _dual_servant_cd.get(key)
    if last and datetime.utcnow() - last < timedelta(hours=1):
        await message.answer(tr(message.from_user.id, "⏳ هر ۱ ساعت یکبار."))
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        if user.gender not in ("مرد", "زن"):
            await message.answer(tr(message.from_user.id, "اول /gender"))
            return
        if user.gender == s["gender"]:
            await message.answer(tr(message.from_user.id, "جنسیت باید مخالف باشد."))
            return
        user.is_virgin = False
        await session.commit()
    _dual_servant_cd[key] = datetime.utcnow()
    if random.random() < CHILD_CHANCE:
        child = {
            "name": f"فرزند {message.from_user.full_name[:10]} و {s['name']}",
            "techs": [],
            "gender": random.choice(["مرد", "زن"]),
            "servant": s["name"],
            "servant_id": sid,
        }
        _servant_children.setdefault(message.from_user.id, []).append(child)
        await message.answer(
            "👶✨ معجزه!" + chr(10)
            + f"{child['name']} ({child['gender']})" + chr(10)
            + "/mychildren"
        )
    else:
        await message.answer(
            "این بار فرزندی نشد." + chr(10)
            + f"شانس بسیار نادر ({CHILD_CHANCE})."
        )


@router.message(Command("mychildren", "فرزندانمن", "بچهها"))
async def cmd_my_children(message: Message):
    kids = _servant_children.get(message.from_user.id, [])
    if not kids:
        await message.answer(
            "فرزندی نیست." + chr(10)
            + "تذهیب دوگانه / خدمتکار شانس بچه دارد." + chr(10)
            + "/childservant شماره | /namechild | /teachchild"
        )
        return
    text = "👶 <b>فرزندان</b>" + chr(10) + chr(10)
    for i, c in enumerate(kids, 1):
        techs = c.get("techs") or []
        text += f"{i}. <b>{c.get('name')}</b> ({c.get('gender')})" + chr(10)
        if c.get("servant"):
            text += f"   مادر/پدر خدمتکار: {c['servant']}" + chr(10)
        text += f"   تکنیکها: {', '.join(techs) if techs else '—'}" + chr(10)
    text += chr(10) + "/namechild شماره نامجدید" + chr(10) + "/teachchild شماره نامتکنیک"
    await message.answer(text)


@router.message(Command("namechild", "اسمبچه", "نامفرزند"))
async def cmd_name_child(message: Message):
    """ /namechild شماره نام """
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("فرمت: /namechild شماره نامجدید" + chr(10) + "مثال: /namechild 1 آریا")
        return
    try:
        idx = int(parts[1]) - 1
    except ValueError:
        await message.answer("شماره نامعتبر.")
        return
    new_name = parts[2].strip()[:32]
    if not new_name:
        await message.answer("نام خالی است.")
        return
    kids = _servant_children.get(message.from_user.id, [])
    if idx < 0 or idx >= len(kids):
        await message.answer("فرزندی با این شماره نیست. /mychildren")
        return
    old = kids[idx].get("name", "?")
    kids[idx]["name"] = new_name
    await message.answer(f"✅ نام فرزند عوض شد:" + chr(10) + f"{old} → <b>{new_name}</b>")


@router.message(Command("teachchild", "آموزشبچه", "تکنیکفرزند"))
async def cmd_teach_child(message: Message):
    """ /teachchild شماره نامتکنیک — از تکنیکهای خودت به فرزند یاد بده """
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            "فرمت: /teachchild شماره نامتکنیک" + chr(10)
            + "باید خودت آن تکنیک را بلد باشی." + chr(10)
            + "مثال: /teachchild 1 تنفس پایه"
        )
        return
    try:
        idx = int(parts[1]) - 1
    except ValueError:
        await message.answer("شماره نامعتبر.")
        return
    tech_name = parts[2].strip()
    kids = _servant_children.setdefault(message.from_user.id, [])
    if idx < 0 or idx >= len(kids):
        await message.answer("فرزند پیدا نشد. /mychildren")
        return
    # چک تکنیک بازیکن
    known = False
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        try:
            from sqlalchemy import select
            from database.models_v2 import UserTechnique, CultivationTechnique
            rows = await session.execute(
                select(CultivationTechnique.name)
                .join(UserTechnique, UserTechnique.technique_id == CultivationTechnique.id)
                .where(UserTechnique.user_id == user.id)
            )
            names = [r[0] for r in rows.all()]
            for n in names:
                if tech_name in n or n in tech_name:
                    tech_name = n
                    known = True
                    break
        except Exception:
            # fallback: accept any short name
            known = len(tech_name) >= 2
    if not known:
        await message.answer(
            f"تکنیک «{tech_name}» را بلد نیستی." + chr(10)
            + "/techniques — لیست تکنیکهای خودت"
        )
        return
    child = kids[idx]
    techs = child.setdefault("techs", [])
    if tech_name in techs:
        await message.answer(f"{child.get('name')} قبلاً «{tech_name}» را بلد است.")
        return
    if len(techs) >= 8:
        await message.answer("این فرزند حداکثر ۸ تکنیک میتواند یاد بگیرد.")
        return
    techs.append(tech_name)
    await message.answer(
        f"📚 به <b>{child.get('name')}</b> تکنیک «{tech_name}» یاد دادی." + chr(10)
        + f"تکنیکهای فرزند: {', '.join(techs)}"
    )



@router.message(Command("harmservant", "آسیبخدمتکار"))
async def cmd_harm_servant(message: Message):
    """آسیب = مرگ + حذف اکانت"""
    ids = _servants_map().get(str(message.from_user.id), [])
    if not ids:
        await message.answer(tr(message.from_user.id, "خدمتکاری نداری."))
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        user.is_dead = True
        await session.commit()
        from services.death import erase_existence
        msg = await erase_existence(session, user)
    (_servants_map().pop(str(message.from_user.id), None), _ss("servants"))
    await message.answer(
        "💀 آسیب به خدمتکار ممنوع بود.\n"
        "اکانت تو برای همیشه پاک شد.\n" + msg
    )


@router.message(Command("rpsduel", "سنگدوئل"))
async def cmd_rps_duel(message: Message):
    if not message.reply_to_message:
        await message.answer(tr(message.from_user.id, "روی حریف ریپلای کن و /rpsduel بزن."))
        return
    opp = message.reply_to_message.from_user
    if opp.id == message.from_user.id:
        await message.answer(tr(message.from_user.id, "با خودت نه."))
        return
    _rps_challenges[opp.id] = {
        "from": message.from_user.id,
        "from_name": message.from_user.full_name,
    }
    builder = InlineKeyboardBuilder()
    for name, em in [("سنگ", "✊"), ("کاغذ", "✋"), ("قیچی", "✌")]:
        builder.button(
            text=f"{em} {name}",
            callback_data=f"rpspv:{message.from_user.id}:{opp.id}:{name}",
        )
    builder.adjust(3)
    await message.answer(
        f"✊✋✌ چالش سنگکاغذقیچی از {message.from_user.full_name}\n"
        f"فقط {opp.full_name} انتخاب کند:",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("rpspv:"))
async def cb_rps_pv(callback: CallbackQuery):
    parts = callback.data.split(":")
    challenger_tg, opp_tg, choice = int(parts[1]), int(parts[2]), parts[3]
    if callback.from_user.id != opp_tg:
        await callback.answer()
        return
    opts = ["سنگ", "کاغذ", "قیچی"]
    # challenger picks random for simplicity if not stored - store both later
    # For fairness: challenger must also have chosen - use random for challenger stored challenge
    ch_choice = random.choice(opts)
    if choice == ch_choice:
        result = "مساوی!"
    elif (choice == "سنگ" and ch_choice == "قیچی") or \
         (choice == "کاغذ" and ch_choice == "سنگ") or \
         (choice == "قیچی" and ch_choice == "کاغذ"):
        result = f"{callback.from_user.full_name} برد! 🎉"
    else:
        result = f"حریف برد! (انتخاب حریف: {ch_choice})"
    await callback.message.edit_text(
        f"تو: {choice}\nحریف: {ch_choice}\n\n{result}"
    )
    await callback.answer()


@router.message(Command("leaders", "برترها"))
async def cmd_leaders(message: Message):
    async with async_session() as session:
        # global by level
        r = await session.execute(
            select(User).where(User.is_active == True).order_by(desc(User.level), desc(User.xp)).limit(10)
        )
        users = r.scalars().all()
        text = "🌍 <b>لیدربورد جهانی (سطح)</b>\n\n"
        for i, u in enumerate(users, 1):
            text += f"{i}. {u.full_name} — Lv.{u.level} | {u.rank}\n"

        r2 = await session.execute(
            select(Sect).where(Sect.is_active == True).order_by(desc(Sect.total_points)).limit(10)
        )
        sects = r2.scalars().all()
        text += "\n🏛️ <b>لیدربورد فرقهها</b>\n\n"
        if not sects:
            text += "فرقهای نیست.\n"
        for i, s in enumerate(sects, 1):
            text += f"{i}. {s.name} ({s.sect_type}) — {s.total_points} امتیاز\n"

        r3 = await session.execute(
            select(Cultivation, User)
            .join(User, Cultivation.user_id == User.id)
            .order_by(desc(Cultivation.energy))
            .limit(10)
        )
        text += "\n🧘 <b>لیدربورد تذهیب</b>\n\n"
        for i, (c, u) in enumerate(r3.all(), 1):
            text += f"{i}. {u.full_name} — {c.realm} {c.stage} | انرژی {c.energy}\n"

    await message.answer(text)

@router.message(Command("solotop", "لیدرجق", "برترخودارضایی"))
async def cmd_solo_top(message: Message):
    async with async_session() as session:
        result = await session.execute(select(User).where(User.is_active == True))
        users = list(result.scalars().all())
        users.sort(key=lambda u: getattr(u, "solo_count", 0) or 0, reverse=True)
        lines = ["🔥 <b>لیدربورد جهانی خودارضایی</b>", ""]
        shown = 0
        for u in users:
            c = getattr(u, "solo_count", 0) or 0
            if c <= 0:
                continue
            shown += 1
            lines.append(f"{shown}. {u.full_name} — <b>{c}</b> بار")
            if shown >= 15:
                break
        if shown == 0:
            lines.append("هنوز آماری نیست. با /solo ثبت میشود.")
        await message.answer(chr(10).join(lines))




@router.message(Command("servants", "خدمتکار", "برده", "بازارخدمتکار"))
async def cmd_servants_v2(message: Message):
    """بازار خدمتکاران به سبک فروشگاه: یک پنل با دکمه‌های قبلی/بعدی."""
    await _send_market_panel(message, position=0, owner_id=message.from_user.id)


async def _send_market_panel(target, position: int = 0, *, owner_id: int, edit: bool = False):
    """نمایش یک خدمتکار از بازار. target می‌تواند Message یا CallbackQuery.message باشد."""
    from bot.utils.servant_panel import (
        servant_image, market_keyboard, market_caption,
    )
    market = list(servmod.MARKET)
    if not market:
        await target.answer("بازار خدمتکار خالی است.")
        return
    total = len(market)
    position = position % total
    item = market[position]
    sid = int(item["id"])
    caption = market_caption(item, position, total)
    kb = market_keyboard(position, total, sid, owner_id)
    img = servant_image(sid)

    if edit:
        try:
            from aiogram.types import InputMediaPhoto
            if img:
                await target.edit_media(
                    media=InputMediaPhoto(media=img, caption=caption),
                    reply_markup=kb,
                )
            else:
                await target.edit_caption(caption=caption, reply_markup=kb)
            return
        except Exception:
            pass  # fallback: send new message

    try:
        if img:
            await target.answer_photo(img, caption=caption, reply_markup=kb)
        else:
            await target.answer(caption, reply_markup=kb)
    except Exception:
        await target.answer(caption, reply_markup=kb)


@router.message(Command("buyservant", "خریدخدمتکار", "خریدخدمتکار"))
async def cmd_buy_servant_v2(message: Message):
    parts=(message.text or "").split()
    if len(parts)<2 or not parts[1].isdigit():
        await message.answer("فرمت: /buyservant شماره")
        return
    async with async_session() as session:
        user=await get_or_create_user(session,message.from_user.id,message.from_user.full_name,message.from_user.username)
        from services.economy import get_or_create_wallet
        w=await get_or_create_wallet(session,user.id)
        sid=int(parts[1])
        karma=int(getattr(w,"karma_points",0) or 0)
        ok,msg,left,karma_left=servmod.buy(message.from_user.id,sid,int(w.coins or 0),karma)
        if ok:
            w.coins=left
            w.karma_points=karma_left
            await session.commit()
            bag=servmod.list_owned(message.from_user.id)
            idx=len(bag)
            s0=bag[-1]
            from bot.utils.servant_panel import servant_keyboard, servant_image
            img=servant_image(sid)
            caption=servmod.servant_panel_text(s0, idx, purchased=True)
            if img:
                await message.answer_photo(img,caption=caption,reply_markup=servant_keyboard(idx, callback.from_user.id))
            else:
                await message.answer(caption,reply_markup=servant_keyboard(idx, callback.from_user.id))
        else:
            await message.answer(msg)


@router.message(Command("myservants", "خدمتکارهایمن", "لیستخدمتکار", "خدمتکارمن"))
async def cmd_my_servants_v2(message: Message):
    """لیست خدمتکارهای من — مرور تکی با قبلی/بعدی."""
    await _send_owned_panel(message, position=0, user_id=message.from_user.id)


async def _send_owned_panel(target, position: int, user_id: int, *, edit: bool = False):
    from bot.utils.servant_panel import servant_image, owned_browse_keyboard
    bag = servmod.list_owned(user_id)
    if not bag:
        text = servmod.owned_text(user_id)
        if edit:
            try:
                await target.edit_caption(caption=text)
                return
            except Exception:
                pass
        await target.answer(text)
        return
    total = len(bag)
    position = position % total
    bag_index = position + 1
    s0 = bag[position]
    img = servant_image(int(s0.get("base_id") or 0))
    caption = servmod.servant_panel_text(s0, bag_index)
    caption = f"📦 <b>خدمتکارهای من</b> — {bag_index}/{total}\n\n" + caption
    kb = owned_browse_keyboard(position, total, bag_index, user_id)

    if edit:
        try:
            from aiogram.types import InputMediaPhoto
            if img:
                await target.edit_media(
                    media=InputMediaPhoto(media=img, caption=caption),
                    reply_markup=kb,
                )
            else:
                await target.edit_caption(caption=caption, reply_markup=kb)
            return
        except Exception:
            pass
    try:
        if img:
            await target.answer_photo(img, caption=caption, reply_markup=kb)
        else:
            await target.answer(caption, reply_markup=kb)
    except Exception:
        await target.answer(caption, reply_markup=kb)


@router.message(Command("showservant", "عکسخدمتکار", "پرترهخدمتکار"))
async def cmd_show_servant(message: Message):
    parts=(message.text or "").split()
    if len(parts)<2 or not parts[1].isdigit():
        await message.answer("فرمت: /showservant شماره")
        return
    bag=servmod.list_owned(message.from_user.id); idx=int(parts[1])
    if idx<1 or idx>len(bag):
        await message.answer("شماره نامعتبر."); return
    from bot.utils.servant_panel import servant_keyboard, servant_image
    s0=bag[idx-1]; img=servant_image(int(s0.get("base_id") or 0))
    caption=servmod.servant_panel_text(s0,idx)
    if img:
        await message.answer_photo(img,caption=caption,reply_markup=servant_keyboard(idx, callback.from_user.id))
    else:
        await message.answer(caption,reply_markup=servant_keyboard(idx, callback.from_user.id))


@router.callback_query(F.data.startswith("servmarket:"))
async def cb_serv_market(callback: CallbackQuery):
    await callback.answer()
    await _send_market_panel(callback.message, position=0, owner_id=callback.from_user.id, edit=True)


@router.callback_query(F.data.startswith("servpage:"))
async def cb_serv_page(callback: CallbackQuery):
    """ورق زدن بازار خدمتکاران با ◀️ ▶️"""
    try:
        pos = int(callback.data.split(":")[2])
    except Exception:
        await callback.answer("صفحه نامعتبر", show_alert=True)
        return
    await callback.answer()
    await _send_market_panel(callback.message, position=pos, owner_id=callback.from_user.id, edit=True)


@router.callback_query(F.data.startswith("servownpage:"))
async def cb_serv_own_page(callback: CallbackQuery):
    """ورق زدن خدمتکارهای من"""
    try:
        pos = int(callback.data.split(":")[2])
    except Exception:
        await callback.answer("صفحه نامعتبر", show_alert=True)
        return
    await callback.answer()
    await _send_owned_panel(callback.message, position=pos, user_id=callback.from_user.id, edit=True)


@router.callback_query(F.data.startswith("servmylist:"))
async def cb_serv_mylist(callback: CallbackQuery):
    await callback.answer()
    await _send_owned_panel(callback.message, position=0, user_id=callback.from_user.id, edit=False)

@router.callback_query(F.data.startswith("servbuy:"))
async def cb_serv_buy(callback: CallbackQuery):
    sid=int(callback.data.split(":")[2])
    # Reuse purchase command logic without requiring text parsing.
    async with async_session() as session:
        user=await get_or_create_user(session,callback.from_user.id,callback.from_user.full_name,callback.from_user.username)
        from services.economy import get_or_create_wallet
        w=await get_or_create_wallet(session,user.id)
        karma=int(getattr(w,"karma_points",0) or 0)
        ok,msg,left,karma_left=servmod.buy(callback.from_user.id,sid,int(w.coins or 0),karma)
        if not ok:
            await callback.answer(msg,show_alert=True); return
        w.coins=left
        w.karma_points=karma_left
        await session.commit()
        bag=servmod.list_owned(callback.from_user.id); idx=len(bag); s0=bag[-1]
        from bot.utils.servant_panel import servant_keyboard, servant_image
        img=servant_image(sid); caption=servmod.servant_panel_text(s0,idx,purchased=True)
        if img:
            await callback.message.answer_photo(img,caption=caption,reply_markup=servant_keyboard(idx, callback.from_user.id))
        else:
            await callback.message.answer(caption,reply_markup=servant_keyboard(idx, callback.from_user.id))
    await callback.answer("خرید انجام شد")

@router.callback_query(F.data.startswith("servstatus:"))
async def cb_serv_status(callback: CallbackQuery):
    parts=callback.data.split(":"); idx=int(parts[2]); bag=servmod.list_owned(callback.from_user.id)
    if idx<1 or idx>len(bag): await callback.answer("خدمتکار پیدا نشد",show_alert=True); return
    from bot.utils.servant_panel import servant_keyboard, servant_image
    s0=bag[idx-1]; img=servant_image(int(s0.get("base_id") or 0)); caption=servmod.servant_panel_text(s0,idx)
    if img:
        await callback.message.answer_photo(img,caption=caption,reply_markup=servant_keyboard(idx, callback.from_user.id))
    else:
        await callback.message.answer(caption,reply_markup=servant_keyboard(idx, callback.from_user.id))
    await callback.answer()

@router.callback_query(F.data.startswith("servloyal:"))
async def cb_serv_loyal(callback: CallbackQuery):
    parts=callback.data.split(":"); idx=int(parts[2]); bag=servmod.list_owned(callback.from_user.id)
    if idx<1 or idx>len(bag): await callback.answer("خدمتکار پیدا نشد",show_alert=True); return
    s0=bag[idx-1]
    await callback.answer(f"❤️ وفاداری: {s0.get('loyalty',0)}٪",show_alert=True)

@router.callback_query(F.data.startswith("servtrain:"))
async def cb_serv_train(callback: CallbackQuery):
    idx=int(callback.data.split(":")[2]); msg=servmod.train(callback.from_user.id,idx)
    await callback.message.answer(msg); await callback.answer("پرورش انجام شد")

@router.callback_query(F.data.startswith("servmarry:"))
async def cb_serv_marry(callback: CallbackQuery):
    idx=int(callback.data.split(":")[2])
    ok,msg,_=servmod.marry_servant(callback.from_user.id,idx)
    await callback.answer(msg,show_alert=True)

@router.message(Command("huntservant", "شکارخدمتکار", "تسخیرنژاد"))
async def cmd_hunt_servant(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(session, message.from_user.id, message.from_user.full_name, message.from_user.username)
        try:
            from services.power import calc_power
            p = await calc_power(session, user)
            power = int(p.get("total") or 20)
        except Exception:
            power = 20 + int(user.level or 1) * 3
        msg = servmod.hunt(message.from_user.id, power)
        await message.answer(msg)
        if 'تسخیر موفق' in msg:
            bag = servmod.list_owned(message.from_user.id)
            if bag:
                s = bag[-1]
                try:
                    from services.portraits import portrait_url, servant_caption
                    await message.answer_photo(
                        photo=portrait_url(s.get('name','?'), s.get('gender','زن'), s.get('race','انسان')),
                        caption=servant_caption(s),
                    )
                except Exception:
                    pass


@router.message(Command("trainservant", "پرورشخدمتکار"))
async def cmd_train_servant(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2 or not parts[1].isdigit():
        await message.answer("فرمت: /trainservant شماره")
        return
    await message.answer(servmod.train(message.from_user.id, int(parts[1])))


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
