"""عضویت اجباری در کانال‌ها — بدون اسپم تکراری"""
from __future__ import annotations

import logging
import time
from typing import Any, Awaitable, Callable, Dict, List

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatMemberStatus

from bot.config import ADMIN_IDS, REQUIRED_CHANNELS

logger = logging.getLogger(__name__)

_OK_STATUSES = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.CREATOR,
    ChatMemberStatus.RESTRICTED,
}

# کاربرانی که اخیراً عضو تأیید شده‌اند (uid -> expiry unix)
_verified_until: Dict[int, float] = {}
# آخرین باری که به کاربر پیام «عضو شو» فرستاده شد (uid -> unix)
_last_warn_at: Dict[int, float] = {}

VERIFY_TTL_SEC = 6 * 3600       # ۶ ساعت کش عضویت (اعضا دوباره چک نمی‌شوند)
WARN_COOLDOWN_SEC = 8           # فقط ضد سیل پشت‌سرهم؛ با هر دستور پیام عضویت می‌آید


def _channels() -> List[str]:
    try:
        chs = list(REQUIRED_CHANNELS or [])
        return [c.strip().lstrip("@") for c in chs if c and str(c).strip()]
    except Exception:
        return ["miogptstudio", "shady_garden"]


async def _is_member(bot: Bot, chat_username: str, user_id: int) -> bool:
    member = await bot.get_chat_member(chat_id=f"@{chat_username}", user_id=user_id)
    return member.status in _OK_STATUSES


def _join_keyboard(missing: List[str]) -> InlineKeyboardMarkup:
    rows = []
    for uname in missing:
        rows.append([
            InlineKeyboardButton(
                text=f"📢 عضویت در @{uname}",
                url=f"https://t.me/{uname}",
            )
        ])
    rows.append([
        InlineKeyboardButton(text="✅ عضو شدم — بررسی دوباره", callback_data="check_channels")
    ])
    return InlineKeyboardMarkup(inline_keyboard=rows)


def mark_verified(user_id: int) -> None:
    _verified_until[user_id] = time.time() + VERIFY_TTL_SEC


def clear_verified(user_id: int) -> None:
    _verified_until.pop(user_id, None)


def _is_bot_related_message(message: Message, bot: Bot) -> bool:
    """فقط دستور واقعی ربات — نه چت عادی و نه هر ریپلای به ربات."""
    text = (message.text or message.caption or "").strip()
    if not text:
        return False

    # دستور با /
    if text.startswith("/"):
        return True

    # نرمال‌سازی دکمه/فارسی
    low = text.lower().replace("\u200c", "").replace("‌", "")
    for ch in ("👤", "🧘", "⚔️", "📊", "🏛", "🏪", "📜", "🎒", "🎁", "🌍", "📖", "⚙️", "🪙", "💰", " "):
        low = low.replace(ch, "")

    exact = {
        "پروفایل", "تزکیه", "تذهیب", "نبرد", "دوئل", "رتبه", "فرقه", "بازار",
        "ماموریت", "مأموریت", "کوله", "روزانه", "جهان", "راهنما", "بیشتر",
        "شروع", "منو", "کیفپول", "کیف", "خدمتکار", "خدمتکارها", "خدمتکاران",
        "کاراکتر", "پولدار", "پولدارترین", "ثروتمند", "richest", "leaders",
        "دستورات", "قوانین", "وضعیت", "قدرت", "فروشگاه", "آرنا", "جمعآوریچی",
        "جمعاور یچی", "تذهیبکردن",
    }
    # بدون فاصله
    low2 = "".join(low.split())
    if low2 in exact or low in exact:
        return True

    # پیام خیلی کوتاه که دقیقاً دستور است
    if len(text) <= 24:
        compact = text.lower().replace("‌", "").strip()
        for s in ("تزکیه", "تذهیب", "دوئل", "پروفایل", "فرقه", "فروشگاه", "روزانه",
                  "خدمتکار", "کاراکتر", "رتبه", "راهنما", "بازار", "جهان", "نبرد", "پولدار"):
            if compact == s or compact.startswith(s + " "):
                return True

    return False


