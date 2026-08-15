"""هر پاسخ ربات به همان پیام دستور ریپلای شود"""
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message


class AutoReplyMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        if not isinstance(event, Message) or not event.chat or not event.message_id:
            return await handler(event, data)

        msg_id = event.message_id
        bot = data.get("bot")
        # بهجای تغییر event.answer از bot.send_message با reply استفاده میکنیم
        # با نگهداشتن answer اصلی و پچ امن
        orig = Message.answer

        async def bound_answer(self_msg, text=None, **kwargs):
            if "reply_to_message_id" not in kwargs and "reply_parameters" not in kwargs:
                kwargs["reply_to_message_id"] = self_msg.message_id
            try:
                return await orig(self_msg, text, **kwargs)
            except Exception:
                kwargs.pop("reply_to_message_id", None)
                kwargs.pop("reply_parameters", None)
                return await orig(self_msg, text, **kwargs)

        # پچ کلاس فقط برای این درخواست خطرناک است؛ فقط این instance:
        try:
            object.__setattr__(event, "answer", bound_answer.__get__(event, Message))
        except Exception:
            pass

        return await handler(event, data)
