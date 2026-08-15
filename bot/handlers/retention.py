"""دستورات نگهداشت کاربر: رویداد، استریک، راهنما، جنگ زماندار، سینک"""
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command
from datetime import datetime

from database.engine import async_session
from database.crud import get_or_create_user
from services.economy import get_or_create_wallet
from services import retention as ret
from services.i18n import tr

router = Router()


@router.message(Command("guide", "راهنماشروع", "آموزش"))
async def cmd_guide(message: Message):
    text = (
        "📖 <b>راهنمای سهمرحلهای تازهکار</b>\n\n"
        "<b>مرحله ۱ — هویت</b>\n"
        "• /setgender مرد | زن\n"
        "• /race برای دیدن نژادها (اختیاری)\n\n"
        "<b>مرحله ۲ — تذهیب</b>\n"
        "• بنویس: <code>تذهیب کردن</code> یا /gather\n"
        "• چند بار تکرار کن تا ریشه بیدار شود\n"
        "• /profile برای دیدن وضعیت\n\n"
        "<b>مرحله ۳ — اولین دوئل</b>\n"
        "• روی پیام کسی ریپلای کن و /duel بزن\n"
        "• یا /arena برای آرنا\n\n"
        "بعدیهای مفید:\n"
        "/daily — ورود روزانه و استریک\n"
        "/missions — مأموریت\n"
        "/wallet — کیف پول\n"
        "/event — رویداد هفتگی\n"
        "/help — فهرست کامل"
    )
    await message.answer(text)


@router.message(Command("daily", "روزانه", "استریک", "ورود"))
async def cmd_daily(message: Message):
    tg = message.from_user.id
    res = ret.claim_streak(tg)
    if res.get("already"):
        await message.answer(f"امروز جایزهات را گرفتی.\n🔥 استریک: <b>{res['count']}</b> روز")
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, tg, message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
        lines = [f"🔥 ورود روزانه! استریک: <b>{res['count']}</b> روز", ""]
        for kind, amt in res.get("rewards") or []:
            if kind == "coins":
                # مالیات فرقه (سینک)
                kept, tax = ret.apply_sect_tax(amt)
                w.coins = int(w.coins or 0) + kept
                lines.append(f"🪙 +{kept} سکه" + (f" (مالیات فرقه −{tax})" if tax else ""))
            elif kind == "heavenly":
                w.heavenly_stones = int(getattr(w, "heavenly_stones", 0) or 0) + amt
                lines.append(f"✨ +{amt} سنگ بهشتی (پاداش ۷روز)")
            elif kind == "celestial":
                w.celestial_stones = int(getattr(w, "celestial_stones", 0) or 0) + amt
                lines.append(f"🌌 +{amt} سنگ آسمانی (پاداش ۳۰روز)")
            elif kind == "god":
                w.god_stones = int(getattr(w, "god_stones", 0) or 0) + amt
                lines.append(f"👑 +{amt} سنگ خدا (استریک ۱۰۰)")
            elif kind == "rare_box":
                w.spirit_stones = int(w.spirit_stones or 0) + 20
                lines.append("🎁 جعبه کمیاب: +۲۰ سنگ روحی")
        await session.commit()
        lines.append(f"\nموجودی سکه: {w.coins}")
        if res["count"] < 7:
            lines.append(f"تا پاداش ۷روز: {7 - res['count']} روز مانده")
        elif res["count"] < 30:
            lines.append(f"تا پاداش ۳۰روز: {30 - (res['count'] % 30)} روز مانده")
    await message.answer("\n".join(lines))


@router.message(Command("event", "رویداد", "eventstatus"))
async def cmd_event(message: Message):
    ev = ret.weekly_event_now()
    war = ret.territory_war_window()
    text = (
        f"{ev['title']}\n"
        f"{'🟢 فعال' if ev['active'] else '⚪ غیرفعال'}\n"
        f"{ev['desc']}\n"
        f"پایان: {ev['ends']}\n\n"
        f"{war['msg']}\n\n"
        "/eventjoin — پیوستن به رویداد\n"
        "/eventscore — ثبت +۱ امتیاز (با عمل بازی بهتر است)\n"
        "/eventtop — برترینهای امروز\n"
        "/warstatus — وضعیت جنگ قلمرو"
    )
    await message.answer(text)


@router.message(Command("eventjoin", "پیوستنرویداد"))
async def cmd_event_join(message: Message):
    await message.answer(ret.event_join(message.from_user.id))


@router.message(Command("eventscore", "امتیازرویداد"))
async def cmd_event_score(message: Message):
    sc = ret.event_add_score(message.from_user.id, 3)
    if sc == 0:
        await message.answer("اول /eventjoin بزن یا رویداد فعال نیست.")
        return
    await message.answer(f"⭐ امتیاز رویداد: <b>{sc}</b>\n/eventtop")


@router.message(Command("eventtop", "برتررویداد"))
async def cmd_event_top(message: Message):
    await message.answer(ret.event_top())


@router.message(Command("warstatus", "جنگقلمرو"))
async def cmd_war_status(message: Message):
    await message.answer(ret.territory_war_window()["msg"])


@router.message(Command("repair", "تعمیر", "تعمیربنا"))
async def cmd_repair(message: Message):
    """سینک سکه — تعمیر ساختمان شخصی"""
    cost = ret.REPAIR_BUILDING_COST
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
        if int(w.coins or 0) < cost:
            await message.answer(f"نیاز {cost} سکه برای تعمیر.")
            return
        w.coins = int(w.coins or 0) - cost
        await session.commit()
    await message.answer(
        f"🔧 تعمیر انجام شد. −{cost} سکه غرق شد (ضد تورم).\n"
        f"ساختمانهایت پایدارتر شدند."
    )


@router.message(Command("revivepay", "هزینهاحیا"))
async def cmd_revive_cost(message: Message):
    await message.answer(
        f"💀 هزینه احیا: <b>{ret.revive_cost()}</b> سکه\n"
        f"با /death و انتخاب پرورشدهنده روح یا پرداخت هنگام مرگ."
    )


@router.message(Command("marketoffer", "پیشنهادمیدم"))
async def cmd_market_offer(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 3:
        await message.answer("فرمت: /marketoffer شمارهآگهی قیمت\nمثال: /marketoffer 1 500")
        return
    try:
        lid = int(parts[1])
        price = int(parts[2])
    except ValueError:
        await message.answer("شماره و قیمت باید عدد باشند.")
        return
    if price <= 0:
        await message.answer("قیمت نامعتبر")
        return
    fee = ret.market_fee(price)
    msg = ret.place_offer(lid, message.from_user.id, price)
    await message.answer(msg + f"\nکارمزد تخمینی هنگام معامله: {fee} سکه\n/offers {lid}")


@router.message(Command("offers", "پیشنهادها"))
async def cmd_offers(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("/offers شمارهآگهی")
        return
    try:
        lid = int(parts[1])
    except ValueError:
        await message.answer("شماره نامعتبر")
        return
    await message.answer(ret.list_offers(lid))