class ChannelMembershipMiddleware(BaseMiddleware):
    """عضویت اجباری با کش و ضد اسپم — در گروه فقط روی دستورات ربات."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        bot: Bot = data["bot"]
        user = None
        is_callback = False

        if isinstance(event, Message):
            user = event.from_user
            try:
                chat_type = getattr(event.chat, "type", None)
            except Exception:
                chat_type = None
            # فقط وقتی پیام دستور/مربوط به ربات است چک کن (گروه و خصوصی)
            # چت عادی → هیچ پیام عضویت نده
            if not _is_bot_related_message(event, bot):
                return await handler(event, data)
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            is_callback = True
            if event.data == "check_channels":
                return await handler(event, data)
            # کال‌بک‌های ربات همیشه مربوط به ربات‌اند → چک عضویت انجام شود

        if not user:
            return await handler(event, data)

        if user.id in ADMIN_IDS:
            return await handler(event, data)
        # ادمین / معاون اضافه‌شده هم معاف از چک کانال
        try:
            from services.staff import has_perm, STAFF_DEPUTY
            if has_perm(user.id, STAFF_DEPUTY):
                return await handler(event, data)
        except Exception:
            pass

        channels = _channels()
        if not channels:
            return await handler(event, data)

        now = time.time()

        # اگر اخیراً تأیید شده، دیگر چک نکن
        if _verified_until.get(user.id, 0) > now:
            return await handler(event, data)

        missing: List[str] = []
        check_errors: List[str] = []

        for uname in channels:
            try:
                ok = await _is_member(bot, uname, user.id)
                if not ok:
                    missing.append(uname)
            except Exception as e:
                logger.error("Channel check failed @%s uid=%s: %s", uname, user.id, e)
                check_errors.append(uname)

        if not missing and not check_errors:
            mark_verified(user.id)
            return await handler(event, data)

        # ربات ادمین کانال نیست
        if check_errors and not missing:
            last = _last_warn_at.get(user.id, 0)
            if now - last < WARN_COOLDOWN_SEC:
                return
            _last_warn_at[user.id] = now
            text = (
                "⚠️ ربات فعلاً نمی‌تواند عضویت کانال را چک کند.\n"
                "مدیر باید ربات را <b>ادمین کانال</b> کند:\n\n"
                + "\n".join(f"👉 @{c}" for c in check_errors)
            )
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.answer("ربات باید ادمین کانال باشد", show_alert=True)
            return

        # کاربر عضو نیست — پیام اخطار با کول‌داون (ضد اسپم)
        all_needed = list(dict.fromkeys(missing + check_errors))
        last = _last_warn_at.get(user.id, 0)
        should_warn = (now - last) >= WARN_COOLDOWN_SEC

        # تشخیص گروه / خصوصی
        chat_type = None
        try:
            if isinstance(event, Message):
                chat_type = getattr(event.chat, "type", None)
            elif isinstance(event, CallbackQuery) and event.message:
                chat_type = getattr(event.message.chat, "type", None)
        except Exception:
            chat_type = None
        is_group = chat_type in ("group", "supergroup")

        if should_warn:
            _last_warn_at[user.id] = now
            links = "\n".join(f"👉 https://t.me/{c}" for c in all_needed)
            # لینک پیوی ربات
            bot_link = "ربات"
            try:
                me = await bot.get_me()
                if me.username:
                    bot_link = f"https://t.me/{me.username}"
            except Exception:
                pass

            if is_group:
                # در گروه: فقط بگو برو پیوی تأیید کن
                text = (
                    f"⛔️ {user.full_name or 'کاربر'} برای استفاده از دستورات بازی\n"
                    "باید اول در <b>چت خصوصی ربات</b> عضویت کانال را تأیید کنی.\n\n"
                    f"1️⃣ برو پیوی ربات: {bot_link}\n"
                    "2️⃣ عضو کانال‌ها شو و روی «عضو شدم» بزن\n"
                    "3️⃣ بعد دوباره همین دستور را بزن\n\n"
                    f"کانال‌ها:\n{links}"
                )
                kb = None
                try:
                    if isinstance(bot_link, str) and bot_link.startswith("http"):
                        from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
                        kb = InlineKeyboardMarkup(inline_keyboard=[
                            [InlineKeyboardButton(text="💬 رفتن به پیوی ربات", url=bot_link)],
                            *[
                                [InlineKeyboardButton(text=f"📢 @{c}", url=f"https://t.me/{c}")]
                                for c in all_needed
                            ],
                        ])
                except Exception:
                    kb = _join_keyboard(all_needed)
            else:
                text = (
                    "⛔️ برای استفاده از ربات باید در کانال‌های زیر عضو باشی:\n\n"
                    f"{links}\n\n"
                    "بعد از عضویت روی «عضو شدم» بزن."
                )
                kb = _join_keyboard(all_needed)

            if isinstance(event, Message):
                await event.answer(text, reply_markup=kb)
            elif isinstance(event, CallbackQuery):
                await event.answer(
                    "اول در پیوی ربات عضویت را تأیید کن" if is_group else "اول عضو کانال‌ها شو",
                    show_alert=True,
                )
                try:
                    await event.message.answer(text, reply_markup=kb)
                except Exception:
                    pass
        else:
            if is_callback:
                try:
                    await event.answer(
                        "اول در پیوی ربات تأیید کن" if is_group else "اول عضو کانال‌ها شو",
                        show_alert=False,
                    )
                except Exception:
                    pass

        return
