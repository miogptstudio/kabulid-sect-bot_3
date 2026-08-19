"""هندلر سیستم کاراکترها."""
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, FSInputFile, CallbackQuery
from aiogram.utils.keyboard import InlineKeyboardBuilder

from services import characters as chars
from database.engine import async_session
from database.crud import get_or_create_user
from services.economy import get_or_create_wallet

router = Router()


def character_list_keyboard(tg_id: int):
    kb = InlineKeyboardBuilder()
    bag = chars._owned.get(tg_id) or []
    for i, c in enumerate(bag[:12], 1):
        kb.button(text=f"🎴 {i}. {c.get('name','کاراکتر')[:18]}", callback_data=f"chars:view:{tg_id}:{i}")
    kb.button(text="🎲 کاراکتر جدید", callback_data=f"chars:pull:{tg_id}")
    kb.button(text="⭐ بهترین کاراکتر", callback_data=f"chars:best:{tg_id}")
    kb.button(text="📊 رتبهها", callback_data=f"chars:rates:{tg_id}")
    kb.button(text="⚔️ دوئل کاراکتر", callback_data=f"chars:duelguide:{tg_id}")
    kb.button(text="🔄 بروزرسانی لیست", callback_data=f"chars:list:{tg_id}")
    kb.adjust(2)
    return kb.as_markup()


def character_detail_keyboard(index: int, owner_id: int):
    kb = InlineKeyboardBuilder()
    kb.button(text="⬅️ لیست کاراکترها", callback_data=f"chars:list:{owner_id}")
    kb.button(text="🎲 کاراکتر جدید", callback_data=f"chars:pull:{owner_id}")
    kb.button(text="⭐ بهترین", callback_data=f"chars:best:{owner_id}")
    kb.button(text="🔀 ترکیب تکراری", callback_data=f"chars:merge:{owner_id}")
    kb.adjust(2, 2)
    return kb.as_markup()


def character_detail_text(card: dict, index: int) -> str:
    stars = "⭐" * max(1, int(card.get("stars") or 1))
    return (
        f"🎴 <b>پنل اختصاصی کاراکتر</b>\n\n"
        f"{card.get('emoji','🎭')} <b>{card.get('name','—')}</b> · شماره {index}\n"
        f"🏆 رتبه: <b>{card.get('rarity','معمولی')}</b> {stars}\n"
        f"⚔️ قدرت: <b>+{card.get('power',0):,}</b>\n"
        f"📈 قدرت پایه: {card.get('base_power',0):,}\n\n"
        f"📜 <b>توصیف:</b> {card.get('description') or chars.character_description(card.get('name',''))}\n\n"
        f"💠 این کاراکتر از سیستم شانسی به دست آمده و با تکرار، ستارههایش افزایش پیدا میکند.\n"
        f"🔹 هر ستاره قدرت نهایی را افزایش میدهد.\n"
        f"🔹 از قویترین ۳ کاراکتر برای محاسبه پاداش قدرت استفاده میشود.\n\n"
        f"/charduel برای دوئل کاراکتری · /tradechar برای معاوضه"
    )


@router.message(Command("charrates", "رتبهکاراکتر"))
async def cmd_rates(message: Message):
    await message.answer(chars.rarity_guide())


async def _pull_character(message: Message):
    async with async_session() as session:
        user = await get_or_create_user(
            session, message.from_user.id,
            message.from_user.full_name, message.from_user.username,
        )
        wallet = await get_or_create_wallet(session, user.id)
        cost = chars.PULL_COST_COINS
        if (wallet.coins or 0) < cost:
            await message.answer(f"🪙 سکه کافی نیست؛ نیاز: {cost}\nاز /dailycoin یا دوئل استفاده کن.")
            return
        ok, msg, card = chars.pull(message.from_user.id)
        if not ok:
            await message.answer(msg)
            return
        wallet.coins -= cost
        await session.commit()

    if card:
        try:
            from services.portraits import character_url
            await message.answer_photo(
                photo=character_url(card.get("name", "؟"), card.get("rarity", "معمولی")),
                caption=msg,
                reply_markup=character_list_keyboard(callback.from_user.id),
            )
            return
        except Exception:
            pass
    await message.answer(msg, reply_markup=character_list_keyboard(callback.from_user.id))


