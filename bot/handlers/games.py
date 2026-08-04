from services.i18n import t_user, get_lang, t as _t
import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command, Filter as _AiogramFilter
from aiogram.utils.keyboard import InlineKeyboardBuilder

from datetime import datetime, timedelta

from database.engine import async_session
from database.crud import get_or_create_user
from services.economy import get_or_create_wallet

router = Router()

GAME_COOLDOWN = timedelta(minutes=2)
_last_game: dict[int, datetime] = {}

def check_game_cooldown(user_id: int, mark: bool = True):
    """اگر هنوز کول‌داون دارد، متن پیام برمی‌گردد؛ وگرنه None و در صورت mark زمان ثبت می‌شود"""
    now = datetime.utcnow()
    last = _last_game.get(user_id)
    if last and now - last < GAME_COOLDOWN:
        left = int((GAME_COOLDOWN - (now - last)).total_seconds())
        m, s = left // 60, left % 60
        return f"⏳ محدودیت بازی: {m} دقیقه و {s} ثانیه دیگر صبر کن."
    if mark:
        _last_game[user_id] = now
    return None


# سنگ کاغذ قیچی در انتظار
_rps_pending: dict[int, dict] = {}


@router.message(Command("games", "بازی", "بازی‌ها"))
async def cmd_games_menu(message: Message):
    _glang = get_lang(message.from_user.id)
    # i18n header always available via /games intro

    # فقط منو — زمان کول‌داون مصرف نمی‌شود
    cd_info = check_game_cooldown(message.from_user.id, mark=False)
    builder = InlineKeyboardBuilder()
    uid = message.from_user.id
    lang = _glang
    labels = {
        "rps": {"fa": "✊ سنگ‌کاغذ‌قیچی", "en": "✊ RPS", "ar": "✊ حجر ورقة", "zh": "✊ 猜拳", "ru": "✊ КНБ", "tr": "✊ TKM"},
        "dice": {"fa": "🎲 تاس", "en": "🎲 Dice", "ar": "🎲 نرد", "zh": "🎲 骰子", "ru": "🎲 Кости", "tr": "🎲 Zar"},
        "nard": {"fa": "🎯 تخته‌نرد", "en": "🎯 Backgammon", "ar": "🎯 طاولة", "zh": "🎯 双陆", "ru": "🎯 Нарды", "tr": "🎯 Tavla"},
        "casino": {"fa": "🎰 کازینو", "en": "🎰 Casino", "ar": "🎰 كازينو", "zh": "🎰 赌场", "ru": "🎰 Казино", "tr": "🎰 Casino"},
        "chess": {"fa": "♟️ شطرنج", "en": "♟️ Chess", "ar": "♟️ شطرنج", "zh": "♟️ 国际象棋", "ru": "♟️ Шахматы", "tr": "♟️ Satranç"},
        "hukum": {"fa": "🃏 حکم", "en": "🃏 Hukum", "ar": "🃏 حكم", "zh": "🃏 卡牌", "ru": "🃏 Карты", "tr": "🃏 Hukum"},
        "puzzle": {"fa": "🧩 پازل", "en": "🧩 Puzzle", "ar": "🧩 ألغاز", "zh": "🧩 谜题", "ru": "🧩 Пазл", "tr": "🧩 Bulmaca"},
        "riddle": {"fa": "🧠 معما", "en": "🧠 Riddle", "ar": "🧠 لغز", "zh": "🧠 谜语", "ru": "🧠 Загадка", "tr": "🧠 Bilmece"},
        "math": {"fa": "🔢 ریاضی", "en": "🔢 Math", "ar": "🔢 رياضة", "zh": "🔢 数学", "ru": "🔢 Математика", "tr": "🔢 Matematik"},
        "web": {"fa": "🌐 وب‌اپ", "en": "🌐 WebApp", "ar": "🌐 ويب", "zh": "🌐 网页", "ru": "🌐 WebApp", "tr": "🌐 WebApp"},
    }
    def _lb(k):
        d = labels.get(k, {})
        return d.get(lang) or d.get("fa") or k
    builder.button(text=_lb("rps"), callback_data=f"game:rps:{uid}")
    builder.button(text=_lb("dice"), callback_data=f"game:dice:{uid}")
    builder.button(text=_lb("nard"), callback_data=f"game:nard:{uid}")
    builder.button(text=_lb("casino"), callback_data=f"game:casino:{uid}")
    builder.button(text=_lb("chess"), callback_data=f"game:chess:{uid}")
    builder.button(text=_lb("hukum"), callback_data=f"game:hukum:{uid}")
    builder.button(text=_lb("puzzle"), callback_data=f"game:puzzlemenu:{uid}")
    builder.button(text=_lb("riddle"), callback_data=f"game:riddle:{uid}")
    builder.button(text=_lb("math"), callback_data=f"game:math:{uid}")
    builder.button(text=_lb("web"), callback_data=f"game:web:{uid}")
    builder.adjust(1)
    text = f"<b>{_t('games_title', lang)}</b>" + chr(10) + chr(10) + _t("games_body", lang)
    if cd_info:
        text += chr(10) + chr(10) + cd_info
    await message.answer(text, reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("game:"))
