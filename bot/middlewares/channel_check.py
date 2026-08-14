import logging
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware, Bot
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram.enums import ChatMemberStatus

from bot.config import ADMIN_IDS

logger = logging.getLogger(__name__)

CHANNEL_USERNAME = "kabulid_manhua"  # بدون @


class ChannelMembershipMiddleware(BaseMiddleware):
    """اجباری کردن عضویت در کانال"""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        bot: Bot = data["bot"]
        user = None

        if isinstance(event, Message):
            user = event.from_user
        elif isinstance(event, CallbackQuery):
            user = event.from_user

        if not user:
            return await handler(event, data)

        # ادمین ربات از چک معاف است
        if user.id in ADMIN_IDS:
            return await handler(event, data)

        try:
            member = await bot.get_chat_member(
                chat_id=f"@{CHANNEL_USERNAME}",
                user_id=user.id
            )
            if member.status in (
                ChatMemberStatus.MEMBER,
                ChatMemberStatus.ADMINISTRATOR,
                ChatMemberStatus.CREATOR,
                ChatMemberStatus.RESTRICTED,
            ):
                return await handler(event, data)
            # left / kicked
            logger.info("User %s not in channel: %s", user.id, member.status)
        except Exception as e:
            logger.error("Channel check failed: %s", e)
            # اگر ربات ادمین نباشد، ادمین‌های لیست را راه بده؛ بقیه پیام خطا بگیرند
            text = (
                "⚠️ ربات فعلاً نمی‌تواند عضویت کانال را چک کند.\n"
                "مدیر باید ربات را <b>ادمین کانال</b> کند:\n"
                f"👉 @{CHANNEL_USERNAME}\n\n"
                "اگر عضو هستی و باز این پیام را می‌بینی، به ادمین بگو."
            )
            if isinstance(event, Message):
                await event.answer(text)
            elif isinstance(event, CallbackQuery):
                await event.answer("خطا در بررسی کانال", show_alert=True)
            return

        text = (
            "⛔️ برای استفاده از ربات باید اول در کانال عضو بشی:\n\n"
            f"👉 https://t.me/{CHANNEL_USERNAME}\n\n"
            "بعد از عضویت، دوباره /start رو بزن."
        )
        if isinstance(event, Message):
            await event.answer(text)
        elif isinstance(event, CallbackQuery):
            await event.answer("اول باید عضو کانال بشی!", show_alert=True)
            try:
                await event.message.answer(text)
            except Exception:
                pass
        return
