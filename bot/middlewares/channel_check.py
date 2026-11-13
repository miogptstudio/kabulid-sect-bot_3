"""عضویت اجباری در کانال‌های مشخص‌شده"""
import logging
from typing import Any, Awaitable, Callable, Dict, List

from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.enums import ChatMemberStatus

from bot.config import ADMIN_IDS, REQUIRED_CHANNELS

logger = logging.getLogger(__name__)

# وضعیت‌های معتبر عضویت
_OK_STATUSES = {
    ChatMemberStatus.MEMBER,
    ChatMemberStatus.ADMINISTRATOR,
    ChatMemberStatus.CREATOR,
    ChatMemberStatus.RESTRICTED,
}


def _channels() -> List[str]:
    """لیست یوزرنیم کانال‌ها بدون @"""
    try:
        chs = list(REQUIRED_CHANNELS or [])
        return [c.strip().lstrip("@") for c in chs if c and str(c).strip()]
    except Exception:
        return ["miogptstudio", "shady_garden"]


async def _is_member(bot: Bot, chat_username: str, user_id: int) -> bool:
    try:
        member = await bot.get_chat_member(chat_id=f"@{chat_username}", user_id=user_id)
        return member.status in _OK_STATUSES
    except Exception as e:
        logger.error("Channel check failed for @%s user %s: %s", chat_username, user_id, e)
        # اگر ربات ادمین کانال نباشد، خطا می‌دهد — در این حالت False برمی‌گردانیم
        # تا کاربر پیام «ربات را ادمین کن» ببیند
        raise


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


class ChannelMembershipMiddleware(BaseMiddleware):
    """اجباری کردن عضویت در همه کانال‌های REQUIRED_CHANNELS"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        bot: Bot = data["bot"]
        user = None

        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            # اجازه بده دکمه «عضو شدم» همیشه کار کند
            if event.data == "check_channels":
                return await handler(event, data)

        if not user:
            return await handler(event, data)

        # ادمین‌های ربات معاف هستند
        if user.id in ADMIN_IDS:
            return await handler(event, data)

        channels = _channels()
        if not channels:
            return await handler(event, data)

        missing: List[str] = []
        check_errors: List[str] = []

        for uname in channels:
            try:
                ok = await _is_member(bot, uname, user.id)
                if not ok:
                    missing.append(uname)
            except Exception:
                check_errors.append(uname)

        if not missing and not check_errors:
            return await handler(event, data)

        # خطای دسترسی ربات به کانال (ربات ادمین نیست)
        if check_errors and not missing:
            text = (
                "⚠️ ربات فعلاً نمی‌تواند عضویت کانال را چک کند.\n"
                "مدیر باید ربات را <b>ادمین کانال</b> کند:\n\n"
                + "\n".join(f"👉 @{c}" for c in check_errors)
                + "\n\nاگر عضو هستی و باز این پیام را می‌بینی، به ادمین بگو."
            )
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.answer("خطا در بررسی کانال — ربات باید ادمین باشد", show_alert=True)
                try:
                    await event.message.answer(text)
                except Exception:
                    pass
            return

        # کاربر عضو بعضی/همه کانال‌ها نیست
        all_needed = list(dict.fromkeys(missing + check_errors))  # unique preserve order
        links = "\n".join(f"👉 https://t.me/{c}" for c in all_needed)
        text = (
            "⛔️ برای استفاده از ربات باید در <b>هر دو کانال</b> عضو باشی:\n\n"
            f"{links}\n\n"
            "بعد از عضویت روی دکمه «عضو شدم» بزن یا دوباره /start بفرست."
        )
        kb = _join_keyboard(all_needed)

        if isinstance(event, Message):
            await event.answer(text, reply_markup=kb)
        elif isinstance(event, CallbackQuery):
            await event.answer("اول باید عضو کانال‌ها بشی!", show_alert=True)
            try:
                await event.message.answer(text, reply_markup=kb)
            except Exception:
                pass
        return