async def cb_game_menu(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) < 3:
        await callback.answer()
        return
    kind, owner = parts[1], int(parts[2])
    if callback.from_user.id != owner:
        await callback.answer()
        return
    # باز کردن زیرمنو زمان مصرف نمی‌کند؛ خود بازی مصرف می‌کند
    browse = kind in ("puzzlemenu", "web", "nard", "casino", "chess", "rps", "hukum")
    if browse:
        pass  # بدون mark
    else:
        cd = check_game_cooldown(callback.from_user.id, mark=True)
        if cd:
            await callback.answer(cd, show_alert=True)
            return

    if kind == "rps":
        builder = InlineKeyboardBuilder()
        for name, emoji in [("سنگ", "✊"), ("کاغذ", "✋"), ("قیچی", "✌")]:
            builder.button(
                text=f"{emoji} {name}",
                callback_data=f"rps:{owner}:{name}",
            )
        builder.adjust(3)
        await callback.message.edit_text(
            "✊✋✌ یکی را انتخاب کن:",
            reply_markup=builder.as_markup(),
        )
    elif kind == "nard":
        await callback.message.edit_text(tr(callback.from_user.id, "🎯 تخته‌نرد: /nard\nآنلاین در وب‌اپ → تخته‌نرد → آنلاین"))
    elif kind == "dice":
        d1, d2 = random.randint(1, 6), random.randint(1, 6)
        await callback.message.edit_text(
            f"🎲 <b>تاس تخته‌نرد</b>\n\n{d1} — {d2}\nجمع: {d1 + d2}"
        )
    elif kind == "casino":
        await callback.message.edit_text(tr(callback.from_user.id, "🎰 برای کازینو بنویس:\n/casino مبلغ\nمثال: /casino 20\n(حداقل ۱۰ سکه)"))
    elif kind == "chess":
        board = _chess_board_text()
        await callback.message.edit_text(
            f"♟️ <b>شطرنج (نمایشی)</b>\n\n<code>{board}</code>\n\n"
            f"نسخه کامل‌تر در وب‌اپ: .../webapp/games.html"
        )
    elif kind == "hukum":
        await callback.message.edit_text(tr(callback.from_user.id, "🃏 <b>حکم</b>\n\nبرای شروع: /hukum\nبا حریف: ریپلای + /hukumduel"))
    elif kind == "puzzlemenu":
        b = InlineKeyboardBuilder()
        b.button(text="🧩 پازل الگو", callback_data=f"game:pattern:{owner}")
        b.button(text="🧠 معما", callback_data=f"game:riddle:{owner}")
        b.button(text="🔢 ریاضی", callback_data=f"game:math:{owner}")
        b.button(text="🔤 به‌هم‌ریخته", callback_data=f"game:scramble:{owner}")
        b.button(text="🎯 حدس عدد", callback_data=f"game:guess:{owner}")
        b.adjust(1)
        await callback.message.edit_text(
            "🧩 <b>بازی‌های فکری و پازل</b>" + chr(10) + chr(10)
            + "یکی را انتخاب کن یا:" + chr(10)
            + "/puzzle /riddle /mathquiz /scramble /guess",
            reply_markup=b.as_markup(),
        )
    elif kind == "riddle":
        await _send_riddle(callback.message, callback.from_user.id, edit=True)
    elif kind == "math":
        await _send_math(callback.message, callback.from_user.id, edit=True)
    elif kind == "scramble":
        await _send_scramble(callback.message, callback.from_user.id, edit=True)
    elif kind == "pattern":
        await _send_pattern(callback.message, callback.from_user.id, edit=True)
    elif kind == "guess":
        await callback.message.edit_text(tr(callback.from_user.id, "🎯 /guess برای حدس عدد ۱ تا ۱۰۰"))
    elif kind == "web":
        await callback.message.edit_text(
            "🌐 در BotFather → Menu Button آدرس وب‌اپ را بگذار:\n"
            "<code>https://آدرس-render-تو/webapp/</code>\n"
            "بازی‌ها: <code>.../webapp/games.html</code>"
        )
    await callback.answer()


