from __future__ import annotations

from aiogram import BaseMiddleware
from aiogram.types import CallbackQuery
from typing import Any, Awaitable, Callable


class PanelOwnerMiddleware(BaseMiddleware):
    """جلوگیری از کلیک بازیکن دیگر روی پنل/دکمههای شخصی.

    فقط callbackهایی که مالکیتشان در خود callback_data مشخص است بررسی میشوند.
    درخواستهای بین دو بازیکن (مثل دوئل) دست handler مربوطه را برای اعتبارسنجی
    کامل نگه میدارند.
    """

    # prefix -> index of owner telegram id after split(':')
    OWNER_INDEX = {
        "helpsec": 1,
        "building": 1, "buyq": 1, "bpage": 1, "shopback": 1, "buy": 1,
        "setlang": 1, "tame": 1, "release": 1, "awaken": 1,
        "setrace": 1, "setjob": 1, "take_mission": 1,
        "voidbuy": 1, "voidshow": 1, "voidlearn": 1,
        "suicide": 2,
        "hkcard": 1, "nardbot": 1, "nardonline": 1,
        "rps": 1,
        "activateblood": 1, "myblood": 1,
        "setgender": 1,
        "servmarket": 1, "servpage": 1, "servownpage": 1, "servmylist": 1,
        "servbuy": 1, "servstatus": 1, "servloyal": 1, "servtrain": 1,
        "servmarry": 1, "servduelguide": 1,
        "chars": 2,
    }

    # game:<kind>:<owner>
    GAME_OWNER_KINDS = {"rps", "dice", "nard", "casino", "chess", "hukum", "puzzlemenu",
                        "riddle", "math", "web", "pattern", "scramble", "guess"}

    async def __call__(self, handler: Callable[[CallbackQuery, dict[str, Any]], Awaitable[Any]],
                       event: CallbackQuery, data: dict[str, Any]) -> Any:
        if not isinstance(event, CallbackQuery) or not event.data or not event.from_user:
            return await handler(event, data)

        parts = event.data.split(":")
        prefix = parts[0]
        owner_index = self.OWNER_INDEX.get(prefix)

        if prefix == "game" and len(parts) >= 3 and parts[1] in self.GAME_OWNER_KINDS:
            owner_index = 2

        if owner_index is not None and len(parts) > owner_index:
            try:
                owner = int(parts[owner_index])
            except (TypeError, ValueError):
                owner = None
            if owner is not None and owner != event.from_user.id:
                try:
                    await event.answer("⛔ این پنل برای صاحبش است.", show_alert=True)
                except Exception:
                    pass
                return None

        return await handler(event, data)
