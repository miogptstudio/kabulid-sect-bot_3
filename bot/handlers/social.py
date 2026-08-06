"""ارسال پول، بازار آزاد، خدمتکار، RPS دو نفره، لیدربوردها"""
import random
from datetime import datetime
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
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

router = Router()

# بازار آزاد حافظه
_market: list[dict] = []
# خدمتکارها (NPC)
SERVANTS = [
    {"id": 1, "name": "آلیس", "gender": "زن", "price": 500, "desc": "خدمتکار وفادار"},
    {"id": 2, "name": "لیان", "gender": "زن", "price": 800, "desc": "خدمتکار جنگی"},
    {"id": 3, "name": "مینگ", "gender": "مرد", "price": 600, "desc": "نگهبان خانه"},
    {"id": 4, "name": "سارا", "gender": "زن", "price": 1200, "desc": "خدمتکار نجیب"},
    {"id": 5, "name": "کای", "gender": "مرد", "price": 900, "desc": "آشپز ماهر"},
]
_user_servants: dict[int, list] = {}  # telegram_id -> list of servant ids
_user_married_servants: dict = {}  # telegram_id -> married servant ids
_servant_children: dict = {}  # telegram_id -> list of child dicts
_dual_servant_cd: dict = {}  # telegram_id -> last dual datetime
_rps_challenges: dict[int, dict] = {}