def _chess_board_text() -> str:
    rows = [
        "♜♞♝♛♚♝♞♜",
        "♟♟♟♟♟♟♟♟",
        "········",
        "········",
        "········",
        "········",
        "♙♙♙♙♙♙♙♙",
        "♖♘♗♕♔♗♘♖",
    ]
    return "\n".join(rows)


@router.message(Command("rps", "سنگ‌کاغذ‌قیچی"))
async def cmd_rps(message: Message):

    cd = check_game_cooldown(message.from_user.id)
    if cd:
        await message.answer(cd)
        return
    builder = InlineKeyboardBuilder()
    uid = message.from_user.id
    for name, emoji in [("سنگ", "✊"), ("کاغذ", "✋"), ("قیچی", "✌")]:
        builder.button(text=f"{emoji} {name}", callback_data=f"rps:{uid}:{name}")
    builder.adjust(3)
    await message.answer("✊✋✌ انتخاب کن:", reply_markup=builder.as_markup())


@router.callback_query(F.data.startswith("rps:"))
async def cb_rps(callback: CallbackQuery):
    parts = callback.data.split(":")
    owner, choice = int(parts[1]), parts[2]
    if callback.from_user.id != owner:
        await callback.answer()
        return
    opts = ["سنگ", "کاغذ", "قیچی"]
    bot_choice = random.choice(opts)
    if choice == bot_choice:
        result = "مساوی!"
    elif (choice == "سنگ" and bot_choice == "قیچی") or \
         (choice == "کاغذ" and bot_choice == "سنگ") or \
         (choice == "قیچی" and bot_choice == "کاغذ"):
        result = "برد! 🎉 +۵ سکه"
        async with async_session() as session:
            user = await get_or_create_user(
                session, callback.from_user.id,
                callback.from_user.full_name, callback.from_user.username
            )
            w = await get_or_create_wallet(session, user.id)
            w.coins += 5
            await session.commit()
    else:
        result = "باخت 😢"
    await callback.message.edit_text(
        f"تو: <b>{choice}</b>\nربات: <b>{bot_choice}</b>\n\n{result}"
    )
    await callback.answer()


@router.message(Command("dice", "تاس", "تخته‌نرد"))
async def cmd_dice(message: Message):

    cd = check_game_cooldown(message.from_user.id)
    if cd:
        await message.answer(cd)
        return
    d1, d2 = random.randint(1, 6), random.randint(1, 6)
    await message.answer(f"🎲 تاس: <b>{d1}</b> — <b>{d2}</b>\nجمع: {d1 + d2}")


