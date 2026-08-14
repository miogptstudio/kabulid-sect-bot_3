"""بارگذاری زبان کاربر در کش"""
from typing import Any, Awaitable, Callable, Dict
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery

class I18nLoadMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        user = None
        if isinstance(event, Message) and event.from_user:
            user = event.from_user
        elif isinstance(event, CallbackQuery) and event.from_user:
            user = event.from_user
        if user:
            try:
                from services.i18n import get_lang, set_lang, _lang_cache
                if user.id not in _lang_cache:
                    # lazy: default fa until /start or /lang
                    pass
            except Exception:
                pass
        return await handler(event, data)
