"""کمک‌کننده‌های امن تلگرام — جلوگیری از TelegramBadRequest: no text to edit"""
from __future__ import annotations
from typing import Any
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup
from aiogram.exceptions import TelegramBadRequest


async def safe_edit_text(
    target: Message | CallbackQuery,
    text: str,
    *,
    reply_markup: InlineKeyboardMarkup | None = None,
    parse_mode: str | None = "HTML",
    disable_web_page_preview: bool = True,
) -> bool:
    """ویرایش امن پیام. اگر پیام متن نداشته باشد یا edit شکست بخورد، پیام جدید می‌فرستد."""
    msg: Message | None = None
    if isinstance(target, CallbackQuery):
        msg = target.message
        try:
            await target.answer()
        except Exception:
            pass
    elif isinstance(target, Message):
        msg = target
    if not msg:
        return False

    text = (text or "").strip() or "—"
    kwargs: dict[str, Any] = {"parse_mode": parse_mode, "disable_web_page_preview": disable_web_page_preview}
    if reply_markup is not None:
        kwargs["reply_markup"] = reply_markup

    # اگر پیام فقط مدیا/کپشن دارد، edit_text ممکن است خطا بدهد
    has_text = bool(getattr(msg, "text", None))
    has_caption = bool(getattr(msg, "caption", None))

    try:
        if has_text:
            await msg.edit_text(text[:4096], **kwargs)
            return True
        if has_caption:
            # فقط کپشن را عوض کن؛ کیبورد جدا
            cap_kwargs = {k: v for k, v in kwargs.items() if k != "disable_web_page_preview"}
            await msg.edit_caption(caption=text[:1024], **cap_kwargs)
            return True
        # پیام بدون متن — پیام جدید
        await msg.answer(text[:4096], **kwargs)
        return True
    except TelegramBadRequest as e:
        err = str(e).lower()
        if "message is not modified" in err:
            return True
        if "no text" in err or "there is no text" in err or "message to edit not found" in err:
            try:
                await msg.answer(text[:4096], parse_mode=parse_mode, reply_markup=reply_markup)
                return True
            except Exception:
                return False
        # سایر خطاها — تلاش برای پاسخ جدید
        try:
            await msg.answer(text[:4096], parse_mode=parse_mode, reply_markup=reply_markup)
            return True
        except Exception:
            return False
    except Exception:
        try:
            await msg.answer(text[:4096], parse_mode=parse_mode, reply_markup=reply_markup)
            return True
        except Exception:
            return False


async def safe_callback_answer(callback: CallbackQuery, text: str | None = None, show_alert: bool = False) -> None:
    try:
        if text:
            await callback.answer(text[:200], show_alert=show_alert)
        else:
            await callback.answer()
    except Exception:
        pass