@router.message(Command("chess", "شطرنج"))
async def cmd_chess(message: Message):

    cd = check_game_cooldown(message.from_user.id)
    if cd:
        await message.answer(cd)
        return
    await message.answer(
        f"♟️ <b>شطرنج نمایشی</b>\n\n<code>{_chess_board_text()}</code>\n\n"
        f"برای صفحه تعاملی: وب‌اپ → games.html"
    )


@router.message(Command("casino", "کازینو"))
async def cmd_casino(message: Message):

    cd = check_game_cooldown(message.from_user.id)
    if cd:
        await message.answer(cd)
        return
    parts = (message.text or "").split()
    bet = 10
    if len(parts) >= 2:
        try:
            bet = int(parts[1])
        except ValueError:
            await message.answer(tr(message.from_user.id, "فرمت: /casino مبلغ\nمثال: /casino 20"))
            return
    if bet < 10:
        await message.answer(tr(message.from_user.id, "حداقل شرط ۱۰ سکه است."))
        return

    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username
        )
        w = await get_or_create_wallet(session, user.id)
        if w.coins < bet:
            await message.answer(f"سکه کافی نیست. داری: {w.coins}")
            return
        w.coins -= bet
        roll = random.randint(1, 100)
        if roll > 95:
            win = bet * 10
            w.coins += win
            msg = f"💎 جکپات! +{win} سکه"
        elif roll > 70:
            win = bet * 2
            w.coins += win
            msg = f"🪙 برد! +{win} سکه"
        elif roll > 45:
            w.coins += bet
            msg = "برگشت شرط (مساوی)"
        else:
            msg = f"💀 باخت −{bet} سکه"
        await session.commit()
        coins = w.coins

    await message.answer(f"🎰 {msg}\nموجودی: {coins}")


_guess: dict[int, int] = {}

@router.message(Command("guess", "حدس‌عدد"))
async def cmd_guess(message: Message):

    cd = check_game_cooldown(message.from_user.id)
    if cd:
        await message.answer(cd)
        return
    parts = (message.text or "").split()
    uid = message.from_user.id
    if uid not in _guess:
        _guess[uid] = random.randint(1, 50)
        await message.answer(tr(message.from_user.id, "🔢 عددی بین ۱ تا ۵۰ انتخاب شد. /guess عدد"))
        return
    if len(parts) < 2:
        await message.answer(tr(message.from_user.id, "/guess عدد"))
        return
    try:
        n = int(parts[1])
    except ValueError:
        await message.answer(tr(message.from_user.id, "عدد بفرست"))
        return
    secret = _guess[uid]
    if n == secret:
        del _guess[uid]
        async with async_session() as session:
            user = await get_or_create_user(
                session, message.from_user.id,
                message.from_user.full_name, message.from_user.username
            )
            w = await get_or_create_wallet(session, user.id)
            w.coins += 15
            await session.commit()
        await message.answer(tr(message.from_user.id, "🎉 درست! +۱۵ سکه"))
    elif n < secret:
        await message.answer(tr(message.from_user.id, "بالاتر ⬆️"))
    else:
        await message.answer(tr(message.from_user.id, "پایین‌تر ⬇️"))


@router.message(Command("coinflip", "شیرخط"))
async def cmd_coin_flip(message: Message):
    parts = (message.text or "").split()
    pick = parts[1] if len(parts) > 1 else None
    if pick not in ("شیر", "خط"):
        await message.answer(tr(message.from_user.id, "/coinflip شیر یا /coinflip خط"))
        return
    result = random.choice(["شیر", "خط"])
    if pick == result:
        async with async_session() as session:
            user = await get_or_create_user(
                session, message.from_user.id,
                message.from_user.full_name, message.from_user.username
            )
            w = await get_or_create_wallet(session, user.id)
            w.coins += 8
            await session.commit()
        await message.answer(f"سکه: {result} — برد! +۸ سکه")
    else:
        await message.answer(f"سکه: {result} — باخت")


