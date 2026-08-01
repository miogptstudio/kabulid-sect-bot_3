import random
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.filters import Command
from aiogram.utils.keyboard import InlineKeyboardBuilder

from database.engine import async_session
from database.crud import get_or_create_user
from services.economy import get_or_create_wallet

router = Router()

# سنگ کاغذ قیچی در انتظار
_rps_pending: dict[int, dict] = {}


@router.message(Command("games", "بازی", "بازی‌ها"))
async def cmd_games_menu(message: Message):
    builder = InlineKeyboardBuilder()
    builder.button(text="✊ سنگ‌کاغذ‌قیچی", callback_data=f"game:rps:{message.from_user.id}")
    builder.button(text="🎲 تاس / تخته‌نرد", callback_data=f"game:dice:{message.from_user.id}")
    builder.button(text="🎰 کازینو", callback_data=f"game:casino:{message.from_user.id}")
    builder.button(text="♟️ شطرنج (نمایشی)", callback_data=f"game:chess:{message.from_user.id}")
    builder.button(text="🃏 حکم", callback_data=f"game:hukum:{message.from_user.id}")
    builder.button(text="🌐 باز کردن وب‌اپ", callback_data=f"game:web:{message.from_user.id}")
    builder.adjust(1)
    await message.answer(
        "🎮 <b>بازی‌ها</b>\n\n"
        "اینجا در چت بازی کن، یا از مینی‌اپ استفاده کن.\n"
        "دستورات مستقیم:\n"
        "/rps — سنگ کاغذ قیچی\n"
        "/dice — تاس\n"
        "/casino — کازینو (شرط سکه)\n"
        "/chess — صفحه شطرنج نمایشی",
        reply_markup=builder.as_markup(),
    )


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
    elif kind == "dice":
        d1, d2 = random.randint(1, 6), random.randint(1, 6)
        await callback.message.edit_text(
            f"🎲 <b>تاس تخته‌نرد</b>\n\n{d1} — {d2}\nجمع: {d1 + d2}"
        )
    elif kind == "casino":
        await callback.message.edit_text(
            "🎰 برای کازینو بنویس:\n/casino مبلغ\nمثال: /casino 20\n(حداقل ۱۰ سکه)"
        )
    elif kind == "chess":
        board = _chess_board_text()
        await callback.message.edit_text(
            f"♟️ <b>شطرنج (نمایشی)</b>\n\n<code>{board}</code>\n\n"
            f"نسخه کامل‌تر در وب‌اپ: .../webapp/games.html"
        )
    elif kind == "hukum":
        await callback.message.edit_text(
            "🃏 <b>حکم</b>\n\nبرای شروع: /hukum\nبا حریف: ریپلای + /hukumduel"
        )
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
    d1, d2 = random.randint(1, 6), random.randint(1, 6)
    await message.answer(f"🎲 تاس: <b>{d1}</b> — <b>{d2}</b>\nجمع: {d1 + d2}")


@router.message(Command("chess", "شطرنج"))
async def cmd_chess(message: Message):
    await message.answer(
        f"♟️ <b>شطرنج نمایشی</b>\n\n<code>{_chess_board_text()}</code>\n\n"
        f"برای صفحه تعاملی: وب‌اپ → games.html"
    )


@router.message(Command("casino", "کازینو"))
async def cmd_casino(message: Message):
    parts = (message.text or "").split()
    bet = 10
    if len(parts) >= 2:
        try:
            bet = int(parts[1])
        except ValueError:
            await message.answer("فرمت: /casino مبلغ\nمثال: /casino 20")
            return
    if bet < 10:
        await message.answer("حداقل شرط ۱۰ سکه است.")
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
    parts = (message.text or "").split()
    uid = message.from_user.id
    if uid not in _guess:
        _guess[uid] = random.randint(1, 50)
        await message.answer("🔢 عددی بین ۱ تا ۵۰ انتخاب شد. /guess عدد")
        return
    if len(parts) < 2:
        await message.answer("/guess عدد")
        return
    try:
        n = int(parts[1])
    except ValueError:
        await message.answer("عدد بفرست")
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
        await message.answer("🎉 درست! +۱۵ سکه")
    elif n < secret:
        await message.answer("بالاتر ⬆️")
    else:
        await message.answer("پایین‌تر ⬇️")


@router.message(Command("coinflip", "شیرخط"))
async def cmd_coin_flip(message: Message):
    parts = (message.text or "").split()
    pick = parts[1] if len(parts) > 1 else None
    if pick not in ("شیر", "خط"):
        await message.answer("/coinflip شیر یا /coinflip خط")
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
    trump = random.choice(SUITS)
    hand = [_draw_card() for _ in range(3)]
    table = _draw_card()
    builder = InlineKeyboardBuilder()
    builder.button(text="بازی کن 🃏", callback_data=f"hukumplay:{message.from_user.id}:{trump}")
    builder.adjust(1)
    await message.answer(
        f"🃏 <b>حکم</b>\n\nحکم این دست: <b>{trump}</b>\nکارت روی میز: {table}\nکارت‌های تو:\n"
        + "\n".join(f"• {c}" for c in hand),
        reply_markup=builder.as_markup(),
    )

@router.callback_query(F.data.startswith("hukumplay:"))
async def cb_hukum_play(callback: CallbackQuery):
    parts = callback.data.split(":")
    if callback.from_user.id != int(parts[1]):
        await callback.answer()
        return
    trump = parts[2] if len(parts) > 2 else "دل"
    if random.random() < 0.5:
        async with async_session() as session:
            user = await get_or_create_user(
                session, callback.from_user.id,
                callback.from_user.full_name, callback.from_user.username
            )
            w = await get_or_create_wallet(session, user.id)
            w.coins += 12
            await session.commit()
        await callback.message.edit_text(f"🃏 حکم: {trump}\nبرد! +۱۲ سکه 🎉")
    else:
        await callback.message.edit_text(f"🃏 حکم: {trump}\nباخت این دست.")
    await callback.answer()

@router.message(Command("hukumduel", "حکم‌دوئل"))
async def cmd_hukum_duel(message: Message):
    if not message.reply_to_message:
        await message.answer("روی حریف ریپلای کن: /hukumduel")
        return
    opp = message.reply_to_message.from_user
    if opp.id == message.from_user.id:
        await message.answer("با خودت نه.")
        return
    trump = random.choice(SUITS)
    builder = InlineKeyboardBuilder()
    builder.button(text="قبول حکم ✅", callback_data=f"hukumacc:{message.from_user.id}:{opp.id}:{trump}")
    await message.answer(
        f"🃏 چالش حکم از {message.from_user.full_name}\nحکم: <b>{trump}</b>\nفقط {opp.full_name} قبول کند.",
        reply_markup=builder.as_markup(),
    )

@router.callback_query(F.data.startswith("hukumacc:"))
async def cb_hukum_acc(callback: CallbackQuery):
    parts = callback.data.split(":")
    ch, opp, trump = int(parts[1]), int(parts[2]), parts[3]
    if callback.from_user.id != opp:
        await callback.answer()
        return
    winner = random.choice(["تو", "حریف"])
    await callback.message.edit_text(f"🃏 حکم {trump}\nبرنده: {winner}")
    await callback.answer()
