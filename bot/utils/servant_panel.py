from aiogram.types import FSInputFile
from aiogram.utils.keyboard import InlineKeyboardBuilder
from bot.servant_images import get_servant_image_by_id

def servant_keyboard(index: int):
    kb=InlineKeyboardBuilder()
    kb.button(text="🛒 خرید", callback_data=f"servbuy:{index}")
    kb.button(text="📋 وضعیت", callback_data=f"servstatus:{index}")
    kb.button(text="❤️ وفاداری", callback_data=f"servloyal:{index}")
    kb.button(text="🧘 پرورش", callback_data=f"servtrain:{index}")
    kb.button(text="💍 ازدواج", callback_data=f"servmarry:{index}")
    kb.button(text="⚔️ دوئل خدمتکار", callback_data=f"servduelguide:{index}")
    kb.button(text="⬅️ بازار", callback_data="servmarket")
    kb.adjust(2,2,2)
    return kb.as_markup()

def servant_image(index: int):
    p=get_servant_image_by_id(index)
    return FSInputFile(p) if p and p.exists() else None
