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
        if isinstance(event, Message) and event.chat and event.message_id:
            orig = event.answer

            async def answer_with_reply(*args, **kwargs):
                if "reply_to_message_id" not in kwargs and "reply_parameters" not in kwargs:
                    kwargs["reply_to_message_id"] = event.message_id
                try:
                    return await orig(*args, **kwargs)
                except Exception:
                    # اگر ریپلای ممکن نبود، بدون ریپلای
                    kwargs.pop("reply_to_message_id", None)
                    return await orig(*args, **kwargs)

            event.answer = answer_with_reply  # type: ignore
        return await handler(event, data)