@router.message(Command("pullchar", "کاراکتر", "کاراکترشانسی", "gacha", "شانسی"))
async def cmd_pull(message: Message):
    await _pull_character(message)


@router.message(Command("mychars", "کاراکترها", "لیستکاراکتر"))
async def cmd_list(message: Message):
    text = chars.list_owned_indexed(message.from_user.id)
    await message.answer(text, reply_markup=character_list_keyboard(callback.from_user.id))


@router.message(Command("charinfo", "اطلاعاتکاراکتر", "پنلکاراکتر"))
async def cmd_char_info(message: Message):
    parts = (message.text or "").split()
    if len(parts) < 2:
        await message.answer("🎴 شماره کاراکتر را وارد کن. مثال: /charinfo 1")
        return
    try:
        idx = int(parts[1])
    except ValueError:
        await message.answer("❌ شماره کاراکتر باید عدد باشد.")
        return
    card = chars.get_char(message.from_user.id, idx)
    if not card:
        await message.answer("❌ این شماره کاراکتر وجود ندارد. /mychars")
        return
    try:
        from services.portraits import character_url
        await message.answer_photo(
            photo=character_url(card.get("name", "کاراکتر"), card.get("rarity", "معمولی")),
            caption=character_detail_text(card, idx),
            reply_markup=character_detail_keyboard(idx, message.from_user.id),
        )
    except Exception:
        await message.answer(character_detail_text(card, idx), reply_markup=character_detail_keyboard(idx, message.from_user.id))


@router.callback_query(F.data.startswith("chars:view:"))
async def cb_char_view(callback: CallbackQuery):
    await callback.answer()
    try:
        parts = callback.data.split(":")
        if len(parts) != 4 or int(parts[2]) != callback.from_user.id:
            await callback.answer("⛔ این پنل برای صاحبش است.", show_alert=True)
            return
        idx = int(parts[3])
    except Exception:
        await callback.message.answer("شماره کاراکتر نامعتبر است.")
        return
    card = chars.get_char(callback.from_user.id, idx)
    if not card:
        await callback.message.answer("❌ کاراکتر پیدا نشد. /mychars")
        return
    try:
        from services.portraits import character_url
        await callback.message.answer_photo(
            photo=character_url(card.get("name", "کاراکتر"), card.get("rarity", "معمولی")),
            caption=character_detail_text(card, idx),
            reply_markup=character_detail_keyboard(idx, callback.from_user.id),
        )
    except Exception:
        await callback.message.answer(character_detail_text(card, idx), reply_markup=character_detail_keyboard(idx, callback.from_user.id))