@router.message(Command("pay", "ارسال‌پول", "بفرست‌پول", "انتقال‌ارز", "transfer"))
async def cmd_pay(message: Message):
    """انتقال همه ارزها به دیگران"""
    CURRENCY = {
        "coins": ("coins", "سکه"),
        "سکه": ("coins", "سکه"),
        "coin": ("coins", "سکه"),
        "spirit": ("spirit_stones", "سنگ روحی"),
        "روحی": ("spirit_stones", "سنگ روحی"),
        "spirit_stones": ("spirit_stones", "سنگ روحی"),
        "سنگ‌روحی": ("spirit_stones", "سنگ روحی"),
        "heavenly": ("heavenly_stones", "سنگ بهشتی"),
        "بهشتی": ("heavenly_stones", "سنگ بهشتی"),
        "heavenly_stones": ("heavenly_stones", "سنگ بهشتی"),
        "celestial": ("celestial_stones", "سنگ آسمانی"),
        "آسمانی": ("celestial_stones", "سنگ آسمانی"),
        "celestial_stones": ("celestial_stones", "سنگ آسمانی"),
        "god": ("god_stones", "سنگ خدا"),
        "خدا": ("god_stones", "سنگ خدا"),
        "god_stones": ("god_stones", "سنگ خدا"),
    }
    HELP = (
        "💸 <b>انتقال ارز</b>" + chr(10) + chr(10)
        + "ریپلای + /pay نوع مقدار" + chr(10)
        + "یا /pay آیدی‌عددی نوع مقدار" + chr(10) + chr(10)
        + "<b>انواع:</b>" + chr(10)
        + "• coins / سکه" + chr(10)
        + "• spirit / روحی" + chr(10)
        + "• heavenly / بهشتی" + chr(10)
        + "• celestial / آسمانی" + chr(10)
        + "• god / خدا" + chr(10) + chr(10)
        + "چند ارز با هم:" + chr(10)
        + "/payall ریپلای‌شده → /payall coins 10 spirit 2" + chr(10)
        + "یا /payall 123456 coins 10 heavenly 1" + chr(10) + chr(10)
        + "مثال: /pay بهشتی 5"
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
            amount = int(args[1])
        except ValueError:
            await message.answer("مقدار باید عدد باشد.")
            return
        if amount <= 0:
            await message.answer(tr(message.from_user.id, "مقدار باید مثبت باشد."))
            return
        if amount > 10**15:
            await message.answer("مقدار خیلی بزرگ است.")
            return
        # جلوگیری از ارسال به اکانت ربات
        try:
            from bot.config import ADMIN_IDS
            # اگر target همان ربات باشد (از طریق getMe ذخیره نشده) — چک username bot
            if getattr(target, "telegram_id", None) and message.bot:
                me = await message.bot.get_me()
                if target.telegram_id == me.id:
                    await message.answer("🤖 ربات چیزی از بازیکن‌ها دریافت نمی‌کند (ارز/آیتم).")
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


@router.message(Command("payall", "انتقال‌چندارز", "بفرست‌همه"))
async def cmd_payall(message: Message):
    """چند ارز در یک دستور: /payall coins 10 spirit 2 heavenly 1"""
    CURRENCY = {
        "coins": ("coins", "سکه"), "سکه": ("coins", "سکه"), "coin": ("coins", "سکه"),
        "spirit": ("spirit_stones", "سنگ روحی"), "روحی": ("spirit_stones", "سنگ روحی"),
        "heavenly": ("heavenly_stones", "سنگ بهشتی"), "بهشتی": ("heavenly_stones", "سنگ بهشتی"),
        "celestial": ("celestial_stones", "سنگ آسمانی"), "آسمانی": ("celestial_stones", "سنگ آسمانی"),
        "god": ("god_stones", "سنگ خدا"), "خدا": ("god_stones", "سنگ خدا"),
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
        for i in range(0, len(args), 2):
            k, a = args[i], args[i + 1]
            if k not in CURRENCY:
                await message.answer(f"نوع نامعتبر: {k}")
                return
            try:
                amt = int(a)
            except ValueError:
                await message.answer(f"مقدار نامعتبر: {a}")
                return
            if amt <= 0:
                await message.answer("مقدار باید مثبت باشد.")
                return
            pairs.append((CURRENCY[k][0], CURRENCY[k][1], amt))
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
    if len(parts) >= 4 and parts[1] == "sell":
        item, price = parts[2], int(parts[3])
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


@router.message(Command("marketbuy", "خرید‌بازار"))
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
    _market.pop(idx)
    await message.answer(f"✅ «{listing['item']}» خریداری شد.")


@router.message(Command("servants", "خدمتکار", "برده"))
async def cmd_servants(message: Message):
    text = "👤 <b>بازار خدمتکار</b>\n\n"
    text += "⚠️ آسیب به خدمتکار = مرگ و حذف اکانت تو\n\n"
    for s in SERVANTS:
        text += f"{s['id']}. {s['name']} ({s['gender']}) — {s['price']} سکه\n  {s['desc']}\n"
    text += ("\n/buyservant شماره\n/myservants\n/marryservant شماره\n/dualservant شماره — تذهیب دوگانه با خدمتکار\n/childservant شماره — تلاش برای بچه با خدمتکار همسر\n/mychildren — لیست فرزندان")
    await message.answer(text)


@router.message(Command("buyservant", "خرید‌خدمتکار"))
async def cmd_buy_servant(message: Message):
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
    _user_servants.setdefault(message.from_user.id, []).append(s["id"])
    await message.answer(
        f"✅ {s['name']} را خریدی.\n"
        f"⚠️ آسیب زدن به خدمتکار ممنوع است و باعث مرگ و حذف اکانت می‌شود."
    )


@router.message(Command("myservants", "خدمتکار‌من"))
async def cmd_my_servants(message: Message):
    ids = _user_servants.get(message.from_user.id, [])
    if not ids:
        await message.answer(
            "خدمتکاری نداری." + chr(10)
            + "/servants — بازار" + chr(10)
            + "/buyservant شماره — خرید"
        )
        return
    married = _user_married_servants.get(message.from_user.id, [])
    text = "👤 <b>خدمتکارهای تو</b>" + chr(10) + chr(10)
    for i in ids:
        s = next((x for x in SERVANTS if x["id"] == i), None)
        if s:
            tag = " 💍 همسر" if i in married else ""
            text += f"• #{s['id']} {s['name']} ({s['gender']}){tag}" + chr(10)
    text += (
        chr(10) + "/marryservant شماره — ازدواج با خدمتکار زن"
        + chr(10) + "/servants — بازار دوباره"
    )
    await message.answer(text)


@router.message(Command("marryservant", "ازدواج‌خدمتکار"))
async def cmd_marry_servant(message: Message):
    """ازدواج با خدمتکار زن: /marryservant شماره  یا  /marry servant شماره"""
    parts = (message.text or "").split()
    # پشتیبانی: /marryservant 1  |  /marry servant 1
    sid = None
    if len(parts) >= 2 and parts[0].replace("/", "").startswith("marry") and parts[1].lower() in ("servant", "خدمتکار"):
        if len(parts) >= 3:
            try:
                sid = int(parts[2])
            except ValueError:
                sid = None
    elif len(parts) >= 2:
        try:
            sid = int(parts[1])
        except ValueError:
            sid = None
    if sid is None:
        await message.answer(
            "ازدواج با خدمتکار زن:" + chr(10)
            + "/marryservant شماره" + chr(10)
            + "یا: /marry servant شماره" + chr(10)
            + "اول /myservants ببین کدام را داری."
        )
        return
    s = next((x for x in SERVANTS if x["id"] == sid), None)
    if not s:
        await message.answer(tr(message.from_user.id, "خدمتکار پیدا نشد. /servants"))
        return
    # ازدواج با خدمتکار هر جنسیتی — برای تذهیب دوگانه باید مخالف باشد
    owned = _user_servants.get(message.from_user.id, [])
    if sid not in owned:
        await message.answer("اول باید این خدمتکار را بخری. /buyservant " + str(sid))
        return
    married = _user_married_servants.setdefault(message.from_user.id, [])
    if sid in married:
        await message.answer(f"قبلاً با {s['name']} ازدواج کرده‌ای.")
        return
    married.append(sid)
    await message.answer(
        f"💍 با خدمتکار «{s['name']}» ازدواج کردی." + chr(10)
        + "آسیب به او = حذف اکانت تو." + chr(10)
        + "/myservants — لیست"
    )






@router.message(F.text.regexp(r"(?i)^/marry\s+servant\s+\d+"))
async def cmd_marry_servant_text(message: Message):
    parts = (message.text or "").split()
    if len(parts) >= 3:
        message.text = f"/marryservant {parts[2]}"
        await cmd_marry_servant(message)


@router.message(Command("dualservant", "تذهیب‌خدمتکار", "دوگانه‌خدمتکار"))
async def cmd_dual_servant(message: Message):
    from datetime import datetime, timedelta
    import random
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(
            "☯️ /dualservant شماره" + chr(10)
            + "نیاز: خرید + ازدواج با خدمتکار + /gender مخالف" + chr(10)
            + "پاداش: +۵۰ انرژی | شانس نادر بچه | کول‌داون ۳۰ دقیقه"
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
    owned = _user_servants.get(message.from_user.id, [])
    married = _user_married_servants.get(message.from_user.id, [])
    if sid not in owned:
        await message.answer("اول بخر: /buyservant " + str(sid))
        return
    if sid not in married:
        await message.answer("اول ازدواج: /marryservant " + str(sid))
        return
    last = _dual_servant_cd.get(message.from_user.id)
    if last and datetime.utcnow() - last < timedelta(minutes=30):
        left = int((timedelta(minutes=30) - (datetime.utcnow() - last)).total_seconds() // 60) + 1
        await message.answer(f"⏳ کول‌داون تذهیب دوگانه خدمتکار: {left} دقیقه")
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


@router.message(Command("childservant", "بچه‌خدمتکار", "فرزند‌خدمتکار"))
async def cmd_child_servant(message: Message):
    import random
    from datetime import datetime, timedelta
    from services.dual import CHILD_CHANCE
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(
            "👶 /childservant شماره" + chr(10)
            + "با خدمتکار همسر و جنسیت مخالف" + chr(10)
            + f"شانس نادر ({CHILD_CHANCE}) | هر ۱ ساعت یک‌بار"
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
    owned = _user_servants.get(message.from_user.id, [])
    married = _user_married_servants.get(message.from_user.id, [])
    if sid not in owned or sid not in married:
        await message.answer(tr(message.from_user.id, "باید /buyservant و /marryservant کرده باشی."))
        return
    key = f"child_{message.from_user.id}"
    last = _dual_servant_cd.get(key)
    if last and datetime.utcnow() - last < timedelta(hours=1):
        await message.answer(tr(message.from_user.id, "⏳ هر ۱ ساعت یک‌بار."))
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


@router.message(Command("mychildren", "فرزندان‌من", "بچه‌ها"))
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
        text += f"   تکنیک‌ها: {', '.join(techs) if techs else '—'}" + chr(10)
    text += chr(10) + "/namechild شماره نام‌جدید" + chr(10) + "/teachchild شماره نام‌تکنیک"
    await message.answer(text)


@router.message(Command("namechild", "اسم‌بچه", "نام‌فرزند"))
async def cmd_name_child(message: Message):
    """ /namechild شماره نام """
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await message.answer("فرمت: /namechild شماره نام‌جدید" + chr(10) + "مثال: /namechild 1 آریا")
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


@router.message(Command("teachchild", "آموزش‌بچه", "تکنیک‌فرزند"))
async def cmd_teach_child(message: Message):
    """ /teachchild شماره نام‌تکنیک — از تکنیک‌های خودت به فرزند یاد بده """
    parts = (message.text or "").split(maxsplit=2)
    if len(parts) < 3:
        await message.answer(
            "فرمت: /teachchild شماره نام‌تکنیک" + chr(10)
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
            + "/techniques — لیست تکنیک‌های خودت"
        )
        return
    child = kids[idx]
    techs = child.setdefault("techs", [])
    if tech_name in techs:
        await message.answer(f"{child.get('name')} قبلاً «{tech_name}» را بلد است.")
        return
    if len(techs) >= 8:
        await message.answer("این فرزند حداکثر ۸ تکنیک می‌تواند یاد بگیرد.")
        return
    techs.append(tech_name)
    await message.answer(
        f"📚 به <b>{child.get('name')}</b> تکنیک «{tech_name}» یاد دادی." + chr(10)
        + f"تکنیک‌های فرزند: {', '.join(techs)}"
    )



@router.message(Command("harmservant", "آسیب‌خدمتکار"))
async def cmd_harm_servant(message: Message):
    """آسیب = مرگ + حذف اکانت"""
    ids = _user_servants.get(message.from_user.id, [])
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
    _user_servants.pop(message.from_user.id, None)
    await message.answer(
        "💀 آسیب به خدمتکار ممنوع بود.\n"
        "اکانت تو برای همیشه پاک شد.\n" + msg
    )


@router.message(Command("rpsduel", "سنگ‌دوئل"))
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
        f"✊✋✌ چالش سنگ‌کاغذ‌قیچی از {message.from_user.full_name}\n"
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


@router.message(Command("leaders", "لیدربورد", "برترها"))
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
        text += "\n🏛️ <b>لیدربورد فرقه‌ها</b>\n\n"
        if not sects:
            text += "فرقه‌ای نیست.\n"
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

@router.message(Command("solotop", "لیدر‌جق", "برتر‌خودارضایی"))
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
            lines.append("هنوز آماری نیست. با /solo ثبت می‌شود.")
        await message.answer(chr(10).join(lines))
