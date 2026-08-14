"""غار، قبیله، بازرگانی، رگ معنوی، بچه زوج"""
import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command

from database.engine import async_session
from database.crud import get_or_create_user
from services.economy import get_or_create_wallet
from services import caves as caves_svc
from services import tribes as tribes_svc
from services import trade_guild as trade_svc
from services.cities import get_city, ensure_user_city
from services.cultivation import SPIRITUAL_VEINS, unlock_vein, get_veins, add_energy
from services.dual import CHILD_CHANCE
from services.i18n import t_user
from services.marriage import get_wives, get_husband

router = Router()

# ---- غار ----
@router.message(Command("cave", "غار", "explorecave", "گردش‌غار"))
async def cmd_cave(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        cid = await ensure_user_city(session, user)
        city = get_city(cid)
        city_name = city.get("name", "شهر")
        result = caves_svc.explore(message.from_user.id, city_name)
        if isinstance(result, str):
            await message.answer(result)
            return
        if isinstance(result, tuple) and result and result[0] == "multi":
            _, rewards, cave, rarity = result
            lines = [f"🕳 <b>«{cave}»</b> ({rarity}) — {city_name}", "غنیمت:"]
            w = await get_or_create_wallet(session, user.id)
            for typ, val in rewards:
                if typ == "coins":
                    w.coins = (w.coins or 0) + val
                    lines.append(f"• +{val} سکه")
                elif typ == "spirit":
                    w.spirit_stones = (w.spirit_stones or 0) + val
                    lines.append(f"• +{val} سنگ روحی")
                elif typ == "energy":
                    res = await add_energy(session, user.id, val)
                    lines.append(f"• +{val} انرژی")
                elif typ == "danger" and hasattr(user, "lifespan"):
                    user.lifespan = max(1, (user.lifespan or 100) - val)
                    lines.append(f"• آسیب (−{val} عمر)")
            await session.commit()
            await message.answer(chr(10).join(lines))
            return
        kind, typ, val, cave, rarity = result
        if typ == "coins":
            w = await get_or_create_wallet(session, user.id)
            w.coins = (w.coins or 0) + val
            await session.commit()
            await message.answer(
                f"🕳 «{cave}» ({rarity}) در {city_name}" + chr(10)
                + f"غنیمت: +{val} سکه"
            )
        elif typ == "spirit":
            w = await get_or_create_wallet(session, user.id)
            w.spirit_stones = (w.spirit_stones or 0) + val
            await session.commit()
            await message.answer(
                f"🕳 «{cave}» ({rarity}) در {city_name}" + chr(10)
                + f"غنیمت: +{val} سنگ روحی"
            )
        elif typ == "energy":
            res = await add_energy(session, user.id, val)
            await message.answer(
                f"🕳 «{cave}» ({rarity})" + chr(10)
                + f"+{val} انرژی" + chr(10)
                + chr(10).join(res.get("messages") or [])
            )
        else:
            # danger - lose lifespan lightly if exists
            if hasattr(user, "lifespan"):
                user.lifespan = max(1, (user.lifespan or 100) - val)
                await session.commit()
            await message.answer(
                f"🕳 «{cave}» خطرناک بود!" + chr(10)
                + f"آسیب دیدی (−{val} عمر تقریبی)."
            )


# ---- قبیله ----
@router.message(Command("createtribe", "تأسیس‌قبیله", "ساخت‌قبیله"))
async def cmd_create_tribe(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "/createtribe نام‌قبیله"))
        return
    msg = tribes_svc.create_tribe(
        message.from_user.id, parts[1], message.from_user.full_name or "?"
    )
    await message.answer(msg)


@router.message(Command("tribes", "قبایل"))
async def cmd_tribes(message: Message):
    await message.answer(tribes_svc.list_tribes())


@router.message(Command("tribe", "قبیله‌من"))
async def cmd_tribe(message: Message):
    await message.answer(tribes_svc.info(message.from_user.id))


@router.message(Command("jointribe", "عضویت‌قبیله"))
async def cmd_join_tribe(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "/jointribe نام"))
        return
    await message.answer(tribes_svc.join_tribe(message.from_user.id, parts[1]))


@router.message(Command("tribeleave", "ترک‌قبیله"))
async def cmd_tribe_leave(message: Message):
    await message.answer(tribes_svc.leave(message.from_user.id))


@router.message(Command("setchief", "بزرگ‌قبیله"))
async def cmd_set_chief(message: Message):
    if not message.reply_to_message:
        await message.answer(tr(message.from_user.id, "ریپلای عضو + /setchief"))
        return
    await message.answer(
        tribes_svc.set_chief(message.from_user.id, message.reply_to_message.from_user.id)
    )


@router.message(Command("tribeinvite", "دعوت‌قبیله"))
async def cmd_tribe_invite(message: Message):
    if not message.reply_to_message:
        await message.answer(tr(message.from_user.id, "ریپلای + /tribeinvite — طرف باید /jointribe نام بزند"))
        return
    info = tribes_svc.info(message.from_user.id)
    await message.answer(
        f"دعوت قبیله برای {message.reply_to_message.from_user.full_name}" + chr(10)
        + info + chr(10)
        + "او باید /jointribe نام‌قبیله بزند."
    )


# ---- بازرگانی ----
@router.message(Command("tradeguild", "گروه‌بازرگانی", "بازرگانی"))
async def cmd_trade_guild(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "/tradeguild نام‌گروه"))
        return
    await message.answer(
        trade_svc.create(message.from_user.id, parts[1], message.from_user.full_name or "?")
    )