@router.callback_query(F.data.startswith("chars:merge:"))
async def cb_chars_merge(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) != 3 or int(parts[2]) != callback.from_user.id:
        await callback.answer("⛔ این پنل برای صاحبش است.", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer(chars.merge_duplicates(callback.from_user.id), reply_markup=character_list_keyboard(callback.from_user.id))


@router.message(Command("bestchar", "بهترینکاراکتر"))
async def cmd_best(message: Message):
    await message.answer(chars.best_char(message.from_user.id), reply_markup=character_list_keyboard(message.from_user.id))


@router.callback_query(F.data.startswith("chars:list:"))
async def cb_chars_list(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) != 3 or int(parts[2]) != callback.from_user.id:
        await callback.answer("⛔ این پنل برای صاحبش است.", show_alert=True)
        return
    text = chars.list_owned_indexed(callback.from_user.id)
    await callback.answer("لیست بروزرسانی شد")
    await callback.message.answer(text, reply_markup=character_list_keyboard(callback.from_user.id))


@router.callback_query(F.data.startswith("chars:pull:"))
async def cb_chars_pull(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) != 3 or int(parts[2]) != callback.from_user.id:
        await callback.answer("⛔ این پنل برای صاحبش است.", show_alert=True)
        return
    await callback.answer()
    await _pull_character(callback.message)


@router.callback_query(F.data.startswith("chars:best:"))
async def cb_chars_best(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) != 3 or int(parts[2]) != callback.from_user.id:
        await callback.answer("⛔ این پنل برای صاحبش است.", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer(chars.best_char(callback.from_user.id), reply_markup=character_list_keyboard(callback.from_user.id))


@router.callback_query(F.data.startswith("chars:rates:"))
async def cb_chars_rates(callback: CallbackQuery):
    parts = callback.data.split(":")
    if len(parts) != 3 or int(parts[2]) != callback.from_user.id:
        await callback.answer("⛔ این پنل برای صاحبش است.", show_alert=True)
        return
    await callback.answer()
    await callback.message.answer(chars.rarity_guide(), reply_markup=character_list_keyboard(callback.from_user.id))


@router.message(Command("tradechar", "معاوضهکاراکتر"))
async def cmd_trade_char(message: Message):
    parts = (message.text or "").split()
    target = None
    try:
        if message.reply_to_message and message.reply_to_message.from_user:
            target = message.reply_to_message.from_user.id
            if len(parts) < 3:
                await message.answer("ریپلای + /tradechar شماره_من شماره_او")
                return
            idx_a, idx_b = int(parts[1]), int(parts[2])
        else:
            if len(parts) < 4:
                await message.answer("فرمت: /tradechar آیدی_عددی شماره_من شماره_او")
                return
            target, idx_a, idx_b = int(parts[1]), int(parts[2]), int(parts[3])
    except ValueError:
        await message.answer("❌ شمارهها باید عدد باشند.")
        return
    ok, msg, _key = chars.propose_trade(message.from_user.id, target, idx_a, idx_b)
    await message.answer(msg)


@router.message(Command("accepttrade", "قبولمعاوضه"))
async def cmd_accept_trade(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("/accepttrade کلید")
        return
    await message.answer(chars.accept_trade(parts[1].strip(), message.from_user.id))


@router.message(Command("charduel", "دوئلکاراکتر"))
async def cmd_char_duel(message: Message):
    parts = (message.text or "").split()
    try:
        if message.reply_to_message and message.reply_to_message.from_user:
            target = message.reply_to_message.from_user.id
            if len(parts) < 3:
                await message.answer("ریپلای + /charduel شماره_من شماره_او")
                return
            idx_a, idx_b = int(parts[1]), int(parts[2])
        else:
            if len(parts) < 4:
                await message.answer("فرمت: /charduel آیدی شماره_من شماره_او")
                return
            target, idx_a, idx_b = int(parts[1]), int(parts[2]), int(parts[3])
    except ValueError:
        await message.answer("❌ شمارهها باید عدد باشند.")
        return
    ok, msg, _key = chars.propose_char_duel(message.from_user.id, target, idx_a, idx_b)
    await message.answer(msg)


@router.message(Command("acceptcharduel", "قبولدوئلکاراکتر"))
async def cmd_accept_cduel(message: Message):
    parts = (message.text or "").split(maxsplit=1)
    if len(parts) < 2:
        await message.answer("/acceptcharduel کلید")
        return
    await message.answer(chars.accept_char_duel(parts[1].strip(), message.from_user.id))


@router.message(Command("mergechar", "ترکیبکاراکتر", "ادغامکاراکتر"))
async def cmd_merge_char(message: Message):
    await message.answer(chars.merge_duplicates(message.from_user.id), reply_markup=character_list_keyboard(callback.from_user.id))


@router.callback_query(F.data.startswith("chars:duelguide:"))
async def cb_chars_duelguide(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer(
        "🎴 <b>دوئل کاراکترها</b>\\n\\n"
        "روی پیام حریف ریپلای کن و بنویس:\\n"
        "<code>/charduel شماره_من شماره_حریف</code>\\n\\n"
        "یا با آیدی حریف:\\n"
        "<code>/charduel آیدی شماره_من شماره_حریف</code>\\n\\n"
        "⚠️ قبل از ارسال، شماره و قدرت هر دو کاراکتر را بررسی کن."
    )
