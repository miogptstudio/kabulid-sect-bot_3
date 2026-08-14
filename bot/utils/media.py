from aiogram.types import Message, URLInputFile
from services.portraits import panel_url

async def answer_panel(message: Message, kind: str, text: str, gender: str = "مرد", name: str = "panel", **kwargs):
    await message.answer_photo(URLInputFile(panel_url(kind, gender, name)), caption=text, **kwargs)
