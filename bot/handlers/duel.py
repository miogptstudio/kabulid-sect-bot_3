import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup

from database.engine import async_session
from database.crud import get_or_create_user, get_user_by_telegram_id, create_duel, update_user_stats
from database.models import User
from services.ranking import process_duel_result
from services.xp import process_xp_for_duel
from services.power import calc_power, win_chance
from services.economy import get_or_create_wallet
from services.sects import add_contribution

router = Router()
_reject_counts: dict[tuple, int] = {}  # (user_id, date) -> count

def _reject_key(uid: int):
    from datetime import date
    return (uid, date.today().isoformat())

def _can_reject(uid: int) -> bool:
    from bot.config import DUEL_REJECT_LIMIT_PER_DAY
    return _reject_counts.get(_reject_key(uid), 0) < DUEL_REJECT_LIMIT_PER_DAY

def _inc_reject(uid: int):
    k = _reject_key(uid)
    _reject_counts[k] = _reject_counts.get(k, 0) + 1



class DuelStates(StatesGroup):
    waiting_accept = State()


async def _resolve_duel(session, challenger: User, opponent: User, stake: int = 0) -> str:
    """دوئل بر اساس قدرت — خون کم می‌شود، یک‌ضرب مرگ نیست."""
    from services.combat_blood import apply_damage, has_cyrus, ensure_blood
    await ensure_blood(challenger)
    await ensure_blood(opponent)
    p1 = await calc_power(session, challenger)
    p2 = await calc_power(session, opponent)
    logs = [f"قدرت: {challenger.full_name} {p1['total']} (سلاح {p1.get('weapon',0)}) vs {opponent.full_name} {p2['total']} (سلاح {p2.get('weapon',0)})"]
    a, b = challenger, opponent
    winner = loser = None
    for rnd in range(1, 12):
        pa = await calc_power(session, a)
        pb = await calc_power(session, b)
        if pa["total"] >= pb["total"]:
            atk, dfn = a, b
            dmg = 8 + (pa["total"] - pb["total"]) // 25
        else:
            atk, dfn = b, a
            dmg = 8 + (pb["total"] - pa["total"]) // 25
        # اگر کوروش مجهز است در دوئل عادی هم خطرناک است اما wipe فقط deathduel
        res = await apply_damage(session, atk, dfn, dmg, is_cyrus_strike=False)
        logs.append(f"راند {rnd}: {atk.full_name} → {dfn.full_name} | آسیب {res.get('damage','?')} | خون حریف {res.get('blood','?')}/{res.get('max_blood',100)}")
        if res.get("killed"):
            winner, loser = atk, dfn
            break
        await session.refresh(a)
        await session.refresh(b)
        if (a.blood or 0) <= 0:
            winner, loser = b, a
            break
        if (b.blood or 0) <= 0:
            winner, loser = a, b
            break
    if not winner:
        # هر که خون بیشتری دارد
        if (a.blood or 0) >= (b.blood or 0):
            winner, loser = a, b
        else:
            winner, loser = b, a
        logs.append("زمان تمام — برنده از روی خون باقی‌مانده")

    await update_user_stats(session, winner, won=True)
    await update_user_stats(session, loser, won=False)
    rank_result = process_duel_result(winner, loser, is_guardian=False)
    xp_messages = process_xp_for_duel(winner, loser, is_guardian=False)
    try:
        await add_contribution(session, winner.id, 10)
    except Exception:
        pass
    extra = []
    try:
        ww = await get_or_create_wallet(session, winner.id)
        ww.coins += 15
        if stake > 0:
            ww.coins += stake * 2
            extra.append(f"🎰 شرط: +{stake * 2} سکه")
    except Exception:
        pass
    # ریکاوری جزئی خون
    winner.blood = min(100, (winner.blood or 0) + 20)
    if (loser.blood or 0) > 0 and not loser.is_dead:
        loser.blood = min(100, loser.blood + 10)
    await session.commit()
    text = "🏁 <b>نتیجه دوئل (قدرت + سلاح)</b>\n" + "\n".join(logs[-6:]) + f"\n\n🩸 خون‌ها: {a.full_name} {a.blood} | {b.full_name} {b.blood}"
    text += f"\n\n🏆 برنده: <b>{winner.full_name}</b>\nبازنده: {loser.full_name}"
    if extra:
        text += "\n" + "\n".join(extra)
    if rank_result.get("messages"):
        text += "\n" + "\n".join(rank_result["messages"])
    if xp_messages:
        text += "\n" + "\n".join(xp_messages)
    return text