SUITS = ["دل", "خشت", "خاج", "پیک"]
RANKS_H = ["آس", "شاه", "بی‌بی", "سرباز", "۱۰", "۹", "۸", "۷"]

def _draw_card():
    return f"{random.choice(RANKS_H)} {random.choice(SUITS)}"


@router.message(Command("hukum", "حکم"))
async def cmd_hukum(message: Message):
    cd = check_game_cooldown(message.from_user.id)
    if cd:
        await message.answer(cd)
        return
    trump = random.choice(["دل", "خشت", "پیک", "گشنیز"])
    ranks = ["آس", "شاه", "بی‌بی", "سرباز", "۱۰", "۹", "۸"]
    suits = ["دل", "خشت", "پیک", "گشنیز"]
    hand = [f"{random.choice(ranks)} {random.choice(suits)}" for _ in range(5)]
    # store hand
    if not hasattr(cmd_hukum, "_hands"):
        cmd_hukum._hands = {}
    cmd_hukum._hands[message.from_user.id] = {"trump": trump, "hand": hand, "score": 0, "bot": 0, "round": 0}
    builder = InlineKeyboardBuilder()
    for i, c in enumerate(hand):
        builder.button(text=c, callback_data=f"hkcard:{message.from_user.id}:{i}")
    builder.adjust(1)
    await message.answer(
        f"🃏 <b>حکم</b>" + chr(10)
        + f"حکم این دست: <b>{trump}</b>" + chr(10)
        + "یک کارت انتخاب کن:",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("hkcard:"))
async def cb_hk_card(callback: CallbackQuery):
    parts = callback.data.split(":")
    owner, idx = int(parts[1]), int(parts[2])
    if callback.from_user.id != owner:
        await callback.answer()
        return
    hands = getattr(cmd_hukum, "_hands", {})
    st = hands.get(owner)
    if not st or not st.get("hand"):
        await callback.answer(tr(callback.from_user.id, "دست تمام شده. /hukum"), show_alert=True)
        return
    if idx < 0 or idx >= len(st["hand"]):
        await callback.answer(tr(callback.from_user.id, "نامعتبر"), show_alert=True)
        return
    my = st["hand"].pop(idx)
    ranks = ["آس", "شاه", "بی‌بی", "سرباز", "۱۰", "۹"]
    suits = ["دل", "خشت", "پیک", "گشنیز"]
    bot = f"{random.choice(ranks)} {random.choice(suits)}"
    def val(c):
        v = 10
        if "آس" in c: v = 14
        elif "شاه" in c: v = 13
        elif "بی‌بی" in c: v = 12
        elif "سرباز" in c: v = 11
        if st["trump"] in c:
            v += 10
        return v
    if val(my) >= val(bot):
        st["score"] += 1
        res = "بردی این دور ✅"
    else:
        st["bot"] += 1
        res = "باختی این دور ❌"
    st["round"] += 1
    if not st["hand"]:
        final = "مساوی"
        if st["score"] > st["bot"]:
            final = "برنده شدی 🎉"
            try:
                async with async_session() as session:
                    user = await get_or_create_user(
                        session, owner, callback.from_user.full_name, callback.from_user.username
                    )
                    w = await get_or_create_wallet(session, user.id)
                    w.coins = (w.coins or 0) + 15
                    await session.commit()
                final += " +15 سکه"
            except Exception:
                pass
        elif st["score"] < st["bot"]:
            final = "ربات برد"
        await callback.message.edit_text(
            f"🃏 حکم: {st['trump']}" + chr(10)
            + f"تو: {my} | ربات: {bot}" + chr(10)
            + res + chr(10) + chr(10)
            + f"پایان — تو {st['score']} | ربات {st['bot']}" + chr(10)
            + final + chr(10)
            + "/hukum دوباره"
        )
        hands.pop(owner, None)
    else:
        builder = InlineKeyboardBuilder()
        for i, c in enumerate(st["hand"]):
            builder.button(text=c, callback_data=f"hkcard:{owner}:{i}")
        builder.adjust(1)
        await callback.message.edit_text(
            f"🃏 حکم: <b>{st['trump']}</b>" + chr(10)
            + f"تو: {my} | ربات: {bot} — {res}" + chr(10)
            + f"امتیاز: تو {st['score']} | ربات {st['bot']}" + chr(10)
            + "کارت بعدی:",
            reply_markup=builder.as_markup(),
        )
    await callback.answer()