@router.message(Command("tradelist", "لیست‌بازرگانی"))
async def cmd_trade_list(message: Message):
    await message.answer(trade_svc.list_all())


@router.message(Command("tradeinfo", "وضعیت‌بازرگانی"))
async def cmd_trade_info(message: Message):
    await message.answer(trade_svc.info(message.from_user.id))


@router.message(Command("tradejoin", "عضویت‌بازرگانی"))
async def cmd_trade_join(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "/tradejoin نام"))
        return
    await message.answer(trade_svc.join(message.from_user.id, parts[1]))


@router.message(Command("tradeleave", "ترک‌بازرگانی"))
async def cmd_trade_leave(message: Message):
    await message.answer(trade_svc.leave(message.from_user.id))


@router.message(Command("tradedeposit", "واریز‌بازرگانی"))
async def cmd_trade_deposit(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "/tradedeposit مبلغ"))
        return
    try:
        amount = int(parts[1])
    except ValueError:
        await message.answer(tr(message.from_user.id, "مبلغ عدد باشد."))
        return
    ok, a, b = trade_svc.deposit(message.from_user.id, amount)
    if not ok:
        await message.answer(a)
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
        if (w.coins or 0) < amount:
            await message.answer(tr(message.from_user.id, "سکه کافی نیست."))
            return
        w.coins -= amount
        await session.commit()
    trade_svc.do_deposit(message.from_user.id, amount)
    await message.answer(f"✅ {amount} سکه به صندوق گروه واریز شد.")


@router.message(Command("tradewithdraw", "برداشت‌بازرگانی"))
async def cmd_trade_withdraw(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "/tradewithdraw مبلغ"))
        return
    try:
        amount = int(parts[1])
    except ValueError:
        await message.answer(tr(message.from_user.id, "مبلغ عدد."))
        return
    ok, msg = trade_svc.withdraw(message.from_user.id, amount)
    if not ok:
        await message.answer(msg)
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
        w.coins = (w.coins or 0) + amount
        await session.commit()
    await message.answer(msg + chr(10) + f"+{amount} سکه به کیف تو")


# ---- رگ معنوی ----
@router.message(Command("vein", "رگ", "رگ‌معنوی", "veins"))
async def cmd_vein(message: Message):
    from services.cultivation import MAX_VEINS
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        cur = get_veins(user.id)
    text = f"🩸 <b>رگ معنوی</b> (حداکثر {MAX_VEINS} همزمان)" + chr(10) + chr(10)
    lines = []
    for name, info in SPIRITUAL_VEINS.items():
        mark = "✅" if name in cur else "○"
        lines.append(f"{mark} {name} — {info['desc']} (×{info['mult']})")
    text += chr(10).join(lines[:20])
    await message.answer(text)
    if len(lines) > 20:
        await message.answer(chr(10).join(lines[20:]))
    await message.answer(
        "فعلی: " + (", ".join(cur) if cur else "هیچ") + chr(10)
        + "/unlockvein نام‌رگ" + chr(10)
        + "مثال: /unlockvein رگ سیمرغ"
    )


@router.message(Command("unlockvein", "باز‌رگ"))
async def cmd_unlock_vein(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("/unlockvein رگ یانگ" + chr(10) + "/unlockvein رگ یین")
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        msg = unlock_vein(user.id, parts[1].strip())
    await message.answer(msg)


# ---- بچه زن و شوهر ----
_couple_child_cd: dict = {}

@router.message(Command("havechild", "بچه", "فرزندآوری"))
async def cmd_have_child(message: Message):
    """بچه برای زوج متاهل — شانس نادر، کول‌داون ۲۴س"""
    from datetime import datetime, timedelta
    from bot.handlers.social import _servant_children
    key = message.from_user.id
    last = _couple_child_cd.get(key)
    if last and datetime.utcnow() - last < timedelta(hours=24):
        await message.answer(tr(message.from_user.id, "⏳ هر ۲۴ ساعت یک‌بار می‌توانی تلاش کنی."))
        return
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        wives = await get_wives(session, user.id)
        hus = await get_husband(session, user.id)
        if not wives and not hus:
            await message.answer(t_user(message.from_user.id, "married_need"))
            return
        partner_name = "?"
        if wives:
            from database.models import User as U
            p = await session.get(U, wives[0].wife_id)
            partner_name = p.full_name if p else "?"
        elif hus:
            from database.models import User as U
            p = await session.get(U, hus.husband_id)
            partner_name = p.full_name if p else "?"
        if user.gender not in ("مرد", "زن"):
            await message.answer(tr(message.from_user.id, "اول /gender"))
            return
    _couple_child_cd[key] = datetime.utcnow()
    if random.random() < CHILD_CHANCE:
        child = {
            "name": f"فرزند {message.from_user.full_name[:8]} و {partner_name[:8]}",
            "gender": random.choice(["مرد", "زن"]),
            "partner": partner_name,
        }
        _servant_children.setdefault(message.from_user.id, []).append(child)
        await message.answer(
            "👶✨ معجزه!" + chr(10)
            + f"{child['name']} ({child['gender']})" + chr(10)
            + "/mychildren"
        )
    else:
        await message.answer(
            "این بار فرزندی به دنیا نیامد." + chr(10)
            + f"شانس بسیار نادر ({CHILD_CHANCE}). فردا دوباره /havechild"
        )
