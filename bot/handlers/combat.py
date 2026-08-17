import random
from aiogram import Router
from aiogram.types import Message
from aiogram.filters import Command

from database.engine import async_session
from database.crud import get_or_create_user
from services.power import calc_power, win_chance
# martial spirit bonus applied inside calc_power
from services.combat_blood import apply_damage, apply_poison, check_poison_death, has_cyrus
from services.i18n import tr

router = Router()


@router.message(Command("kill", "بکش", "قتل"))
async def cmd_kill(message: Message):
    try:
        await _cmd_kill_impl(message)
    except Exception as e:
        import logging, traceback
        logging.getLogger(__name__).exception("kill error: %s", e)
        await message.answer(f"⚠️ خطا در /kill: {type(e).__name__}\n{str(e)[:200]}")

async def _cmd_kill_impl(message: Message):
    if message.reply_to_message and message.reply_to_message.from_user:
        if message.reply_to_message.from_user.is_bot:
            await message.answer("🤖 کسی نمیتواند ربات را بکشد.")
            return

    if not message.reply_to_message:
        await message.answer(
            "☠️ حمله: ریپلای + /kill\n"
            "با یک ضربه نمیمیرد — زخمی و مسموم میشود.\n"
            "۳ ساعت فرصت /heal با قرص سلامتی."
        )
        return
    if message.reply_to_message.from_user.id == message.from_user.id:
        await message.answer(tr(message.from_user.id, "خودت را نه."))
        return

    async with async_session() as session:
        attacker = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        t = message.reply_to_message.from_user
        victim = await get_or_create_user(session, t.id, t.full_name, t.username)
        if attacker.is_dead:
            await message.answer(tr(message.from_user.id, "تو مردهای."))
            return
        from services.prison import check_prison_block, record_kill, put_in_prison, KILL_LIMIT_PER_DAY
        block = await check_prison_block(session, attacker)
        if block:
            await message.answer(block)
            return
        from services.cultivation import is_immortal_race
        from services.immortal import is_immortal_tg, is_immortal_user
        if is_immortal_race(getattr(victim, "race", None)) or is_immortal_tg(t.id) or is_immortal_user(victim):
            await message.answer("🛡️ این بازیکن نامیراست و نمیمیرد.")
            return
        if victim.is_dead:
            await message.answer(tr(message.from_user.id, "طرف مرده است."))
            return
        msg_p = await check_poison_death(session, attacker)
        if msg_p:
            await message.answer(msg_p)
            return

        p1 = await calc_power(session, attacker)
        p2 = await calc_power(session, victim)
        # قدرت تعیین میکند چقدر آسیب
        dmg = 12 + max(0, (p1["total"] - p2["total"]) // 15)
        cyrus = has_cyrus(attacker)
        if cyrus:
            res = await apply_damage(
                session, attacker, victim, dmg,
                is_cyrus_strike=True, is_death_duel=True
            )
            await message.answer(
                f"⚔️ {attacker.full_name} با شمشیر کوروش به {victim.full_name} زد!\n"
                + str(res.get("msg") or "")
            )
            return

        res = await apply_damage(session, attacker, victim, dmg)
        poison_msg = await apply_poison(session, victim)
        text = (
            f"⚔️ حمله {attacker.full_name} به {victim.full_name}" + chr(10)
            + f"قدرت {p1['total']} vs {p2['total']}" + chr(10)
            + f"آسیب: {res.get('damage')} | خون حریف: {res.get('blood')}/{res.get('max_blood', 100)}" + chr(10)
            + str(res.get("msg") or "") + chr(10) + poison_msg
        )
        if res.get("killed"):
            n = record_kill(attacker.id)
            text += chr(10) + f"📊 قتلهای امروز تو: {n}/{KILL_LIMIT_PER_DAY}"
            if n > KILL_LIMIT_PER_DAY:
                text += chr(10) + await put_in_prison(session, attacker)
        try:
            await session.commit()
        except Exception:
            pass
        await message.answer(text)