@router.message(Command("hukumduel", "حکم‌دوئل"))
async def cmd_hukum_duel(message: Message):
    if not message.reply_to_message:
        await message.answer(tr(message.from_user.id, "روی حریف ریپلای کن: /hukumduel"))
        return
    opp = message.reply_to_message.from_user
    if opp.id == message.from_user.id:
        await message.answer(tr(message.from_user.id, "با خودت نه."))
        return
    trump = random.choice(["دل", "خشت", "پیک", "گشنیز"])
    builder = InlineKeyboardBuilder()
    builder.button(
        text="قبول حکم ✅",
        callback_data=f"hukumacc:{message.from_user.id}:{opp.id}:{trump}",
    )
    await message.answer(
        f"🃏 چالش حکم از {message.from_user.full_name}" + chr(10)
        + f"حکم: <b>{trump}</b>" + chr(10)
        + f"فقط {opp.full_name} قبول کند.",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("hukumacc:"))
async def cb_hukum_acc(callback: CallbackQuery):
    parts = callback.data.split(":")
    ch, opp, trump = int(parts[1]), int(parts[2]), parts[3]
    if callback.from_user.id != opp:
        await callback.answer()
        return
    winner = random.choice([callback.from_user.full_name, "حریف"])
    await callback.message.edit_text(f"🃏 حکم {trump}" + chr(10) + f"برنده: {winner}")
    await callback.answer()


@router.message(Command("nard", "تخته‌نرد", "نرد"))
async def cmd_nard(message: Message):
    cd = check_game_cooldown(message.from_user.id)
    if cd:
        await message.answer(cd)
        return
    builder = InlineKeyboardBuilder()
    uid = message.from_user.id
    builder.button(text="🎲 با ربات", callback_data=f"nardbot:{uid}")
    builder.button(text="🌐 آنلاین (وب‌اپ)", callback_data=f"nardonline:{uid}")
    builder.adjust(1)
    await message.answer(
        "🎲 <b>تخته‌نرد</b>" + chr(10)
        + "با ربات اینجا، آنلاین در وب‌اپ (ساخت/ورود اتاق).",
        reply_markup=builder.as_markup(),
    )


@router.callback_query(F.data.startswith("nardbot:"))
async def cb_nard_bot(callback: CallbackQuery):
    owner = int(callback.data.split(":")[1])
    if callback.from_user.id != owner:
        await callback.answer()
        return
    a, b = random.randint(1, 6), random.randint(1, 6)
    c, d = random.randint(1, 6), random.randint(1, 6)
    me, bot = a + b, c + d
    res = "مساوی"
    if me > bot:
        res = "تو جلو هستی ✅"
    elif me < bot:
        res = "ربات جلو ❌"
    await callback.message.edit_text(
        f"🎲 تخته‌نرد" + chr(10)
        + f"تو: {a}-{b} = {me}" + chr(10)
        + f"ربات: {c}-{d} = {bot}" + chr(10)
        + res + chr(10)
        + "/nard دوباره | آنلاین: وب‌اپ → تخته‌نرد → آنلاین"
    )
    await callback.answer()


@router.callback_query(F.data.startswith("nardonline:"))
async def cb_nard_online(callback: CallbackQuery):
    await callback.message.edit_text(
        "🌐 تخته‌نرد آنلاین در وب‌اپ:" + chr(10)
        + "۱) منوی ربات → Open WebApp" + chr(10)
        + "۲) بخش بازی‌ها → تخته‌نرد → آنلاین" + chr(10)
        + "۳) ساخت اتاق یا ورود با کد"
    )
    await callback.answer()