@router.message(Command("duel", "دوئل"))
async def cmd_duel(message: Message, state: FSMContext):
    # /duel [مبلغ شرط] با ریپلای
    stake = 0
    parts = (message.text or "").split()
    if len(parts) >= 2:
        try:
            stake = max(0, int(parts[1]))
        except ValueError:
            stake = 0
    async with async_session() as session:
        challenger = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        opponent = None
        if message.reply_to_message and message.reply_to_message.from_user:
            ou = message.reply_to_message.from_user
            if ou.id == message.from_user.id:
                await message.answer("❌ با خودت نه!")
                return
            opponent = await get_or_create_user(session, ou.id, ou.full_name, ou.username)
        elif message.entities:
            for entity in message.entities:
                if entity.type == "text_mention" and entity.user:
                    ou = entity.user
                    opponent = await get_or_create_user(session, ou.id, ou.full_name, ou.username)
                    break
            if not opponent:
                await message.answer("روی پیام حریف ریپلای کن و /duel بزن.")
                return
        else:
            await message.answer("⚔️ روی پیام حریف ریپلای کن و /duel بزن.")
            return

        if opponent.is_banned or not opponent.is_active:
            await message.answer("کاربر در دسترس نیست.")
            return

        p1 = await calc_power(session, challenger)
        p2 = await calc_power(session, opponent)
        if stake > 0:
            cw = await get_or_create_wallet(session, challenger.id)
            ow = await get_or_create_wallet(session, opponent.id)
            if cw.coins < stake:
                await message.answer(f"سکه کافی برای شرط نداری (نیاز {stake}).")
                return
            if ow.coins < stake:
                await message.answer(f"حریف سکه کافی برای شرط {stake} ندارد.")
                return
        await create_duel(session, challenger.id, opponent.id)

        builder = InlineKeyboardBuilder()
        builder.button(text="قبول ✅", callback_data=f"duelacc:{challenger.id}:{opponent.id}:{stake}")
        builder.button(text="رد ❌", callback_data=f"duelrej:{challenger.id}:{opponent.id}")
        builder.adjust(2)

        chance = win_chance(p1["total"], p2["total"]) * 100
        stake_line = f"\n🎰 شرط: <b>{stake}</b> سکه از هر طرف" if stake else "\nبدون شرط — برای شرط: /duel مبلغ"
        await message.answer(
            f"⚔️ <b>درخواست دوئل</b>\n\n"
            f"از: {challenger.full_name} — قدرت {p1['total']}\n"
            f"به: {opponent.full_name} — قدرت {p2['total']}\n"
            f"شانس چالش‌گر: ~{chance:.0f}%{stake_line}\n\n"
            f"قدرت شامل تکنیک و سلاح است.\n"
            f"فقط <b>{opponent.full_name}</b> دکمه بزند.",
            reply_markup=builder.as_markup(),
        )
        await state.update_data(challenger_id=challenger.id, opponent_id=opponent.id, stake=stake)
        await state.set_state(DuelStates.waiting_accept)


@router.callback_query(F.data.startswith("duelacc:"))
async def cb_duel_accept(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    challenger_id, opponent_id = int(parts[1]), int(parts[2])
    stake = int(parts[3]) if len(parts) > 3 else 0
    async with async_session() as session:
        me = await get_user_by_telegram_id(session, callback.from_user.id)
        if not me or me.id != opponent_id:
            await callback.answer()
            return
        challenger = await session.get(User, challenger_id)
        opponent = me
        if stake > 0:
            cw = await get_or_create_wallet(session, challenger.id)
            ow = await get_or_create_wallet(session, opponent.id)
            if cw.coins < stake or ow.coins < stake:
                await callback.message.edit_text("یکی از طرفین سکه شرط را ندارد. دوئل لغو.")
                await state.clear()
                await callback.answer()
                return
            cw.coins -= stake
            ow.coins -= stake
            await session.commit()
        text = await _resolve_duel(session, challenger, opponent, stake=stake)
        await callback.message.edit_text(text)
    await state.clear()
    await callback.answer()


@router.callback_query(F.data.startswith("duelrej:"))
async def cb_duel_reject(callback: CallbackQuery, state: FSMContext):
    parts = callback.data.split(":")
    opponent_id = int(parts[2])
    async with async_session() as session:
        me = await get_user_by_telegram_id(session, callback.from_user.id)
        if not me or me.id != opponent_id:
            await callback.answer()
            return
        if not _can_reject(callback.from_user.id):
            await callback.answer("امروز ۵ بار رد کردی. فردا دوباره.", show_alert=True)
            return
        _inc_reject(callback.from_user.id)
    await callback.message.edit_text("❌ دوئل رد شد.")
    await state.clear()
    await callback.answer()


@router.message(DuelStates.waiting_accept, F.text.lower().in_(["قبول", "accept", "آره"]))
async def accept_text(message: Message, state: FSMContext):
    data = await state.get_data()
    async with async_session() as session:
        me = await get_user_by_telegram_id(session, message.from_user.id)
        if not me or me.id != data.get("opponent_id"):
            await message.answer("فقط طرف مقابل!")
            return
        challenger = await session.get(User, data["challenger_id"])
        text = await _resolve_duel(session, challenger, me)
        await message.answer(text)
    await state.clear()


@router.message(DuelStates.waiting_accept, F.text.lower().in_(["رد", "reject", "نه"]))
async def reject_text(message: Message, state: FSMContext):
    data = await state.get_data()
    async with async_session() as session:
        me = await get_user_by_telegram_id(session, message.from_user.id)
        if not me or me.id not in (data.get("opponent_id"), data.get("challenger_id")):
            await message.answer("این دوئل مال تو نیست.")
            return
    await message.answer("❌ دوئل رد شد.")
    await state.clear()
