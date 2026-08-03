"""قطع خدمات هنگام زندان یا زمین تمرین"""
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

# دستوراتی که حتی در قفل مجازند
ALLOWED_PREFIXES = (
    "/start", "/help", "/commands", "/دستورات", "/راهنما", "/منو",
    "/trainstatus", "/trainclaim", "/train", "/تمرین", "/وضعیت‌تمرین", "/پایان‌تمرین", "/دریافت‌تمرین",
    "/prison", "/زندان", "/bail", "/وثیقه", "/آزادی‌زندان",
    "/version", "/نسخه", "/ping", "/تست", "/profile", "/me", "/پروفایل",
    "/rules", "/قوانین",
)


class ServiceLockMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        text = None
        user = None
        if isinstance(event, Message):
            user = event.from_user
            text = (event.text or event.caption or "").strip()
        elif isinstance(event, CallbackQuery):
            user = event.from_user
            text = (event.data or "").strip()

        if not user:
            return await handler(event, data)

        # اجازه دستورات سفید
        if text:
            low = text.lower()
            for p in ALLOWED_PREFIXES:
                if low.startswith(p.lower()):
                    return await handler(event, data)
            # دکمه‌های کیبورد تذهیب هم بلاک شوند مگر train
            if text in ("تذهیب کردن", "جمع آوری چی", "جمع‌آوری چی", "مدیتیت", "پروفایل"):
                if text == "پروفایل":
                    return await handler(event, data)

        try:
            from database.engine import async_session
            from database.crud import get_or_create_user
            from services.prison import check_prison_block
            async with async_session() as session:
                u = await get_or_create_user(
                    session, user.id, user.full_name, user.username
                )
                block = await check_prison_block(session, u)
                if block:
                    if isinstance(event, CallbackQuery):
                        await event.answer(block[:180], show_alert=True)
                        return None
                    if isinstance(event, Message):
                        await event.answer(block)
                        return None
        except Exception:
            pass

        return await handler(event, data)