# ========== فکری و پازل ==========
_pending_puzzle: dict[int, dict] = {}

RIDDLES = [
    ("چیزی که هرچه بیشتر از آن برداری بزرگ‌تر می‌شود؟", ["حفره", "چاله", "سوراخ"]),
    ("چه چیزی مال توست اما بیشتر دیگران از آن استفاده می‌کنند؟", ["اسم", "نام"]),
    ("کدام ماه ۲۸ روز دارد؟", ["همه", "همه ماه‌ها", "همه ماه ها"]),
    ("هرچه خشک‌تر شود، خیس‌تر می‌شود؟", ["حوله", "دستمال"]),
    ("چه چیزی بالا می‌رود ولی هرگز پایین نمی‌آید؟", ["سن", "عمر"]),
    ("کلید دارد اما قفل نیست، فضا دارد اما اتاق نیست؟", ["کیبورد", "صفحه‌کلید", "صفحه کلید"]),
    ("دو نفر زیر یک چتر راه می‌روند و خیس نمی‌شوند. چرا؟", ["باران نمی‌بارد", "نمی بارد", "بارانی نیست"]),
    ("چه چیزی پر از سوراخ است ولی آب نگه می‌دارد؟", ["اسفنج"]),
]

WORDS = [
    ("تذهیب", "تهذیب انرژی فرقه‌ای"),
    ("فرقه", "گروه پرورش‌دهندگان"),
    ("آسمان", "بالای سر"),
    ("شمشیر", "سلاح تیز"),
    ("جاویدان", "بی‌مرگ"),
    ("معما", "پازل فکری"),
    ("رعد", "صدای طوفان"),
    ("کیمیا", "تبدیل فلزات"),
]


def _scramble_word(w: str) -> str:
    chars = list(w)
    for _ in range(20):
        random.shuffle(chars)
        s = "".join(chars)
        if s != w:
            return s
    return "".join(reversed(w))


async def _reward(uid: int, coins: int, xp: int = 5) -> str:
    async with async_session() as session:
        user = await get_or_create_user(session, uid, "بازیکن", None)
        w = await get_or_create_wallet(session, user.id)
        w.coins = (w.coins or 0) + coins
        user.xp = (user.xp or 0) + xp
        await session.commit()
    return f"+{coins} سکه | +{xp} XP"


async def _send_riddle(message: Message, uid: int, edit: bool = False):
    q, answers = random.choice(RIDDLES)
    _pending_puzzle[uid] = {"type": "riddle", "answers": [a.strip().lower() for a in answers]}
    text = f"🧠 <b>معما</b>\n\n{q}\n\nپاسخ را بنویس (یک کلمه)."
    if edit:
        await message.edit_text(text)
    else:
        await message.answer(text)


async def _send_math(message: Message, uid: int, edit: bool = False):
    op = random.choice(["+", "-", "*"])
    if op == "+":
        a, b = random.randint(10, 99), random.randint(10, 99)
        ans = a + b
        q = f"{a} + {b} = ?"
    elif op == "-":
        a, b = random.randint(30, 120), random.randint(5, 40)
        ans = a - b
        q = f"{a} − {b} = ?"
    else:
        a, b = random.randint(3, 12), random.randint(3, 12)
        ans = a * b
        q = f"{a} × {b} = ?"
    _pending_puzzle[uid] = {"type": "math", "answers": [str(ans)]}
    text = f"🔢 <b>هوش ریاضی</b>\n\n{q}\n\nفقط عدد پاسخ را بفرست."
    if edit:
        await message.edit_text(text)
    else:
        await message.answer(text)


