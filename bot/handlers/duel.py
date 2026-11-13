import random
from aiogram import Router, F
from bot.utils.safe_telegram import safe_edit_text
from aiogram.types import Message, FSInputFile, CallbackQuery, URLInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from sqlalchemy import select

from database.engine import async_session
from database.crud import get_or_create_user, get_user_by_telegram_id, create_duel, update_user_stats
from database.models import User
from services.ranking import process_duel_result
from services.xp import process_xp_for_duel
from services.power import calc_power, win_chance
from services.economy import get_or_create_wallet
from services.sects import add_contribution
from services.i18n import tr
from services.portraits import panel_url
from bot.utils.media import safe_answer_photo
import random as _rnd_dodge

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
    """دوئل پیشرفته v61: قدرت + سرعت + کریت + واریانس + کمبو — خون کم می‌شود، مرگ یک‌ضرب نیست."""
    from services.combat_blood import apply_damage, ensure_blood, max_blood_async
    import random as _rnd

    await ensure_blood(challenger)
    await ensure_blood(opponent)

    # قدرت فقط یک‌بار در شروع محاسبه می‌شود (بهینه‌تر و پایدارتر)
    p1 = await calc_power(session, challenger)
    p2 = await calc_power(session, opponent)
    logs = [
        f"⚡ قدرت: {challenger.full_name} <b>{p1['total']}</b> "
        f"(سلاح {p1.get('weapon',0)} | سرعت {p1.get('speed',10)}) vs "
        f"{opponent.full_name} <b>{p2['total']}</b> "
        f"(سلاح {p2.get('weapon',0)} | سرعت {p2.get('speed',10)})"
    ]

    a, b = challenger, opponent
    pa, pb = p1, p2
    winner = loser = None
    max_rounds = 14

    for rnd in range(1, max_rounds + 1):
        # ابتکار عمل بر اساس سرعت + کمی شانس
        spd_a = int(pa.get("speed", 10) or 10) + _rnd.randint(0, 8)
        spd_b = int(pb.get("speed", 10) or 10) + _rnd.randint(0, 8)
        if spd_a >= spd_b:
            atk, dfn, atk_p, dfn_p = a, b, pa, pb
        else:
            atk, dfn, atk_p, dfn_p = b, a, pb, pa

        # آسیب پایه + واریانس + کریت
        power_diff = max(0, atk_p["total"] - dfn_p["total"])
        base_dmg = 10 + power_diff // 20 + _rnd.randint(0, 6)
        # کریت بر اساس سرعت و dodge حریف
        crit_chance = min(0.28, 0.06 + (atk_p.get("speed", 10) / 200) + (atk_p.get("penetration", 0) / 300))
        is_crit = _rnd.random() < crit_chance
        if is_crit:
            base_dmg = int(base_dmg * 1.65) + 5

        # شانس فعال شدن کمبو
        combo_msg = ""
        try:
            from services.combo_combat import try_combo
            # بررسی مالکیت آرش برای کمبوهای ویژه
            has_arash = False
            try:
                from services.persist import get_dict
                owners = (get_dict("arash_event") or {}).get("owners") or {}
                has_arash = str(int(getattr(atk, "telegram_id", 0) or 0)) in owners
            except Exception:
                pass
            combo_res = try_combo(int(getattr(atk, "telegram_id", 0) or 0), has_arash=has_arash)
            if combo_res:
                base_dmg = int(base_dmg * float(combo_res.get("mult", 1.3)))
                combo_msg = f" | 🔥{combo_res.get('name', 'کمبو')}"
        except Exception:
            pass

        res = await apply_damage(session, atk, dfn, base_dmg, is_cyrus_strike=False)
        dmg_done = res.get("damage", base_dmg)
        if res.get("dodged"):
            logs.append(f"راند {rnd}: 🛡️ {dfn.full_name} جاخالی داد!{combo_msg}")
        else:
            crit_tag = "💥کریت! " if is_crit else ""
            logs.append(
                f"راند {rnd}: {crit_tag}{atk.full_name} → {dfn.full_name} | "
                f"آسیب <b>{dmg_done}</b> | خون {res.get('blood','?')}/{res.get('max_blood',100)}"
                f"{combo_msg}"
            )

        if res.get("killed") or (getattr(dfn, "blood", 0) or 0) <= 0:
            winner, loser = atk, dfn
            break

        await session.refresh(a)
        await session.refresh(b)

    if not winner:
        # تصمیم نهایی با خون + کمی شانس قدرت
        blood_a = int(getattr(a, "blood", 0) or 0)
        blood_b = int(getattr(b, "blood", 0) or 0)
        if blood_a > blood_b:
            winner, loser = a, b
        elif blood_b > blood_a:
            winner, loser = b, a
        else:
            # تساوی خون → شانس بر اساس قدرت
            if _rnd.random() < win_chance(pa["total"], pb["total"]):
                winner, loser = a, b
            else:
                winner, loser = b, a
        logs.append("⏱ زمان تمام — برنده بر اساس خون باقیمانده و قدرت")

    await update_user_stats(session, winner, won=True)
    extra = []
    try:
        from services.achievements import check_and_award
        msg_a = await check_and_award(session, winner, "first_win")
        if msg_a:
            extra.append(msg_a)
        if int(getattr(winner, "win_streak", 0) or 0) >= 10:
            msg_b = await check_and_award(session, winner, "win_streak_10")
            if msg_b:
                extra.append(msg_b)
    except Exception:
        pass
    try:
        from services.retention import event_add_score
        if getattr(winner, 'telegram_id', None):
            event_add_score(int(winner.telegram_id), 5)
        try:
            from services.martial_quests import progress
            if getattr(winner, "telegram_id", None):
                progress(int(winner.telegram_id), "duels_won", 1)
                progress(int(winner.telegram_id), "duels_done", 1)
            if getattr(loser, "telegram_id", None):
                progress(int(loser.telegram_id), "duels_done", 1)
        except Exception:
            pass
        try:
            from services.campaign import progress as camp_prog
            from services.season_league import add_score
            from services.combo_combat import unlock_by_progress
            camp_prog(int(winner.telegram_id), "duels_won", 1)
            camp_prog(int(winner.telegram_id), "duels_done", 1)
            if getattr(loser, "telegram_id", None):
                camp_prog(int(loser.telegram_id), "duels_done", 1)
            add_score(int(winner.telegram_id), 15, "duel_win")
            if getattr(loser, "telegram_id", None):
                add_score(int(loser.telegram_id), 3, "duel_loss")
            unlock_by_progress(int(winner.telegram_id), duels_won=int(getattr(winner, "wins", 0) or 0))
        except Exception:
            pass
    except Exception:
        pass
    try:
        from services.missions_progress import bump_mission
        await bump_mission(session, winner.id, "duels")
        await bump_mission(session, winner.id, "wins")
        await bump_mission(session, loser.id, "duels")
    except Exception:
        pass
    await update_user_stats(session, loser, won=False)
    rank_result = process_duel_result(winner, loser, is_guardian=False)
    xp_messages = process_xp_for_duel(winner, loser, is_guardian=False)
    try:
        await add_contribution(session, winner.id, 10)
    except Exception:
        pass
    try:
        ww = await get_or_create_wallet(session, winner.id)
        ww.coins += 15
        if stake > 0:
            ww.coins += stake * 2
            extra.append(f"🎰 شرط: +{stake * 2} سکه")
    except Exception:
        pass
    # ریکاوری جزئی خون
    try:
        from services.combat_blood import max_blood_async
        _mxw = await max_blood_async(session, winner)
        winner.blood = min(_mxw, (winner.blood or 0) + max(20, _mxw // 10))
    except Exception:
        winner.blood = min(100, (winner.blood or 0) + 20)
    if (loser.blood or 0) > 0 and not loser.is_dead:
        loser.blood = min(100, loser.blood + 10)
    await session.commit()

    # خلاصه آسیب
    dmg_total = 0
    try:
        import re as _re
        for _ln in logs:
            _m = _re.search(r"آسیب\s+(?:<b>)?(\d+)", _ln)
            if _m:
                dmg_total += int(_m.group(1))
    except Exception:
        pass

    blood_w = getattr(winner, "blood", 0) or 0
    blood_l = getattr(loser, "blood", 0) or 0
    text = (
        f"⚔️ <b>نتیجه دوئل پیشرفته</b>\n"
        f"🏆 برنده: <b>{winner.full_name}</b> (خون {blood_w})\n"
        f"💀 بازنده: {loser.full_name} (خون {blood_l})\n"
        f"💥 آسیب کل تقریبی: {dmg_total or '—'}\n"
    )
    # لاگ کوتاه و خوانا
    if len(logs) <= 5:
        text += "\n" + "\n".join(logs)
    else:
        text += "\n" + "\n".join(logs[:2] + ["…"] + logs[-2:])
    if extra:
        text += "\n\n" + "\n".join(extra)
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
                await message.answer(tr(message.from_user.id, "❌ با خودت نه!"))
                return
            opponent = await get_or_create_user(session, ou.id, ou.full_name, ou.username)
        elif message.entities:
            for entity in message.entities:
                if entity.type == "text_mention" and entity.user:
                    ou = entity.user
                    opponent = await get_or_create_user(session, ou.id, ou.full_name, ou.username)
                    break
            if not opponent:
                await message.answer(tr(message.from_user.id, "روی پیام حریف ریپلای کن و /duel بزن."))
                return
        else:
            await message.answer(tr(message.from_user.id, "⚔️ روی پیام حریف ریپلای کن و /duel بزن."))
            return

        if opponent.is_banned or not opponent.is_active:
            await message.answer(tr(message.from_user.id, "کاربر در دسترس نیست."))
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
        await message.answer_photo(
            FSInputFile(panel_url("duel", getattr(challenger, "gender", "مرد"), f"{challenger.id}-{opponent.id}")),
            caption=f"⚔️ <b>درخواست دوئل پیشرفته</b>\n\n"
            f"از: {challenger.full_name} — قدرت <b>{p1['total']}</b> (سرعت {p1.get('speed',10)})\n"
            f"به: {opponent.full_name} — قدرت <b>{p2['total']}</b> (سرعت {p2.get('speed',10)})\n"
            f"شانس تقریبی چالشگر: <b>{chance:.0f}%</b>{stake_line}\n\n"
            f"نبرد نوبتی با کریت، جاخالی، کمبو و خون.\n"
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
                await safe_edit_text(callback, tr(callback.from_user.id, "یکی از طرفین سکه شرط را ندارد. دوئل لغو."))
                await state.clear()
                await callback.answer()
                return
            cw.coins -= stake
            ow.coins -= stake
            await session.commit()
        text = await _resolve_duel(session, challenger, opponent, stake=stake)
        try:
            await callback.message.delete()
        except Exception:
            pass
        await callback.message.answer_photo(
            FSInputFile(panel_url("duel", getattr(winner if "winner" in locals() else opponent, "gender", "مرد"), f"result-{challenger.id}-{opponent.id}")),
            caption=text
        )
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
            await callback.answer(tr(callback.from_user.id, "امروز ۵ بار رد کردی. فردا دوباره."), show_alert=True)
            return
        _inc_reject(callback.from_user.id)
    await safe_edit_text(callback, tr(callback.from_user.id, "❌ دوئل رد شد."))
    await state.clear()
    await callback.answer()


@router.message(DuelStates.waiting_accept, F.text.lower().in_(["قبول", "accept", "آره"]))
async def accept_text(message: Message, state: FSMContext):
    data = await state.get_data()
    async with async_session() as session:
        me = await get_user_by_telegram_id(session, message.from_user.id)
        if not me or me.id != data.get("opponent_id"):
            await message.answer(tr(message.from_user.id, "فقط طرف مقابل!"))
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
            await message.answer(tr(message.from_user.id, "این دوئل مال تو نیست."))
            return
    await message.answer(tr(message.from_user.id, "❌ دوئل رد شد."))
    await state.clear()



# ---- دوئل اختصاصی خدمتکاران ----

@router.message(Command("servantduel", "دوئلخدمتکار", "دوئلخدمتکاران"))
async def cmd_servant_duel(message: Message):
    parts = (message.text or "").split()
    try:
        if message.reply_to_message and message.reply_to_message.from_user:
            target = message.reply_to_message.from_user.id
            if len(parts) < 3:
                await message.answer(
                    "فرمت:\n<code>/servantduel شماره_خدمتکار_من شماره_خدمتکار_حریف</code>\n"
                    "یا روی پیام حریف ریپلای کن."
                )
                return
            idx_a, idx_b = int(parts[1]), int(parts[2])
        else:
            if len(parts) < 4:
                await message.answer(
                    "فرمت:\n<code>/servantduel آیدی_حریف شماره_من شماره_حریف</code>"
                )
                return
            target, idx_a, idx_b = int(parts[1]), int(parts[2]), int(parts[3])
    except ValueError:
        await message.answer("❌ شمارهها و آیدی باید عدد باشند.")
        return

    if target == message.from_user.id:
        await message.answer("❌ نمیتوانی با خودت دوئل خدمتکار راه بیندازی.")
        return

    from services.servants import propose_servant_duel
    ok, text, _key = propose_servant_duel(
        message.from_user.id, target, idx_a, idx_b
    )
    await message.answer(text)

@router.message(Command("acceptservduel", "قبولدوئلخدمتکار"))
async def cmd_accept_servant_duel(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("<code>/acceptservduel کلید</code>")
        return
    from services.servants import accept_servant_duel
    ok, text = accept_servant_duel(parts[1].strip(), message.from_user.id)
    await message.answer(text)

# ---- صف دوئل رندوم ----
_random_queue: dict[int, float] = {}  # tg_id -> timestamp
_QUEUE_TTL = 120  # ثانیه


@router.message(Command("randomduel", "دوئلرندوم", "رندومدوئل", "duelrandom", "rd"))
async def cmd_random_duel(message: Message, state: FSMContext):
    """دوئل با حریف تصادفی — صف یا انتخاب از بازیکنان فعال"""
    import time
    tg = message.from_user.id
    now = time.time()
    # پاکسازی صف منقضی
    expired = [k for k, t0 in _random_queue.items() if now - t0 > _QUEUE_TTL]
    for k in expired:
        _random_queue.pop(k, None)

    stake = 0
    parts = (message.text or "").split()
    if len(parts) >= 2:
        try:
            stake = max(0, int(parts[1]))
        except ValueError:
            stake = 0

    # اگر کسی در صف است (غیر از خودت) → مچ
    partner_tg = None
    for other_tg, t0 in list(_random_queue.items()):
        if other_tg != tg and now - t0 <= _QUEUE_TTL:
            partner_tg = other_tg
            break

    async with async_session() as session:
        me = await get_or_create_user(
            session, tg, message.from_user.full_name, message.from_user.username
        )
        if partner_tg:
            _random_queue.pop(partner_tg, None)
            _random_queue.pop(tg, None)
            from database.crud import get_user_by_telegram_id
            partner = await get_user_by_telegram_id(session, partner_tg)
            if not partner or partner.id == me.id:
                await message.answer("حریف صف پیدا نشد. دوباره /randomduel بزن.")
                return
            if stake > 0:
                from services.economy import get_or_create_wallet
                cw = await get_or_create_wallet(session, me.id)
                ow = await get_or_create_wallet(session, partner.id)
                if int(cw.coins or 0) < stake or int(ow.coins or 0) < stake:
                    await message.answer("یکی از طرفین سکه شرط را ندارد.")
                    return
                cw.coins -= stake
                ow.coins -= stake
                await session.commit()
            text = await _resolve_duel(session, me, partner, stake=stake)
            await message.answer(
                f"🎲 مچ رندوم!\n{me.full_name} ⚔️ {partner.full_name}\n\n" + text
            )
            try:
                await message.bot.send_message(
                    partner_tg,
                    f"🎲 در دوئل رندوم با <b>{me.full_name}</b> مچ شدی!\n\n" + text,
                )
            except Exception:
                pass
            return

        # کسی در صف نیست — سعی کن حریف تصادفی از دیتابیس
        result = await session.execute(
            select(User).where(
                User.is_active == True,
                User.is_banned == False,
                User.id != me.id,
            )
        )
        candidates = list(result.scalars().all())
        # فقط حریفهایی که اختلاف سطحشان بیش از حد مجاز نیست
        my_level = int(me.level or 1)
        near = [u for u in candidates if abs(int(u.level or 1) - my_level) <= 15]
        pool = near

        if not pool:
            # ورود به صف
            _random_queue[tg] = now
            await message.answer(
                "🎲 کسی برای دوئل رندوم آنلاین/ثبتنامشده پیدا نشد.\n"
                f"به صف اضافه شدی ({_QUEUE_TTL} ثانیه).\n"
                "نفر بعدی که /randomduel بزند با تو مچ میشود.\n"
                "لغو: /cancelrandom"
            )
            return

        opponent = random.choice(pool)
        # درخواست دوئل مثل دوئل عادی
        from aiogram.utils.keyboard import InlineKeyboardBuilder
        builder = InlineKeyboardBuilder()
        builder.button(
            text="✅ قبول رندوم",
            callback_data=f"duelacc:{me.id}:{opponent.id}:{stake}",
        )
        builder.button(
            text="❌ رد",
            callback_data=f"duelrej:{me.id}:{opponent.id}",
        )
        builder.adjust(2)
        p1 = 0
        p2 = 0
        try:
            p1 = await calc_power(session, me)
            p2 = await calc_power(session, opponent)
        except Exception:
            pass
        p1_total = p1.get("total", 0) if isinstance(p1, dict) else p1
        p2_total = p2.get("total", 0) if isinstance(p2, dict) else p2
        await message.answer(
            f"🎲 <b>دوئل رندوم</b>\n"
            f"حریف پیشنهادی: <b>{opponent.full_name}</b>\n"
            f"سطح: {opponent.level or 1} | قدرت≈{p2_total:,} (تو≈{p1_total:,})\n"
            + (f"شرط: {stake} سکه\n" if stake else "")
            + "اگر حریف آنلاین باشد میتواند قبول کند.\n"
            "یا صبر کن تا کسی /randomduel بزند و مچ شو.\n"
            "صف: دوباره /randomduel بدون حریف = ورود به صف"
        )
        # همزمان خودت را در صف بگذار برای مچ سریعتر
        _random_queue[tg] = now
        try:
            await message.bot.send_message(
                opponent.telegram_id,
                f"🎲 <b>{me.full_name}</b> تو را برای دوئل رندوم چالش کرد!\n"
                + (f"شرط: {stake} سکه\n" if stake else "")
                + f"قدرت≈{p1_total:,} vs تو≈{p2_total:,}",
                reply_markup=builder.as_markup(),
            )
            await message.answer("📨 درخواست برای حریف ارسال شد. منتظر قبول باش یا در صف بمان.")
        except Exception:
            await message.answer(
                "ارسال به حریف ممکن نشد (پیوی بسته).\n"
                f"در صف ماندی — نفر بعدی /randomduel با تو مچ میشود.\n"
                f"حریف پیشنهادی بود: {opponent.full_name}"
            )


@router.message(Command("cancelrandom", "لغورندوم"))
async def cmd_cancel_random(message: Message):
    tg = message.from_user.id
    if tg in _random_queue:
        _random_queue.pop(tg, None)
        await message.answer("✅ از صف دوئل رندوم خارج شدی.")
    else:
        await message.answer("در صف نبودی.")


@router.message(Command("randomduelfight", "رندومفوری", "rdfast"))
async def cmd_random_duel_fast(message: Message):
    """دوئل فوری با یک بازیکن تصادفی (بدون انتظار قبول — شبیهسازی)"""
    tg = message.from_user.id
    async with async_session() as session:
        me = await get_or_create_user(
            session, tg, message.from_user.full_name, message.from_user.username
        )
        result = await session.execute(
            select(User).where(
                User.is_active == True,
                User.is_banned == False,
                User.id != me.id,
            )
        )
        pool = list(result.scalars().all())
        if not pool:
            await message.answer("بازیکن دیگری نیست. اول دوستانت را دعوت کن.")
            return
        my_level = int(me.level or 1)
        near = [u for u in pool if abs(int(u.level or 1) - my_level) <= 20]
        if not near:
            await message.answer("❌ حریف مناسبی برای دوئل رندوم پیدا نشد؛ اختلاف سطح بازیکنان موجود زیاد است.")
            return
        opponent = random.choice(near)
        text = await _resolve_duel(session, me, opponent, stake=0)
        await message.answer(
            f"🎲 <b>دوئل رندوم فوری</b>\n"
            f"{me.full_name} ⚔️ {opponent.full_name}\n\n" + text
        )

