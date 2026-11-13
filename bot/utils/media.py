"""ارسال امن پنل — اگر عکس نباشد فقط متن می‌فرستد (بدون عکس رندوم)."""
from pathlib import Path
from aiogram.types import Message, FSInputFile
from services.portraits import panel_url


async def answer_panel(message: Message, kind: str, text: str, gender: str = "مرد", name: str = "panel", **kwargs):
    path = panel_url(kind, gender, name)
    if path and Path(path).is_file():
        try:
            return await message.answer_photo(FSInputFile(path), caption=text, **kwargs)
        except Exception:
            pass
    return await message.answer(text, **kwargs)


async def safe_answer_photo(message: Message, path: str | None, caption: str = "", **kwargs):
    """اگر path معتبر باشد عکس، وگرنه فقط متن."""
    if path and Path(str(path)).is_file():
        try:
            return await message.answer_photo(FSInputFile(str(path)), caption=caption, **kwargs)
        except Exception:
            pass
    return await message.answer(caption or "—", **kwargs)
