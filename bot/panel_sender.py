"""Helpers for sending local panel images with aiogram 3.x."""
from aiogram.types import FSInputFile
from .panel_images import get_panel_image

async def send_panel(message, panel: str, caption: str = "", gender: str | None = None, **kwargs):
    path = get_panel_image(panel, gender)
    if path is None or not path.exists():
        return await message.answer(caption, **kwargs)
    return await message.answer_photo(
        photo=FSInputFile(path),
        caption=caption,
        **kwargs,
    )