async def _send_scramble(message: Message, uid: int, edit: bool = False):
    word, hint = random.choice(WORDS)
    scrambled = _scramble_word(word)
    _pending_puzzle[uid] = {"type": "scramble", "answers": [word.lower()]}
    text = f"🔤 <b>کلمه به‌هم‌ریخته</b>\n\n<code>{scrambled}</code>\nراهنما: {hint}\n\nکلمه درست را بنویس."
    if edit:
        await message.edit_text(text)
    else:
        await message.answer(text)


async def _send_pattern(message: Message, uid: int, edit: bool = False):
    patterns = [
        ([2, 4, 8, 16], 32, "هر جمله ×۲"),
        ([1, 1, 2, 3, 5], 8, "فیبوناچی"),
        ([3, 6, 9, 12], 15, "+۳"),
        ([100, 90, 80, 70], 60, "−۱۰"),
        ([1, 4, 9, 16], 25, "مربع اعداد"),
        ([2, 3, 5, 7, 11], 13, "اعداد اول"),
    ]
    seq, ans, hint = random.choice(patterns)
    _pending_puzzle[uid] = {"type": "pattern", "answers": [str(ans)]}
    shown = " ، ".join(str(x) for x in seq) + " ، ؟"
    text = f"🧩 <b>پازل الگو</b>\n\n{shown}\n\nعدد بعدی چیست؟"
    if edit:
        await message.edit_text(text)
    else:
        await message.answer(text)


@router.message(Command("puzzle", "پازل", "فکری"))
async def cmd_puzzle(message: Message):
    cd = check_game_cooldown(message.from_user.id)
    if cd:
        await message.answer(cd)
        return
    builder = InlineKeyboardBuilder()
    uid = message.from_user.id
    builder.button(text="🧩 الگو", callback_data=f"game:pattern:{uid}")
    builder.button(text="🧠 معما", callback_data=f"game:riddle:{uid}")
    builder.button(text="🔢 ریاضی", callback_data=f"game:math:{uid}")
    builder.button(text="🔤 به‌هم‌ریخته", callback_data=f"game:scramble:{uid}")
    builder.adjust(2)
    await message.answer("🧩 بازی فکری را انتخاب کن:", reply_markup=builder.as_markup())


@router.message(Command("riddle", "معما"))
async def cmd_riddle(message: Message):
    cd = check_game_cooldown(message.from_user.id)
    if cd:
        await message.answer(cd)
        return
    await _send_riddle(message, message.from_user.id)


@router.message(Command("mathquiz", "ریاضی", "هوش‌ریاضی"))
async def cmd_math(message: Message):
    cd = check_game_cooldown(message.from_user.id)
    if cd:
        await message.answer(cd)
        return
    await _send_math(message, message.from_user.id)


@router.message(Command("scramble", "به‌هم‌ریخته", "کلمه"))
async def cmd_scramble(message: Message):
    cd = check_game_cooldown(message.from_user.id)
    if cd:
        await message.answer(cd)
        return
    await _send_scramble(message, message.from_user.id)


class PuzzlePendingFilter(_AiogramFilter):
    async def __call__(self, message: Message) -> bool:
        if not message.text or message.text.startswith("/"):
            return False
        return message.from_user.id in _pending_puzzle


@router.message(PuzzlePendingFilter())
async def puzzle_answer(message: Message):
    """پاسخ پازل — فقط اگر pending باشد"""
    uid = message.from_user.id
    pending = _pending_puzzle.get(uid)
    if not pending:
        return
    text = (message.text or "").strip().lower()
    if text.startswith("/"):
        return
    answers = pending.get("answers") or []
    ok = any(text == a or text.replace("ي", "ی") == a.replace("ي", "ی") for a in answers)
    # عدد با فاصله
    if not ok and pending["type"] in ("math", "pattern"):
        ok = text.replace(" ", "") in answers
    del _pending_puzzle[uid]
    if ok:
        reward = await _reward(uid, random.randint(15, 40), random.randint(5, 12))
        await message.answer(f"✅ درست بود!\n{reward}")
    else:
        correct = answers[0] if answers else "?"
        await message.answer(f"❌ غلط. پاسخ درست: <b>{correct}</b>")
